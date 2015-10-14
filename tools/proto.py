#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Parses protos in text format.

Protos often have lots of complicated members, with lots of nesting
and repetition.  We represent all values as strings, all objects as
dicts, and all fields as lists (since they could be repeated, and we
don't know which are repeated and which aren't).  So a proto is a dict
of lists (of dicts of lists of dicts of lists of dicts, etc).

Protos can be seen as trees, represented as dicts of lists.  The
elements of the lists are either strings (in which case the node is a
leaf) or sub-Protos (i.e., another dict of lists).

EXAMPLES:

  ipython -i proto.py ~/data/proto.txt

  ipython -i ~/code/bin/proto.py *.txt

This command will parse the protos, then drop you in an ipython shell
with the variable "parsed" set to a map from filename to the protos
found in that file.

"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import contextlib
import gzip
import itertools
import json
import logging
import optparse
import os
import re

# --------------------------------------------------------------------------- #

logging.basicConfig(format="[%(asctime)s "
                    "%(funcName)s:%(lineno)s %(levelname)-5s] "
                    "%(message)s")

# --------------------------------------------------------------------------- #


def main():
  (opts, args) = getopts()

  if opts.verbose:
    logat(logging.DEBUG)
  if opts.log_level:
    logat(opts.log_level)

  parsed = {}
  if opts.sample:
    parsed["sample"] = parse(sample_response())
  for filename in args:
    parsed[filename] = parse(filename=filename)
  print parsed
  return parsed


def getopts():
  parser = optparse.OptionParser()
  parser.add_option("--verbose", action="store_true")
  parser.add_option("--log_level", help="The level to log at")
  parser.add_option("--no_write",
                    action="store_true",
                    help="Just print commands without running them")
  parser.add_option("--sample", action="store_true")
  return parser.parse_args()


def logat(level):
  if isinstance(level, basestring):
    level = getattr(logging, level.upper())
  logging.getLogger().setLevel(level)
  logging.info("Setting log level to %s", level)

# --------------------------------------------------------------------------- #


def file_lines(filename):
  with zopen(filename) as fd:
    for line in fd:
      yield line


@contextlib.contextmanager
def zopen(filename, mode="r"):
  if filename.endswith(".gz"):
    with gzip.open(filename, mode=mode) as fd:
      yield fd
  else:
    with open(filename, mode=mode) as fd:
      yield fd

# --------------------------------------------------------------------------- #


# unused
def enc(string):
  return string.encode("utf-8").replace('"', "")


# http://bytes.com/topic/python/answers/743965-converting-octal-escaped-utf-8-a
def decode(encoded):
  """Decoding octal utf-8
  """
  decoded = encoded.encode("utf-8")
  matches = set()
  for octc in re.findall(r"\\(\d{3})", decoded):
    matches.add(octc)
  for octc in matches:
    decoded = decoded.replace(r"\%s" % octc, chr(int(octc, 8)))
  try:
    return decoded.decode("utf8")
  except UnicodeDecodeError as e:
    return decoded


# Unused
def make_table(table, delim=",", ors="\n", left=True, align=False):
  transposed = itertools.izip_longest(*table, fillvalue=u"")
  widths = (min(25, max(len(fld) for fld in line)) for line in transposed)
  lch = "-" if left else ""
  if align:
    formats = ["%{0}{1}s".format(lch, width) for width in widths]
  else:
    formats = ["%s" for width in widths]
  return ors.join(delim.join(fmt % fld for (fmt, fld) in zip(formats, line))
                  for line in table)

# --------------------------------------------------------------------------- #


