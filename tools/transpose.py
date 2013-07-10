#!/usr/bin/env python
"""
transpose.py --patt <pattern> [<file>]

Take tabular input that looks like this, where every field has a
different length:

 aa bbbb cccccc dd eeee
 1 2 3 4 5
 6 7 8 9 10
 11 12 13 14 15

And output it transposed, and with columns lined up:

 aa     1 6  11
 bbbb   2 7  12
 cccccc 3 8  13
 dd     4 9  14
 eeee   5 10 15

Only transposes if there are no more than 6 rows to transpose,
otherwise just line the columns up without transposing:

 aa bbbb cccccc dd eeee
 1     2      3  4    5
 6     7      8  9   10
 11   12     13 14   15

Tries to be intelligent about parsing the input: Tries to guess
whether the input is fixed width or delimited.  If delimited, tries to
guess what the separator is.

Takes an optional pattern.  If given a pattern, then grep the file for
that pattern and only show matching lines.  Also output the header so
you can see what the fields mean.

"""

# --------------------------------------------------------------------
from __future__ import absolute_import, division, with_statement

import contextlib
import itertools
import logging
import json
import optparse
import os.path
import re
import shlex
import sqlite3
import subprocess
import sys

# --------------------------------------------------------------------

DEFAULT_CONFIG_FILE = '~/.transrc'

HEADERS = ('#@desc',)

# These delimiters should be in order from least likely to appear by
# accident to most likely to appear by accident.
#
# The RE: "(?<!\\\) " is an attempt to split on space, but allowing
# backslash to escape the space.  ?<! means a "negative lookbehind
# assertion", it specifies what must come before the regexp being
# matched.
#
DELIMITERS = (' \| ', "~", '\|', '@', ',', "\t", '(?<!\\\)\s+', "\s+")

DECOMPRESSORS = (('.bz2', 'bzcat'),
                 ('.gz', 'zcat'))

COMMENT_CHAR = '#'

# input record separator
IRS = "\n"
# output record separator
ORS = "\n"
# output field separator
OFS = " "
CLEAN_CHAR = '-'
PADDING = 4

# These are the types of filters that we support.  This is the order
# in which we will look for the operator.  It's important that all
# operators must come after operators they are a substring of.  That
# is, '=' must come after '!=', '<=', and '>='; '<' must come after
# '<='; '>' must come after '>='.
FILTER_OPS = ('!=', '<=', '>=', '<', '>', '=')

__all__ = ['zopen',
           'read_input',
           'transpose',
           'texttable',
           'pretty_print',
           'read_files',
           'do_sql',
           'make_one_table',
           ]

logging.basicConfig(format='[%(asctime)s '
                    '%(module)s:%(lineno)s %(levelname)-5s] '
                    '%(message)s')

# --------------------------------------------------------------------

def main():
    """
    The main function, gets configuration from the command line, reads
    input, and outputs pretty data
    """
    opts, args = getopts()

    rf_args = dict((v, getattr(opts, v))
                   for v in ('patt', 'delim', 'reverse', 'kind', 'header_patt',
                             'head', 'filters', 'by_col_no', 'columns',
                             'noheader', 'add_filename', 'raw', 'width',
                             'clean_output', 'immediate'))

    def get_input(fns):
        """
        A wrapper around read_files
        """
        return read_files(fns, **rf_args)

    if opts.sql is not None and len(opts.sql) > 0:
        tables = do_sql(opts.sql, args, get_input, opts.config, cvars=opts.vars)
    else:
        if len(args) == 0:
            args = [sys.stdin]
        tables = get_input(args)

    for table in tables:
        logging.debug("Printing table")
        pretty_print(table,
                     left=opts.left,
                     should_transpose=opts.should_transpose,
                     raw=opts.raw)
        logging.debug("Done printing table")

