#!/usr/bin/env python
#
"""
Run a command, and send email when it is finished.

If the ~/.longjob directory exists, then we will also save a record of
the command to a sqlite database at ~/.longjob/job.db, so that we can
see which jobs are currently running and which jobs finished recently.

Run doctests with:
  python -m doctest -v  longjob.py
"""

#
# todo:
#
# when displaying a job summary for a job that was run from a
#   template, just show the template name and the arguments (unless
#   the user asks for the full command)
# list all runs of a particular template
# job chains:
#    after one job has finished running, run another (if succeeded)
#    continue a job chain from the last failed link
# templated job chains
#

from __future__ import absolute_import, division, with_statement

import collections
import getpass
import itertools
import logging
import optparse
import os
import os.path
import select
import socket
import string
import subprocess
import sys
import time
import traceback

from email.mime.text import MIMEText

# --------------------------------------------------------------------

DB_FILENAME = 'job.db'
DEFAULT_CONFIG_DIR = os.path.expanduser('~/.longjob')

logging.basicConfig(format='%(asctime)-15s %(levelname)-5s %(message)s')

def main():
    """
    The main function.  Most of the logic is in process_args
    """
    opts, args = getopts()
    process_args(opts, args)

def process_args(opts, args):
    """
    Handle the different script arguments
    """

    tpl_table = TemplateTable.get_table(opts.config_dir)
    if opts.templates:
        if tpl_table is None:
            raise ValueError("No longjob database")
        for tpl in tpl_table.get_all_templates():
            print tpl.desc()
        return

    if opts.create_template is not None:
        if tpl_table is None:
            raise ValueError("No longjob database")
        tpl_table.add_template(opts.create_template, ' '.join(args))
        return

    if opts.remove_template is not None:
        if tpl_table is None:
            raise ValueError("No longjob database")
        tpl_table.delete_template(
            tpl_table.get_template_by_id(opts.remove_template))
        return

    if opts.rename_template is not None:
        if tpl_table is None:
            raise ValueError("No longjob database")
        tpl_table.rename(
            tpl_table.get_template(opts.rename_template).template_id,
            ' '.join(args))
        return

    if opts.template_runs is not None:
        if tpl_table is None:
            raise ValueError("No longjob database")
        template = tpl_table.get_template(opts.template_runs)
        raise NotImplementedError()
        return

    table = JobTable.get_table(opts.config_dir)

    if opts.detail or opts.delete or opts.all:
        if table is None:
            raise ValueError("No longjob database")
        if opts.all:
            for job in table.get_all_jobs():
                print job.summary()
        else:
            for job_id in unrange(uncomma(args)):
                job = table.get_job(job_id)
                if opts.delete:
                    table.delete_job(job)
                else:
                    print job.report()
        return

    if (opts.rerun or opts.redo or opts.redolast):
        if table is None:
            raise ValueError("No longjob database")
        job_id = (opts.rerun
                  if opts.rerun is not None
                  else opts.redo if opts.redo is not None
                  else table.get_most_recent_job_id())
        job = table.get_job(job_id)
        new_job_id = None
        if opts.redo or opts.redolast:
            new_job_id = job_id
            table.delete_job(job)
        Job.new_job(job.cmd, table=table, shell=job.shell,
                    job_id=new_job_id,
                    template_id=job.template_id,
                    template_args=job.template_args).run()
        return

    if len(args) == 0:
        if table is not None:
            for job in table.get_recent_jobs(7):
                print job.summary()
    elif opts.from_template:
        if tpl_table is None:
            raise ValueError("No longjob database")
        template = tpl_table.get_template(opts.from_template)
        cmd = template.eval(args)
        Job.new_job(cmd, table=table, shell=opts.shell,
                    template_id=template.template_id,
                    template_args=args).run()
    else:
        Job.new_job(args, table=table, shell=opts.shell).run()

# --------------------------------------------------------------------

