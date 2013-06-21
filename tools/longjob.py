#!/usr/bin/env python
#
"""
Run a command, and send email when it is finished.

If the ~/.longjob directory exists, then we will also save a record of
the command to a sqlite database at ~/.longjob/job.db, so that we can
see which jobs are currently running and which jobs finished recently.
"""

#
# todo:
#
# ability to easily rerun past jobs
# easily remove old jobs from the table (in bulk)
#

from __future__ import absolute_import, division, with_statement

import collections
import getpass
import logging
import optparse
import os
import os.path
import select
import subprocess
import sys
import time
import traceback

from email.mime.text import MIMEText

# --------------------------------------------------------------------

DB_FILENAME='job.db'
DEFAULT_CONFIG_DIR=os.path.expanduser('~/.longjob')

def main():
    opts, args = getopts()

    if os.path.exists(opts.config_dir):
        logging.info("Using config dir {0} db {1}".
                     format(opts.config_dir, DB_FILENAME))
        table = JobTable(os.path.join(opts.config_dir, DB_FILENAME))
    else:
        logging.info("Config dir {0} does not exist".
                     format(opts.config_dir))
        table = None

    if opts.detail or opts.delete or opts.all:
        if table is None:
            raise ValueError("No longjob database")
        if opts.all:
            for job in table.get_all_jobs():
                print job.summary()
        else:
            for job_id in args:
                job = table.get_job(job_id)
                if opts.delete:
                    table.delete_job(job)
                else:
                    print job.report()
        return


    if len(args) == 0:
        if table is not None:
            for job in table.get_recent_jobs(7):
                print job.summary()
    else:
        Job.new_job(args, table=table, shell=opts.shell).run()

# --------------------------------------------------------------------

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--verbose',
                      action='store_true',
                      help='turn on debug logging')
    parser.add_option('--no_write',
                      action='store_true',
                      help='turn off all side effects')
    parser.add_option('-c', '--config_dir', '--dir',
                      help='location of the config directory',
                      default=DEFAULT_CONFIG_DIR)
    parser.add_option('-s', '--shell',
                      action='store_true',
                      help='use the shell to parse the command')
    parser.add_option('--delete',
                      action='store_true',
                      help='delete the given job ids')
    parser.add_option('--detail',
                      action='store_true',
                      help='show details of the given job ids')
    parser.add_option('--all',
                      action='store_true',
                      help='show all jobs in the database')

    opts, args = parser.parse_args()

    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if opts.no_write:
        Job.NO_WRITE    = True
        SqlDb.NO_WRITE  = True
        Mailer.NO_WRITE = True

    return (opts, args)

# --------------------------------------------------------------------

def is_non_string_sequence(obj):
    return (
        isinstance(obj, collections.Sequence)
        and not isinstance(obj, basestring))

def to_sequence(obj):
    return obj if is_non_string_sequence(obj) else (obj,)

# --------------------------------------------------------------------

class Mailer(object):
    """
    Mailer is a class for sending email.  Each Mailer object
    represents a single email.
    """
    SENDMAIL = '/usr/lib/sendmail'
    NO_WRITE = False

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
            if self.NO_WRITE:
                logging.info('NO WRITE: Would send via {0}:\n{1}'.
                             format(self.SENDMAIL, msg.as_string()))
                return
            logging.info("Sending mail via {0}".format(self.SENDMAIL))
            logging.debug(msg.as_string())
            pipe = os.popen("%s -t" % self.SENDMAIL, "w")
            pipe.write(msg.as_string())
            pipe.close()
        else:
            if self.NO_WRITE:
                logging.info('NO WRITE: Would send via smtplib:\n{0}'.
                             format(msg.as_string()))
                return
            logging.info("Sending mail via smtplib")
            logging.debug(msg.as_string())
            import smtplib
            s = smtplib.SMTP('localhost')
            s.sendmail(self.sender, self.to, msg.as_string())
            s.quit()

# --------------------------------------------------------------------

