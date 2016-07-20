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

  Use this command to read a bunch of files, each of which contains a
  proto or a list of protos, and output the result to stdout.

  $ proto.py *.txt

  Or, use this command to start IPython with that data read into a
  variable called "parsed", which will be a dict from filename to the
  protos parsed from that file.

  $ ipython -i proto.py ~/my/file/name.txt.txt
  $ ipython -i proto.py *.txt

  Here are examples (and doctests) of how to use this library from
  inside of python.

  >>> import proto
  >>> proto.parse( # doctest: +ELLIPSIS
  ... filename="/dev/null")
  (...)
  >>> proto.parse(filename="/dev/null")
  ()
  >>> p = proto.ProtoDict()
  >>> p.add('mykey', 'myvalue')
  {'mykey': myvalue}
  >>> p.add('mykey2', {4: 5, 6: 7})
  {'mykey2': [{4: 5, 6: 7}], 'mykey': myvalue}
  >>> p.mykey2[0]._4
  5
  >>> print p.full_proto_string().encode("utf-8")
  mykey2 {
    4: 5
    6: 7
  }
  mykey: myvalue
  >>> p = proto.ProtoDict.from_dict(
  ... {'request':
  ...  {'location':
  ...   {'center':
  ...    { 'lat': 4,
  ...      'lng': 5,
  ... }}}})
  >>> p
  {'request': ProtoList(len=1, depth=0, height=4)}
  >>> print p.full_proto_string()
  request {
    location {
      center {
        lat: 4
        lng: 5
      }
    }
  }
  >>> print p.full_proto_string(pretty=False)
  request { location { center { lat: 4, lng: 5 } } }
  >>> p == parse(p.full_proto_string())[0]
  True
  >>> p.request[0].location[0].add('max_radius_meters', 100)
  {'max_radius_meters': 100, 'center': [{'lat': 4, 'lng': 5}]}
  >>> p = parse('''single_request {
  ...   id {
  ...     v1: 4123124123123
  ...     v2: 1502959385023
  ...   }
  ... }
  ... single_request {
  ...   id {
  ...     v1: 20593950293402934
  ...     v2: 19289402093012930
  ...   }
  ... }
  ... single_request {
  ...   id {
  ...     v1: 10592003940293949394
  ...     v2: 89297492883749283839
  ...   }
  ... }
  ... ''')
  >>> print p[0].full_proto_string()
  single_request {
    id {
      v1: 4123124123123
      v2: 1502959385023
    }
  }
  single_request {
    id {
      v1: 20593950293402934
      v2: 19289402093012930
    }
  }
  single_request {
    id {
      v1: 10592003940293949394
      v2: 89297492883749283839
    }
  }
  >>> p[0] == parse(p[0].full_proto_string())[0]
  True
  >>> p[0].follow("single_request", 1, "id", 0, "v1", 0)
  u'20593950293402934'
  >>> p[0].follow("single_request", 1, "id", 0)
  {u'v1': 20593950293402934, u'v2': 19289402093012930}
  >>> p[0].single_request.follow(1, "id", 0, "v1", 0)
  u'20593950293402934'
  >>> p = parse('''single_request: {
  ...   id: {
  ...     v1: 4123124123123 # this is a comment
  ...     v2: '150295 9385023' # this is a multiline string
  ...   }
  ... }
  ... single_request {
  ...   id {
  ...     v1: 10592003940293949394
  ...     v2: 89297492883749283839
  ...   }
  ... }
  ... ''')
  >>> p[0]
  {u'single_request': ProtoList(len=2, depth=0, height=3)}
  >>> p[0].single_request[0].id[0].v2[0]
  u"'150295 9385023'"

This command will parse the protos, then drop you in an ipython shell
with the variable "parsed" set to a map from filename to the protos
found in that file.

"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import collections
import contextlib
import gzip
import itertools
import json
import logging
import optparse
import os
import re
import sys

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
    print "Reading ", filename
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
  filename = os.path.expanduser(filename)
  if filename.endswith(".gz"):
    with gzip.open(filename, mode=mode) as fd:
      yield fd
  else:
    if not os.path.exists(filename) and filename == "-":
      yield sys.stdin
    else:
      with open(filename, mode=mode) as fd:
        yield fd