def getopts():
    """
    Parse the command-line options
    """
    parser = optparse.OptionParser()
    parser.add_option('--patt', '--pattern',
                      help="the pattern to look for")
    parser.add_option('--delim', '-d', '--delimiter',
                      help="the delimiter to use")
    parser.add_option('--left',
                      action="store_true",
                      default=True,
                      help="left justify (True by default)")
    parser.add_option('--right',
                      action="store_false",
                      dest='left',
                      help="right justify (False by default)")
    parser.add_option('--reverse', '-v',
                      action="store_true",
                      help="reverse the pattern matching")
    parser.add_option('--kind',
                      default='delimited',
                      help="the kind of table")
    parser.add_option('--header_patt',
                      help="a pattern that distinguishes the header")
    parser.add_option('--head',
                      type=int,
                      help="Only show the first <head> lines")
    parser.add_option('--by_col_no', '--by_column_number',
                      action="store_true",
                      help="Just number the columns instead of "
                      "using the header")
    parser.add_option('--verbose',
                      action='store_true',
                      help='verbose mode')
    parser.add_option('--log_level',
                      help='set the log level')
    parser.add_option('--filter',
                      dest='filters',
                      action='append',
                      help='Filter results.  If multiple filters given, '
                      'will only print lines that match them all.')
    parser.add_option('--columns', '--select', '--column',
                      dest='columns',
                      action='append',
                      help='Which columns to show')
    parser.add_option('--noheader', '--no_header', '--no-header',
                      action='store_true',
                      help='do not print the header')
    parser.add_option('--transpose',
                      dest='should_transpose',
                      action='store_true',
                      help='transpose')
    parser.add_option('--notranspose', '--no-transpose', '--no_transpose',
                      '--notrans',
                      dest='should_transpose',
                      action='store_false',
                      help='do not transpose')
    parser.add_option('--no_filename', '--no-filename', '--nofilename',
                      dest='add_filename',
                      action='store_false',
                      help='do not include the filename')
    parser.add_option('--add_filename', '--add-filename',
                      dest='add_filename',
                      action='store_true',
                      help='include the filename')
    parser.add_option('--raw',
                      dest='raw',
                      action='store_true',
                      help='just grep without any other processing')
    parser.add_option('--width',
                      type=int,
                      help='only show the first N characters of each column')
    parser.add_option('--compact',
                      action='store_const',
                      const=30,
                      dest='width',
                      help='set width to 30')
    parser.add_option('--full',
                      action='store_const',
                      const=None,
                      dest='width',
                      help='show full columns')
    parser.add_option('--ofs',
                      dest='ofs',
                      help='set the output field separator')
    parser.add_option('--clean-output', '--clean',
                      action='store_true',
                      dest='clean_output',
                      help='remove the ofs from output fields')
    parser.add_option('--immediate',
                      action='store_true',
                      help="don't pretty-print, print rows "
                      "immediately and guess at the format")
    parser.add_option('--sql',
                      action='append',
                      help="don't print the output, run a sql query on it")
    parser.add_option('--config', '--config-file', '--config_file',
                      '--configfile',
                      help="A file that contains configuration",
                      default=DEFAULT_CONFIG_FILE)
    parser.add_option('--vars',
                      action='append',
                      help='Args to use for interpolating commands',
                      default=[])
    opts, args = parser.parse_args()

    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if opts.log_level is not None:
        level = getattr(logging, opts.log_level.upper())
        logging.getLogger().setLevel(level)
        logging.info("Setting log level to {0}".format(level))

    if opts.filters is not None:
        opts.filters = [_parse_filter(f) for f in opts.filters]

    if opts.vars is not None:
        opts.vars = dict(v.split('=', 1) for v in opts.vars)

    if opts.ofs is not None:
        global OFS
        global CLEAN_CHAR
        OFS = opts.ofs
        if OFS == CLEAN_CHAR:
            CLEAN_CHAR = '~'

    return (opts, args)

def _opfunc(operator, val):
    """
    Translate a filter operator and a given value into a function that
    takes a new value and returns true if that new value passes the
    filter.
    """
    if operator == '=':
        return lambda v: v == val
    if operator == '!=':
        return lambda v: v != val
    if operator == '>=':
        return lambda v: float(v) >= float(val)
    if operator == '<=':
        return lambda v: float(v) <= float(val)
    if operator == '>':
        return lambda v: float(v) > float(val)
    if operator == '<':
        return lambda v: float(v) < float(val)
    raise AssertionError("Unknown operator '%s'" % operator)

