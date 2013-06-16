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

from contextlib   import contextmanager
from itertools    import izip_longest
from logging      import getLogger, DEBUG, info, debug
from optparse     import OptionParser
from subprocess   import Popen, PIPE
from StringIO     import StringIO

import re
import sys

# --------------------------------------------------------------------

HEADERS = ('#@desc',)

# These delimiters should be in order from least likely to appear by
# accident to most likely to appear by accident.
#
# The RE: "(?<!\\\) " is an attempt to split on space, but allowing
# backslash to escape the space.  ?<! means a "negative lookbehind
# assertion", it specifies what must come before the regexp being
# matched.
#
DELIMITERS = (' \| ', "~", '\|', '@', ',', "\t", '(?<!\\\) ', "\s+")

DECOMPRESSORS = (('.bz2', 'bzcat'),
                 ('.gz', 'zcat'))

COMMENT_CHAR='#'

# input record separator
IRS = "\n"
# output record separator
ORS = "\n"
# output field separator
OFS = " "
CLEAN_CHAR = '-'

# These are the types of filters that we support.  This is the order
# in which we will look for the operator.  It's important that all
# operators must come after operators they are a substring of.  That
# is, '=' must come after '!=', '<=', and '>='; '<' must come after
# '<='; '>' must come after '>='.
FILTER_OPS = ('!=', '<=', '>=', '<', '>', '=')

# --------------------------------------------------------------------

def main():
    opts, args = getopts()

    if len(args) == 0:
        read_transpose(sys.stdin, **opts)
    else:
        read_files(args, **opts)

def getopts():
    """
    Parse the command-line options
    """
    parser = OptionParser()
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
    opts, args = parser.parse_args()

    if opts.verbose:
        getLogger().setLevel(DEBUG)

    if opts.filters is not None:
        opts.filters = [parse_filter(f) for f in opts.filters]

    if opts.ofs is not None:
        global OFS
        global CLEAN_CHAR
        OFS = opts.ofs
        if OFS == CLEAN_CHAR:
            CLEAN_CHAR = '~'

    opts = dict((v, getattr(opts, v))
                for v in ('patt', 'delim', 'left', 'reverse',
                          'kind', 'header_patt', 'head', 'filters',
                          'by_col_no', 'columns', 'noheader',
                          'should_transpose', 'add_filename', 'raw',
                          'width', 'clean_output'))

    return (opts, args)

def opfunc(op, val):
    """
    Translate a filter operator and a given value into a function that
    takes a new value and returns true if that new value passes the
    filter.
    """
    if op == '=':
        return lambda v: v == val
    if op == '!=':
        return lambda v: v != val
    if op == '>=':
        return lambda v: float(v) >= float(val)
    if op == '<=':
        return lambda v: float(v) <= float(val)
    if op == '>':
        return lambda v: float(v) > float(val)
    if op == '<':
        return lambda v: float(v) < float(val)
    raise AssertionError("Unknown op '%s'" % op)

def parse_filter(filter_string):
    """
    Parse the valid values for the filter argument.  Valid filters
    look like:
       <name> = 3
    Where <name> is the name of the field given by the file's header.

    The return value is a tuple of (var, func) where var is the name
    of the field that we are filtering on and func is a function that
    returns True if the value passes the filter.
    """
    for op in FILTER_OPS:
        if filter_string.find(op) >= 0:
            (var, val) = filter_string.split(op, 2)

            # Strip whitespace.  That way, we can parse expressions like
            #   count = 0
            # which looks a little nicer than
            #   count=0
            # but it also means that we can't handle filters where
            # leading or trailing whitespace is actually part of the
            # filter.
            var = var.strip()
            val = val.strip()

            return (var, opfunc(op, val))

    raise ValueError("Can't parse filter '%s', can't find an operator" %
                     filter_string)

# --------------------------------------------------------------------

