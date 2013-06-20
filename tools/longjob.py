#!/usr/bin/env python
#
"""
Run a job, and send email when it is finished.
"""

#
# todo:
#
# save all jobs and their status to a sqlite database at ~/.longjob/job.db
# allow querying this db to see the status of jobs
# easily rerun failed jobs
#

from __future__ import absolute_import, division, with_statement

import collections
import getpass
import logging
import optparse
import os
import os.path
import subprocess
import time

from email.mime.text import MIMEText

# --------------------------------------------------------------------

def main():
    args = getopts()

    result = Job(args).run()
    Mailer(subject=result.summary(), body=result.report()).send()

# --------------------------------------------------------------------

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--verbose',
                      help='turn on debug logging',
                      action='store_true')
    parser.add_option('--no_write',
                      help='turn off all side effects',
                      action='store_true')
    opts, args = parser.parse_args()

    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if opts.no_write:
        Job.NO_WRITE = True

    return args

# --------------------------------------------------------------------

def is_non_string_sequence(obj):
    return (
        isinstance(obj, collections.Sequence)
        and not isinstance(obj, basestring))

def to_sequence(obj):
    return obj if is_non_string_sequence(obj) else (obj,)

# --------------------------------------------------------------------

class Mailer(object):
    SENDMAIL = '/usr/lib/sendmail'

    def __init__(self,
                 to=None,
                 subject='',
                 body='',
                 sender=None):
        self.to      = to_sequence(to if to is not None
                                   else getpass.getuser())
        self.subject = subject
        self.body    = body
        self.sender  = (sender if sender is not None
                        else getpass.getuser())
        self.use_sendmail = True

    def __repr__(self):
        strform = ('{cn}('
                   + '\n{pd} '.join('{0:10} = {{self.{0}!r}}'.format(name)
                                    for name in ('sender', 'to',
                                                 'subject', 'body'))
                   + ')')
        return strform.format(cn=type(self).__name__,
                              pd=' ' * len(type(self).__name__),
                              self=self)

    def send(self):
        # Create a text/plain message
        msg = MIMEText(self.body)
        msg['Subject'] = self.subject
        msg['From']    = self.sender
        msg['To']      = ','.join(self.to)

        if os.path.exists(self.SENDMAIL):
            if Job.NO_WRITE:
                logging.info('NO WRITE: Would send via {0}:\n{1}'.
                             format(self.SENDMAIL, msg.as_string()))
                return
            logging.info("Sending mail via {0}".format(self.SENDMAIL))
            pipe = os.popen("%s -t" % self.SENDMAIL, "w")
            pipe.write(msg.as_string())
            pipe.close()
        else:
            if Job.NO_WRITE:
                logging.info('NO WRITE: Would send via smtplib:\n{0}'.
                             format(msg.as_string()))
                return
            logging.info("Sending mail via smtplib")
            import smtplib
            s = smtplib.SMTP('localhost')
            s.sendmail(self.sender, self.to, msg.as_string())
            s.quit()

# --------------------------------------------------------------------

class Job(object):
    NO_WRITE = False

    NEVER_RUN = 'never_run'
    RUNNING   = 'running'
    FAILED    = 'failed'
    SUCCEEDED = 'succeeded'

    TIME_FORMAT = '%Y%m%d %H:%M:%S'

    def __init__(self, cmd):
        if isinstance(cmd, basestring):
            self.cmd    = cmd.split()
            self.strcmd = cmd
        else:
            self.cmd    = cmd
            self.strcmd = ' '.join(cmd)
        self.status = self.NEVER_RUN
        self.rc     = None
        self.stdout = None
        self.stderr = None
        self.start_time = None
        self.end_time   = None

    def run(self):
        #if self.NO_WRITE:
        #    logging.info("NO WRITE: {0}".format(self.strcmd))
        #    return self

        logging.info("Running:  {0}".format(self.strcmd))
        process = subprocess.Popen(self.cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        self.start_time = time.localtime()
        self.status = self.RUNNING
        (self.stdout, self.stderr) = process.communicate()
        self.end_time = time.localtime()
        self.rc = process.returncode
        if process.returncode == 0:
            self.status = self.SUCCEEDED
        else:
            self.status = self.FAILED
        logging.info("Finished")
        return self

    @property
    def finished(self):
        return self.status in (self.FAILED, self.SUCCEEDED)

    @property
    def duration(self):
        if not self.finished:
            return 'never_run'
        secs = time.mktime(self.end_time) - time.mktime(self.start_time)
        output = []
        for (num, name) in ((24 * 60 * 60, 'day'),
                            (60 * 60,      'hr'),
                            (60,           'min')):
            if secs > num:
                output.append('{0} {1}'.format(int(secs / num),
                                               name))
                secs = secs % num
        output.append('{0} {1}'.format(secs, 'sec'))
        return ' '.join(output)

    def _format_time(self, this_time):
        if not self.finished:
            return None
        return time.strftime(self.TIME_FORMAT, this_time)

    @property
    def start_time_str(self):
        return self._format_time(self.start_time)

    @property
    def end_time_str(self):
        return self._format_time(self.end_time)

    def summary(self):
        return 'Job {0}'.format(self.status)

    def report(self):
        return ('Command:  {self.strcmd}\n'
                'Started:  {self.start_time_str}\n'
                'End:      {self.end_time_str} ({self.duration})\n'
                'Status:   {self.status} (rc = {self.rc})\n'
                '-----------------------------------------------\n'
                'Stdout:\n\n'
                '{self.stdout}\n'
                '-----------------------------------------------\n'
                'Stderr:\n\n'
                '{self.stderr}\n'
                '-----------------------------------------------\n'
                .format(self=self))

# --------------------------------------------------------------------

class JobTable(object):
    def __init__(self, filename):
        import sqlite3

        # http://docs.python.org/2/library/sqlite3.html
        # # This is the qmark style:
        # cur.execute("insert into people values (?, ?)", (who, age))
        #
        # # And this is the named style:
        # cur.execute("select * from people where name_last=:who and age=:age", {"who": who, "age": age})

        self.conn = sqlite3.connect(filename)
        self.cursor = self.conn.cursor()
        self._create_table_if_necessary()

    def _create_table_if_necessary(self):
        # http://stackoverflow.com/questions/508627/auto-increment-in-sqlite-problem-with-python
        #
        # CREATE TABLE t1( a INTEGER PRIMARY KEY, b INTEGER ); With this table, the statement
        #
        # To create keys that are unique over the lifetime of the
        # table, add the AUTOINCREMENT keyword to the INTEGER PRIMARY
        # KEY declaration.
        #
        # http://stackoverflow.com/questions/305378/get-list-of-tables-db-schema-dump-etc-in-sqlite-databases
        #
        # con = sqlite3.connect('database.db')
        # cursor = con.cursor()
        # cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        # print(cursor.fetchall())
        pass

    def add_job(self, job):
        # http://stackoverflow.com/questions/6242756/how-to-retrieve-inserted-id-after-inserting-row-in-sqlite-using-python
        self.cursor.execute("INSERT INTO {0} () VALUES (?, ?)", ())
        return self.cursor

    def update_job(self, job):
        pass

    def get_job(self, job):
        pass

    def get_all_jobs(self):
        pass

# --------------------------------------------------------------------

if __name__ == "__main__":
    main()