# --------------------------------------------------------------------------- #


# http://bytes.com/topic/python/answers/743965-converting-octal-escaped-utf-8-a
def decode(encoded):
  """Decoding octal utf-8
  """
  try:
    decoded = encoded.encode("utf-8")
  except UnicodeDecodeError as e:
    decoded = encoded
  matches = set()
  for octc in re.findall(r"\\(\d{3})", decoded):
    matches.add(octc)
  for octc in matches:
    try:
      decoded = decoded.replace(r"\%s" % octc, chr(int(octc, 8)))
    except ValueError:
      logging.debug("Skipping non-octal: %s", octc)
  try:
    return decoded.decode("utf8")
  except UnicodeDecodeError as e:
    pass
  try:
    return decoded.decode("latin-1")
  except UnicodeDecodeError as e:
    return decoded

# --------------------------------------------------------------------------- #


class ProtoMixin(object):

  def follow(self, *path):
    if not path:
      return self
    elt = self[path[0]]
    if isinstance(elt, ProtoMixin) or isinstance(elt, ProtoMixin):
      return elt.follow(*path[1:])
    else:
      return elt

  @classmethod
  def apply_auto_quote(cls, elt):
    if not isinstance(elt, basestring):
      logging.debug("Not quoting non-string '%s'", elt)
      return elt
    if all(c.isupper() for c in elt if c.isalpha()):
      logging.debug("Not quoting uppercase '%s'", elt)
      return elt
    if elt[0] == '"' and elt[-1] == '"':
      logging.debug("Element already quoted '%s'", elt)
      return elt
    try:
      float(elt)
      logging.debug("Not quoting string that looks like a number '%s'", elt)
      return elt
    except ValueError:
      pass
    if elt.lower() == "true" or elt.lower() == "false":
      logging.debug("Not quoting string that looks like a bool '%s'", elt)
      return elt
    logging.debug("Quoting: '%s'", elt)
    return '"{0}"'.format(elt)

  @classmethod
  def to_unicode(cls, elt):
    if isinstance(elt, unicode):
      return elt
    return unicode(elt, errors="replace")