def _parse_filter(filter_string):
    """
    Parse the valid values for the filter argument.  Valid filters
    look like:
       <name> = 3
    Where <name> is the name of the field given by the file's header.

    The return value is a tuple of (var, func) where var is the name
    of the field that we are filtering on and func is a function that
    returns True if the value passes the filter.
    """
    for operator in FILTER_OPS:
        if filter_string.find(operator) >= 0:
            (var, val) = filter_string.split(operator, 2)

            # Strip whitespace.  That way, we can parse expressions like
            #   count = 0
            # which looks a little nicer than
            #   count=0
            # but it also means that we can't handle filters where
            # leading or trailing whitespace is actually part of the
            # filter.
            var = var.strip()
            val = val.strip()

            return (var, _opfunc(operator, val))

    raise ValueError("Can't parse filter '%s', can't find an operator" %
                     filter_string)

# --------------------------------------------------------------------

@contextlib.contextmanager
def zopen(filename, input_type=None):
    """
    Return the contents of a file, even if it might be compressed.
    Returns a file object, just like open would return.  This is a
    context manager so it's meant to be called using the "with"
    command, like this:

    with zopen(file_name) as file_object:
       ....


    We are usually given a file name.  But we may have been given a
    file dsecriptor, or we may have been given a command to run.  If
    input_type is given, that will tell us what we were given.  If
    input_type is None, we'll try to guess at what we were given:

      if it's not a string, assume it's a file descriptor and just
      return it

      if it's not a file that exists, assume it's a command
    """
    if input_type not in (None, 'fd', 'cmd', 'file'):
        raise ValueError("Invalid input_type {0}, must be one of "
                         "None, 'fd', 'cmd', 'file'".format(input_type))

    if input_type is None and not hasattr(filename, 'endswith'):
        logging.debug("Input is not a string, assuming it's a file descriptor")
        input_type = 'fd'

    if input_type == 'fd':
        yield filename
        return

    if (input_type is None
        and not os.path.exists(filename)):
        # if we are given a file that doesn't exist, maybe it's a
        # command.
        logging.debug("Input file does not exist, assuming it's a command")
        input_type = 'cmd'

    command = None
    if input_type == 'cmd':
        command = shlex.split(filename)
    else:
        for (sfx, cmd) in DECOMPRESSORS:
            if filename.endswith(sfx):
                command = [cmd, filename]
                break

    if command is None:
        with open(filename) as filedesc:
            yield filedesc
        return

    logging.info('running {0}'.format(' '.join(command)))
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    yield proc.stdout
    proc.wait()
    proc.stdout.close()
    logging.info('done running {0}'.format(' '.join(command)))

# --------------------------------------------------------------------

def _guess_delim(header, kind):
    """
    Guess the form of the data based on the header.  Most cases are
    delimiter separated, so it's mostly a matter of figuring out the
    delimiter.

    This assumes that the header uses the same format as the rest of
    the table.
    """
    if kind is None:
        # Ideally we could detect whether we are delimited or whether
        # we are using a fixed format, but so far I haven't tried
        # implementing that logic yet.  So just assume we are
        # delimited unless the user tells us differently.
        kind = 'delimited'

    if kind == 'delimited':
        # We go through the possible delimiters in order from least
        # likely to most likely.  As soon as one of the delimiters
        # appears on the line more than 5 times, it's probably the
        # delimiter.
        for this_delim in DELIMITERS:
            if len(re.findall(this_delim, header)) > 5:
                delim = this_delim
                break
        else:
            # If no delimiter appears more than 5 times, we're
            # probably just white-space delimited.
            delim = '\s+'

    elif kind == 'fixed':
        # return a list containing the locations of the the first
        # letter of each word in the header.
        delim = [m.start() for m in re.finditer('[^\s]+', header)]

    else:
        raise ValueError ("Invalid input kind: %s" % kind)

    logging.info("Guessing kind %s with delimiter '%s' from header %s" %
                 (kind, delim, header))

    return (kind, delim)

def _is_header(line, comment_char, header_patt):
    """
    Is this row the header?
    """
    # Sometimes we are given a pattern and we should only match that
    # pattern
    if header_patt is not None:
        return re.search(header_patt, line) is not None

    # Some files use special strings to mark the header.
    if any(line.startswith(pfx) for pfx in HEADERS):
        return True

    # Otherwise we just take the first non-comment
    return not _is_comment(line, comment_char)

def _is_comment(line, char):
    """
    Returns true if line is a comment.
    """
    return line.startswith(char)

