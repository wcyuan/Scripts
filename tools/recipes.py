'''
A place to store useful python recipes
'''

# --------------------------------------------------------------------------- #

# http://stackoverflow.com/questions/1885161/
# how-can-i-get-optparses-optionparser-to-ignore-invalid-options

from optparse import (OptionParser,BadOptionError,AmbiguousOptionError)

class PassThroughOptionParser(OptionParser):
    """
    An unknown option pass-through implementation of OptionParser.

    When unknown arguments are encountered, bundle with largs and try again,
    until rargs is depleted.

    sys.exit(status) will still be called if a known argument is passed
    incorrectly (e.g. missing arguments or bad argument types, etc.)

    >>> parser = PassThroughOptionParser()
    >>> _ = parser.add_option('--test', action='store_true')
    >>> parser.disable_interspersed_args()

    # We don't recognize any options, so just pass them through
    >>> (opts, args) = parser.parse_args(['a', 'b', 'c'])
    >>> opts.test
    >>> args
    ['a', 'b', 'c']

    # Pass through '--' unchanged
    >>> (opts, args) = parser.parse_args(['a', 'b', '--', 'c'])
    >>> args
    ['a', 'b', '--', 'c']
    >>> (opts, args) = parser.parse_args(['a', 'b', '--', 'c', '--'])
    >>> args
    ['a', 'b', '--', 'c', '--']

    # We remove the leading '--' if it is the first argument
    >>> (opts, args) = parser.parse_args(['--', 'a', 'b', '--', 'c', '--'])
    >>> args
    ['a', 'b', '--', 'c', '--']


    # Consume the option we expected
    >>> (opts, args) = parser.parse_args(['--test', 'a', 'b', '--', 'c', '--'])
    >>> opts.test
    True
    >>> args
    ['a', 'b', '--', 'c', '--']

    >>> (opts, args) = parser.parse_args(['--test', '--', 'a', 'b', '--', 'c', '--'])
    >>> opts.test
    True
    >>> args
    ['a', 'b', '--', 'c', '--']

    >>> (opts, args) = parser.parse_args(['--', '--test', 'a', 'b', '--', 'c', '--'])
    >>> opts.test
    >>> args
    ['--test', 'a', 'b', '--', 'c', '--']

    """
    def _process_args(self, largs, rargs, values):
        try:
            OptionParser._process_args(self,largs,rargs,values)
        except (BadOptionError,AmbiguousOptionError), e:
            largs.append(e.opt_str)

def pass_through_example():
    preparser = PassThroughOptionParser()
    preparser.add_option('--full', action='store_true',
                         help='an added flag argument')
    (options, args) = preparser.parse_args()

    # Now pass the rest of the arguments to the original parser
    parser = OptionParser()
    parser.add_option('--orig', action='store_true',
                         help='the original argument')
    (opts, args) = parser.parse_args(args)



# --------------------------------------------------------------------------- #

# http://stackoverflow.com/questions/5136611/
# capture-stdout-from-a-script-in-python

import sys
import StringIO

def save_stdout(func):
    old_stdout = sys.stdout
    new_stdout = StringIO.StringIO()
    sys.stdout = new_stdout
    func()
    sys.stdout = old_stdout
    return new_stdout.getvalue()

def save_stdout_example():
    def myfunc():
        """ A function that has lots of output """
        for i in xrange(100):
            print 'abc' * 100

    # capture the output
    output = save_stdout(lambda : myfunc())
    # only print the first 100 characters
    print output[:100]

# --------------------------------------------------------------------------- #