class ProtoList(list):
  """A list whose repr summarizes long lists.

  Protos' string representations can be long and difficult to read.
  The purpose of this class is to show summary information instead of
  showing the full proto.

  This class inherits from list, and if the string representation of
  the list is relatively short (<= 50 characters), then it behaves a
  lot like a list.  But if the string representation is long, then
  when you take the instance's repr, it shows a summary, like:

    ProtoList(len=10, depth=3, height=6)

  This means that there are 10 elements in the list, this node is 3
  hops from the root of the tree (the outermost Proto), and this node
  is 6 levels up from the farthest leaf.

  """

  def __init__(self, seq, depth=0, *args, **kwargs):
    # keep track of this node's depth in the tree
    self._depth = depth
    if not seq:
      seq = ()
    return super(ProtoList, self).__init__(seq, *args, **kwargs)

  # fullstring returns the string that a normal list would return
  fullstring = list.__repr__

  # summary is a string representation that just shows a bit of key
  # information.  Most importantly, it does not recursively include
  # the string representation of each sub-element.  But it does show
  # the height of the tree, which does require visiting each
  # sub-element.
  def summary(self, show_height=True):
    val = "{cn}(len={len}, depth={depth}".format(
        cn=self.__class__.__name__,
        len=len(self),
        depth=self._depth)
    if show_height:
      val += ", height={height})".format(height=self.height())
    else:
      val += ")"
    return val

  # If you compute the height naively, you get exponential explosion.
  # So you have to make sure to keep a cache.  However, since this is
  # a mutable data structure, you need to know when to invalidate the
  # cache (i.e., any time anything is added to the tree).  The easiest
  # way is to basically use a temporary cache that is only used for
  # this single height computation.  So each call to height has to
  # visit every node once, which isn't great, but it's fine for medium
  # size trees (depth of around 10-20), which seems to work for most
  # protos we care about.
  def height(self, cache=None):
    if not cache:
      cache = {}
    if id(self) not in cache:
      val = 0
      for elt in self:
        if isinstance(elt, dict):
          for vl in elt.itervalues():
            if hasattr(vl, "height"):
              val = max(val, vl.height(cache=cache) + 1)
        elif hasattr(elt, "height"):
          val = max(val, elt.height(cache=cache) + 1)
        else:
          val = max(val, 1)
      cache[id(self)] = val
    return cache[id(self)]

  def string(self, show_height=True):
    full = self.fullstring()
    if len(full) > 50:
      return self.summary(show_height=show_height)
    else:
      return full

  def __repr__(self):
    return self.string()

  def search(self, patt, path=None, case_insensitive=True):
    """Search for a string in a proto.
    """
    if not path:
      path = []
    if case_insensitive:
      patt = patt.lower()

    def strmatch(patt, strng):
      if not isinstance(strng, basestring):
        return False
      if case_insensitive:
        # Assumes that patt is already lowered
        return patt in strng.lower()
      else:
        return patt in strng

    def eltmatch(patt, elt):
      if isinstance(elt, basestring):
        return strmatch(patt, elt)
      else:
        return strmatch(patt, str(elt))

    for ii, elt in enumerate(self):
      if isinstance(elt, dict):
        # For dicts, match against the key or the value
        for ky, vl in elt.iteritems():
          if strmatch(patt, ky) or strmatch(patt, vl):
            print path, ii, ky, vl
          if isinstance(vl, ProtoList):
            vl.search(patt,
                      path=path + [ii, ky],
                      case_insensitive=case_insensitive)
      elif isinstance(elt, ProtoList):
        elt.search(patt, path=path + [ii], case_insensitive=case_insensitive)
      elif eltmatch(patt, elt):
        print path, ii, elt

# --------------------------------------------------------------------------- #


# unused
def parse_blocks(string):
  level = 0
  block = ""
  for c in string:
    block += c
    if c == "{":
      level += 1
    if c == "}":
      level -= 1
    if level == 0:
      if block:
        yield block[1:-1]
      block = ""


def parse_iter(lines=None, filename=None, depth=0):
  """Parses the text format of a Protobuf

  This returns an iterator, so you have to tuplize it.  Then you'll
  get a single element, which is a dictionary with a single key,
  "result".  The value for that key will be a list of all the
  responses.

  In general, we don't know how many of a value there will be.  I.e.,
  there could be a single candidate or there could be many candidates.
  There could be a single key or there could be many keys.  So we
  assume that all fields are lists.  The clients of the data should
  know which fields are really lists and which fields you just need to
  take the [0] element of.
  """
  if not lines:
    if filename:
      lines = file_lines(filename)
    else:
      raise ValueError("No data to parse")
  if isinstance(lines, basestring):
    lines = lines.split("\n")
  # if we were given a list, we have to make it a generator so that on
  # our recursive call, we start from where the iterator left off, not
  # at the beginning of the list.
  lines = iter(lines)
  block = {}
  for line in lines:
    # TODO: decoding the line again could cause problems if the line
    # has already been decoded
    line = decode(line).lstrip().rstrip("\n\r")
    if line == "{" and not block:
      # We are ready to accept protos that are not wrapped in braces.
      # If we see a proto that is wrapped in braces, well we already
      # stop if we see a close brace, so all we need to add is to
      # ignore the opening brace.
      continue
    if line == "}":
      yield block
      block = {}
      continue
    if ": " in line:
      var, val = line.split(": ", 1)
    elif line.endswith(" {"):
      var = line[:-2]
      val = next(parse_iter(lines, depth=depth + 1))
    else:
      if line.strip():
        logging.warning("Can't parse line %s (file %s)", line, filename)
      continue
    block.setdefault(var, ProtoList((), depth=depth)).append(val)
  if block:
    yield block