def _is_match(line, patt, reverse=False):
    """
    Returns true if the line matches the pattern.
    """
    match = re.search(patt, line)
    if reverse:
        return match is None
    else:
        return match is not None

def _separate(line, kind, delim, raw=False):
    """
    Split a line according to its format.
    """
    magic_word = None
    if kind == 'delimited':
        vals = re.split(delim, line)
        # If the row starts with #@desc, we should get rid of that.
        if vals[0] in HEADERS:
            magic_word = vals.pop(0)
        # If we have escaped spaces, remove the backslashes in the output
        if not raw and delim == '(?<!\\\)\s+':
            vals = [v.replace('\ ', ' ') for v in vals]
        logging.debug("line (%s delim='%s') %s separated into %s" %
                      (kind, delim, line, vals))
        return (vals, magic_word)
    elif kind == 'fixed':
        # Fixed-width format.  To try to parse something like:
        #
        #   F1      F2   F3    F4     F5   F6
        #   this    is   a    fixed  width format
        #
        # You'd like to just split the line into pieces according to
        # the words in the title.  But there could be columns that
        # start before the header did.  So what we do is we start at
        # the location of the header word, then we search backwards
        # until we find a space.  We split the word in those places.
        indexes = [delim[0]]
        indexes.extend(line.rfind(' ', 0, idx)+1 for idx in delim[1:])
        vals = [x.strip()
                for x in (line[start:] if end is None else line[start:end]
                          for (start, end) in
                          itertools.izip_longest(indexes, indexes[1:],
                                                 fillvalue=None))]
        logging.debug("line (%s delim='%s') %s separated into %s" %
                      (kind, delim, line, vals))
        return (vals, magic_word)
    else:
        raise ValueError ("Invalid input kind: %s" % kind)

def _should_filter(values, names, filters):
    """
    Returns False if and only if the set of values passes all the
    filters.  Otherwise we return True because we should filter out
    the row.

    The filters should be an iterable whose values are tuples of:
        (varname, filterfunc)
    Where varname is the field to check and filterfunc is a function
    which returns True if the value passes the filter.
    """
    if filters is None or len(filters) == 0:
        # only construct valdict if necessary
        return False

    valdict = dict(zip(names, values))
    for (var, criteria) in filters:
        if not criteria(valdict[var]):
            return True

    return False

def _sanitize(row):
    """
    Given a list of strings, make sure none of the strings in the list
    contain the OFS (output field separator).  If they do, replace it
    with the CLEAN_CHAR.
    """
    return [CLEAN_CHAR if r == '' else r.replace(OFS, CLEAN_CHAR)
            for r in row]

