#!/usr/bin/env python
"""
Read from stdin, output it, and save that to a file.  The next
time we are called, if the stdin hasn't changed, then don't output it.
"""

from __future__ import absolute_import, division, with_statement

import optparse
import os
import sys

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

def main():
    """
    Main body of the script.
    """
    (_, statefile) = getopts()
    old_data = get_data(statefile)
    new_data = sys.stdin.read()
    if old_data != new_data:
        sys.stdout.write(new_data)
    write_data(statefile, new_data)

def getopts():
    """
    Parse the command-line options
    """
    parser = optparse.OptionParser()
    opts, args = parser.parse_args()
    if not args:
        statefile = DEFAULT_STATE
    elif len(args) == 1:
        statefile = args[0]
    else:
        raise ValueError("Too many arguments: {0}".
                         format(args))

    return opts, statefile

##################################################################

if __name__ == "__main__":
    main()
