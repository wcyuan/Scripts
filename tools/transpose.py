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


EXAMPLES

Extract the column named 'aa' from the data in filename.txt:

  transpose.py --columns aa filename.txt

Extract columns named 'aa' and 'bbb' from the data in filename.txt:

  transpose.py --col_list aa,bbb filename.txt

Extract all lines that match a pattern:

  transpose.py --patt xyz filename.txt

Extract all lines where a particular column has a particular value

  transpose.py --filter <col>=<val> filename.txt

The filter understands a number of operations

  transpose.py --filter 'price > 5' --filter 'size < 30' filename.txt

The --raw option is useful if you want to chain transpose.py commands

  transpose.py --raw --patt xyz filename.txt | transpose.py --filter 'price > 5' --filter 'size < 30'

Run a sql query on data from some files which all share the same
structure.  The filename should be changed to "<table>=<filename>",
then you refer to it as <table> in the query.

  transpose.py --var DATE='2014/*/*' --sql "select Name, count(*), avg(Price) FROM orders WHERE OrderType='All' GROUP BY Trader" orders='/data/{DATE}/data.txt'

Instead of a filename, you can give it a command

  transpose.py --var DATE='2014/*/*' --sql "select Name, count(*), avg(Price) FROM orders WHERE OrderType='All' GROUP BY Trader" orders='cat /data/{DATE}/data.txt'

When there are multiple files, the column FILE is added automatically,
or you can force it with the --add_filename option:

  transpose.py --var DATE='2014/*/*' --sql "select FILE, Name, count(*), avg(Price) FROM orders WHERE OrderType='All' GROUP BY Trader" orders='/data/{DATE}/data.txt'


You can put the definition of the file into the config file .transrc
(which is in JSON):

  $ cat .transrc
  {
    "orders": "/data/{DATE}/data.txt"
  }

  transpose.py --var DATE='2014/*/*' --sql "select Name, count(*), avg(Price) FROM orders WHERE OrderType='All' GROUP BY Trader"

  transpose.py --config .transrc --var DATE='2014/*/*' --sql "select Name, count(*), avg(Price) FROM orders WHERE OrderType='All' GROUP BY Trader"

