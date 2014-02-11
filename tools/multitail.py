#!/usr/bin/env python
'''
Tail many files at once

Related to, but different from:

http://www.slideshare.net/dabeaz/python-generator-hacking/82
https://github.com/kasun/python-tail
http://stackoverflow.com/questions/5725051/tail-multiple-logfiles-in-python
'''
# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import optparse
import logging
import time

# --------------------------------------------------------------------------- #

def main():
    (opts, args) = getopts()
    if opts.write:
        slow_write(args, s=opts.sleep)
    else:
        for (fn, line) in multitail(args, s=opts.sleep,
                                    from_beginning=opts.from_beginning):
            print fn, line.strip()

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--sleep',  type=float, default=1)
    parser.add_option('--verbose',  action='store_true')
    parser.add_option('--write',  action='store_true')
    parser.add_option('--from_beginning',  action='store_true')
    (opts, args) = parser.parse_args()
    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    return (opts, args)

# --------------------------------------------------------------------------- #

def tail(filename, from_beginning=False):
    with open(filename) as fh:
        logging.info("Opening {0}".format(filename))
        if not from_beginning:
            # go to the end of the file
            fh.seek(0, 2)
        while True:
            curr_position = fh.tell()
            line = fh.readline()
            if not line:
                fh.seek(curr_position)
                logging.debug("File {0} is not ready".format(filename))
                yield None
            else:
                yield line

def multitail(filenames, s=1, from_beginning=False):
    tails = tuple((fn, tail(fn, from_beginning=from_beginning))
                  for fn in filenames)
    while True:
        has_data = False
        for (fn, ftail) in tails:
            line = ftail.next()
            if line is not None:
                has_data = True
                yield (fn, line)
        if not has_data:
            time.sleep(s)

# --------------------------------------------------------------------------- #

def slow_write(filenames, s=1):
    """
    This is just a function that occasionally appends to some files,
    to help test multitail

    For example try, in one window
    $ multitail.py --write --sleep 0.4 one two three

    And in another window:
    $ multitail.py one two three

    """
    ii = 0
    while True:
        for fn in filenames:
            with open(fn, 'a') as fd:
                fd.write('{0}\n'.format(ii))
        time.sleep(s)
        ii += 1

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()

# --------------------------------------------------------------------------- #