def read_input(filedesc, patt=None, delim=None, comment=COMMENT_CHAR,
               kind='delimited', reverse=False, head=None,
               header_patt=None, filters=None, by_col_no=False,
               columns=(), raw=False, width=None, immediate=False,
               noheader=False, clean_output=False):
    """
    Reads a file with tabular data.  Returns a list of rows, where a
    row is a list of fields.  The first row is the header.

    So this function:
     - Looks for a header
     - Skips comments (lines that start with '#')
     - Guesses at how the line is formatted (if the user didn't tell us)
     - Parses each row into separate fields
     - Applies filters
     - Stops after <head> rows

    """
    table = []
    header = None
    keep_idx = None
    formats = []
    header_printed = False
    for line in filedesc:
        line = line.strip(IRS)

        # First step is to look for the header.  If we haven't found
        # it yet, we'll skip all lines until we find it.  We use the
        # header to figure out the format for the rest of the file.
        if header is None:
            if not _is_header(line, comment, header_patt):
                continue
            if delim is None:
                (kind, delim) = _guess_delim(line, kind)
            (header, magic_word) = _separate(line, kind, delim, raw=raw)
            if by_col_no:
                col_nos = [str(r) for r in range(1, len(header)+1)]
                header = col_nos
            if columns is not None and len(columns) > 0:
                keep_idx = [header.index(c) for c in columns]
                print_header = [header[i] for i in keep_idx]
            else:
                print_header = header
            if raw and magic_word is not None:
                print_header[0] = magic_word + ' ' + print_header[0]

            if clean_output:
                print_header = _sanitize(print_header)

            table.append(print_header)
            if not by_col_no:
                continue

        # Skip comments
        if _is_comment(line, comment):
            continue

        # If there is a pattern to match, skip until we find that pattern
        if (patt is not None and
            not _is_match(line, patt, reverse=reverse)):
            continue

        # Found a valid line!  Parse it into separate fields.
        (row, _) = _separate(line, kind, delim, raw=raw)

        # Apply filters
        if _should_filter(row, header, filters):
            continue

        if keep_idx is not None:
            row = [row[i] for i in keep_idx]

        if width is not None:
            row = [r if len(r) < width else (r[:width]+"...") for r in row]

        if clean_output:
            row = _sanitize(row)

        if immediate:
            # In immediate mode, we print our output right here,
            # without transposing or aligning rows.  However, we still
            # try to guess at a nice format.  We assume that the
            # values in each row are about the same width, within
            # PADDING characters.  We use the values first non-header
            # row as an estimate for the width of the row.  The width
            # we use is:
            #
            #  max(width of value, width of header) + PADDING
            #
            if len(formats) == 0:
                if raw:
                    formats = ["{0}"] * len(print_header)
                else:
                    formats = ["{{0:{0}}}".format(max(len(f), len(h) + PADDING))
                               for (f, h) in zip(row, print_header)]
                logging.debug(formats)
            if not header_printed and not noheader:
                print OFS.join(f.format(s)
                               for (f, s)
                               in zip(formats, table[0]))
                header_printed = True
            print OFS.join(f.format(s)
                           for (f, s)
                           in zip(formats, row))

            # To save memory, don't save the row.  However, we still
            # need to keep track of the number of rows for head, so
            # just add a None.
            table.append(None)
        else:
            table.append(row)

        # If we were given a number of lines to look for, stop after
        # that number.
        if head is not None:
            if len(table) >= head+1:
                break

    if immediate:
        return []
    return table

def transpose(intable):
    """
    Given a table represented as an iterable of iterables, we return a
    transposed version of that table.

    Returns an iterator, which can only be traversed once.
    """
    return itertools.izip_longest(*intable, fillvalue="")

def texttable(table, transposed=None, delim=OFS, left=False):
    """
    print a table with columns lined up.  Every column's width is the
    width of the widest field in that column.

    The given table should be a list of lists.  That is, it should be
    a list of rows, where every row is a list of fields.

    To get the width of each column, we'll transpose the table.  For
    efficiency, if the caller already has a transposed version of the
    table, they can pass that into us so we don't have to re-transpose
    it.

    Both the table, and the transposed version of the table, will be
    traversed exactly once, so it's fine if they are just generator
    functions.
    """
    if transposed is None:
        transposed = transpose(table)
    widths = (max(len(fld) for fld in line) for line in transposed)
    lch = '-' if left else ''
    formats = ["%{0}{1}s".format(lch, width) for width in widths]
    return ORS.join("%s" % delim.join(format % (fld)
                                      for (format, fld) in zip(formats, line))
                    for line in table)

def pretty_print(intable, left=False, should_transpose=None, raw=False):
    """
    Wrapper around texttable.  If the table has fewer than 6 rows,
    transpose first.
    """
    if raw:
        print ORS.join(("%s" % OFS.join(line)) for line in intable)
        return

    if ((should_transpose is None and len(intable) < 6) or should_transpose):
        ttable = transpose(intable)
        logging.debug("transposed table: %s" % ttable)
    else:
        ttable = intable
        intable = None
    print texttable(ttable, transposed=intable, left=left)


def read_files(fns, patt=None, delim=None, comment=COMMENT_CHAR,
               kind='delimited', reverse=False, head=None, header_patt=None,
               filters=None, by_col_no=False, columns=(), noheader=False,
               add_filename=None, raw=False, width=None, clean_output=False,
               immediate=False, input_type=None):
    """
    Reads multiple files, transposes (if necessary), and pretty-prints
    the output.
    """

    table = None
    prev_header = None
    for filename in fns:
        with zopen(filename, input_type=input_type) as filedesc:
            filetable = read_input(filedesc, patt=patt, delim=delim,
                                   comment=comment, kind=kind,
                                   reverse=reverse, head=head,
                                   header_patt=header_patt,
                                   filters=filters, by_col_no=by_col_no,
                                   columns=columns, raw=raw, width=width,
                                   immediate=immediate, noheader=noheader,
                                   clean_output=clean_output)

            if len(filetable) == 0:
                continue

            # Save the header from before we add filenames
            header = filetable[0]

            # If there are multiple files, add a column of filenames
            # to the table.
            if (add_filename is None and len(fns) > 1) or add_filename:
                filetable = ([['FILE'] + filetable[0]] +
                             [[filename] + l for l in filetable[1:]])

            if table is None:
                if noheader:
                    filetable = filetable[1:]
                table = filetable
            elif prev_header == header:
                # the header matches the previous file, so just stick
                # the data onto the existing table.
                table.extend(filetable[1:])
            else:
                yield(table)
                if noheader:
                    filetable = filetable[1:]
                table = filetable
            prev_header = header

    if table is not None:
        yield(table)

