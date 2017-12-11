#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python; eval: (no-pyformat-mode) -*-
"""
"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import logging
import math
import operator
import optparse
import time
import itertools
import re

# --------------------------------------------------------------------------- #

logging.basicConfig(format="[%(asctime)s "
                    "%(funcName)s:%(lineno)s %(levelname)-5s] "
                    "%(message)s")

# --------------------------------------------------------------------------- #

def main():
  (opts, args) = getopts()
  if not args:
    args.append(time.time())
  rows = []
  for dt in args:
    time_struct = parse_time(dt, manual_formats=opts.in_format)
    # this adds the time zone name
    time_struct = time.localtime(time.mktime(time_struct))
    rows.append([str(time.mktime(time_struct))] +
                [time.strftime(fmt, time_struct)
                 for fmt in opts.out_format])
  print make_table(rows)

def make_table(table, delim=' ', ors='\n', left=True):
  transposed = itertools.izip_longest(*table, fillvalue='')
  widths = (max(len(fld) for fld in line) for line in transposed)
  lch = '-' if left else ''
  formats = ['%{0}{1}s'.format(lch, width) for width in widths]
  return ors.join('%s' % delim.join(format % (fld)
                                    for (format, fld) in zip(formats, line))
                  for line in table)

# from itertools recipes
def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return itertools.chain.from_iterable(
        itertools.combinations(s, r) for r in range(len(s)+1))

def explicit_parse_time(dt, manual_formats=None):
  for fmt in manual_formats:
    try:
      logging.debug("Trying to parse %s with %s", dt, fmt)
      return time.strptime(str(dt), fmt)
    except ValueError:
      pass

def epoch_parse_time(dt):
  # if we were given seconds since epoch, convert it to a time struct
  #
  # try to figure out if we got seconds since the epoch, milliseconds
  # since the epoch, or microseconds since the epoch.  Try each one
  # and see which one is closer to the current time.  "closer" is defined
  # by having the smallest absolute value of the log of the ratios.
  try:
    input = float(dt)
  except ValueError:
    pass
  current = time.time()
  divisors = (1.0, 1e3, 1e6)
  ratios = [abs(math.log(input / divisor / current)) for divisor in divisors]
  min_index, min_ratio = min(enumerate(ratios), key=operator.itemgetter(1))
  best_divisor = divisors[min_index]
  divisor_name = ("seconds", "milliseconds", "microseconds")[min_index]
  logging.debug("Current time: %s seconds since epoch", current)
  logging.debug("Input value: %s", input)
  logging.debug("Divisors: %s -> ratios: %s", divisors, ratios)
  logging.debug("Min ratio = %s, index = %s, divisor = %s, name = %s",
                min_ratio, min_index, best_divisor, divisor_name)
  logging.debug("Parsed %s as %s since epoch", dt, divisor_name)
  return time.localtime(input/best_divisor)

def get_all_formats():
  formats = {
      "tm_year": ["%Y", "%y"],
      "tm_mon": ["%m", "%b", "%B"],
      "tm_mday": ["%d"],
      "tm_hour": ["%H", "%I%p", "%I %p"],
      "tm_min": ["%M"],
      "tm_sec": ["%S"],
  }
  orders = [
      ["tm_year", "tm_mon", "tm_mday", "tm_hour", "tm_min", "tm_sec"],
      ["tm_hour", "tm_min", "tm_sec", "tm_year", "tm_mon", "tm_mday"],
      ["tm_mon", "tm_mday", "tm_year", "tm_hour", "tm_min", "tm_sec"],
      ["tm_hour", "tm_min", "tm_sec", "tm_mon", "tm_mday", "tm_year"],
  ]
  # Too slow to try all possible delims, so instead, require that the
  # caller replace all delims with space.
  #
  # delims = ["-", " ", "/", ":"]
  delims = [" "]
  for order in orders:
    for names in powerset(order):
      all_directives = [formats[name] for name in names]
      for directives in itertools.product(*all_directives):
        delim_list = [delims] * (len(directives)-1)
        for delim in itertools.product(*delim_list):
          fmt = "".join(itertools.chain.from_iterable(itertools.izip_longest(
              directives, delim, fillvalue="")))
          yield fmt, names

def loose_parse_time(dt, apply_defaults=True):
  try:
    simple_dt = " ".join(re.split("[-\s/:]", dt))
  except TypeError:
    return
  for fmt, names in get_all_formats():
    try:
      logging.debug("Trying to parse %s (from %s) with %s",
                    simple_dt, dt, fmt)
      struct = time.strptime(str(simple_dt), fmt)
    except ValueError:
      continue
    logging.debug("Parsed %s (from %s) with %s",
                  simple_dt, dt, fmt)
    if apply_defaults:
      now = time.localtime()
      time_dict = [(getattr(struct, key)
                    if key in names
                    else getattr(now, key))
                   for key in ["tm_year", "tm_mon", "tm_mday",
                               "tm_hour", "tm_min", "tm_sec"]]
      time_dict.extend([0, 1, -1])
      struct = time.struct_time(time_dict)
    return struct

def parse_time(dt, manual_formats=None, apply_defaults=True):
  struct = loose_parse_time(dt, apply_defaults=apply_defaults)
  if struct:
    return struct
  struct = explicit_parse_time(dt, manual_formats=manual_formats)
  if struct:
    return struct
  struct = epoch_parse_time(dt)
  if struct:
    return struct

  raise ValueError("Can't parse {0}".format(dt))

# --------------------------------------------------------------------------- #

def getopts():
  parser = optparse.OptionParser()
  parser.add_option("--verbose", action="store_true")
  parser.add_option("--log_level", help="The level to log at")
  parser.add_option("--out_format", help="The output format", action="append",
                    default=[
                        "%Y-%m-%d %H:%M:%S %Z",
                    ])
  parser.add_option("--in_format", help="The input format", action="append",
                    default=[
                        "%Y-%m-%d %H:%M:%S %Z",
                        "%Y-%m-%d %H:%M:%S",
                        "%m/%d/%Y %H:%M:%S",
                        "%Y-%m-%d",
                        "%m/%d/%Y",
                        "%m-%d",
                        "%m/%d",
                        "%b %d",
                        "%b %d %y",
                        "%b %d %Y",
                        "%H:%M:%S",
                        "%H:%M",
                    ])
  (opts, args) = parser.parse_args()

  if opts.verbose:
    logat(logging.DEBUG)

  if opts.log_level:
    logat(opts.log_level)

  return (opts, args)


def logat(level):
  if isinstance(level, basestring):
    level = getattr(logging, level.upper())
  logging.getLogger().setLevel(level)
  logging.info("Setting log level to %s", level)

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
  main()

# --------------------------------------------------------------------------- #