class FieldMixin(object):
    """
    This Mixin applies to classes that have a few key attributes that
    determine all the other behavior.  Those attributes have to be
    settable as keyword arguments in the __init__ function.  In that
    case, if you put the names of those attributes in _flds, then this
    Mixin will provide repr, cmp, and hash functions.

    """
    @property
    def _flds(self):
        raise NotImplementedError

    @staticmethod
    def _vals(obj):
        return tuple(getattr(obj, fld) for fld in obj._flds)

    def __repr__(self):
        """
        Must satisfy:
          obj == eval(repr(obj))
        for any obj
        """
        cn = self.__class__.__name__
        fmt = ('{cn}(' +
               ',\n{pd} '.join('{0} = {{self.{0}!r}}'.format(fld)
                               for fld in (self._flds)) +
               ')')
        return fmt.format(self=self, cn=cn, pd=' '*len(cn))

    def __cmp__(self, other):
        tcmp = cmp(type(self), type(other))
        if tcmp == 0:
            return cmp(self._vals(self), self._vals(other))
        else:
            return tcmp

    def __hash__(self):
        return hash(self._vals(self))

# --------------------------------------------------------------------------- #

class SpellChecker(object):
    """
    Initialize with a dictionary.  After that, given a word, look for
    words in the dictionary with edit distance two or less.  If there
    are none of those, look for names that start with the given word,
    or which contain the given word.

    Based on http://norvig.com/spell-correct.html

    The default alphabet is all lowercase letters plus underscore (no
    numbers, no upper case, no other punctuation)

    >>> sc = SpellChecker(('apple', 'honey', 'pooh'))
    >>> sc.correct('appl')
    'apple'
    >>> sc.correct('a')
    'apple'
    >>> sc.correct('n')
    'honey'

    """

    @classmethod
    def train(cls, features):
        import collections
        model = collections.defaultdict(lambda: 1)
        for f in features:
            model[f] += 1
        return model

    def __init__(self, wordlist, alphabet=None,
                 include_starts=False,
                 include_contains=True,
                 return_all=False):
        self.nwords = self.train(wordlist)
        if alphabet is None:
            alphabet = 'abcdefghijklmnopqrstuvwxyz_'
        self.alphabet = alphabet
        self.include_starts = include_starts
        self.include_contains = include_contains
        self.return_all = return_all

    def edits1(self, word):
        splits     = [(word[:i], word[i:]) for i in range(len(word) + 1)]
        deletes    = [a + b[1:] for a, b in splits if b]
        transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
        replaces   = [a + c + b[1:] for a, b in splits for c in self.alphabet
                      if b]
        inserts    = [a + c + b     for a, b in splits for c in self.alphabet]
        return set(deletes + transposes + replaces + inserts)

    def known_edits2(self, word):
        return set(e2 for e1 in self.edits1(word) for e2 in self.edits1(e1)
                   if e2 in self.nwords)

    def known(self, words):
        return set(w for w in words if w in self.nwords)

    def starts(self, words):
        if not self.include_contains:
            return set()
        return set(w for given in words for w in self.nwords
                   if w.startswith(given))

    def contains(self, words):
        if not self.include_contains:
            return set()
        return set(w for given in words for w in self.nwords
                   if given in w)

    def correct(self, word):
        candidates = (self.known([word]) or
                      self.known(self.edits1(word)) or
                      self.known_edits2(word) or
                      self.starts([word]) or
                      self.contains([word]) or
                      [word])
        if self.return_all:
            return sorted(candidates, key=self.nwords.get)
        else:
            return max(candidates, key=self.nwords.get)

# --------------------------------------------------------------------------- #

# Floating point comparison

class FP(object):
    EPSILON = 1e-6

    @classmethod
    def EQ(cls, a, b):
        return abs(a - b) < cls.EPSILON

    @classmethod
    def LT(cls, a, b):
        return b - a > cls.EPSILON

    @classmethod
    def GT(cls, a, b):
        return a - b > cls.EPSILON

    @classmethod
    def LTE(cls, a, b):
        return cls.LT(a, b) or cls.EQ(a, b)

    @classmethod
    def GTE(cls, a, b):
        return cls.GT(a, b) or cls.EQ(a, b)

# --------------------------------------------------------------------------- #

import functools

def memoize(obj):
  """from https://wiki.python.org/moin/PythonDecoratorLibrary
  """
  cache = obj.cache = {}

  @functools.wraps(obj)
  def memoizer(*args, **kwargs):
    key = str(args) + str(kwargs)
    if key not in cache:
      cache[key] = obj(*args, **kwargs)
    return cache[key]

  return memoizer

