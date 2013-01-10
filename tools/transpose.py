#!/usr/bin/env python
"""
transpose.py --patt <pattern> [<file>]

Take tabular input that looks like, whre every field has a different length
 aa bbbb cccccc dd eeee
 1 2 3 4 5
 6 7 8 9 10
 11 12 13 14 15

And output it transposed:
 aa bbbb cccccc dd eeee
 1     2      3  4    5
 6     7      8  9   10
 11   12     13 14   15


Only transposes if there are no more than 6 rows to transpose.

Tries to be intelligent about how to parse the tabular input.  Tries
to guess whether the input is fixed width or delimited.  If delimited,
tries to guess what the separator is.

Takes an optional pattern.  If we are given a pattern, then we grep
the file for that pattern and only show matching lines.  However, we
also output the header so you can see what the fields mean.

"""

# --------------------------------------------------------------------
from __future__ import absolute_import, division, with_statement

from contextlib   import contextmanager
from itertools    import izip_longest
from optparse     import OptionParser
from subprocess   import Popen, PIPE
from StringIO     import StringIO

import re
import sys

# --------------------------------------------------------------------

def main():
    opts, args = getopts()

    if len(args) == 0:
        read_transpose(sys.stdin, **opts)
    else:
        for fn in args:
            with zopen(fn) as fd:
                read_transpose(fd, **opts)

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
                      help="left justify")
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
    opts, args = parser.parse_args()

    opts = dict((v, getattr(opts, v))
                for v in ('patt', 'delim', 'left', 'reverse',
                          'kind', 'header_patt', 'head'))

    return (opts, args)

# --------------------------------------------------------------------

HEADERS = ('#@desc',)

DELIMITERS = (' \| ', '\|', ',', '@', "\t", "~", "\s+")

DECOMPRESSORS = (('.bz2', 'bzcat'),
                 ('.gz', 'zcat'))

# input record separator
IRS = "\n"
# output record separator
ORS = "\n"
# output field separator
OFS = " "

# --------------------------------------------------------------------

@contextmanager
def zopen(fn):
    """
    Return the contents of a file, even if it might be compressed.
    Returns a list of strings, one string per line of the file.
    """
    for (sfx, cmd) in DECOMPRESSORS:
        if fn.endswith(sfx):
            proc = Popen([cmd, fn], stdout=PIPE)
            stdout = proc.communicate()[0]

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
    """
    if kind is None:
        kind = 'delimited'
    if kind == 'delimited':
        for d in DELIMITERS:
            if len(re.findall(d, header)) > 5:
                delim = d
                break
        else:
            delim = '\s+'
    elif kind == 'fixed':
        # return a list containing the locations of the the first
        # letter of each word in the header.
        delim = [m.start() for m in re.finditer('[^\s]+', header)]
    else:
        raise ValueError ("Invalid input kind: %s" % kind)
    return (kind, delim)

def is_header(line, comment_char, header_patt):
    if any(line.startswith(pfx) for pfx in HEADERS):
        return True
    if header_patt is not None:
        return re.search(header_patt, line) is not None
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

def separate(line, kind, delim):
    if kind == 'delimited':
        vals = re.split(delim, line)
        # If the row starts with #@desc, we should get rid of that.
        if vals[0] in HEADERS:
            vals.pop(0)
        return vals
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
        return [x.strip()
                for x in (line[start:] if end is None else line[start:end]
                          for (start, end) in izip_longest(indexes, indexes[1:],
                                                           fillvalue=None))]
    else:
        raise ValueError ("Invalid input kind: %s" % kind)

def read_input(fd, patt=None, delim=None, comment='#',
               kind='delimited', reverse=False, head=None,
               header_patt=None):
    table = []
    header = None
    for line in fd:
        line = line.strip(IRS)
        if header is None:
            if not is_header(line, comment, header_patt):
                continue
            if delim is None:
                (kind, delim) = guess_delim(line, kind)
            header = separate(line, kind, delim)
            table.append(header)
            continue
        if is_comment(line, comment):
            continue
        if (patt is not None and
            not is_match(line, patt, reverse=reverse)):
            continue
        table.append(separate(line, kind, delim))
        if head is not None:
            if len(table) >= head+1:
                break
    return table

def transpose(intable):
    """
    intable should be an iterable where every element is a list of
    fields
    """
    return izip_longest(*intable, fillvalue="")

def texttable(outtable, intable=None, delim=OFS, left=False):
    """
    intable should be an iterable where every element is a list of
    fields
    """
    if intable is None:
        intable = list(transpose(outtable))
    widths = (max(len(fld) for fld in line)
              for line in intable)
    lc = '-' if left else ''
    formats = ["%{0}{1}s".format(lc, width) for width in widths]
    return ORS.join("%s" % delim.join(format % fld
                                      for (format, fld) in zip(formats, line))
                    for line in outtable)

def read_transpose(fd, patt=None, delim=None, left=False,
                   comment='#', kind='delimited', reverse=False,
                   head=None, header_patt=None):
    intable = list(read_input(fd, patt=patt, delim=delim,
                              comment=comment, kind=kind,
                              reverse=reverse, head=head,
                              header_patt=header_patt))
    if len(intable) < 6:
        ttable = transpose(intable)
    else:
        ttable = intable
    print texttable(ttable, intable=intable, left=left)

# --------------------------------------------------------------------

if __name__ == "__main__":
    main()