# --------------------------------------------------------------------

def do_sql(sql, args=None, get_input=read_input, config=None, cvars=None):
    """
    Build an in memory sqlite database and execute a sql query against
    it.  The tables of the database come from reading files or
    executing commands that generate tabular data.  The files to read
    or commands to run for each table are determined by the arguments
    passed in, or the config file.  This only reads the tables that
    are needed to execute the sql query.
    """
    if cvars is None:
        cvars = {}

    tables = {}
    if args is not None:
        for arg in args:
            (table_name, filename) = arg.split('=', 1)
            tables[table_name] = filename

    if config is not None:
        config = os.path.expanduser(config)
        if os.path.exists(config):
            logging.info("Reading config file {0}".format(config))
            with zopen(config) as config_fd:
                data = json.load(config_fd)
                for table in data:
                    logging.debug("Got table {0} = ({1}) from config file {2}".
                                  format(table, data[table], config))
                    if table in tables:
                        logging.debug("Skipping table {0} = ({1}) "
                                      "from config file {2}, overriden "
                                      "on the command line".
                                      format(table, data[table], config))
                    else:
                        tables[table] = str(data[table])

    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    conn.text_factory = str

    for query in sql:
        while True:
            try:
                logging.info("Running query {0}".format(query))
                cursor.execute(query)
                data = cursor.fetchall()
                logging.info("Finished query {0}".format(query))
                # If the query was a command, rather than a select
                # statement, there may be no data to return.
                if cursor.description is None:
                    break
                table = [[d[0] for d in cursor.description]]
                for row in data:
                    table.append([str(v) for v in row])
                yield table
            except sqlite3.OperationalError as exc:
                msg = exc.args[0]
                if not msg.startswith('no such table: '):
                    raise
                missing = msg[15:]
                if missing not in tables:
                    # If you run the query 'create index spn on
                    # esecurity (spn)' the error you get is that there
                    # is no table called main.esecurity.  So try
                    # stripping off the "main."
                    if missing.startswith('main.'):
                        missing = missing[5:]
                if missing not in tables:
                    raise
                logging.info("Trying to load table {0} with file {1}".
                             format(missing, tables[missing]))
                try:
                    filename = tables[missing].format(**cvars)
                except KeyError as kexc:
                    raise KeyError("Table {0} command {1} needs var {2} "
                                   "to be set".format(missing, tables[missing],
                                                      kexc.args[0]))
                table = list(get_input([filename]))[0]
                make_one_table(conn, cursor, missing, table[0], table[1:])


def _guess_type(value):
    """
    Guess the sqlite type for a given value
    """
    for (pytype, sqltype) in ((int, 'INTEGER'),
                              (float, 'FLOAT')):
        try:
            pytype(value)
            return sqltype
        except ValueError:
            pass
    return 'TEXT'

def make_one_table(database, cursor, name, header, data):
    """
    Given data in tabular form (as a list of rows, where each row has
    the same columns), insert that table into a sqlite database.
    """
    command = ('CREATE TABLE {name} ({cols});'.
               format(name=name,
                      cols=', '.join("'{0}' {1}".
                                     format(h, _guess_type(d))
                                     for (h, d) in zip(header, data[0]))))
    logging.debug(command)
    cursor.execute(command)

    command = ('INSERT INTO {0} VALUES ({1});'.
               format(name,
                      ', '.join('?' for v in header)))
    cursor.executemany(command, (row[:len(header)] for row in data))
    database.commit()
    logging.debug("Finished inserting rows")


# --------------------------------------------------------------------

if __name__ == "__main__":
    main()