# --------------------------------------------------------------------------- #

import itertools

def make_table(table, delim=" ", left=True, ors="\n"):
    """
    Args:
      table: A sequence of rows, where each row is a sequence of fields.
      Can't be a generator, it will be traversed twice.
    Returns:
      A string where the rows are printed with the columns lined up
    """
    transposed = itertools.izip_longest(*table, fillvalue="")
    widths = (max(len(fld) for fld in line) for line in transposed)
    lch = "-" if left else ""
    formats = ["%{0}{1}s".format(lch, width) for width in widths]
    return ors.join("%s" % delim.join(format % (fld)
                                      for (format, fld) in zip(formats, line))
                    for line in table)

# --------------------------------------------------------------------------- #

def extract_from_string(full_str, start_str, end_str=None, default=''):
    """Extract a substring from full_str.

    Extract the substring that starts with start_str and ends with
    end_str.  If end_str is None, or if it is not found, the extract
    until the end of the string.  The extracted string will include
    start_str, but will not include end_str.  If start_str is not
    found, return default (which defaults to the empty string).
    """
    idx = full_str.find(start_str)
    if idx < 0:
        return default
    if end_str is not None:
        length = full_str[idx + len(start_str):].find(end_str)
        if length >= 0:
            return full_str[idx:idx + len(start_str) + length]
    return full_str[idx:]

def partition_string(full_str, markers):
    """Parition a string into pieces.

    >>> list(partition_string("abcdef", []))
    ['abcdef']
    >>> list(partition_string("abcdef", ["g"]))
    ['abcdef', '']
    >>> list(partition_string("abcdef", ["c"]))
    ['ab', 'cdef']
    >>> list(partition_string("abcdef", ["c", "e"]))
    ['ab', 'cd', 'ef']
    >>> list(partition_string("abcdef", ["bc", "e"]))
    ['a', 'bcd', 'ef']
    >>> list(partition_string("abcdef abcdef", ["bc", "a"]))
    ['a', 'bcdef ', 'abcdef']
    >>> list(partition_string("abcdef abcdef", ["bc", "g"]))
    ['a', 'bcdef abcdef', '']
    >>> list(partition_string("abcdef abcdef", ["bc", "c"]))
    ['a', 'bcdef ab', 'cdef']
    """
    idx = 0
    last_marker = ''
    rest = full_str
    for marker in markers:
        next_idx = rest.find(marker)
        if next_idx < 0:
            next_idx = len(rest)
            marker = ''
        yield last_marker + rest[idx:next_idx]
        last_marker = marker
        rest = rest[next_idx + len(marker):]
    yield last_marker + rest

# --------------------------------------------------------------------------- #

import contextlib
import gzip
import logging
import sys

@contextlib.contextmanager
def zopen(filename, mode="w"):
  compressors = [(".gz", gzip.open)]
  action = "Reading" if mode == "r" else "Writing"
  if not filename:
    if mode == "r":
      logging.info("%s from stdin", action)
      yield sys.stdin
    else:
      logging.info("%s to stdout", action)
      yield sys.stdout
  else:
    func = open
    for (suffix, compress_func) in compressors:
      if filename.endswith(suffix):
        logging.info("%s compressed to %s", action, filename)
        func = compress_func
        break
    else:
      logging.info("%s to %s", action, filename)
    with func(filename, mode) as fd:
      yield fd

# An alternative version that is not as nice, in some ways, but probably
# easier to read
#
# @contextlib.contextmanager
# def zopen(filename, mode="r"):
#   if filename.endswith('.gz'):
#     with gzip.open(filename, mode=mode) as fd:
#       yield fd
#   else:
#     with open(filename, mode=mode) as fd:
#       yield fd