def getopts(argv=None):
    """
    Parse the command line
    """
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
    parser.add_option('--delete', '--rm',
                      action='store_true',
                      help='delete the given job ids')
    parser.add_option('--detail', '--details',
                      action='store_true',
                      help='show details of the given job ids')
    parser.add_option('--all', '-a',
                      action='store_true',
                      help='show all jobs in the database')
    parser.add_option('--rerun',
                      help='rerun a particular job')
    parser.add_option('--redo',
                      help='rerun a particular job, replacing the old record')
    parser.add_option('--redolast',
                      action='store_true',
                      help='rerun the last job, replacing the old record')
    parser.add_option('--create_template',
                      help='Create a new job template')
    parser.add_option('--from_template',
                      help='Run a templated job')
    parser.add_option('--remove_template',
                      help='Remove a job template')
    parser.add_option('--rename_template',
                      type=int,
                      help='Rename a job template')
    parser.add_option('--templates',
                      action='store_true',
                      help='List all job templates')
    parser.add_option('--template_runs',
                      help='List all runs of this template')

    parser.disable_interspersed_args()

    opts, args = parser.parse_args(argv)

    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if opts.no_write:
        Job.NO_WRITE    = True
        SqlDb.NO_WRITE  = True
        Mailer.NO_WRITE = True

    if (sum(int(opt is not None)
            for opt in (opts.rerun, opts.redo, opts.redolast)) > 1):
        raise ValueError("May only specify one of rerun, redo, and redolast")

    return (opts, args)

# --------------------------------------------------------------------

def apply_list(job_ids, cond, func):
    """
    Apply a function to each element of a list, if the element matches
    a condition, then flatten the list.
    """
    return itertools.chain.from_iterable(func(j) if cond(j) else (j,)
                                         for j in job_ids)

def uncomma(job_ids):
    """
    >>> list(uncomma(['a', 'b,c', 'd', 'e,f']))
    ['a', 'b', 'c', 'd', 'e', 'f']
    """
    return apply_list(job_ids,
                      lambda j: j.find(',') >= 0,
                      lambda j: j.split(','))

def unrange(job_ids):
    """
    >>> list(unrange(['1', '2-4', '5', '6-9']))
    ['1', 2, 3, 4, '5', 6, 7, 8, 9]
    """
    def parse_range(job_range):
        """
        Given a string like '2-4' return a generator that results in [2, 3, 4]
        """
        (start, stop) = job_range.split('-')
        return xrange(int(start), int(stop)+1)

    return apply_list(job_ids,
                      lambda j: j.find('-') >= 0,
                      parse_range)

def is_non_string_sequence(obj):
    """
    Return true if the argument is a sequence, but is not a string.
    """
    return (
        isinstance(obj, collections.Sequence)
        and not isinstance(obj, basestring))

