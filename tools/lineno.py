#!/usr/bin/env python
"""
"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import fileinput
import itertools
import logging
import optparse

logging.basicConfig(format="[%(asctime)s "
                    "%(funcName)s:%(lineno)s %(levelname)-5s] "
                    "%(message)s")

# --------------------------------------------------------------------------- #


def main():
  (opts, args) = getopts()

  data = enumerate(fileinput.input(args))
  data = itertools.islice(data, opts.start, opts.end, opts.step)

  for (lineno, line) in data:
    if opts.bare:
      print line.rstrip("\n")
    else:
      print lineno, line.rstrip("\n")

def getopts():
  parser = optparse.OptionParser()
  parser.add_option("--verbose", action="store_true")
  parser.add_option("--log_level", help="The level to log at")
  parser.add_option("--start", type=int)
  parser.add_option("--end", type=int)
  parser.add_option("--num", type=int)
  parser.add_option("--step", type=int, default=1)
  parser.add_option("--bare", action="store_true")
  (opts, args) = parser.parse_args()

  if opts.verbose:
    logat(logging.DEBUG)

  if opts.log_level:
    logat(opts.log_level)

  if opts.num and opts.start and not opts.end:
    opts.end = opts.start + opts.num

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