"""

# --------------------------------------------------------------------
from __future__ import absolute_import, division, with_statement

import contextlib
import itertools
import logging
import optparse
import os.path
import re
import sqlite3

# --------------------------------------------------------------------

DEFAULT_CONFIG_FILE = '~/.transrc'

HEADERS = ['#@desc']

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
           'transpose',
           'texttable',
           'pretty_print',
           # The name "read_files" is a bit generic, maybe we
           # shouldn't export it by default
           'read_files',
           'file_to_table',
           ]

logging.basicConfig(format='[%(asctime)s '
                    '%(funcName)s:%(lineno)s %(levelname)-5s] '
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
                             'add_filename', 'raw', 'width',
                             'clean_output', 'full_filenames', 'headerless'))

    def get_input(fns):
        """
        A wrapper around read_files
        """
        return read_files(fns, **rf_args)

    if opts.sql is not None and len(opts.sql) > 0:
        tables = do_sql(opts.sql, args, get_input, opts.config, cvars=opts.vars)
    else:
        if len(args) == 0:
            import sys
            args = [sys.stdin]
        tables = get_input(args)

    for table in tables:
        logging.debug("Printing table")
        pretty_print(table,
                     left=opts.left,
                     should_transpose=opts.should_transpose,
                     nopretty=opts.nopretty,
                     immediate=opts.immediate,
                     noheader=opts.noheader)
        logging.debug("Done printing table")

def getopts():
    """
    Parse the command-line options
    """
    parser = optparse.OptionParser()
    parser.add_option('--patt', '--pattern',
                      help="the pattern to look for")
    parser.add_option('--delimeter', '--ifs', '-d',
                      dest='delim',
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
    parser.add_option('--columns', '--select',
                      dest='columns',
                      action='append',
                      help='Which columns to show')
    parser.add_option('--col_list',
                      help='Which columns to show, as a comma-separated-list')
    parser.add_option('--noheader', '--no_header', '--no-header',
                      action='store_true',
                      help='do not print the header')
    # The only effect headerless has right now is that when you add a
    # filename to the output, you always add the filename, never the
    # word FILE, which is what you would normally add to the header.
    parser.add_option('--headerless',
                      action='store_true',
                      help='the input has no header')
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
    parser.add_option('--nopretty', '--no_pretty',
                      action='store_true',
                      help='do not pretty pretty')
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
    parser.add_option('--clean-output',
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
    parser.add_option('--magic_words',
                      action='append',
                      help='specify a magic word that marks the header')
    parser.add_option('--full_filenames',
                      action='store_true',
                      help='Show the full filename instead of just '
                      'a shortened version')
    opts, args = parser.parse_args()

    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if opts.log_level is not None:
        level = getattr(logging, opts.log_level.upper())
        logging.getLogger().setLevel(level)
        logging.info("Setting log level to %s", level)

    if opts.filters is not None:
        opts.filters = [_parse_filter(f) for f in opts.filters]

    if opts.vars is not None:
        opts.vars = dict(v.split('=', 1) for v in opts.vars)

    if opts.raw:
        opts.nopretty = True

    if opts.magic_words is not None:
        HEADERS.extend(opts.magic_words)

    if opts.ofs is not None:
        global OFS
        global CLEAN_CHAR
        OFS = opts.ofs
        if OFS == CLEAN_CHAR:
            CLEAN_CHAR = '~'

    if opts.col_list is not None:
        if opts.columns is None:
            opts.columns = []
        opts.columns.extend(opts.col_list.split(','))

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
        import shlex
        command = shlex.split(filename)
    else:
        for (sfx, cmd) in DECOMPRESSORS:
            if filename.endswith(sfx):
                command = [cmd, filename]
                break

    if command is None:
        logging.debug("opening filename")
        with open(filename) as filedesc:
            yield filedesc
        logging.debug("Closing filename")
        return

    logging.info('running %s', ' '.join(command))
    import subprocess
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    yield proc.stdout
    proc.stdout.close()
    logging.info('done running %s', ' '.join(command))

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

    logging.info("Guessing kind %s with delimiter '%s' from header %s",
                 kind, delim, header)

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
        logging.debug("line (%s delim='%s') %s separated into %s",
                      kind, delim, line, vals)
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
        logging.debug("line (%s delim='%s') %s separated into %s",
                      kind, delim, line, vals)
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

    valdict = dict(itertools.izip_longest(names, values, fillvalue=None))
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

def _read_input(filename, patt=None, delim=None, comment=COMMENT_CHAR,
                kind='delimited', reverse=False, head=None,
                header_patt=None, filters=None, by_col_no=False,
                columns=(), raw=False, width=None,
                clean_output=False):
    """
    Reads a file with tabular data.  Returns a generator of rows, where a
    row is a list of fields.  The first row is the header.

    So this function:
     - Looks for a header
     - Skips comments (lines that start with '#')
     - Guesses at how the line is formatted (if the user didn't tell us)
     - Parses each row into separate fields
     - Applies filters
     - Stops after <head> rows

    """
    nrows = 0
    header = None
    keep_idx = None
    with zopen(filename) as filedesc:
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

                yield print_header
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

            nrows += 1
            yield row

            # If we were given a number of lines to look for, stop after
            # that number.
            if head is not None:
                if nrows >= head:
                    return

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

def pretty_print(intable, left=False, should_transpose=None, nopretty=False,
                 immediate=False, noheader=False):
    """
    If raw, just print each row of the table after joining with the
    OFS.

    If immediate, guess at the format based on the header and the
    first row, then use that format to print each line.

    Wrapper around texttable.  If the table has fewer than 6 rows,
    transpose first.
    """
    if nopretty:
        print ORS.join(("%s" % OFS.join(line)) for line in intable)
        return

    if immediate:
        # In immediate mode, we print our output as it comes, without
        # without transposing or aligning rows.  That way we don't
        # need to wait for the last row before printing the first row.
        #
        # However, we still try to guess at a nice format.  We assume
        # that the values in each row are about the same width, within
        # PADDING characters.  We use the values first non-header row
        # as an estimate for the width of the row.  The width we use
        # is:
        #
        #  max(width of value, width of header) + PADDING
        #
        formats = []
        header = next(intable)
        header_printed = False
        for row in intable:
            if len(formats) == 0:
                formats = ["{{0:{0}}}".format(max(len(f), len(h) + PADDING))
                           for (f, h) in zip(row, header)]
                logging.debug(formats)
            if not header_printed and not noheader:
                print OFS.join(f.format(s)
                               for (f, s)
                               in zip(formats, header))
                header_printed = True
            # if this row is longer than the number of formats, pad
            # with extra formats so that we don't lose data
            pad = ['{0}'] * max(0, len(row) - len(formats))
            print OFS.join(f.format(s)
                           for (f, s)
                           in zip(formats + pad, row))
        return

    # convert generator to list
    intable = tuple(intable)
    if ((should_transpose is None and len(intable) < 6) or should_transpose):
        ttable = transpose(intable)
        logging.debug("transposed table: %s", ttable)
    else:
        ttable = intable
        intable = None
    print texttable(ttable, transposed=intable, left=left)

def pathparts(path):
    """
    Split a path by the path separator (/)

    >>> pathparts('/')
    ('/',)
    >>> pathparts('2011')
    ('2011',)
    >>> pathparts('2011/')
    ('2011',)
    >>> pathparts('/2011')
    ('/', '2011')
    >>> pathparts('a/b')
    ('a', 'b')
    >>> pathparts('a/b/')
    ('a', 'b')
    >>> pathparts('/a/b')
    ('/', 'a', 'b')
    >>> pathparts('/a/b/')
    ('/', 'a', 'b')
    >>> os.path.join(*(pathparts('/')))
    '/'
    >>> os.path.join(*(pathparts('2011')))
    '2011'
    >>> os.path.join(*(pathparts('2011/')))
    '2011'
    >>> os.path.join(*(pathparts('/2011')))
    '/2011'
    >>> os.path.join(*(pathparts('a/b')))
    'a/b'
    >>> os.path.join(*(pathparts('a/b/')))
    'a/b'
    >>> os.path.join(*(pathparts('/a/b')))
    '/a/b'
    >>> os.path.join(*(pathparts('/a/b/')))
    '/a/b'
    >>>

    """
    (direc, base) = os.path.split(path)
    if direc == '':
        return (base,)

    if direc == path:
        # If the whole path is returned as the directory, then we are
        # at the root ('/')
        direc = (direc,)
    else:
        direc = pathparts(direc)

    if base == '':
        return direc
    else:
        return direc + (base,)

def shorten_filenames(filenames):
    """
    >>> shorten_filenames(['a', 'b', 'c'])
    ('a', 'b', 'c')
    >>> shorten_filenames(['/foo/a', '/foo/b', '/foo/c'])
    ('a', 'b', 'c')
    >>> shorten_filenames(['/foo/a/bar', '/foo/b/bar', '/foo/c/bar'])
    ('a', 'b', 'c')
    >>> shorten_filenames(['/foo/a/bar/x', '/foo/b/bar/y', '/foo/c/bar/z'])
    ('a/x', 'b/y', 'c/z')
    >>> shorten_filenames(['/foo/a/bar/x/', '/foo/b/bar/y', '/foo/c/bar/z'])
    ('a/x', 'b/y', 'c/z')
    >>> shorten_filenames(['/foo/a', '../foo/y', 'bar/z'])
    ('/foo/a', '../foo/y', 'bar/z/')
    >>> shorten_filenames(['/foo/a'])
    ['/foo/a']
    >>> import sys
    >>> shorten_filenames([sys.stdin])[0] == sys.stdin
    True
    """
    if len(filenames) == 1:
        return filenames
    try:
        fileparts = [pathparts(f) for f in filenames]
    except:
        logging.warning("Can't parse filenames %s", filenames)
        return filenames
    short = []
    splits = tuple(itertools.izip_longest(*fileparts, fillvalue=''))
    for parts in splits:
        if len(parts) > 0 and not all(p == parts[0] for p in parts):
            short.append(parts)
    return tuple(os.path.join(*p) for p in itertools.izip_longest(*short, fillvalue=""))


def read_files(fns, patt=None, delim=None, comment=COMMENT_CHAR,
               kind='delimited', reverse=False, head=None, header_patt=None,
               filters=None, by_col_no=False, columns=(),
               add_filename=None, raw=False, width=None, clean_output=False,
               full_filenames=False, headerless=False):
    """
    Reads multiple files and returns a generator of tables, where a
    table is a generator of rows.
    """

    table = None
    prev_header = None
    for (shortname, filename) in zip(shorten_filenames(fns), fns):
        filetable = _read_input(filename, patt=patt, delim=delim,
                                comment=comment, kind=kind,
                                reverse=reverse, head=head,
                                header_patt=header_patt,
                                filters=filters, by_col_no=by_col_no,
                                columns=columns, raw=raw, width=width,
                                clean_output=clean_output)

        try:
            # Save the header from before we add filenames
            header = next(filetable)
        except StopIteration:
            continue

        # If there are multiple files, add a column of filenames
        # to the table.
        if (add_filename is None and len(fns) > 1) or add_filename:
            fn_to_add = filename if full_filenames else shortname
            if headerless:
                header = [fn_to_add] + header
            else:
                header = ['FILE'] + header
            def _newfiletable(filetable, filename):
                '''
                Add the filename as the first column to each row
                '''
                for line in filetable:
                    yield [filename] + line
            filetable = _newfiletable(filetable, fn_to_add)

        if table is None:
            table = itertools.chain([header], filetable)
        elif prev_header == header:
            # the header matches the previous file, so just stick
            # the data onto the existing table.
            table = itertools.chain(table, filetable)
        else:
            yield(table)
            table = itertools.chain([header], filetable)
        prev_header = header

    if table is not None:
        yield(table)


def file_to_table(filename, *args, **kwargs):
    """
    A helper function for the case where you just have a single file
    and want a table instead of a generator.  This isn't used from
    main, but could be useful for someone loading this as a module.
    """
    return list(next(read_files([filename], *args, **kwargs)))

# --------------------------------------------------------------------

class Config(object):
    """
    This class represents a map from table name to the file or command
    to read in order to create that table.  Each table may also have a
    set of sql commands that should be run after the table is created.
    For example, the extra sql commands could be used to create an
    index on the new table.

    This class just keeps the map from table name to the file to read
    or command to run.  It doesn't actually read the file or run the
    command.  It doesn't actually add the data to the database.  It's
    just the list of available tables.
    """
    def __init__(self, config=None, args=None):
        """
        All our data is in a map from table name to information about
        that table.  The information about the table is a two element
        list of the form:
          [ file_or_command , [ extra_sql_commands ] ]

        If no config file is given, try to read from the
        DEFAULT_CONFIG_FILE
        """
        self.tables = {}
        if config is None:
            config = DEFAULT_CONFIG_FILE
        self.add_config(config)
        # Add args after adding config so that the args take
        # precedence
        if args is not None:
            self.add_args_table(*args)

    def add_tables(self, tables):
        """
        Add a new set of tables to the map.  These will override any
        existing tables
        """
        for table_name in tables:
            if table_name in self.tables:
                logging.warning("Overriding table %s = (%s) "
                                "with (%s)",
                                table_name,
                                self.tables[table_name],
                                tables[table_name])
        self.tables.update(tables)
        return self

    @classmethod
    def tables_from_args(cls, *args):
        """
        Add tables as they are read from the command line.  Each
        argument should be a string like:
          table_name=filename
        or
          table_name=command
        """
        tables = {}
        for arg in args:
            (table_name, filename) = arg.split('=', 1)
            tables[table_name] = [filename, []]
        return tables

    @classmethod
    def read_config(cls, config_filename):
        """
        The config file should have a form roughly like this:

        {
          "tables": {
            "table1": "/home/user/myfilename.txt",
            "table2": {
              "create": "/usr/bin/mycmd",
              "sql": ["create index _table2_id_ on table2 (id)"]
            }
          }
        }
        """
        tables = {}
        if config_filename is None:
            return tables
        config_filename = os.path.expanduser(config_filename)
        if not os.path.exists(config_filename):
            return tables
        logging.info("Reading config file %s", config_filename)
        with zopen(config_filename) as config_fd:
            import json
            config = json.load(config_fd)
            # Everything should be in the tables subarea
            if 'tables' not in config:
                return tables
            config = config['tables']
            for table in config:
                # Each table is either just a string, or a dictionary
                # If a table is a dictionary, then it has two fields:
                #   create - a string indicating the file to read or
                #            command to run to build the table
                #   sql    - extra sql statements to execute after creating
                #            the table.  You can use this to build indexes
                #            on the table, for example.
                if isinstance(config[table], dict):
                    table_command = config[table]['create']
                    if isinstance(config[table]['sql'], basestring):
                        table_sql = [config[table]['sql']]
                    elif isinstance(config[table]['sql'], list):
                        table_sql = config[table]['sql']
                    else:
                        raise ValueError("Malformed config file {0}: sql is "
                                         "neither string nor list".
                                         format(table))
                elif isinstance(config[table], basestring):
                    table_command = config[table]
                    table_sql = []
                else:
                    raise ValueError("Malformed config file {0}: table info is "
                                     "neither string nor dict".format(table))
                logging.debug("Got table %s = (%s, %s) from config file %s",
                              table, table_command, table_sql, config)
                tables[table] = [str(table_command), table_sql]
        return tables

    def add_config(self, config_filename):
        """
        Read from a config file and add the tables.
        """
        return self.add_tables(self.read_config(config_filename))

    def add_args_table(self, *args):
        """
        Read the arguments and add the tables
        """
        return self.add_tables(self.tables_from_args(*args))

    def has_table(self, table_name):
        """
        Returns True iff we know about this table.
        """
        return table_name in self.tables

    def get_table_command(self, table_name):
        """
        Returns the filename to read or command to run to create this
        table.
        """
        return self.tables[table_name][0]

    def get_table_sqls(self, table_name):
        """
        Returns a list of the extra sql commands to run after this
        table has been created.
        """
        return self.tables[table_name][1]

class Database(object):
    '''
    Interface to an in-memory sqlite database that knows how to create
    database tables from the tables returned by read_files.
    '''
    DEFAULT_INSTANCE = None

    def __init__(self):
        self.database = sqlite3.connect(':memory:')
        self.database.text_factory = str
        self.cursor = self.database.cursor()

    @classmethod
    def get(cls):
        '''
        Get the defaulting instance, initializing it if necessary
        '''
        if cls.DEFAULT_INSTANCE is None:
            cls.DEFAULT_INSTANCE = cls()
        return cls.DEFAULT_INSTANCE

    @classmethod
    def _guess_type(cls, value):
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

    def make_table_from_data(self, name, header, data):
        """
        Given data in tabular form (as a list of rows, where each row has
        the same columns), insert that table into a sqlite database.
        """

        command = ('CREATE TABLE {name} ({cols});'.
                   format(name=name,
                          cols=', '.join("'{0}' {1}".
                                         format(h, self._guess_type(d))
                                         for (h, d) in zip(header, data[0]))))
        logging.debug(command)
        self.cursor.execute(command)

        command = ('INSERT INTO {0} VALUES ({1});'.
                   format(name,
                          ', '.join('?' for v in header)))
        pad = [None]*len(header)
        self.cursor.executemany(command, ((row+pad)[:len(header)]
                                          for row in data))
        self.database.commit()
        logging.debug("Finished inserting rows")

    def make_table_from_command(self, table_name,
                                command, get_input=read_files):
        """
        Given a table name and file to read or a command to run,
        create a table with that name from the file or command.
        """
        import glob
        matches = glob.glob(command)
        if len(matches) == 0:
            matches = [command]
        table = tuple(next(get_input(matches)))
        self.make_table_from_data(table_name, table[0], table[1:])

    def make_table_by_name(self, table_name,
                           table_config,
                           get_input=read_files,
                           cvars=None):
        """
        Given a Config object, plus the name of a table in that
        Config, create the table.  Run any additional sql commands as
        necessary.
        """
        table_create = table_config.get_table_command(table_name)
        sql_commands = table_config.get_table_sqls(table_name)
        logging.info("Trying to load table %s with file or command %s",
                     table_name, table_create)
        try:
            filename = table_create.format(**cvars)
        except KeyError as kexc:
            raise KeyError("Table {0} command {1} needs var {2} "
                           "to be set".format(table_name, table_create,
                                              kexc.args[0]))
        self.make_table_from_command(table_name, filename,
                                     get_input=get_input)
        for sql in sql_commands:
            logging.info("Running extra sql command for table %s: %s",
                         table_name, sql)
            self.cursor.execute(sql)
            self.database.commit()

    def query(self, sql, table_config=None, get_input=read_files, cvars=None):
        """
        Execute a command.

        If there are no results to return, return None

        If there are results to return, return them as a list of lists
        (i.e., the same structure that is returned by read_files, etc)

        If the query requires a table that hasn't yet been loaded into
        the database, load it as required.
        """
        if table_config is None:
            table_config = Config()
        if cvars is None:
            cvars = {}
        while True:
            try:
                logging.info("Running query %s", sql)
                self.cursor.execute(sql)
                data = self.cursor.fetchall()
                logging.info("Finished query %s", sql)
                # If the query was a command, rather than a select
                # statement, there may be no data to return.
                if self.cursor.description is None:
                    return
                table = [[d[0] for d in self.cursor.description]]
                for row in data:
                    table.append([str(v) for v in row])
                return table
            except sqlite3.OperationalError as exc:
                msg = exc.args[0]
                if not msg.startswith('no such table: '):
                    raise
                missing = msg[15:]
                if not table_config.has_table(missing):
                    # If you run the query 'create index spn on
                    # esecurity (spn)' the error you get is that there
                    # is no table called main.esecurity.  So try
                    # stripping off the "main."
                    if missing.startswith('main.'):
                        missing = missing[5:]
                if not table_config.has_table(missing):
                    raise
                self.make_table_by_name(missing, table_config,
                                        get_input=get_input, cvars=cvars)

def do_sql(sql, args=None, get_input=read_files, config=None, cvars=None):
    """
    Build an in memory sqlite database and execute a sql query against
    it.  The tables of the database come from reading files or
    executing commands that generate tabular data.  The files to read
    or commands to run for each table are determined by the arguments
    passed in, or the config file.  This only reads the tables that
    are needed to execute the sql query.
    """
    database = Database.get()
    table_config = Config(config, args)
    for query in sql:
        data = database.query(query, table_config=table_config,
                              get_input=get_input, cvars=cvars)
        if data is not None:
            yield data

# --------------------------------------------------------------------

if __name__ == "__main__":
    main()