def to_sequence(obj):
    """
    Turn the argument into a sequence.  If the argument is a
    non-string sequence, return it, otherwise return a one-element
    tuple with that element.
    """
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
                 recv=None,
                 subject='',
                 body='',
                 sender=None):
        self.recv    = to_sequence(recv if recv is not None
                                   else getpass.getuser())
        self.subject = subject
        self.body    = body
        self.sender  = (sender if sender is not None
                        else getpass.getuser())
        self.use_sendmail = True

    def __repr__(self):
        strform = ('{cn}('
                   + '\n{pd} '.join('{0:10} = {{self.{0}!r}}'.format(name)
                                    for name in ('sender', 'recv',
                                                 'subject', 'body'))
                   + ')')
        return strform.format(cn=type(self).__name__,
                              pd=' ' * len(type(self).__name__),
                              self=self)

    def send(self):
        """
        Create and send the mail
        """
        # Create a text/plain message
        msg = MIMEText(self.body)
        msg['Subject'] = self.subject
        msg['From']    = self.sender
        msg['To']      = ','.join(self.recv)

        if os.path.exists(self.SENDMAIL):
            if self.NO_WRITE:
                logging.info('NO WRITE: Would send via %s:\n%s',
                             self.SENDMAIL, msg.as_string())
                return
            logging.info("Sending mail via %s", self.SENDMAIL)
            logging.debug(msg.as_string())
            pipe = os.popen("%s -t" % self.SENDMAIL, "w")
            pipe.write(msg.as_string())
            pipe.close()
        else:
            if self.NO_WRITE:
                logging.info('NO WRITE: Would send via smtplib:\n%s',
                             msg.as_string())
                return
            logging.info("Sending mail via smtplib")
            logging.debug(msg.as_string())
            import smtplib
            smtp = smtplib.SMTP('localhost')
            smtp.sendmail(self.sender, self.recv, msg.as_string())
            smtp.quit()

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
                 returncode      = -1,
                 stdout          = '',
                 stderr          = '',
                 shell           = False,
                 host            = None,
                 template_id     = None,
                 template_args   = None):
        """
        This initialize could be for an existing job or a new job that
        has never been run.
        """
        self.table         = table
        self.job_id        = job_id
        if isinstance(cmd, basestring):
            self.cmd       = cmd.split()
            self.strcmd    = cmd
        else:
            self.cmd       = cmd
            self.strcmd    = ' '.join(cmd)
        self.status        = status
        self.start_time    = start_time
        self.end_time      = end_time
        self.returncode    = returncode
        self.stdout        = stdout
        self.stderr        = stderr
        self.shell         = shell
        self.host          = host
        self.template_id   = template_id
        self.template_args = template_args

    @classmethod
    def new_job(cls, cmd, table=None, shell=False,
                job_id=None, template_id=None, template_args=None):
        """
        This is a constructor for a new job that has never been run.

        @param cmd: a command as accepted by Popen.  It should be a
        list, though a single string is also accepted.

        @param table: the JobTable to use

        @param shell: will be passed into Popen to tell it whether or
        not to use the shell to parse the command before running it.
        """
        obj = cls(cmd=cmd, table=table, shell=shell, template_id=template_id,
                  template_args=template_args)
        obj.addtodb(job_id=job_id)
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
        # http://stackoverflow.com/questions/4271740/how-can-i-use-python-to-get-the-system-name
        self.host = socket.getfqdn()
        self.updatedb()

        # If we get a control-c, mark it as a failure
        import signal
        def handle(signum, frame):
            """
            Mark a job as a failure.  Should only be called on a SIGTERM
            """
            logging.error("Received SIGTERM (signum = %s), marking "
                          "job as a failure", signum)
            self.status = self.FAILED
            self.stderr += 'Received SIGTERM'
            self._finish()
        signal.signal(signal.SIGTERM, handle)

        try:
            if self.NO_WRITE:
                logging.info("NO WRITE: %s", self.strcmd)
                # in NO_WRITE mode, pretend we succeeded
                self.returncode = 0
            else:
                self._run_capture_output()
        except:
            logging.error("Received exception, marking job as a failure")
            self.stderr += traceback.format_exc()
            raise
        finally:
            if self.returncode == 0:
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
        Mailer(subject='[longjob] {0}'.format(self.summary()),
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
            logging.info("Running (shell): %s", self.strcmd)
            proc = subprocess.Popen(self.strcmd,
                                    shell=self.shell,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        else:
            logging.info("Running: %s", self.strcmd)
            proc = subprocess.Popen(self.cmd,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

        # We capture stdout and stderr, but we also output them to the
        # terminal.
        # http://stackoverflow.com/questions/12270645/can-you-make-a-python-subprocess-output-stdout-and-stderr-as-usual-but-also-cap
        while True:
            ret = select.select([proc.stdout.fileno(),
                                 proc.stderr.fileno()], [], [])
            for fdesc in ret[0]:
                if fdesc == proc.stdout.fileno():
                    read = proc.stdout.readline()
                    sys.stdout.write(read)
                    self.stdout += read
                if fdesc == proc.stderr.fileno():
                    read = proc.stderr.readline()
                    sys.stderr.write(read)
                    self.stderr += read
            self.updatedb()
            if proc.poll() != None:
                break
        self.returncode = proc.returncode

    # -----------------------
    # Time formatting

    @classmethod
    def _format_time(cls, time_struct):
        """
        Return the time_struct formatted with TIME_FORMAT
        """
        if time_struct is None:
            return 'NEVER'
        return time.strftime(cls.TIME_FORMAT, time_struct)

    @classmethod
    def _time_secs(cls, time_struct):
        """
        Return the time_struct as seconds since the epoch
        """
        if time_struct is None:
            return 0
        else:
            try:
                return time.mktime(time_struct)
            except OverflowError:
                return 0

    @property
    def start_time_str(self):
        """
        Return a string version of the start time
        """
        return self._format_time(self.start_time)

    @property
    def end_time_str(self):
        """
        Return a string version of the end time
        """
        return self._format_time(self.end_time)

    @property
    def start_time_secs(self):
        """
        Return the number of seconds from the epoch to the start time
        """
        return self._time_secs(self.start_time)

    @property
    def end_time_secs(self):
        """
        Return the number of seconds from the epoch to the end time
        """
        return self._time_secs(self.end_time)

    @property
    def duration(self):
        """
        Return the duration of the job as a human readable string
        """
        secs = self.end_time_secs - self.start_time_secs
        if secs < 0:
            return '-'
        output = []
        for (num, name) in ((7 * 24 * 60 * 60, 'wk'),
                            (    24 * 60 * 60, 'd'),
                            (         60 * 60, 'h'),
                            (              60, 'm')):
            if secs > num:
                output.append('{0}{1}'.format(int(secs / num),
                                              name))
                secs = secs % num
        output.append('{0}{1}'.format(int(secs), 's'))
        return ''.join(output)

    @property
    def shorthost(self):
        """
        Return the hostname to the first dot
        """
        try:
            dot = self.host.index('.')
        except AttributeError:
            # In case self.host is None
            return self.host
        except ValueError:
            # In case self.host does not have a '.' in it
            return self.host
        return self.host[:dot]

    # -----------------------
    # DB updates

    def updatedb(self):
        """
        Update this job's information in the database
        """
        if self.table is not None:
            self.table.update_job(self)

    def addtodb(self, job_id):
        """
        Add this job to the database
        """
        if self.table is not None:
            self.job_id = self.table.add_job(self, job_id=job_id)
            logging.info("Got job id %s", self.job_id)

    # -----------------------
    # Text summaries

    def summary(self):
        """
        This appears as the subject of emails and this is the line we
        print when summarizing the JobTable.
        """
        return ('{self.job_id:3} {stat} '
                '{start_time} '
                '({self.duration:9}) {self.shorthost:10} {self.strcmd}'.
                format(self=self,
                       stat=self.status[:3],
                       start_time=time.strftime('%m/%d %H:%M',
                                                self.start_time)))

    def report(self):
        """
        This appears as the body of emails.
        """
        return ('Command:  {self.strcmd}\n'
                'Started:  {self.start_time_str}\n'
                'End:      {self.end_time_str} ({self.duration})\n'
                'Status:   {self.status} (rc = {self.returncode})\n'
                'Template: id {self.template_id} args {self.template_args}\n'
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

    DATABASES = {}

    @classmethod
    def get_db(cls, filename):
        abspath = os.path.abspath(filename)
        if abspath not in cls.DATABASES:
            cls.DATABASES[abspath] = cls(abspath)
        return cls.DATABASES[abspath]

    def __init__(self, filename):
        import sqlite3
        self.filename = filename
        self.conn = sqlite3.connect(filename)
        self.cursor = self.conn.cursor()
        self.conn.text_factory = str

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
        logging.info("SqlDb Executing: '%s' '%s'", args, kwargs)
        return self.cursor.execute(*args, **kwargs)

    def execute(self, *args, **kwargs):
        """
        Run state changing commands, if allowed by NO_WRITE, then
        commit the changes.
        """
        if self.NO_WRITE:
            logging.info("SqlDb NO WRITE: would run '%s' '%s'",
                         args, kwargs)
            logging.info("SqlDb NO_WRITE: would commit")
        else:
            self.execute_always(*args, **kwargs)
            logging.info("SqlDb commit")
            self.commit()

    def commit(self):
        """
        Commit the transaction
        """
        self.conn.commit()

    def fetchall(self):
        """
        Fetch all rows
        """
        return self.cursor.fetchall()

    def query_one_row_always(self, *args, **kwargs):
        """
        Run a query that returns only one row.  Run the query even in
        no_write mode.  Throws an error if the query returns more than
        one row.
        """
        self.execute_always(*args, **kwargs)
        return self.fetch_one_row()

    def fetch_one_row(self):
        """
        Get the data from a query that returns only one row.  Throws
        an error if the query returns more than one row.
        """
        rows = self.cursor.fetchall()
        if len(rows) < 1:
            raise ValueError("No matching rows")
        elif len(rows) > 1:
            raise ValueError("Too many matching rows")
        else:
            return rows[0]

    def fetch_one_value(self):
        """
        Get the data from a query that returns only one value.  Does
        not throw an error if the query returns more than one value
        (multiple columns in the same row), but does not throw an
        error if the query returns more than one row
        """
        return self.fetch_one_row()[0]

    def query_one_value_always(self, *args, **kwargs):
        """
        Run a query that returns only one value.  Run the query even
        in no_write mode.  Throws an error if the query returns more
        than one row, but if the query returns more than one value
        (multiple columns in the same row), just returns the first
        value.
        """
        return self.query_one_row_always(*args, **kwargs)[0]

    @property
    def lastrowid(self):
        """
        The id of the last row that was added
        """
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
        self.sdb       = SqlDb.get_db(filename)
        self.table     = table
        self.columns   = columns
        self.key_col   = key_col
        self.obj_ctor  = obj_constructor
        self._create_table_if_necessary()

    def _create_table_if_necessary(self):
        """
        Create a table that matches this object, if it doesn't already
        exist.  If a table with this name already exists, add any
        missing columns.
        """
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
        self.sdb.execute_always("SELECT name "
                                "FROM   sqlite_master "
                                "WHERE  type = 'table' "
                                "  AND  name = '{0}';".format(self.table))
        matches = self.sdb.fetchall()
        if len(matches) > 0:
            # http://stackoverflow.com/questions/604939/how-can-i-get-the-list-of-a-columns-in-a-table-for-a-sqlite-database
            self.sdb.execute_always("pragma table_info({0})".
                                    format(self.table))
            existing = dict((ci[1], ci[2]) for ci in self.sdb.fetchall())
            for colinfo in self.columns:
                if colinfo[0] not in existing:
                    # http://stackoverflow.com/questions/4253804/insert-new-column-into-table-in-sqlite
                    self.sdb.execute("ALTER TABLE {0} ADD {1} {2}".
                                     format(self.table, colinfo[0], colinfo[1]))
            return
        self.sdb.execute("CREATE TABLE {0} ( "
                         "{1} INTEGER PRIMARY KEY, {2});".
                         format(self.table,
                                self.key_col,
                                ', '.join('{0} {1}'.format(ci[0], ci[1])
                                          for ci in self.columns)))

    def add_obj(self, obj, key_value=None):
        """
        Add an object as a row in the table
        """
        # http://stackoverflow.com/questions/6242756/how-to-retrieve-inserted-id-after-inserting-row-in-sqlite-using-python
        values = [(ci[0], getattr(obj, ci[0])) for ci in self.columns]
        if key_value is not None:
            values.insert(0, (self.key_col, key_value))
        self.sdb.execute("INSERT INTO {0} ({1}) VALUES ({2});".
                         format(self.table,
                                ', '.join(pair[0] for pair in values),
                                ', '.join('?' for pair in values)),
                         [pair[1] for pair in values])
        return self.sdb.lastrowid

    def update_obj(self, obj):
        """
        Update a row in the table to match the current state of the object
        """
        return self.update_obj_fields(
            getattr(obj, self.key_col),
            [(ci[0], getattr(obj, ci[0])) for ci in self.columns])

    def update_obj_fields(self, key, fld_val_pairs):
        """
        Update the specified fields for given a row in the table

        @param fld_val_pairs: a list of (field, value) pairs.  Must be
        traversable multiple times.
        """
        self.sdb.execute("UPDATE {0} SET {1} WHERE {2} = ?;".
                         format(self.table,
                                ', '.join('{0} = ?'.format(fld)
                                          for (fld, _) in fld_val_pairs),
                                self.key_col),
                         [val for (_, val) in fld_val_pairs] +
                         [key])

    def delete_obj(self, obj):
        """
        Delete the row in the table that matches the given object
        """
        # Would be nice if we returned 1 if the object existed and was
        # deleted and 0 if there was no row with this id.
        self.sdb.execute("DELETE FROM {0} WHERE {1} = ?;".
                         format(self.table,
                                self.key_col),
                         [getattr(obj, self.key_col)])

    def get_obj(self, key):
        """
        Get the row in the table that matches the given keys, and
        return it as a new object.
        """
        return self._row_to_obj(self.sdb.query_one_row_always(
                "SELECT {cols}, {key_col} "
                "FROM {table} "
                "WHERE {key_col} = {key};".
                format(key_col=self.key_col,
                       cols=', '.join(ci[0] for ci in self.columns),
                       table=self.table,
                       key=key)))

    def get_objs(self, where='', *args):
        """
        Get the rows in the table that match the given where clause,
        and return them as new objects
        """
        self.sdb.execute_always(
            "SELECT {cols}, {key_col} "
            "FROM {table} {where};".
            format(key_col=self.key_col,
                   cols=', '.join(ci[0] for ci in self.columns),
                   table=self.table,
                   where=where),
            *args)
        return [self._row_to_obj(r) for r in self.sdb.fetchall()]

    def _row_to_obj(self, row):
        """
        Creates a new object that matches the given row in the table.
        """
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
        """
        Given a Job object, translates that into the corresponding
        fields of the JobTable sql table.  Handles the conversion of
        all fields from python types to the desired sql types.
        """
        self.job_id        = job.job_id
        self.command       = job.strcmd
        self.status        = self.STATUS_IDS.index(job.status)
        self.start_time    = job.start_time_secs
        self.end_time      = job.end_time_secs
        self.returncode    = job.returncode
        self.stdout        = job.stdout
        self.stderr        = job.stderr
        self.shell         = bool(job.shell)
        self.host          = job.host
        self.template_id   = job.template_id
        self.template_args = (job.template_args
                              if job.template_args is None
                              else ' '.join(job.template_args))

    @classmethod
    def make_job(cls, job_id, command, status, start_time, end_time,
                 returncode, stdout, stderr, shell, host, template_id,
                 template_args):
        """
        Given the fields of a row in the JobTable table, return a Job
        object.  Handles the conversion of all rows from sql types to
        the desired python types.
        """
        return Job(job_id        = job_id,
                   cmd           = command.split(),
                   status        = cls.STATUS_IDS[status],
                   start_time    = time.localtime(start_time),
                   end_time      = time.localtime(end_time),
                   returncode    = returncode,
                   stdout        = stdout,
                   stderr        = stderr,
                   shell         = bool(shell),
                   host          = host,
                   template_id   = template_id,
                   template_args = (template_args
                                    if template_args is None
                                    else template_args.split()))

    @classmethod
    def status_name_to_id(cls, *statuses):
        """
        A helper function that translates a Job STATUS to an integer
        that we store in the database
        """
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
            columns=(('command',       'TEXT'),
                     ('status',        'INTEGER'),
                     ('start_time',    'INTEGER'),
                     ('end_time',      'INTEGER'),
                     ('returncode',    'INTEGER'),
                     ('stdout',        'TEXT'),
                     ('stderr',        'TEXT'),
                     ('shell',         'INTEGER'),
                     ('host',          'TEXT'),
                     ('template_id',   'INTEGER'),
                     ('template_args', 'TEXT'),
                     ),
            key_col='job_id',
            obj_constructor=DbJob.make_job)

    @classmethod
    def get_table(cls, config_dir=DEFAULT_CONFIG_DIR):
        if os.path.exists(config_dir):
            logging.info("Using config dir %s db %s",
                         config_dir, DB_FILENAME)
            return cls(os.path.join(config_dir, DB_FILENAME))
        else:
            logging.info("Config dir %s does not exist", config_dir)
            return None


    def add_job(self, job, job_id=None):
        """
        Add a job to the database
        """
        return self.table.add_obj(DbJob(job), key_value=job_id)

    def get_job(self, job_id):
        """
        Get a job from the database, from a job id.  Returns a new Job object.
        """
        try:
            return self.table.get_obj(job_id)
        except ValueError:
            (errortype, value, trace) = sys.exc_info()
            msg = "Could not find job with id {0}: {1}".format(job_id, value)
            raise errortype, msg, trace

    def update_job(self, job):
        """
        Update a job's entry in the database.
        """
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
            return ('(start_time >= {0} OR start_time <= 0)'.
                    format(time.time() - since * 24 * 60 * 60))

    def get_all_jobs(self, since=None):
        """
        Returns all jobs in the database
        """
        return self.table.get_objs('{0} {1} '
                                   'ORDER BY start_time DESC'.
                                   format(('' if since is None else 'WHERE'),
                                          self.get_since(since)))

    def get_running_jobs(self):
        """
        Returns all running jobs in the database
        """
        return self.table.get_objs('WHERE status IN (?)',
                                   DbJob.status_name_to_id(Job.RUNNING))

    def get_incomplete_jobs(self, since=None):
        """
        Returns all jobs that have not succeeded and are not currently
        running.  This should be jobs that failed, or jobs that failed
        to even run the first time.
        """
        return self.table.get_objs('WHERE status NOT IN (?, ?) {0} {1} '
                                   'ORDER BY start_time DESC'.
                                   format(('' if since is None else 'AND'),
                                          self.get_since(since)),
                                   DbJob.status_name_to_id(Job.SUCCEEDED,
                                                           Job.RUNNING))

    def get_succeeded_jobs(self, since=None):
        """
        Returns all jobs that have succeeded
        """
        return self.table.get_objs('WHERE status IN (?) {0} {1}'.
                                   format(('' if since is None else 'AND'),
                                          self.get_since(since)),
                                   DbJob.status_name_to_id(Job.SUCCEEDED))

    def get_recent_jobs(self, since=None):
        """
        Return recent jobs that were started in the last <since> days
        """
        return (self.get_all_jobs(since))

    def delete_job(self, job):
        """
        Remove the database row corresponding to a particular job.
        """
        # In a more pure world, we might wrap the job as a DbJob
        # before passing it to the SqlTable.  But we know that it's
        # only going to use the job_id and DbJob doesn't need to do
        # any translation on the job_id, so just pass the Job directly
        # and avoid the overhead of wrapping it.
        if job.job_id is None:
            raise AssertionError("Can't delete job with no job id: {0}".
                                 format(job.summary()))
        print "Deleting job {0}".format(job.job_id)
        logging.info("Job to delete: %s", job.summary())
        return self.table.delete_obj(job)

    def get_most_recent_job_id(self):
        """
        Get the largest job id in the database.
        """
        return self.table.sdb.query_one_value_always(
            'SELECT MAX(job_id) FROM jobs')

# --------------------------------------------------------------------

class Template(object):
    @classmethod
    def get_formatter(cls):
        """
        Returns an instance of string.Formatter.  Just make it a
        classmethod so that we don't construct more than necessary.
        """
        if not hasattr(cls, '_formatter'):
            cls._formatter = string.Formatter()
        return cls._formatter


    def __init__(self, template_id, name, template_str):
        self.template_id = template_id
        self.name = name
        self.template_str = template_str
        self.keys = sorted(fld
                           for (_, fld, _, _) in
                           self.get_formatter().parse(template_str)
                           if fld is not None)

    def eval(self, args):
        position_params = []
        named_params = {}
        for arg in args:
            if '=' in arg:
                (name, value) = arg.split('=', 1)
                named_params[name] = value
            else:
                position_params.append(arg)
        return self.format(*position_params, **named_params)

    def format(self, *args, **kwargs):
        return self.template_str.format(*args, **kwargs)

    def __repr__(self):
        return ('{cn}(template_id={self.template_id!r}, '
                'name={self.name!r}, '
                'template_str={self.template_str!r}'.
                format(cn=type(self).__name__, self=self))

    def desc(self):
        return ('{self.template_id:3} {self.name:10} '
                '{self.keys:20} {self.template_str}'.
                format(self=self))

# --------------------------------------------------------------------

class TemplateTable(object):
    """
    This is a wrapper around a SqlTable for a table whose rows
    correspond specifically to Template objects (using DbJob as a wrapper)
    """
    def __init__(self, filename):
        self.table = SqlTable(
            filename,
            table='templates',
            columns=(('name',         'TEXT'),
                     ('template_str', 'TEXT'),
                     ),
            key_col='template_id',
            obj_constructor=Template)

    @classmethod
    def get_table(cls, config_dir=DEFAULT_CONFIG_DIR):
        if os.path.exists(config_dir):
            logging.info("Using config dir %s db %s",
                         config_dir, DB_FILENAME)
            return cls(os.path.join(config_dir, DB_FILENAME))
        else:
            logging.info("Config dir %s does not exist", config_dir)
            return None

    def add_template(self, name, template_str):
        template = Template(None, name, template_str)
        template.template_id = self.table.add_obj(template)
        logging.info("Got template id %s", template.template_id)

    def get_template_by_id(self, template_id):
        try:
            int(template_id)
            return self.table.get_obj(template_id)
        except ValueError:
            (errortype, value, trace) = sys.exc_info()
            msg = "Could not find template with id {0}: {1}".format(
                template_id, value)
            raise errortype, msg, trace

    def get_template_by_name(self, name):
        """
        Returns a list of matching templates
        """
        return self.table.get_objs('WHERE name = "{0}"'.format(name))

    def get_template(self, id_or_name):
        try:
            return self.get_template_by_id(id_or_name)
        except ValueError:
            logging.info("Couldn't find template by id %s, trying by name",
                         id_or_name)
        existing = self.get_template_by_name(id_or_name)
        if len(existing) < 0:
            raise ValueError("Could not find template {0}".format(id_or_name))
        else:
            if existing > 1:
                logging.error("Multiple templates with name %s, "
                              "returning the first.  %s",
                              id_or_name, existing)
            return existing[0]

    def rename(self, template_id, newname):
        existing = self.get_template_by_name(newname)
        if len(existing) > 0:
            raise ValueError(
                "Can't rename {0} to {1}, a template "
                "with that name already exists: {2}".format(
                    template_id, newname, existing))
        return self.table.update_obj_fields(template_id, [('name', newname)])

    def get_all_templates(self):
        return self.table.get_objs('ORDER BY name DESC')

    def delete_template(self, template):
        print "Deleting template {0}".format(template.desc())
        return self.table.delete_obj(template)

# --------------------------------------------------------------------

if __name__ == "__main__":
    main()

