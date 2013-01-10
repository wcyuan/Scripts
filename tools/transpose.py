#!/usr/bin/env python
"""
transpose.py --patt <pattern> [<file>]

Take tabular input that looks like:
 a b c
 1 2 3
 4 5 6

And output it transposed:
 a 1 4
 b 2 5
 c 3 6

Tries to be intelligent about how to parse the tabular input.  Tries
to guess whether the input is fixed width or delimited.  If delimited,
tries to guess what the separator is.

Takes an optional pattern
"""

# --------------------------------------------------------------------
from __future__ import absolute_import, division, with_statement

from contextlib   import contextmanager
from itertools    import izip_longest
from optparse     import OptionParser
from subprocess   import Popen, PIPE

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
    opts, args = parser.parse_args()

    opts = dict((v, getattr(opts, v))
                for v in ('patt', 'delim', 'left', 'reverse', 'kind'))

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
            # XXX not sure this works...
            proc = Popen([cmd, fn], stdout=PIPE)
            proc.wait()
            yield proc.stdout
            return
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
        delim = [m.start() for m in re.finditer('[^\s]+', header)]
    else:
        raise ValueError ("Invalid input kind: %s" % kind)
    return (kind, delim)

def is_header(line, comment_char):
    if not is_comment(line, comment_char):
        return True
    if any(line.startswith(pfx) for pfx in HEADERS):
        return True
    return False

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
        # XXX have to do something about #@desc
        return re.split(delim, line)
    elif kind == 'fixed':
        raise NotImplementedError
    else:
        raise ValueError ("Invalid input kind: %s" % kind)

def read_input(fd, patt=None, delim=None, comment='#',
               kind='delimited', reverse=False):
    table = []
    header = None
    info = None
    for line in fd:
        line = line.strip(IRS)
        if header is None and is_header(line, comment):
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
                   comment='#', kind='delimited', reverse=False):
    intable = list(read_input(fd, patt=patt, delim=delim,
                              comment=comment, kind=kind,
                              reverse=reverse))
    if len(intable) < 6:
        ttable = transpose(intable)
    else:
        ttable = intable
    print texttable(ttable, intable=intable, left=left)

# --------------------------------------------------------------------

if __name__ == "__main__":
    main()
