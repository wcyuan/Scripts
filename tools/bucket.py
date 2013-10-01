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
 $ bucket.py 1
 Column-0 N
 Circle   4
 Rect     1
 Square   3

You can bucket by the last column with
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

If your input has headers and no blank fields

 Shape  Name Color
 Circle -    Blue
 Square abc  Blue
 Circle -    Red
 Circle -    Blue
 Circle -    Brown
 Rect   abc  Purple
 Square -    Purple
 Square -    Red

You can bucket by column name
 $ bucket.py --header Shape
 Shape  N
 Circle 4
 Rect   1
 Square 3


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

    lines = args.input.readlines()
    if args.header:
        header = lines.pop(0)
    else:
        header = None
    buckets = Buckets(args.buckets, header=header)
    for line in lines:
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
    parser.add_argument('--header',
                        action='store_true',
                        help='first line is a header')
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
    def __init__(self, bucket, header=None):
        self.bucket = bucket
        try:
            self.bucket = int(bucket)
            self.type = 'column'
        except ValueError:
            if header is not None:
                try:
                    index = header.split().index(bucket)
                    self.type = 'column'
                    self.bucket = index + 1
                except ValueError:
                    self.type = 'regexp'
            else:
                self.type = 'regexp'
        self.name = self._make_name(header)


    def __repr__(self):
        return "{0}({1})".format(self.__class__.__name__, self.bucket)

    def __str__(self):
        return self.name

    @classmethod
    def _index(cls, values, idx):
        if idx >= 0 and len(values) >= idx:
            # allow people to enter one indexed column numbers
            return values[idx-1]
        elif idx < 0 and len(values) >= -1 * idx:
            # but if the column number is negative, just use it
            return values[idx]
        else:
            return None

    def _make_name(self, header=None):
        if self.type == 'column':
            if header is not None:
                return str(self._index(header.split(), self.bucket))
            else:
                return 'Column-{0}'.format(self.bucket)
        else:
            return '/{0}/'.format(self.bucket)

    def get_value(self, line, splitline):
        if self.type == 'column':
            return self._index(splitline, self.bucket)
        else:
            m = re.search(self.bucket, line)
            return m is not None

class Buckets(object):
    def __init__(self, buckets, header=None):
        self.buckets = tuple(Bucket(b, header=header)
                             for b in buckets)
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
