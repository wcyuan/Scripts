#!/usr/bin/python
"""Wrapper around the gnu command shuf.

Handles the case where the file has a header.

It's literally a wrapper around:

$ { head -1 myfile.txt ; gawk 'NR > 1' myfile.txt | shuf -n 100000 ; }
or
$ savehead 1 myfile.txt shuf -n 100000

"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import
from __future__ import division
from __future__ import with_statement

import logging
import optparse
import subprocess

# --------------------------------------------------------------------------- #

logging.basicConfig(format="[%(asctime)s "
                    "%(funcName)s:%(lineno)s %(levelname)-5s] "
                    "%(message)s")

# --------------------------------------------------------------------------- #


def main():
  opts, args = getopts()
  if opts.num_out_lines:
    out_head = "-n {0}".format(opts.num_out_lines)
  else:
    out_head = ""
  for arg in args:
    cmd = (
        "{{ head -{h} {fn}; gawk 'NR > {h}' {fn} | shuf {out_head}; }}".format(
            h=opts.num_header_lines,
            out_head=out_head,
            fn=arg))
    logging.info(cmd)
    proc = subprocess.Popen(cmd, shell=True)
    proc.communicate()


def getopts():
  parser = optparse.OptionParser()
  parser.add_option("--verbose", action="store_true")
  parser.add_option("--log_level", help="The level to log at")
  parser.add_option("--num_header_lines", "--header", type=int, default=1)
  parser.add_option("-n", "--num_out_lines", type=int)
  opts, args = parser.parse_args()

  if opts.verbose:
    logat(logging.DEBUG)

  return opts, args


def logat(level):
  if isinstance(level, basestring):
    level = getattr(logging, level.upper())
  logging.getLogger().setLevel(level)
  logging.info("Setting log level to %s", level)

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
  main()

# --------------------------------------------------------------------------- #