@contextmanager
def zopen(fn):
    """
    Return the contents of a file, even if it might be compressed.
    Returns a file object, just like open would return.  This is a
    context manager so it's meant to be called using the "with"
    command, like this:

    with zopen(file_name) as file_object:
       ....
    """
    for (sfx, cmd) in DECOMPRESSORS:
        if fn.endswith(sfx):
            info('running %s %s' % (cmd, fn))
            proc = Popen([cmd, fn], stdout=PIPE)
            stdout = proc.communicate()[0]
            info('done running %s %s' % (cmd, fn))

            # stdout is just a string, but StringIO allows us to treat
            # it like a file.  Just for convenience so that we can
            # always return file objects.
            string = StringIO(stdout)
            yield string
            string.close()
            break
    else:
        with open(fn) as f:
            yield f

# --------------------------------------------------------------------

def guess_delim(header, kind):
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
        for d in DELIMITERS:
            if len(re.findall(d, header)) > 5:
                delim = d
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

    info("Guessing kind %s with delimiter '%s' from header %s" %
         (kind, delim, header))

    return (kind, delim)

def is_header(line, comment_char, header_patt):
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
    return not is_comment(line, comment_char)

def is_comment(line, char):
    """
    Returns true if line is a comment.
    """
    return line.startswith(char)

def is_match(line, patt, reverse=False):
    """
    Returns true if the line matches the pattern.
    """
    match = re.search(patt, line)
    if reverse:
        return match is None
    else:
        return match is not None

