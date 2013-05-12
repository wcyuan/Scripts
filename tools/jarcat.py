#!/usr/bin/env python
"""
jarcat.py [-list|-cat] [-j <jar>] [<file>]*

Description: Read a file out of a jar

In -list mode, treat the given file name as a pattern and list all
files in the jar matching that pattern.  The pattern only needs to
match the basename of the file.  This is the default if no file is
provided.

In -cat mode, cat the contents of files matching the given patterns.
This is the default if a file is provided.

If a jar file name is provided, and it's not an aboslute path, we'll
look for that jar in the current directory.

Created by: Conan Yuan (yuanc), 20120607
"""

from __future__ import absolute_import, division, with_statement

from   os.path                  import basename, exists, join as pathjoin
import re
from   zipfile                  import ZipFile

from   optparse                 import OptionParser
from   logging                  import getLogger, DEBUG, info

__version__ = "$Revision: 1.3 $"

##################################################################

def main():
    """
    Main body of the script.
    """
    opts,args = getopts()

    jars = [jar for jar_list in
            (find_jar(j) for j in opts.jarfiles)
            for jar in jar_list]
    info("Searching jars: {0}".format(', '.join(jars)))
    if opts.list:
        for (jar, patt, fn) in list_jar(jars, args):
            print ' '.join((jar, fn))
    elif opts.cat:
        read_jar(jars, args)

def getopts():
    """
    Parse the command-line options
    """
    parser = OptionParser()
    parser.add_option('-j', '--jarfiles', '--jar', '--jarfile',
                      action='append',
                      help='The jar file(s) to read')
    parser.add_option('--list', '--find', '--ls',
                      action='store_true',
                      help='List the files in the jar')
    parser.add_option('--cat',
                      action='store_true',
                      help='Cat the contents of files in the jar')
    parser.add_option('-i', '--case_insensitive',
                      action='store_true',
                      help='when listing, search case insensitively')
    parser.add_option('--verbose',
                      action='store_true',
                      help='verbose mode')
    opts,args = parser.parse_args()

    if opts.list and opts.cat:
        raise ValueError("Can't specify both list and cat");

    if not opts.list and not opts.cat:
        if len(args) > 0:
            opts.cat = True
        else:
            opts.list = True

    if opts.verbose:
        getLogger().setLevel(DEBUG)

    # Do further analysis here, if necessary
    return (opts,args)

##################################################################

def find_jar(jar):
    if exists(jar):
        yield jar
        return

    if not hasattr(find_jar, 'search_dirs'):
        dirs = []
        find_jar.search_dirs = ['.']
        find_jar.search_dirs.extend(pathjoin(d, 'java', 'jar') for d in dirs)

    for d in find_jar.search_dirs:
        full = pathjoin(d, jar)
        if exists(full):
            yield full

def read_jar(jars, files):
    found = dict((f, False) for f in files)
    for jar in jars:
        remaining = [f for f in files if not found[f]]
        if len(remaining) == 0:
            # If there are no files left, return, otherwise list_jar
            # will return every file.
            return
        for (x, patt, fn) in list_jar([jar], remaining):
            data = ZipFile(jar).read(fn)
            found[patt] = True
            if fn.endswith('.class'):
                info("Skipping class file {0} from {1} ({2})".
                     format(fn, jar, patt))
                continue
            info("Reading {0} from {1} ({2})".format(fn, jar, patt))
            print data

def list_jar(jars, patterns):
    for jar in jars:
        for fn in ZipFile(jar).namelist():
            if len(patterns) > 0:
                base = basename(fn)
                for patt in patterns:
                    if (fn == patt or
                        re.search(patt, base, re.IGNORECASE) is not None):
                        yield (jar, patt, fn)
            else:
                yield (jar, '', fn)

##################################################################

if __name__ == "__main__":
    main()
