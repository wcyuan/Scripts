#!/usr/bin/env python
"""
bucket.py --patt <input> [<bucket>]*

Take an input file, put each row in a bucket, then list the buckets
and the number of rows in each.

You can bucket each row by whether it matches a regexp, or by the
value in a given column.

For example, given the input:

 Circle     Blue
 Square abc Blue
 Circle     Red
 Circle     Blue
 Circle     Brown
 Rect   abc Purple
 Square     Purple
 Square     Red

You can bucket by the first column (the shape) with
 $ bucket.py 0
 Column-0 N
 Circle   4
 Rect     1
 Square   3

Columns are zero indexed.  You can bucket by the last column with
 $ bucket.py -1
 Column--1 N
 Blue      3
 Brown     1
 Purple    2
 Red       2

You can bucket by a regexp by just entering the regexp (as long as the
regexp cannot also be parsed as an integer)
 $ bucket.py abc
 /abc/ N
 False 6
 True  2

"""

# --------------------------------------------------------------------

from __future__ import absolute_import, division, with_statement

import argparse
import itertools
import logging
import re
import sys

OFS=' '
ORS='\n'

# --------------------------------------------------------------------

def main():
    args = getopts()

    buckets = Buckets(args.buckets)
    for line in args.input.readlines():
        buckets.add(line)
    print buckets

def getopts():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose',
                        action='store_true',
                        help='turn on verbose logging')
    parser.add_argument('--input',
                        type=argparse.FileType('r'),
                        default=sys.stdin,
                        help='the input file to read')
    parser.add_argument('buckets',
                        nargs='+',
                        help='buckets to use')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    return args

# --------------------------------------------------------------------

def texttable(table, left=False):
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
    widths = (max(len(fld) for fld in line)
              for line in itertools.izip_longest(*table, fillvalue=""))
    lc = '-' if left else ''
    formats = ["%{0}{1}s".format(lc, width) for width in widths]
    return ORS.join("%s" % OFS.join(format % fld
                                    for (format, fld) in zip(formats, line))
                    for line in table)

# --------------------------------------------------------------------

class Bucket(object):
    def __init__(self, bucket):
        self.bucket = bucket
        try:
            self.bucket = int(bucket)
            self.type = 'column'
        except ValueError:
            self.type = 'regexp'

    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, self.bucket)

    def __str__(self):
        if self.type == 'column':
            return 'Column-{0}'.format(self.bucket)
        else:
            return '/{0}/'.format(self.bucket)

    def get_value(self, line, splitline):
        if self.type == 'column':
            if len(splitline) > self.bucket:
                return splitline[self.bucket]
            else:
                return None
        else:
            m = re.search(self.bucket, line)
            return m is not None

class Buckets(object):
    def __init__(self, buckets):
        self.buckets = tuple(Bucket(b) for b in buckets)
        self.values = {}

    def add(self, line):
        splitline = line.split()
        values = tuple(b.get_value(line, splitline) for b in self.buckets)
        logging.debug(splitline)
        logging.debug(self.buckets)
        logging.debug(values)
        self.values[values] = self.values.setdefault(values, 0) + 1

    def __str__(self):
        table = [[str(b) for b in self.buckets] + ['N']]
        for values in sorted(self.values):
            table.append([str(v) for v in list(values) + [self.values[values]]])
        return texttable(table, left=True)

# --------------------------------------------------------------------

if __name__ == "__main__":
    main()
