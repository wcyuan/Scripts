#!/usr/bin/env python
#
"""
Run a job, and send email when it is finished.
"""

#
# todo:
#
# rerun failed jobs
# print all jobs ever
# clean up the table
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

    if len(args) == 0:
        if table is not None:
            for job in table.get_recent_jobs(7):
                print job.summary()
    else:
        result = Job.new_job(args, table=table).run()
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
    parser.add_option('-d', '--config_dir', '--dir',
                      help='location of the config directory',
                      default=DEFAULT_CONFIG_DIR)
    opts, args = parser.parse_args()

    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if opts.no_write:
        Job.NO_WRITE = True

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

    _status_ids = (NEVER_RUN, RUNNING, FAILED, SUCCEEDED)

    TIME_FORMAT = '%Y%m%d %H:%M:%S'

    def __init__(self,
                 cmd             = None,
                 strcmd          = None,
                 table           = None,
                 status          = None,
                 status_id       = None,
                 rc              = -1,
                 stdout          = '',
                 stderr          = '',
                 start_time      = None,
                 start_time_secs = None,
                 end_time        = None,
                 end_time_secs   = None,
                 job_id          = None):

        if cmd is None:
            if strcmd is None:
                raise ValueError("No command provided")
            else:
                cmd = strcmd
        if isinstance(cmd, basestring):
            self.cmd    = cmd.split()
            self.strcmd = cmd
        else:
            self.cmd    = cmd
            self.strcmd = ' '.join(cmd)
        self.status     = (status if status is not None
                           else self.status_id_to_name(status_id)
                           if status_id is not None else self.NEVER_RUN)
        self.rc         = rc
        self.stdout     = stdout
        self.stderr     = stderr
        self.start_time = (start_time if start_time is not None
                           else time.localtime(start_time_secs)
                           if start_time_secs is not None
                           else None)
        self.end_time   = (end_time if end_time is not None
                           else time.localtime(end_time_secs)
                           if end_time_secs is not None
                           else None)
        self.table      = table
        self.job_id     = job_id

    @classmethod
    def new_job(cls, cmd, table=None):
        obj = cls(cmd=cmd, table=table)
        obj.addtodb()
        return obj

    def run(self):
        if self.NO_WRITE:
            logging.info("NO WRITE: {0}".format(self.strcmd))
            process = None
        else:
            logging.info("Running:  {0}".format(self.strcmd))
            process = subprocess.Popen(self.cmd,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        self.start_time = time.localtime()
        self.status = self.RUNNING
        self.updatedb()
        if self.NO_WRITE:
            self.status = self.SUCCEEDED
            self.rc = 0
            self.stdout = ''
            self.stderr = ''
        else:
            (self.stdout, self.stderr) = process.communicate()
            self.rc = process.returncode
        self.end_time = time.localtime()
        if self.rc == 0:
            self.status = self.SUCCEEDED
        else:
            self.status = self.FAILED
        self.updatedb()
        logging.info("Finished")
        return self

    @property
    def status_id(self):
        return self.status_name_to_id(self.status)

    @classmethod
    def status_name_to_id(cls, status_name):
        return cls._status_ids.index(status_name)

    @classmethod
    def status_id_to_name(cls, status_id):
        return cls._status_ids[status_id]

    @property
    def finished(self):
        return self.status in (self.FAILED, self.SUCCEEDED)

    @property
    def duration(self):
        if not self.finished:
            return 'never_run'
        secs = self.end_time_secs - self.start_time_secs
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
            return ''
        return time.strftime(self.TIME_FORMAT, this_time)

    @property
    def start_time_str(self):
        return self._format_time(self.start_time)

    @property
    def end_time_str(self):
        return self._format_time(self.end_time)

    @property
    def start_time_secs(self):
        if self.start_time is None:
            return -1
        else:
            return time.mktime(self.start_time)

    @property
    def end_time_secs(self):
        if self.end_time is None:
            return -1
        else:
            return time.mktime(self.end_time)

    def updatedb(self):
        if self.table is not None:
            self.table.update_job(self)

    def addtodb(self):
        if self.table is not None:
            self.job_id = self.table.add_job(self)
            logging.info("Got job id {0}".format(self.job_id))

    def summary(self):
        return ('Job id {self.job_id} {self.status} '
                'time {self.start_time_str}-{self.end_time_str} '
                '{self.strcmd}'.
                format(self=self))

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

class SqlDb(object):
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
        Run state changing commands, if allowed by NO_WRITE
        """
        if Job.NO_WRITE:
            logging.info("SqlDb NO WRITE: would run '{0}' '{1}'".
                         format(args, kwargs))
        else:
            self.execute_always(*args, **kwargs)
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
        if len(rows) != 1:
            raise ValueError("Too many matching rows")
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
    def __init__(self, filename,
                 obj_constructor, columns,
                 table, key_col, key_attr):
        """
        @param obj_constructor: this is a function which takes each of
        the object_attributes as keyword arguments and returns an
        instance of that object.

        @param columns: a mapping from the table's columns to the
        object's attributes and the table's sql types.  Should be a
        list of lists having this form:
          [
            [ table_column_name1, object_attribute_name1, sql_type1 ],
            [ table_column_name2, object_attribute_name2, sql_type2 ],
            [ table_column_name3, object_attribute_name3, sql_type3 ]
          ]
        """
        self.db = SqlDb(filename)
        self.obj_ctor  = obj_constructor
        self.columns   = columns
        self.table     = table
        self.key_col   = key_col
        self.key_attr  = key_attr
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
                        format(', '.join('{0} {1}'.format(ci[0], ci[2])
                                         for ci in self.columns)))

    def add_obj(self, obj):
        # http://stackoverflow.com/questions/6242756/how-to-retrieve-inserted-id-after-inserting-row-in-sqlite-using-python
        self.db.execute("INSERT INTO {0} ({1}) VALUES ({2});".
                        format(self.table,
                               ', '.join(ci[0] for ci in self.columns),
                               ', '.join('?' for ci in self.columns)),
                        [getattr(obj, ci[1]) for ci in self.columns])
        return self.db.lastrowid

    def update_obj(self, obj):
        self.db.execute("UPDATE {0} SET {1} WHERE {2} = ?;".
                        format(self.table,
                               ', '.join('{0} = ?'.format(ci[0])
                                         for ci in self.columns),
                               self.key_col),
                        [getattr(obj, ci[1]) for ci in self.columns] +
                        [getattr(obj, self.key_attr)])

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
        kwargs = dict((col_info[1], val)
                      for (val, col_info) in zip(row, self.columns))
        kwargs[self.key_attr] = row[-1]
        logging.debug(kwargs)
        return self.obj_ctor(**kwargs)

# --------------------------------------------------------------------

class JobTable(object):
    def __init__(self, filename):
        self.table = SqlTable(
            filename,
            obj_constructor=Job,
            columns=(('command',    'strcmd',          'TEXT'),
                     ('status',     'status_id',       'INTEGER'),
                     ('start_time', 'start_time_secs', 'INTEGER'),
                     ('end_time',   'end_time_secs',   'INTEGER'),
                     ('returncode', 'rc',              'INTEGER'),
                     ('stdout',     'stdout',          'TEXT'),
                     ('stderr',     'stderr',          'TEXT'),
                     ),
            table='jobs',
            key_col='job_id',
            key_attr='job_id')

    def add_job(self, job):
        return self.table.add_obj(job)

    def get_job(self, job_id):
        return self.table.get_obj(job_id)

    def update_job(self, job):
        self.table.update_obj(job)

    @classmethod
    def get_since(cls, since):
        '''
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
                                   [Job.status_name_to_id(s)
                                    for s in (Job.RUNNING,)])

    def get_incomplete_jobs(self, since=None):
        return self.table.get_objs('WHERE status NOT IN (?, ?) {0}'.
                                   format(self.get_since(since)),
                                   [Job.status_name_to_id(s)
                                    for s in (Job.SUCCEEDED, Job.RUNNING)])

    def get_succeeded_jobs(self, since=None):
        return self.table.get_objs('WHERE status IN (?) {0}'.
                                   format(self.get_since(since)),
                                   [Job.status_name_to_id(s)
                                    for s in (Job.SUCCEEDED,)])

    def get_recent_jobs(self, since=None):
        return (self.get_running_jobs() +
                self.get_incomplete_jobs(since) +
                self.get_succeeded_jobs(since))

# --------------------------------------------------------------------

if __name__ == "__main__":
    main()

