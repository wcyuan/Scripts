#!/usr/bin/env python
"""
Read from stdin, output it, and save that to a file.  The next
time we are called, if the stdin hasn't changed, then don't output it.
"""

from __future__ import absolute_import, division, with_statement

import logging
import optparse
import os
import sys

logging.basicConfig(format='[%(asctime)s '
                    '%(funcName)s:%(lineno)s %(levelname)-5s] '
                    '%(message)s')

DEFAULT_STATE = '/tmp/output_if_changed.out'

#################################################################

def write_data(filename, data):
    with open(filename, 'w') as fd:
        fd.write(data)

def get_data(filename):
    if not os.path.exists(filename):
        return None
    with open(filename) as fd:
        return fd.read()

def splitlines(data, eol="\n"):
    """
    Split a string into lines, but keep the newline character.
    """
    if data is None:
        return ()
    return tuple(d + eol for d in data.split(eol))

def udiff(before, after):
    import difflib
    return difflib.unified_diff(splitlines(before), splitlines(after),
                                fromfile='old-output', tofile='new-output')

def main():
    """
    Main body of the script.
    """
    (opts, statefile) = getopts()
    old_data = get_data(statefile)
    new_data = sys.stdin.read()
    if old_data != new_data:
        if opts.diffs:
            for line in udiff(old_data, new_data):
                sys.stdout.write(line)
        elif opts.show_blanks and new_data == '':
            print "<new output is empty>"
        else:
            sys.stdout.write(new_data)
        if opts.no_write:
            logging.info("NO WRITE: Not storing changes to %s", statefile)
        else:
            write_data(statefile, new_data)

def getopts():
    """
    Parse the command-line options
    """
    parser = optparse.OptionParser()
    parser.add_option('--diffs', action='store_true')
    parser.add_option('--show_blanks', action='store_true')
    parser.add_option('--no_write', action='store_true')
    parser.add_option('--verbose', action='store_true')
    opts, args = parser.parse_args()
    if not args:
        statefile = DEFAULT_STATE
    elif len(args) == 1:
        statefile = args[0]
    else:
        raise ValueError("Too many arguments: {0}".
                         format(args))

    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    return opts, statefile

##################################################################

if __name__ == "__main__":
    main()