def separate(line, kind, delim, raw=False):
    """
    Split a line according to its format.
    """
    magic_word = None
    if kind == 'delimited':
        vals = re.split(delim, line.strip())
        # If the row starts with #@desc, we should get rid of that.
        if vals[0] in HEADERS:
            magic_word = vals.pop(0)
        # If we have escaped spaces, remove the backslashes in the output
        if not raw and delim == '(?<!\\\) ':
            vals = [v.replace('\ ', ' ') for v in vals]
        debug("line (%s delim='%s') %s separated into %s" %
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
        vals= [x.strip()
               for x in (line[start:] if end is None else line[start:end]
                         for (start, end) in izip_longest(indexes, indexes[1:],
                                                          fillvalue=None))]
        debug("line (%s delim='%s') %s separated into %s" %
              (kind, delim, line, vals))
        return (vals, magic_word)
    else:
        raise ValueError ("Invalid input kind: %s" % kind)

def should_filter(values, names, filters):
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

def read_input(fd, patt=None, delim=None, comment=COMMENT_CHAR,
               kind='delimited', reverse=False, head=None,
               header_patt=None, filters=None, by_col_no=False,
               columns=(), raw=False, width=None):
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
    for line in fd:
        line = line.strip(IRS)

        # First step is to look for the header.  If we haven't found
        # it yet, we'll skip all lines until we find it.  We use the
        # header to figure out the format for the rest of the file.
        if header is None:
            if not is_header(line, comment, header_patt):
                continue
            if delim is None:
                (kind, delim) = guess_delim(line, kind)
            (header, magic_word) = separate(line, kind, delim, raw=raw)
            if by_col_no:
                col_nos = [str(r) for r in range(1, len(header)+1)]
                header = col_nos
            if columns is not None and len(columns) > 0:
                keep_idx = [header.index(c) for c in columns]
                print_header = [header[i] for i in keep_idx]
            else:
                print_header = header
            if raw and magic_word is not None:
                print_header.insert(0, magic_word)

            table.append(print_header)
            if not by_col_no:
                continue

        # Skip comments
        if is_comment(line, comment):
            continue

        # If there is a pattern to match, skip until we find that pattern
        if (patt is not None and
            not is_match(line, patt, reverse=reverse)):
            continue

        # Found a valid line!  Parse it into separate fields.
        (row, _) = separate(line, kind, delim, raw=raw)

        # Apply filters
        if should_filter(row, header, filters):
            continue

        if keep_idx is not None:
            row = [row[i] for i in keep_idx]

        if width is not None:
            row = [r if len(r) < width else (r[:width]+"...") for r in row]

        table.append(row)

        # If we were given a number of lines to look for, stop after
        # that number.
        if head is not None:
            if len(table) >= head+1:
                break

    return table

def transpose(intable):
    """
    Given a table represented as an iterable of iterables, we return a
    transposed version of that table.

    Returns an iterator, which can only be traversed once.
    """
    return izip_longest(*intable, fillvalue="")

def texttable(table, transposed=None, delim=OFS, left=False,
              clean_output=False):
    """
    pretty-print a table.  Every column's width is the width of the
    widest field in that column.

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
    lc = '-' if left else ''
    formats = ["%{0}{1}s".format(lc, width) for width in widths]
    return ORS.join("%s" % delim.join(format % (fld
                                                if not clean_output
                                                else fld.replace(OFS,
                                                                 CLEAN_CHAR))
                                      for (format, fld) in zip(formats, line))
                    for line in table)

def pretty_print(intable, left=False, should_transpose=None, raw=False,
                 clean_output=False):
    if raw:
        print ORS.join(("%s" % OFS.join(line)) for line in intable)
        return

    if ((should_transpose is None and len(intable) < 6) or should_transpose):
        ttable = transpose(intable)
        debug("transposed table: %s" % ttable)
    else:
        ttable = intable
        intable = None
    print texttable(ttable, transposed=intable, left=left,
                    clean_output=clean_output)

def read_transpose(fd, patt=None, delim=None, left=False,
                   comment=COMMENT_CHAR, kind='delimited', reverse=False,
                   head=None, header_patt=None, filters=None, by_col_no=False,
                   columns=(), noheader=False, should_transpose=None,
                   add_filename=None, raw=False, width=None,
                   clean_output=False):
    """
    Puts it all together (for a single, uncompressed file).  Reads the
    file, transposes (if necessary), and pretty-prints the output.
    """
    intable = read_input(fd, patt=patt, delim=delim,
                         comment=comment, kind=kind,
                         reverse=reverse, head=head,
                         header_patt=header_patt,
                         filters=filters, by_col_no=by_col_no,
                         columns=columns, raw=raw, width=width)
    if noheader:
        intable = intable[1:]
    pretty_print(intable, left=left, should_transpose=should_transpose,
                 raw=raw, clean_output=clean_output)

def read_files(fns, patt=None, delim=None, left=False,
               comment=COMMENT_CHAR, kind='delimited', reverse=False,
               head=None, header_patt=None, filters=None, by_col_no=False,
               columns=(), noheader=False, should_transpose=None,
               add_filename=None, raw=False, width=None, clean_output=False):
    """
    Reads multiple files, transposes (if necessary), and pretty-prints
    the output.
    """
    table = None
    prev_header = None
    for fn in fns:
        with zopen(fn) as fd:
            filetable = read_input(fd, patt=patt, delim=delim,
                                   comment=comment, kind=kind,
                                   reverse=reverse, head=head,
                                   header_patt=header_patt,
                                   filters=filters, by_col_no=by_col_no,
                                   columns=columns, raw=raw, width=width)

            if len(filetable) == 0:
                continue

            # Save the header from before we add filenames
            header = filetable[0]

            # If there are multiple files, add a column of filenames
            # to the table.
            if (add_filename is None and len(fns) > 1) or add_filename:
                filetable = ([['FILE'] + filetable[0]] +
                             [[fn] + l for l in filetable[1:]])

            if table is None:
                if noheader:
                    filetable = filetable[1:]
                table = filetable
            elif prev_header == header:
                # the header matches the previous file, so just stick
                # the data onto the existing table.
                table.extend(filetable[1:])
            else:
                pretty_print(table, left=left,
                             should_transpose=should_transpose,
                             raw=raw, clean_output=clean_output)
                if noheader:
                    filetable = filetable[1:]
                table = filetable
            prev_header = header

    if table is not None:
        pretty_print(table, left=left, should_transpose=should_transpose,
                     raw=raw, clean_output=clean_output)


# --------------------------------------------------------------------

if __name__ == "__main__":
    main()
