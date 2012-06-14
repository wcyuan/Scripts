#!/usr/local/bin/python
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

from   os.path                  import basename, exists
import re
from   zipfile                  import ZipFile

from   optparse                 import OptionParser
from   logging                  import getLogger

__version__ = "$Revision: 1.3 $"

##################################################################

LOGGER = getLogger(__name__)

def main():
    """
    Main body of the script.
    """
    opts,args = getopts()

    jars = [jar for jar_list in
            (find_jar(j) for j in opts.jarfiles)
            for jar in jar_list]
    LOGGER.info("Searching jars: {0}".format(', '.join(jars)))
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
    opts,args = parser.parse_args()

    if opts.list and opts.cat:
        raise ValueError("Can't specify both list and cat");

    if not opts.list and not opts.cat:
        if len(args) > 0:
            opts.cat = True
        else:
            opts.list = True

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
        find_jar.search_dirs.extend('{0}/java/jar'.format(d) for d in dirs)

    for d in find_jar.search_dirs:
        full = '%s/%s' % (d, jar)
        if exists(full):
            yield full

def read_jar(jars, files):
    found = dict((f, False) for f in files)
    for jar in jars:
        for (x, patt, fn) in list_jar([jar],
                                      [f for f in files if not found[f]]):
            data = ZipFile(jar).read(fn)
            found[patt] = True
            if fn.endswith('.class'):
                LOGGER.info("Skipping class file {0} from {1} ({2})".
                     format(fn, jar, patt))
                continue
            LOGGER.info("Reading {0} from {1} ({2})".format(fn, jar, patt))
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