# --------------------------------------------------------------------------- #
# Here an example of how to use cache_to_disk
#
#   @cache_to_disk(lambda input: "~/data/foo_{0}.csv.gz".format(input))
#   def get_data(input):
#     return to_csv_string(get_data_raw(input))
#
#   def main():
#     ...
#     foo = from_csv_string(get_data(input))
#     ...
#
# The output from get_data_raw will be stored in the specified file.
# If that file exists, it will read the data from the file instead of
# running the command again.
#

import logging
import os

def cache_to_disk(make_filename,
                  serializer=None,
                  deserializer=None,
                  make_cache_key=None):
  if not hasattr(cache_to_disk, "NO_WRITE"):
    cache_to_disk.NO_WRITE = False
  if isinstance(make_filename, basestring):
    single_filename = make_filename
    make_filename = None
  else:
    single_filename = None
  cache = {}
  def wrapped(func):
    def newfunc(*args, **kwargs):
      if make_cache_key:
        key = make_cache_key(*args, **kwargs)
      else:
        key = (tuple(args), tuple(kwargs.items()))
      logging.debug("Cache key: %s", key)
      if key not in cache:
        if single_filename:
          filename = single_filename
        else:
          filename = make_filename(*args, **kwargs)
        filename = os.path.expanduser(filename)
        logging.debug("Cache filename: %s", filename)
        if not os.path.exists(filename):
          logging.debug("Calling func %s", func)
          output = func(*args, **kwargs)
          if serializer:
            logging.debug("Serializing to file %s", filename)
            serializer(filename, output, no_write=cache_to_disk.NO_WRITE)
          else:
            if cache_to_disk.NO_WRITE:
              logging.debug("NO WRITE: Would write to file %s", filename)
            else:
              logging.debug("Writing to file %s", filename)
              with zopen(filename, "w") as fd:
                cache[key] = fd.write(output)
        if deserializer:
          logging.debug("Deserializing from file %s", filename)
          cache[key] = deserializer(filename)
        else:
          logging.debug("Reading from file %s", filename)
          with zopen(filename) as fd:
            cache[key] = fd.read()
      return cache[key]
    return newfunc
  return wrapped

def to_csv_string(list_of_lists, ors="\n", ofs=","):
  return ors.join(ofs.join(lst) for lst in list_of_lists)

def from_csv_string(csv_string, ors="\n", ofs=","):
  return [line.split(ofs) for line in csv_string.split(ors)]

# --------------------------------------------------------------------------- #
# Exception chaining
#

import sys
def exception_chaining(func, msg):
    try:
        return func()
    except:
        (exc_type, exc_value, exc_traceback) = sys.exc_info()
        exc_value = '{0}: {1}'.format(msg, exc_value)
        raise exc_type, exc_value, exc_traceback

# --------------------------------------------------------------------------- #
# deep copy
#

import itertools
import logging

def deepcmp(a, b, path=None):
  if not path:
    path = []
  if type(a) != type(b):
    logging.warning("Diff in type %s != %s of path %s", type(a), type(b), path)
    return cmp(type(a), type(b))
  if isinstance(a, dict):
    if len(a) != len(b):
      logging.warning("Diff in len %s != %s of path %s", len(a), len(b), path)
      return cmp(len(a), len(b))
    for x in a.iterkeys():
      if x not in b:
        logging.warning("Extra key %s at path %s", x, path)
        return 1
      res = deepcmp(a[x], b[x], path=path+[x])
      if res != 0:
        return res
    for y in b.iterkeys():
      if y not in a:
        logging.warning("missing key %s at path %s", y, path)
        return -1
    return 0
  if isinstance(a, list):
    if len(a) != len(b):
      logging.warning("Diff in len %s != %s of path %s", len(a), len(b), path)
      return cmp(len(a), len(b))
    for ii, (x, y) in enumerate(itertools.izip(a, b)):
      res = deepcmp(x, y, path=path+[ii])
      if res != 0:
        return res
    return 0
  res = cmp(a, b)
  if res != 0:
    logging.warning("Diff in path %s", path)
  return res

# --------------------------------------------------------------------------- #


