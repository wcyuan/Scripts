#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python; eval: (no-pyformat-mode) -*-
"""
Some functions to compute the day of week for a given year.
Not meant to be efficient at all.
Inspired by https://teals-introcs.gitbooks.io/introduction-to-computer-science-principles/content/lesson_34.html
"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import datetime
import logging
import optparse
import subprocess

# --------------------------------------------------------------------------- #

logging.basicConfig(format="[%(asctime)s "
                    "%(funcName)s:%(lineno)s %(levelname)-5s] "
                    "%(message)s")

# --------------------------------------------------------------------------- #


def main():
  (opts, args) = getopts()

# --------------------------------------------------------------------------- #


def getopts():
  parser = optparse.OptionParser()
  parser.add_option("--verbose", action="store_true")
  parser.add_option("--log_level", help="The level to log at")
  parser.add_option("--no_write",
                    action="store_true",
                    help="Just print commands without running them")
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


def is_leap(year):
  if year % 400 == 0:
    return True
  elif year % 100 == 0:
    return False
  elif year % 4 == 0:
    return True
  else:
    return False


def year_days(year):
  return 366 if is_leap(year) else 365


def mon_days(mon, is_leap_year=False):
  if mon in (1, 3, 5, 7, 8, 10, 12):
    return 31
  if mon in (4, 6, 9, 11):
    return 30
  if mon == 2:
    return 29 if is_leap_year else 28
  raise ValueError("Invalid mon: {0}".format(mon))


def day_diff(elt, ref_elt, nday_func=None):
  diff = 0
  if not nday_func:
    nday_func = lambda x: 1
  if ref_elt > elt:
    incr = -1
    ref_elt, elt = elt, ref_elt
  else:
    incr = 1
  while elt != ref_elt:
    diff = (diff + nday_func(ref_elt)) % 7
    ref_elt += 1
  return (diff * incr) % 7


def dow(year, month, day):
  ref_year = 2000
  # ref_dow's units are 0=Sun, 1=Mon, 2=Tue, ... 6=Sat
  ref_dow = 6  # 2000-1-1 was a Saturday
  # when we output the dow, add 1 to translate it to
  # 1=Sun, 2=Mon, 3=Tue, ... 7=Sat
  ref_dow += day_diff(year, ref_year, year_days)
  ref_dow += day_diff(month, 1, lambda m: mon_days(m, is_leap(year)))
  ref_dow += day - 1
  return ref_dow % 7 + 1


def dow_golden(year, month, day):
  # returns 1=Mon, 2=Tue, 3=Wed, ... 7=Sun
  iso = datetime.date(year, month, day).isoweekday()
  # translate it to 1=Sun, 2=Mon, 3=Tue, ... 7=Sat
  return iso % 7 + 1


def check_dow(year, month, day):
  ours = dow(year, month, day)
  gauss = gauss_dow(year, month, day)
  golden = dow_golden(year, month, day)
  return ours != golden or gauss != golden


def check_years(years):
  return tuple((year, month, day)
               for year in years for month in range(1, 13)
               for day in range(1, mon_days(month, is_leap(year)) + 1)
               if check_dow(year, month, day))


def gauss_dow(year, month, day):
  # from https://en.wikipedia.org/wiki/Determination_of_the_day_of_the_week
  import math
  if month in (1, 2):
    year = year - 1
  month = (month - 2) % 12
  if month == 0:
    month = 12
  return (day + math.floor(2.6 * month - 0.2) + 5 * (year % 4) + 4 *
          (year % 100) + 6 * (year % 400)) % 7 + 1

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
  main()

# --------------------------------------------------------------------------- #