class ProtoList(list, ProtoMixin):
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
    val = "{cn}(len={len}, depth={depth}".format(cn=self.__class__.__name__,
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
    try:
      # try to catch ascii/unicode errors
      full = self.fullstring()
    except:
      full = None
    if not full or len(full) > 50:
      return self.summary(show_height=show_height)
    elif len(self) == 1 and not isinstance(self[0], ProtoDict):
      return self[0]
    else:
      return full

  def full_proto_string(self, pretty=True, indent_amount=0, auto_quote=False):
    if pretty:
      ors = u"\n"
      indent = u"  " * indent_amount
    else:
      ors = u" "
      indent = u""

    def print_elt(elt):
      if isinstance(elt, ProtoDict):
        return elt.full_proto_string(pretty=pretty,
                                     indent_amount=indent_amount,
                                     auto_quote=auto_quote)
      else:
        selt = ProtoMixin.apply_auto_quote(elt) if auto_quote else elt
        return u"{0}{1}".format(indent, ProtoMixin.to_unicode(selt))

    return ors.join(print_elt(elt) for elt in self)

  def is_simple(self):
    return not any(isinstance(elt, ProtoDict) for elt in self)

  def __unicode__(self):
    return self.string()

  def __repr__(self):
    return unicode(self).encode("ascii", "replace")

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
      if isinstance(elt, ProtoDict):
        elt.search(patt, path=path + [ii], case_insensitive=case_insensitive)
      elif isinstance(elt, dict):
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

  def add(self, elt):
    if isinstance(elt, dict):
      self.append(ProtoDict().add_dict(elt))
    elif isinstance(elt, ProtoDict):
      self.append(elt)
    else:
      self.append(str(elt))
    return self

  def to_list(self):
    return list((elt.to_dict() if isinstance(elt, ProtoDict) else elt)
                for elt in self)


class ProtoDict(dict, ProtoMixin):
  """A custom dict class for Protos.

  This just allows element access through both getitem (the normal
  way) and getattr.  It also adds the attributes to dir so tab
  completion works.

  """

  @classmethod
  def normalize_attr(cls, attr):
    """Return a version of a string that is suitable for an attribute

    http://stackoverflow.com/questions/10120295/valid-characters-in-a-python-class-name
    https://docs.python.org/2/reference/lexical_analysis.html#identifiers
    """
    attr = str(attr)
    attr = "".join(
        c
        for c in attr
        if c in
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
    if attr and attr[0] in "0123456789":
      attr = "_" + attr
    return attr

  def __getattr__(self, attr):
    if attr in self:
      return self[attr]
    # if we were given a normalized attribute, there could be multiple
    # keys that normalize to the same thing.  We just arbitrarily take
    # the first one.
    for key in self.iterkeys():
      if attr == self.normalize_attr(key):
        return self[key]
    raise AttributeError("Can't find field '{0}'".format(attr))

  def __dir__(self):
    """The __dir__ method controls ipython tab completion

    http://stackoverflow.com/questions/13870241/ipython-tab-completion-for-custom-dict-class
    https://ipython.org/ipython-doc/dev/config/integrating.html
    """
    return dir(dict) + list(set(self.normalize_attr(ky) for ky in self.iterkeys(
    )))

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

    for ky, vl in self.iteritems():
      if strmatch(patt, ky) or strmatch(patt, vl):
        print path, ky, vl
      elif isinstance(vl, ProtoList):
        vl.search(patt, path=path + [ky], case_insensitive=case_insensitive)

  def full_proto_string(self, pretty=True, indent_amount=0, auto_quote=False):
    if pretty:
      ors = u"\n"
      line_sep = u"\n"
      indent = u"  " * indent_amount
    else:
      ors = u", "
      line_sep = u" "
      indent = u""

    def print_elt(key, value):
      if isinstance(value, ProtoList):
        if value.is_simple():
          for elt in value:
            selt = ProtoMixin.apply_auto_quote(elt) if auto_quote else elt
            yield u"{0}{1}: {2}".format(indent, key,
                                        ProtoMixin.to_unicode(selt))
        else:
          for elt in value:
            if isinstance(elt, ProtoDict):
              inner = elt.full_proto_string(pretty=pretty,
                                            indent_amount=indent_amount + 1,
                                            auto_quote=auto_quote)
            else:
              selt = ProtoMixin.apply_auto_quote(elt) if auto_quote else elt
              inner = u"{0}{1}".format(indent, ProtoMixin.to_unicode(selt))
            yield line_sep.join((u"{0}{1} {{".format(indent, key), inner,
                                 u"{0}}}".format(indent)))
      else:
        yield u"{0}{1}: {2}".format(indent, key, value)

    return ors.join(elt
                    for (key, value) in self.iteritems()
                    for elt in print_elt(key, value))

  def to_dict(self):
    return dict((key, value.to_list() if isinstance(value, ProtoList) else
                 value) for (key, value) in self.iteritems())

  def add(self, key, value):
    if isinstance(value, ProtoList):
      self.setdefault(key, ProtoList(())).extend(value)
    else:
      self.setdefault(key, ProtoList(())).add(value)
    return self

  def add_dict(self, dct):
    for (key, value) in dct.iteritems():
      self.add(key, value)
    return self

  @classmethod
  def from_dict(cls, dct):
    return cls().add_dict(dct)

# --------------------------------------------------------------------------- #


def parse(*args, **kwargs):
  """Run parse_root but return a tuple

  # empty proto
  >>> parse("")
  ()

  # a single value
  >>> parse("a: 1")
  ({u'a': 1},)

  # a single value in braces.  Braces must be on separate lines by themselves.
  >>> parse("{\\na: 1\\n}")
  ({u'a': 1},)

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
   u'b': [{u'c': [u'x', u'y', {u'z': 6}]}]},)

  # ProtoList summary
  >>> ProtoList(parse("a: 1\\na: 2\\na: 3\\nb {\\nc: x\\nc: y\\n}\\na: 4"))
  ProtoList(len=1, depth=0, height=3)

  # multiple protos in a single string
  >>> parse(          # doctest: +NORMALIZE_WHITESPACE
  ...       "{\\na: 1\\na: 2\\na: 3\\n \
              b {\\nc: x\\nc: y\\n}\\n}\\n \
             {\\na: 4\\n}\\n{\\na: 4\\n}")
  ({u'a': [u'1', u'2', u'3'], u'b': [{u'c': [u'x', u'y']}]}, \
   {u'a': 4}, \
   {u'a': 4})

  # An enum with each value on the same line
  >>> parse("obj {\\nenum: v1\\nenum: v2\\nenum: v3\\n}")
  ({u'obj': [{u'enum': [u'v1', u'v2', u'v3']}]},)

  # The same enum with values in block style
  >>> parse("obj {\\nenum {\\nv1\\n}\\nenum {\\nv2\\n}\\nenum {\\nv3\\n}\\n}")
  ({u'obj': [{u'enum': [u'v1', u'v2', u'v3']}]},)

  # An invalid enum
  # This would generate a warning
  #  [ ...parse_tokens:868 WARNING] Can't parse line [u'v1', u'v2'] (file None)
  # except that we suppress it with log_errors_at
  >>> parse("obj {\\nenum {\\nv1\\nv2\\n}\\nenum {\\nv3\\n}\\n}",
  ...       log_errors_at=logging.DEBUG)
  ({u'obj': [{u'enum': [{u'v1': [], u'v2': []}, u'v3']}]},)

  # Another invalid enum
  # This also generates a warning
  #  [ ...parse_tokens:868 WARNING] Can't parse line [u'v1'] (file None)
  # except that we suppress it with log_errors_at
  >>> parse("obj {\\nenum {\\nv1\\nv2: asdf\\n}\\nenum {\\nv3\\n}\\n}",
  ...       log_errors_at=logging.DEBUG)
  ({u'obj': [{u'enum': [{u'v1': [], u'v2': asdf}, u'v3']}]},)

  # An inline list
  >>> p = parse('''single_request: {
  ...   id: {
  ...     val: [ "myvalue" , "yourvalue" , "third value" ]
  ...   }
  ... }
  ... single_request {
  ...   id: {
  ...     val: [ "John" , "George" ]
  ...     val: [ "Ringo", "Paul" ]
  ...   }
  ... }
  ... ''')
  >>> len(p[0].single_request[0].id[0].val)
  3
  >>> p[0].single_request[0].id[0].val[1]
  u'"yourvalue"'
  >>> p[0].single_request[0].id[0].val[2]
  u'"third value"'
  >>> len(p[0].single_request[1].id[0].val)
  4
  >>> p[0].single_request[1].id[0].val[3]
  u'"Paul"'

  # Treat [] differently in vars and vals
  >>> p = parse('''[foo]: {
  ...   id: {
  ...     val: [ "myvalue" , "yourvalue" , "third value" ]
  ...   }
  ... }
  ... single_request {
  ...   id: {
  ...     val: [ "John" , "George" ]
  ...     val: [ "Ringo", "Paul" ]
  ...   }
  ... }
  ... ''')
  >>> print p[0].full_proto_string()
  [foo] {
    id {
      val: "myvalue"
      val: "yourvalue"
      val: "third value"
    }
  }
  single_request {
    id {
      val: "John"
      val: "George"
      val: "Ringo"
      val: "Paul"
    }
  }
  >>> p[0].foo[0].id[0].val[0]
  u'"myvalue"'

  # Test of enum_or_proto
  >>> parse('TrainStation : [{source: OYSTER , eid: PROVIDER}]')
  ({u'TrainStation': [{u'source': OYSTER, u'eid': PROVIDER}]},)

  # Test that we tokenize braces ([]) properly for lists
  >>> parse('TrainStation : [OYSTER, PROVIDER]')
  ({u'TrainStation': [u'OYSTER', u'PROVIDER']},)

  >>> parse('x {}')
  ({u'x': [{}]},)
  >>> parse('{x {}}')
  ({u'x': [{}]},)
  >>> parse('x: {}')
  ({u'x': [{}]},)

  # this is malformed -- the return value doesn't matter, but make sure we don't
  # go into an infinite loop
  >>> parse('}')
  ({},)

  >>> parse('a:\\nb:c')
  ({u'a': , u'b': c},)
  >>> parse('a: http://myval\\nb:c')
  ({u'a': http://myval, u'b': c},)
  """
  return tuple(parse_root(*args, **kwargs))


def parse_lisp(string, idx=0, is_value=True):
  """Parse a lisp list

  Read a lisp list like this:
    (extension1 ((field1 value1) (field2 value2)))
  And return a python list like this:
    [extension1 [[field1 value1] [field2 value2]]]
  It's a very simple grammar, like this:
    element = (element element ...) | (value element) | value

  >>> parse_lisp("val")
  ('val', 3)
  >>> parse_lisp("(field value)")
  (['field', 'value'], 13)
  >>> parse_lisp('(field "string value")')
  (['field', '"string value"'], 22)
  >>> parse_lisp("(extension1 ((field1 value1) (field2 value2)))")
  (['extension1', [['field1', 'value1'], ['field2', 'value2']]], 46)
  >>> parse_lisp(            # doctest: +NORMALIZE_WHITESPACE
  ... "(extension1 ((field1 value1) (field2 value2) (field3 value3)))")
  (['extension1', [['field1', 'value1'], ['field2', 'value2'],
   ['field3', 'value3']]], 62)

  """
  while idx < len(string) and string[idx].isspace():
    idx += 1
  if idx >= len(string):
    return ("", idx)
  if string[idx] == "(":
    # This is a list, parse each element and add it to the return list
    idx += 1
    retval = []
    while len(string) > idx and string[idx] != ")":
      # read an element
      element, new_idx = parse_lisp(string, idx)
      logging.debug("Read '%s' from %s, new idx = %s", element, string, new_idx)
      retval.append(element)
      idx = new_idx
    # skip over the closing paren
    idx += 1
    logging.debug("Finished '%s', new idx = %s", retval, idx)
    return (retval, idx)
  else:
    # This is a value, not an list.  Take the string up to the next
    # whitespace, close paren, or end of string.
    regexp = ".*?(\s|\)|$)"
    if string[idx] == '"':
      # If this value starts with a double-quote (") then take
      # everything up to the next double-quote (or end-of-string)
      regexp = '\".*?(\"|$)'
    mo = re.match(regexp, string[idx:])
    if mo:
      # set the variables end and next_idx.  end is the index of the
      # end of the value.  next_idx is where we should start parsing
      # the rest of the string.
      if re.match("\s*$", mo.group(1)):
        # if the delimeter is whitespace, skip over it
        end = idx + mo.start(1)
        next_idx = idx + mo.end(1)
      elif mo.group(1) == '"':
        # if the delimeter is a quote, include it in the value
        next_idx = idx + mo.end(1)
        end = next_idx
      else:
        # otherwise, let the caller deal with the delimeter
        end = idx + mo.start(1)
        next_idx = end
      logging.debug("Finished value '%s', new idx = %s", string[idx:end],
                    next_idx)
      return (string[idx:end], next_idx)
    else:
      logging.error("Error parsing value '%s' at idx %s", string, idx)
    return ("", idx)


def list_to_proto(lst):
  """Convert a list to a Proto

  >>> print list_to_proto(['a', 'b']).full_proto_string()
  a: b
  >>> print list_to_proto(['a', ['b', 'c']]).full_proto_string()
  a {
    b: c
  }
  >>> print list_to_proto(['a', [['b', 'c'], ['b', 'e']]]).full_proto_string()
  a {
    b: c
    b: e
  }
  >>> print list_to_proto(
  ... ['a', [['b', 'c'], ['b', 'e']]]).full_proto_string(auto_quote=True)
  a {
    b: "c"
    b: "e"
  }
  """
  if not isinstance(lst, list):
    return lst
  if len(lst) > 0 and not isinstance(lst[0], list):
    lst = [lst]
  block = ProtoDict()
  for elt in lst:
    if len(elt) != 2:
      logging.error("Can't parse element '%s' of list '%s'", elt, lst)
    (var, val) = elt[:2]
    block.setdefault(var, ProtoList(())).append(list_to_proto(val))
  return block


# http://stackoverflow.com/questions/1517862/using-lookahead-with-generators
class LookaheadIter(collections.Iterator):

  def __init__(self, it):
    self.orig = it
    self.it, self.nextit = itertools.tee(iter(it))
    self.idx = 0
    self._advance()

  def _advance(self):
    self.lookahead = next(self.nextit, None)
    self.idx += 1

  def next(self):
    return self.__next__()

  def __next__(self):
    self._advance()
    return next(self.it)

# --------------------------------------------------------------------------- #

# Grammar that we are parsing:
#
# ROOT = PROTO | BODY
# PROTO = '{' BODY '}'
# BODY = ITEM*
# ITEM = VAR ':' VAL | VAR VAL
# VAR = VARTOKEN
# VAL = VALTOKEN | PROTO | LIST | ENUM_VAL
# ENUM_VAL = '{' ELEMENT '}'
# LIST = '[' VAL* ']'
# VAR_TOKEN = (COMMENT) VAR_ELEMENT (COMMENT) | STRING
# VAL_TOKEN = (COMMENT) VAL_ELEMENT (COMMENT) | STRING
# VAR_ELEMENT = VAR_CHAR+
# VAL_ELEMENT = VAL_CHAR+
# STRING = '"' S2CHAR* '"' | "'" S1CHAR* '"'
# COMMENT = '#' ANY* '\n'
# VAL_CHAR = any non-whitespace, non-special character, non [] character:
#            '#', ':', ';', '{', '}', '[', ']', '"', "'"
# VAR_CHAR = any non-whitespace, non-special character:
#            '#', ':', ';', '{', '}', '"', "'"
# S1CHAR = any character except an un-escaped single quote
# S2CHAR = any character except an un-escaped double quote
# ANY = any character
#
# () means optional
# *  means any number of repetitions
# +  means one or more repetitions
# |  means any one of


def parse_root(tokens=None,
               lines=None,
               filename=None,
               depth=0,
               log_errors_at=logging.WARN):
  if isinstance(tokens, basestring):
    lines = [tokens]
    tokens = None
  if isinstance(tokens, collections.Sequence):
    lines = tokens
    tokens = None
  if filename and not tokens and not lines:
    lines = file_lines(filename)
  if lines and not tokens:
    # tokens = itertools.chain.from_iterable(tokenify(line,
    #                                                 log_errors_at=log_errors_at)
    #                                        for line in lines)
    tokens = itertools.chain.from_iterable(lines)
  if not tokens:
    raise ValueError("No data to parse")
  if not isinstance(tokens, LookaheadIter):
    tokens = LookaheadIter(tokens)
    consume_spaces(tokens, log_errors_at=log_errors_at)

  path = ["root"]
  while tokens.lookahead:
    last = tokens.idx
    yield parse_proto(tokens,
                      log_errors_at=log_errors_at,
                      path=path,
                      expect_braces=False)
    if tokens.idx == last:
      logging.log(log_errors_at, "Couldn't continue parsing %s %s",
                  tokens.lookahead, tokens.idx)
      break


def parse_proto(tokens,
                log_errors_at=logging.WARN,
                path=None,
                expect_braces=True):
  logging.debug("%s", tokens.lookahead)
  if path:
    path = path + ["proto"]
  if tokens.lookahead == "{":
    # consume the '{'
    advance_tokens(tokens)
  elif expect_braces:
    logging.log(log_errors_at, "proto does not start with {: %s %s", tokens.idx,
                path)
  block = ProtoDict()
  fill_body_block(tokens, block, log_errors_at=log_errors_at, path=path)
  if tokens.lookahead == "}":
    # consume the '}'
    advance_tokens(tokens)
  elif expect_braces:
    logging.log(log_errors_at, "proto %s does not end with }: %s %s", block,
                tokens.idx, path)
  return block


def fill_body_block(tokens, block, log_errors_at=logging.WARN, path=None):
  logging.debug("%s", tokens.lookahead)
  if path:
    path = path + ["body"]
  while tokens.lookahead and tokens.lookahead != "}":
    (var, val) = parse_item(tokens, log_errors_at=log_errors_at, path=path)
    block.setdefault(var, ProtoList(())).extend(val)
    if tokens.lookahead == ",":
      advance_tokens(tokens)
    elif tokens.lookahead == "}":
      break
  return block


def parse_item(tokens, log_errors_at=logging.WARN, path=None):
  logging.debug("%s", tokens.lookahead)
  if path:
    path = path + ["item"]
  var = parse_var(tokens, log_errors_at=log_errors_at, path=path)
  val = parse_item_val(tokens, log_errors_at=log_errors_at, path=path + [var])
  return (var, val)


# Note, this always returns a sequence
def parse_item_val(tokens, log_errors_at=logging.WARN, path=None):
  logging.debug("%s", tokens.lookahead)
  if path:
    path = path + ["item_val"]
  if tokens.lookahead == ":":
    advance_tokens(tokens, stop_at_newline=True)
    val = parse_val(tokens,
                    log_errors_at=log_errors_at,
                    path=path,
                    stop_at_newline=True)
  elif tokens.lookahead == "{":
    val = [parse_enum_or_proto(tokens, log_errors_at=log_errors_at, path=path)]
  else:
    logging.log(log_errors_at,
                "Can't parse value, next char is %s, idx=%s, path=%s",
                tokens.lookahead, tokens.idx, path)
    val = ()
  return val


def parse_var(tokens, log_errors_at=logging.WARN, path=None):
  logging.debug("%s", tokens.lookahead)
  if path:
    path = path + ["var"]
  return parse_token(tokens, for_var=True, log_errors_at=log_errors_at)


def parse_token(tokens,
                for_var,
                log_errors_at=logging.WARN,
                path=None,
                stop_at_newline=False):
  if path:
    path = path + ["token"]
  val = decode(get_next_token(tokens=tokens,
                              for_var=for_var,
                              log_errors_at=log_errors_at,
                              stop_at_newline=stop_at_newline,
                              path=path))
  logging.debug("token = %s, path=%s", val, path)
  return val


# Note, this always returns a sequence
def parse_val(tokens,
              log_errors_at=logging.WARN,
              path=None,
              stop_at_newline=False):
  logging.debug("%s", tokens.lookahead)
  if path:
    path = path + ["val"]
  if tokens.lookahead == "{":
    return [parse_enum_or_proto(tokens, log_errors_at=log_errors_at, path=path)]
  elif tokens.lookahead == "[":
    return parse_list(tokens, log_errors_at=log_errors_at, path=path)
  else:
    return [parse_token(tokens,
                        for_var=False,
                        log_errors_at=log_errors_at,
                        stop_at_newline=stop_at_newline,
                        path=path)]


def parse_enum_or_proto(tokens, log_errors_at=logging.WARN, path=None):
  logging.debug("%s", tokens.lookahead)
  if path:
    path = path + ["enum_or_proto"]
  if tokens.lookahead == "{":
    advance_tokens(tokens)
  else:
    logging.log(log_errors_at, "proto or enum does not start with {: %s %s",
                tokens.idx, path)
  if tokens.lookahead == "}":
    # empty block
    advance_tokens(tokens)
    return ProtoDict()
  var = parse_var(tokens, log_errors_at=log_errors_at, path=path)
  if tokens.lookahead == "}":
    # this is an enum
    advance_tokens(tokens)
    return var
  else:
    # this is a proto
    block = ProtoDict()
    path = path + [var]
    val = parse_item_val(tokens, log_errors_at=log_errors_at, path=path)
    block.setdefault(var, ProtoList(())).extend(val)
    if tokens.lookahead == ",":
      advance_tokens(tokens)
    fill_body_block(tokens, block, log_errors_at=log_errors_at, path=path)
    if tokens.lookahead == "}":
      advance_tokens(tokens)
    else:
      logging.log(log_errors_at, "proto %s does not end with }: %s %s", block,
                  tokens.idx, path)
    return block


def parse_list(tokens, log_errors_at=logging.WARN, path=None):
  logging.debug("%s", tokens.lookahead)
  if path:
    path = path + ["list"]
  if tokens.lookahead == "[":
    advance_tokens(tokens)
  else:
    logging.log(log_errors_at, "list does not start with [: %s %s", tokens.idx,
                path)
  retval = []
  while tokens.lookahead and tokens.lookahead != "]":
    retval.extend(parse_val(tokens, log_errors_at=log_errors_at, path=path))
    if tokens.lookahead == ",":
      advance_tokens(tokens)
  if tokens.lookahead == "]":
    advance_tokens(tokens)
  else:
    logging.log(log_errors_at, "list %s does not end with ]: %s, %s", retval,
                tokens.idx, path)
  return retval

# --------------------------------------------------------------------------- #


def consume_spaces(tokens, log_errors_at=logging.WARN, stop_at_newline=False):
  while tokens.lookahead is not None:
    if tokens.lookahead == "#":
      while tokens.lookahead and tokens.lookahead != "\n":
        next(tokens)
      if tokens.lookahead == "\n":
        next(tokens)
    elif stop_at_newline and tokens.lookahead == "\n":
      break
    elif tokens.lookahead.isspace():
      next(tokens)
    else:
      break


def advance_tokens(tokens, log_errors_at=logging.WARN, stop_at_newline=False):
  retval = next(tokens)
  consume_spaces(tokens,
                 log_errors_at=log_errors_at,
                 stop_at_newline=stop_at_newline)
  return retval


def get_next_token(tokens,
                   for_var=True,
                   log_errors_at=logging.WARN,
                   path=None,
                   die_on_error=False,
                   stop_at_newline=False):
  # It's possible that the set of places where we want stop_at_newline
  # is exactly the same as when for_var is False.  But I think it's still
  # clearer to keep them as two separate ideas.
  logging.debug("%s", tokens.lookahead)
  special = "{};,"
  if for_var:
    special += ":"
  else:
    special += "[]"

  retval = ""
  while tokens.lookahead is not None:
    if tokens.lookahead in special:
      if retval:
        break
      else:
        retval = next(tokens)
        break
    elif tokens.lookahead in ("'", '"'):
      # String
      quote = next(tokens)
      retval += quote
      while tokens.lookahead is not None and tokens.lookahead != "\n":
        if tokens.lookahead == quote:
          retval += next(tokens)
          break
        if tokens.lookahead == "\\":
          retval += next(tokens)
        retval += next(tokens)
      else:
        err = "No end of string found: {0}.  idx={1}, path={2}".format(
            retval, tokens.idx, path)
        if die_on_error:
          raise ValueError(err)
        else:
          logging.log(log_errors_at, err)
    elif tokens.lookahead.isspace():
      if retval:
        break
      elif tokens.lookahead == "\n" and stop_at_newline:
        break
      else:
        next(tokens)
    else:
      retval += next(tokens)

  consume_spaces(tokens)
  return retval

# --------------------------------------------------------------------------- #


def sample_response():
  return """
  result {
    key: "\357\275\212\357\275\222\345\214\227\346\265\267\351\201\223\343\203\220\343\202\271"
    candidate {
      mid: "/m/asdfasdf"
      name: "jekyl and hyde"
      score: 0.534235234
      decision: NO_MATCH
    }
    candidate {
      mid: "/o/154213123"
      name: "JRJRJRJRJ"
      score: 0.9299293949128
      decision: NO_MATCH
    }
  }
  result {
    key: "\357\275\212\357\275\222\345\233\233\345\233\275\343\203\220\343\202\271"
    candidate {
      mid: "/z/xxxxxxxx"
      name: "\357\274\252\357\274\262\345\233\233\345\233\275\343\203\220\343\202\271\351\253\230\351\200\237"
      score: 0.12345678901
      decision: NO_MATCH
    }
    candidate {
      mid: "/r/yyyyyyyy"
      name: "\343\202\270\343\202\247\343\202\244\343\202\242\343\203\274\343\203\253\345\233\233\345\233\275"
      score: 0.2345678901
      decision: NO_MATCH
    }
    candidate {
      mid: "/c/ppppppppp"
      name: "PPSPSP"
      score: 0.0000230300
      decision: NO_MATCH
    }
    candidate {
      mid: "/b/agasdfasd"
      name: "\346\235\276\345\261\261\351\253\230\347\237\245\346\200\245\350\241\214\347\267\232"
      score: 1.1828912382e-05
      decision: NO_MATCH
    }
  }
""".decode("utf-8")

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
  print "The parsed protos will appear in the variable 'parsed'"
  parsed = main()

# --------------------------------------------------------------------------- #
