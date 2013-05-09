#!/usr/local/bin/python
"""
Check that two paths are the same.

Sys#378645

Randomly choose a file in the path and compare them to make sure they
are the same.

"""

from __future__ import absolute_import, division, with_statement

from subprocess import check_call
from random     import randrange
from os.path    import join as pathjoin, isdir, exists, split as pathsplit
from os         import listdir
import re
from optparse   import OptionParser

# ------------------------------------------------------------------

def main():
    (opts, root1, root2, files) = getopt()

    if len(files) == 0:
        files = [randfile(root1)
                 for _ in range(opts.num)]
        print "Running on {0}".format(', '.join(files))

    for fn in files:
        fn1 = pathjoin(root1, fn)
        fn2 = pathjoin(root2, fn)
        compare(fn1, fn2)

# ------------------------------------------------------------------

def getopt():
    parser = OptionParser()
    parser.add_option('--num', '-n',
                      type=int,
                      default=1,
                      help='number of files to try')
    opts, args = parser.parse_args()
    if len(args) < 2:
        raise ValueError("Need at least two args")

    root1 = args[0]
    root2 = args[1]

    return (opts, root1, root2, args[2:])

# ------------------------------------------------------------------

def parts(path):
    """
    Split a path by the path separator (/)

    run doctests with the command:

    python -m doctest -v randdiff.py

    >>> parts('/')
    ('/',)
    >>> parts('2011')
    ('2011',)
    >>> parts('2011/')
    ('2011',)
    >>> parts('/2011')
    ('/', '2011')
    >>> parts('a/b')
    ('a', 'b')
    >>> parts('a/b/')
    ('a', 'b')
    >>> parts('/a/b')
    ('/', 'a', 'b')
    >>> parts('/a/b/')
    ('/', 'a', 'b')
    >>> pathjoin(*(parts('/')))
    '/'
    >>> pathjoin(*(parts('2011')))
    '2011'
    >>> pathjoin(*(parts('2011/')))
    '2011'
    >>> pathjoin(*(parts('/2011')))
    '/2011'
    >>> pathjoin(*(parts('a/b')))
    'a/b'
    >>> pathjoin(*(parts('a/b/')))
    'a/b'
    >>> pathjoin(*(parts('/a/b')))
    '/a/b'
    >>> pathjoin(*(parts('/a/b/')))
    '/a/b'
    >>>

    """
    (direc, base) = pathsplit(path)
    if direc == '':
        return (base,)

    if direc == '/':
        direc = (direc,)
    else:
        direc = parts(direc)

    if base == '':
        return direc
    else:
        return direc + (base,)

def randfile(orig):
    """
    Pick a random file somewhere in the directory orig.

    Returns a relative path from orig
    """
    curr = orig
    if not exists(curr):
        raise ValueError("Can't find {0}".format(curr))
    while isdir(curr):
        ls = listdir(curr)
        curr = pathjoin(curr, ls[randrange(len(ls))])
    return pathjoin(*(parts(curr)[len(parts(orig)):]))

def compare(fn1, fn2):
    """
    Make sure that two files are the same
    """
    if not exists(fn1):
        raise ValueError("Can't find {0}".format(fn1))
    if not exists(fn2):
        raise ValueError("Can't find {0}".format(fn2))
    check_call(["ls", "-l", fn1, fn2])
    cmd = ['diff', fn1, fn2]
    print "Running {0}".format(cmd)
    check_call(cmd);

# ------------------------------------------------------------------

if __name__ == '__main__':
    main()