class Job(object):
    """
    A Job encompasses a command to run.  If given a JobTable, it will
    save a record of the command to that table.  After a command has
    finished, it will use the Mailer class to send an email to the user.
    """
    NO_WRITE = False

    NEVER_RUN = 'never_run'
    RUNNING   = 'running'
    FAILED    = 'failed'
    SUCCEEDED = 'succeeded'

    TIME_FORMAT = '%Y%m%d %H:%M:%S'

    # -----------------------
    # Constructors

    def __init__(self,
                 table           = None,
                 job_id          = None,
                 cmd             = None,
                 status          = NEVER_RUN,
                 start_time      = None,
                 end_time        = None,
                 rc              = -1,
                 stdout          = '',
                 stderr          = '',
                 shell           = False):
        """
        This initialize could be for an existing job or a new job that
        has never been run.
        """
        self.table      = table
        self.job_id     = job_id
        if isinstance(cmd, basestring):
            self.cmd    = cmd.split()
            self.strcmd = cmd
        else:
            self.cmd    = cmd
            self.strcmd = ' '.join(cmd)
        self.status     = status
        self.start_time = start_time
        self.end_time   = end_time
        self.rc         = rc
        self.stdout     = stdout
        self.stderr     = stderr
        self.shell      = shell

    @classmethod
    def new_job(cls, cmd, table=None, shell=False):
        """
        This is a constructor for a new job that has never been run.

        @param cmd: a command as accepted by Popen.  It should be a
        list, though a single string is also accepted.

        @param table: the JobTable to use

        @param shell: will be passed into Popen to tell it whether or
        not to use the shell to parse the command before running it.
        """
        obj = cls(cmd=cmd, table=table, shell=shell)
        obj.addtodb()
        return obj

    # -----------------------
    # Running jobs

    def run(self):
        """
        Run a job while updating its status in the JobTable (if
        necessary).  After the job completes, notify the user.  This
        method respects the NO_WRITE attribute.
        """
        self.start_time = time.localtime()
        self.status = self.RUNNING
        self.updatedb()

        # If we get a control-c, mark it as a failure
        import signal
        def handle(signum, frame):
            logging.error("Received SIGTERM (signum = {0}), marking "
                          "job as a failure".format(signum))
            self.status = self.FAILED
            self.stderr += 'Received SIGTERM'
            self._finish()
        signal.signal(signal.SIGTERM, handle)

        try:
            if self.NO_WRITE:
                logging.info("NO WRITE: {0}".format(self.strcmd))
                # in NO_WRITE mode, pretend we succeeded
                self.rc = 0
            else:
                self._run_capture_output()
        except:
            logging.error("Received exception, marking job as a failure")
            self.stderr += traceback.format_exc()
            raise
        finally:
            if self.rc == 0:
                self.status = self.SUCCEEDED
            else:
                self.status = self.FAILED
            self._finish()

        return self

    def _finish(self):
        """
        This method does the common work to clean up after the job
        completes, whether successful or not.  It saves the job to the
        database and sends mail.
        """
        self.end_time = time.localtime()
        self.updatedb()
        Mailer(subject=self.summary(),
               body=self.report()).send()
        logging.info("Finished")


    def _run_capture_output(self):
        """
        Run the command while saving stdout and stderr.  This does not
        respect the NO_WRITE attribute, it is assumed that the caller
        will already have confirmed that NO_WRITE is False before
        calling this method.
        """
        if self.shell:
            logging.info("Running (shell): {0}".format(self.strcmd))
            proc = subprocess.Popen(self.strcmd,
                                    shell=self.shell,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        else:
            logging.info("Running: {0}".format(self.strcmd))
            proc = subprocess.Popen(self.cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

        # We capture stdout and stderr, but we also output them to the
        # terminal.
        # http://stackoverflow.com/questions/12270645/can-you-make-a-python-subprocess-output-stdout-and-stderr-as-usual-but-also-cap
        while True:
            ret = select.select([proc.stdout.fileno(),
                                 proc.stderr.fileno()], [], [])
            for fd in ret[0]:
                if fd == proc.stdout.fileno():
                    read = proc.stdout.readline()
                    sys.stdout.write(read)
                    self.stdout += read
                if fd == proc.stderr.fileno():
                    read = proc.stderr.readline()
                    sys.stderr.write(read)
                    self.stderr += read
            if proc.poll() != None:
                break
        self.rc = proc.returncode

    # -----------------------
    # Time formatting

    @classmethod
    def _format_time(cls, time_struct):
        if time_struct is None:
            return 'NEVER'
        return time.strftime(cls.TIME_FORMAT, time_struct)

    @classmethod
    def _time_secs(cls, time_struct):
        if time_struct is None:
            return 0
        else:
            try:
                return time.mktime(time_struct)
            except OverflowError:
                return 0

    @property
    def start_time_str(self):
        return self._format_time(self.start_time)

    @property
    def end_time_str(self):
        return self._format_time(self.end_time)

    @property
    def start_time_secs(self):
        return self._time_secs(self.start_time)

    @property
    def end_time_secs(self):
        return self._time_secs(self.end_time)

    @property
    def duration(self):
        secs = self.end_time_secs - self.start_time_secs
        if secs < 0:
            return 'never finished'
        output = []
        for (num, name) in ((7 * 24 * 60 * 60, 'week'),
                            (    24 * 60 * 60, 'day'),
                            (         60 * 60, 'hr'),
                            (              60, 'min')):
            if secs > num:
                output.append('{0} {1}'.format(int(secs / num),
                                               name))
                secs = secs % num
        output.append('{0} {1}'.format(int(secs), 'sec'))
        return ' '.join(output)

    # -----------------------
    # DB updates

    def updatedb(self):
        if self.table is not None:
            self.table.update_job(self)

    def addtodb(self):
        if self.table is not None:
            self.job_id = self.table.add_job(self)
            logging.info("Got job id {0}".format(self.job_id))

    # -----------------------
    # Text summaries

    def summary(self):
        """
        This appears as the subject of emails and this is the line we
        print when summarizing the JobTable.
        """
        return ('Job id {self.job_id:3} {self.status:10} '
                'time {self.start_time_str}-{self.end_time_str} '
                '({self.duration}) {self.strcmd}'.
                format(self=self))

    def report(self):
        """
        This appears as the body of emails.
        """
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

class SqlDb(object):
    """
    SqlDb is a wrapper around a sqlite database with some added
    convenience methods.
    """
    NO_WRITE = False

    def __init__(self, filename):
        import sqlite3
        self.filename = filename
        self.conn = sqlite3.connect(filename)
        self.cursor = self.conn.cursor()

    def __repr__(self):
        return ('{cn}({fn!r})'.format(cn=type(self).__name__,
                                      fn=self.filename))

    def execute_always(self, *args, **kwargs):
        """
        Run a command without checking NO_WRITE.  Use this for
        non-state changing commands, like queries.  Or use this for
        state changing commands after you have already checked
        NO_WRITE, but in that case you need to call commit yourself.
        """
        # http://docs.python.org/2/library/sqlite3.html
        # # This is the qmark style:
        # cur.execute("insert into people values (?, ?)", (who, age))
        #
        # # And this is the named style:
        # cur.execute("select * from people where name_last=:who and age=:age", {"who": who, "age": age})
        logging.info("SqlDb Executing: '{0}' '{1}'".format(args, kwargs))
        return self.cursor.execute(*args, **kwargs)

    def execute(self, *args, **kwargs):
        """
        Run state changing commands, if allowed by NO_WRITE, then
        commit the changes.
        """
        if self.NO_WRITE:
            logging.info("SqlDb NO WRITE: would run '{0}' '{1}'".
                         format(args, kwargs))
            logging.info("SqlDb NO_WRITE: would commit")
        else:
            self.execute_always(*args, **kwargs)
            logging.info("SqlDb commit")
            self.commit()

    def commit(self):
        self.conn.commit()

    def fetchall(self):
        return self.cursor.fetchall()

    def query_one_row_always(self, *args, **kwargs):
        self.execute_always(*args, **kwargs)
        return self.fetch_one_row()

    def fetch_one_row(self):
        rows = self.cursor.fetchall()
        if len(rows) < 1:
            raise ValueError("No matching rows")
        elif len(rows) > 1:
            raise ValueError("Too many matching rows")
        else:
            return rows[0]

    def fetch_one_value(self):
        return self.fetch_one_row()[0]

    def query_one_value_always(self, *args, **kwargs):
        self.query_one_row_always(*args, **kwargs)[0]

    @property
    def lastrowid(self):
        return self.cursor.lastrowid

# --------------------------------------------------------------------

class SqlTable(object):
    """
    SqlTable is a wrapper around a table whose rows are supposed
    to mimic the objects of a particular Python class.  The column
    names of the table must be attributes of the Python object,
    such that getattr(obj, col_name) returns the value to put in
    that column (with the correct type).

    When an object is written to the table, it will be given a
    unique id, which will be attached to the object from then on.
    """

    def __init__(self,
                 filename,
                 table,
                 columns,
                 key_col,
                 obj_constructor):
        """
        @param filename: the filename of the sqlite database

        @param table: the name of the table in the sqlite database

        @param columns: a list or tuple of the table's columns and
        their sql types, not including the key.

        Should be a list of lists having this form:
          [
            [ table_column_name1, sql_type1 ],
            [ table_column_name2, sql_type2 ],
            [ table_column_name3, sql_type3 ]
          ]

        @param key_col: the name of the key column

        @param obj_constructor: a function which takes each of the
        column names as keyword arguments and produces the desired
        Python object.
        """
        self.db = SqlDb(filename)
        self.table     = table
        self.columns   = columns
        self.key_col   = key_col
        self.obj_ctor  = obj_constructor
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
        self.db.execute("SELECT name "
                        "FROM   sqlite_master "
                        "WHERE  type = 'table' "
                        "  AND  name = '{0}';".format(self.table))
        matches = self.db.fetchall()
        if len(matches) > 0:
            return
        self.db.execute("CREATE TABLE jobs ( "
                        "job_id INTEGER PRIMARY KEY, {0});".
                        format(', '.join('{0} {1}'.format(ci[0], ci[1])
                                         for ci in self.columns)))

    def add_obj(self, obj):
        # http://stackoverflow.com/questions/6242756/how-to-retrieve-inserted-id-after-inserting-row-in-sqlite-using-python
        self.db.execute("INSERT INTO {0} ({1}) VALUES ({2});".
                        format(self.table,
                               ', '.join(ci[0] for ci in self.columns),
                               ', '.join('?' for ci in self.columns)),
                        [getattr(obj, ci[0]) for ci in self.columns])
        return self.db.lastrowid

    def update_obj(self, obj):
        self.db.execute("UPDATE {0} SET {1} WHERE {2} = ?;".
                        format(self.table,
                               ', '.join('{0} = ?'.format(ci[0])
                                         for ci in self.columns),
                               self.key_col),
                        [getattr(obj, ci[0]) for ci in self.columns] +
                        [getattr(obj, self.key_col)])

    def delete_obj(self, obj):
        # Would be nice if we returned 1 if the object existed and was
        # deleted and 0 if there was no row with this id.
        self.db.execute("DELETE FROM {0} WHERE {1} = ?;".
                        format(self.table,
                               self.key_col),
                        [getattr(obj, self.key_col)])

    def get_obj(self, key):
        return self._row_to_obj(self.db.query_one_row_always(
                "SELECT {cols}, {key_col} "
                "FROM {table} "
                "WHERE {key_col} = {key};".
                format(key_col=self.key_col,
                       cols=', '.join(ci[0] for ci in self.columns),
                       table=self.table,
                       key=key)))

    def get_objs(self, where='', *args):
        self.db.execute_always(
            "SELECT {cols}, {key_col} "
            "FROM {table} {where};".
            format(key_col=self.key_col,
                   cols=', '.join(ci[0] for ci in self.columns),
                   table=self.table,
                   where=where),
            *args)
        return [self._row_to_obj(r) for r in self.db.fetchall()]

    def _row_to_obj(self, row):
        kwargs = dict((col_info[0], val)
                      for (val, col_info) in zip(row, self.columns))
        kwargs[self.key_col] = row[-1]
        logging.debug(kwargs)
        return self.obj_ctor(**kwargs)

# --------------------------------------------------------------------

class DbJob(object):
    """
    A class for translating between a Job object and a row in our
    JobTable
    """

    STATUS_IDS = (Job.NEVER_RUN, Job.RUNNING, Job.FAILED, Job.SUCCEEDED)

    def __init__(self, job):
        self.job_id     = job.job_id
        self.command    = job.strcmd
        self.status     = self.STATUS_IDS.index(job.status)
        self.start_time = job.start_time_secs
        self.end_time   = job.end_time_secs
        self.returncode = job.rc
        self.stdout     = job.stdout
        self.stderr     = job.stderr
        self.shell      = bool(job.shell)

    @classmethod
    def make_job(cls, job_id, command, status, start_time, end_time,
                 returncode, stdout, stderr, shell):
        return Job(job_id     = job_id,
                   cmd        = command.split(),
                   status     = cls.STATUS_IDS[status],
                   start_time = time.localtime(start_time),
                   end_time   = time.localtime(end_time),
                   rc         = returncode,
                   stdout     = stdout,
                   stderr     = stderr,
                   shell      = bool(shell))

    @classmethod
    def status_name_to_id(cls, *statuses):
        return [cls.STATUS_IDS.index(s) for s in statuses]

# --------------------------------------------------------------------

class JobTable(object):
    """
    This is a wrapper around a SqlTable for a table whose rows
    correspond specifically to Job objects (using DbJob as a wrapper)

    We *have* a SqlTable, instead of *being* (deriving from / subclassing)
    a SqlTable (we use composition rather than inheritance).  That's
    because we want to present a different API to the world, one which
    is aware that the objects are jobs.
    """

    def __init__(self, filename):
        self.table = SqlTable(
            filename,
            table='jobs',
            columns=(('command',    'TEXT'),
                     ('status',     'INTEGER'),
                     ('start_time', 'INTEGER'),
                     ('end_time',   'INTEGER'),
                     ('returncode', 'INTEGER'),
                     ('stdout',     'TEXT'),
                     ('stderr',     'TEXT'),
                     ('shell',      'INTEGER'),
                     ),
            key_col='job_id',
            obj_constructor=DbJob.make_job)

    def add_job(self, job):
        return self.table.add_obj(DbJob(job))

    def get_job(self, job_id):
        return self.table.get_obj(job_id)

    def update_job(self, job):
        self.table.update_obj(DbJob(job))

    @classmethod
    def get_since(cls, since):
        '''
        Return a SQL clause for selecting jobs that started recently
        (within the last <since> days)

        @param since: number of days ago
        '''
        if since is None:
            return ''
        else:
            return ('AND (start_time >= {0} OR start_time <= 0)'.
                    format(time.time() - since * 24 * 60 * 60))

    def get_all_jobs(self):
        return self.table.get_objs()

    def get_running_jobs(self):
        return self.table.get_objs('WHERE status IN (?)',
                                   DbJob.status_name_to_id(Job.RUNNING))

    def get_incomplete_jobs(self, since=None):
        return self.table.get_objs('WHERE status NOT IN (?, ?) {0}'.
                                   format(self.get_since(since)),
                                   DbJob.status_name_to_id(Job.SUCCEEDED,
                                                           Job.RUNNING))

    def get_succeeded_jobs(self, since=None):
        return self.table.get_objs('WHERE status IN (?) {0}'.
                                   format(self.get_since(since)),
                                   DbJob.status_name_to_id(Job.SUCCEEDED))

    def get_recent_jobs(self, since=None):
        """
        Return recent jobs in what we guess would be the most natural
        order (most important first): running jobs, then failed jobs,
        then successful jobs.
        """
        return (self.get_running_jobs() +
                self.get_incomplete_jobs(since) +
                self.get_succeeded_jobs(since))

    def delete_job(self, job):
        # In a more pure world, we might wrap the job as a DbJob
        # before passing it to the SqlTable.  But we know that it's
        # only going to use the job_id and DbJob doesn't need to do
        # any translation on the job_id, so just pass the Job directly
        # and avoid the overhead of wrapping it.
        if job.job_id is None:
            raise AssertionError("Can't delete job with no job id: {0}".
                                 format(job.summary()))
        print "Deleting job {0}".format(job.job_id)
        logging.info("Job to delete: {0}".format(job.summary()))
        return self.table.delete_obj(job)

# --------------------------------------------------------------------

if __name__ == "__main__":
    main()