def parse(*args, **kwargs):
  """Run parse_iter but return a tuple

  # empty proto
  >>> parse("")
  Traceback (most recent call last):
  ...
  ValueError: No data to parse

  # a single value
  >>> parse("a: 1")
  ({u'a': [u'1']},)

  # a single value in braces.  Braces must be on separate lines by themselves.
  >>> parse("{\\na: 1\\n}")
  ({u'a': [u'1']},)

  # a list of values
  >>> parse("a: 1\\na: 2\\na: 3")
  ({u'a': [u'1', u'2', u'3']},)

  # a complex object breaking up the list
  >>> parse("a: 1\\na: 2\\na: 3\\nb {\\nc: x\\nc: y\\n}\\na: 4")
  ({u'a': [u'1', u'2', u'3', u'4'], u'b': [{u'c': [u'x', u'y']}]},)

  # nested complex objects
  >>> parse(          # doctest: +NORMALIZE_WHITESPACE
  ... "a: 1\\na: 2\\na: 3\\nb {\\nc: x\\nc: y\\nc {\\nz: 6\\n}\\n}\\na: 4")
  ({u'a': [u'1', u'2', u'3', u'4'], \
   u'b': [{u'c': [u'x', u'y', {u'z': [u'6']}]}]},)

  # ProtoList summary
  >>> ProtoList(parse("a: 1\\na: 2\\na: 3\\nb {\\nc: x\\nc: y\\n}\\na: 4"))
  ProtoList(len=1, depth=0, height=3)

  # multiple protos in a single string
  >>> parse(          # doctest: +NORMALIZE_WHITESPACE
  ...       "{\\na: 1\\na: 2\\na: 3\\n \
              b {\\nc: x\\nc: y\\n}\\n}\\n \
             {\\na: 4\\n}\\n{\\na: 4\\n}")
  ({u'a': [u'1', u'2', u'3'], u'b': [{u'c': [u'x', u'y']}]}, \
   {u'a': [u'4']}, \
   {u'a': [u'4']})

  """
  return tuple(parse_iter(*args, **kwargs))

# --------------------------------------------------------------------------- #


def sample_response():
  return """
  result {
    key: "\357\275\212\357\275\222\345\214\227\346\265\267\351\201\223\343\203\220\343\202\271"
    candidate {
      mid: "/m/0j_3tph"
      name: "JR Hokkaido Bus Company"
      score: 0.150605774486
      decision: NO_MATCH
    }
    candidate {
      mid: "/m/03cfjg_"
      name: "JR Bus"
      score: 0.000991709262653
      decision: NO_MATCH
    }
  }
  result {
    key: "\357\275\212\357\275\222\345\233\233\345\233\275\343\203\220\343\202\271"
    candidate {
      mid: "/g/11bc8ccbqc"
      name: "\357\274\252\357\274\262\345\233\233\345\233\275\343\203\220\343\202\271\351\253\230\351\200\237"
      score: 0.148700021658
      decision: NO_MATCH
    }
    candidate {
      mid: "/g/121w1jsf"
      name: "\343\202\270\343\202\247\343\202\244\343\202\242\343\203\274\343\203\253\345\233\233\345\233\275"
      score: 0.140173489149
      decision: NO_MATCH
    }
    candidate {
      mid: "/m/03cfjg_"
      name: "JR Bus"
      score: 0.00991709262653
      decision: NO_MATCH
    }
    candidate {
      mid: "/g/122njc5v"
      name: "\346\235\276\345\261\261\351\253\230\347\237\245\346\200\245\350\241\214\347\267\232"
      score: 1.26111478455e-05
      decision: NO_MATCH
    }
  }
""".decode("utf-8")

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
  print "The parsed protos will appear in the variable 'parsed'"
  parsed = main()

# --------------------------------------------------------------------------- #
