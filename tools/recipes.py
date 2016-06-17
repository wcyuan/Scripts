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

    def __init__(self, **kwargs):
      for var in self._flds:
        if var in kwargs:
          setattr(self, var, kwargs[var])
        else:
          setattr(self, var, None)
      for var in kwargs:
        if var not in self._flds:
          raise ValueError("Unknown keyword argument: {0} = {1}".format(
              var, kwargs[var]))

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
    Returns:
      A string where the rows are printed with the columns lined up
    """
    # make it a tuple so we can traverse it twice.
    table = tuple(table)
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
        #
        # The raise statement is described here:
        #   https://docs.python.org/2/reference/simple_stmts.html#raise
        #
        #   If the first object is a class, it becomes the type of the exception.
        #   The second object is used to determine the exception value: If it is an
        #   instance of the class, the instance becomes the exception value. If the
        #   second object is a tuple, it is used as the argument list for the class
        #   constructor; if it is None, an empty argument list is used, and any other
        #   object is treated as a single argument to the constructor. The instance
        #   so created by calling the constructor is used as the exception value.
        #
        # This code changes the value to a string, which will then be used
        # to construct a new copy of the exception.  If that's not the right way
        # to create this type of exception, this won't work.  For example, this
        # doesn't work for UnicodeEncodeError.
        #
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
# Generic proto parsing

import logging

def pretty_string(record, indent=0):
  indent_str = "   " * indent
  lines = ["{"]
  for key in record:
    for val in record[key]:
      line = "{0}{1}".format(indent_str, key)
      if isinstance(val, dict):
        line += " " + pretty_string(val, indent=indent+1)
      else:
        line += ": " + val
      lines.append(line)
  lines.append(indent_str + "}")
  return "\n".join(lines)


def parse_blocks(string):
  level = 0
  block = ""
  logging.debug("length = %s", len(string))
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


def parse_responses(lines, is_split=False, is_reversed=False):
  """Sample response looks like:

  result {
    key: "value"
    entry {
      foo: "bar"
      name: "John"
      value: 0.12
      enum_val: FOOT
    }
    entry {
      foo: "safd"
      name: "Sara"
      value: 2.5
      enum_val: ARM
    }
  }
  result {
  }

  This returns an iterator, so you have to tuplize it.  Then you'll
  get a single element, which is a dictionary with a single key,
  "result".  The value for that key will be a list of all the
  responses.

  In general, we don't know how many of a value there will be.  I.e.,
  there could be a single entry or there could be many entries.
  There could be a single foo or there could be many foos.  So we
  assume that all fields are lists.  The clients of the data should
  know which fields are really lists and which fields you just need to
  take the [0] element of.
  """
  if not is_split:
    lines = lines.split("\n")
  if not is_reversed:
    lines.reverse()
  block = {}
  while lines:
    line = lines.pop().lstrip()
    if line == "}":
      yield block
      block = {}
      continue
    if ": " in line:
      var, val = line.split(": ", 1)
    elif line.endswith(" {"):
      var = line[:-2]
      val = ""
      # Just take the first response, there should either 0 or 1 responses.
      for response in parse_responses(lines, is_split=True, is_reversed=True):
        val = response
        break
    else:
      if line.strip():
         logging.warning("Can't parse line %s", line)
      continue
    block.setdefault(var, []).append(val)
  if block:
    yield block

# --------------------------------------------------------------------------- #

import logging
import subprocess

class Runner(object):
  """A class to run commands."""
  NO_WRITE = False

  @classmethod
  def run(cls, cmd,
          always=False,
          die_on_error=True,
          warn_on_error=True,
          capture_stdout=True):
    """Run the command.

    Args:

      cmd: the command to run.  Should be a string or a list of strings.

      always: If True, we will run even if no_write is true.  False by
      default.

      die_on_error: If False, then if the command exits with a
      non-zero exit code, we will log a warning, but we won't throw an
      exception.  True by default.

      However, if the command doesn't even exist, or if Popen is
      called with invalid arguments, then we will still throw an
      exception.

      warn_on_error: If the command fails and die_on_error is False,
      then we will either log a warning (if warn_on_error is True)
      or a debug message (if warn_on_error is False)

      capture_stdout: If true, this function will return the stdout.
      That means the stdout won't appear on the terminal.

    Returns:
      In NO_WRITE mode, we always return None.
      Otherwise, if capture_stdout is True, we return the command's stdout.
      Otherwise, if capture_stdout is False, we return (returncode == 0)

    Raises:
      RuntimeError: if the command fails and die_on_error is True.
      Can throw other errors if the command doesn't exist or if
      Popen is called with invalid arguments.

    """
    if isinstance(cmd, basestring):
      strcmd = cmd
    else:
      strcmd = "{0} ({1})".format(cmd, " ".join(cmd))

    if cls.NO_WRITE and not always:
      logging.info("NO WRITE: %s", strcmd)
      if capture_stdout:
        return
      else:
        return True

    logging.info("Running:  %s", strcmd)
    if capture_stdout:
      stdout_opt = subprocess.PIPE
    else:
      stdout_opt = None
    process = subprocess.Popen(cmd,
                               shell=isinstance(cmd, basestring),
                               stdout=stdout_opt)
    stdout = process.communicate()[0]
    if process.returncode != 0:
      if die_on_error:
        raise RuntimeError("Failure running {0}".format(cmd))
      elif warn_on_error:
        logging.warning("Error running %s", cmd)
      else:
        logging.debug("Error running %s", cmd)
    logging.info("Command %s finished with return code %s", cmd,
                 process.returncode)
    if capture_stdout:
      return stdout
    else:
      return process.returncode == 0

# --------------------------------------------------------------------------- #

class AttrDict(dict):
  """A dict that allows element access via attributes.

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

# --------------------------------------------------------------------------- #

import collections

class BufferedIter(collections.Iterator):
  """An iterator that saves its results

  >>> bi = BufferedIter("abcde")
  >>> next(bi)
  'a'
  >>> next(bi)
  'b'
  >>> next(bi)
  'c'
  >>> next(bi)
  'd'
  >>> bi.rewind()
  >>> next(bi)
  'a'
  >>> next(bi)
  'b'
  >>> bi.rewind(1)
  >>> next(bi)
  'b'
  >>> next(bi)
  'c'
  >>> bi.rewind(2)
  >>> next(bi)
  'b'
  >>> next(bi)
  'c'
  >>> bi.rewind()
  >>> next(bi)
  'a'
  >>> next(bi)
  'b'
  >>> bi.clear_buffer()
  >>> next(bi)
  'c'
  >>> bi.peek()
  'd'
  >>> next(bi)
  'd'
  >>> bi.peek()
  'e'
  >>> next(bi)
  'e'
  >>> bi.peek() is None
  True
  >>> next(bi)
  Traceback (most recent call last):
      ...
  StopIteration
  >>> bi.peek() is None
  True
  >>> next(bi)
  Traceback (most recent call last):
      ...
  StopIteration
  """
  def __init__(self, itr):
    self.itr = iter(itr)
    self.buffer = []
    self.replay = []

  def next(self):
    return self.__next__()

  def __next__(self):
    self.buffer.append(self.advance())
    return self.buffer[-1]

  def clear_buffer(self):
    self.buffer = []

  def advance(self):
    # doesn't save to the buffer
    if self.replay:
      return self.replay.pop()
    return next(self.itr)

  def rewind(self, n=None):
    while (self.buffer if n is None else n > 0):
      self.replay.append(self.buffer.pop())
      if n:
        n -= 1

  def peek(self):
    try:
      retval = next(self)
      self.rewind(1)
      return retval
    except StopIteration:
      return None


class ChooseIter(object):
  """An iterator which can be advanced in multiple ways

  Not a proper iter -- extra arguments to next are handled unconventionally

  >>> ci = ChooseIter("abcdef", func=lambda x, n=1: [next(x)] * n)
  >>> ci.peek(4)
  ['a', 'a', 'a', 'a']
  >>> ci.peek()
  ['a']
  >>> ci.peek(3)
  ['a', 'a', 'a']
  >>> ci.peek(4)
  ['a', 'a', 'a', 'a']
  >>> ci.peek(3)
  ['a', 'a', 'a']
  >>> ci.next(3)
  ['a', 'a', 'a']
  >>> ci.peek(3)
  ['b', 'b', 'b']
  >>> ci.next(3)
  ['b', 'b', 'b']
  >>> ci.next(4)
  ['c', 'c', 'c', 'c']
  >>> ci.next(4)
  ['d', 'd', 'd', 'd']
  >>> next(ci)
  ['e']
  >>> ci.peek()
  ['f']
  >>> next(ci)
  ['f']
  >>> ci.peek() is None
  True
  >>> next(ci)
  Traceback (most recent call last):
      ...
  StopIteration
  >>> ci.peek() is None
  True
  >>> next(ci)
  Traceback (most recent call last):
      ...
  StopIteration
  """

  def __init__(self, itr, func=None):
    self.itr = BufferedIter(itr)
    if func:
      self.func = func
    else:
      self.func = lambda itr, *args, **kwargs: next(itr)
    self.cache = {}

  def peek(self, *args, **kwargs):
    key = (args, tuple((k, v) for (k, v) in kwargs.iteritems()))
    if key not in self.cache:
      try:
        self.cache[key] = self.func(self.itr, *args, **kwargs)
        self.itr.rewind()
      except StopIteration:
        self.cache[key] = None
    return self.cache[key]

  def next(self, *args, **kwargs):
    return self.__next__(*args, **kwargs)

  def __next__(self, *args, **kwargs):
    self.cache.clear()
    val = self.func(self.itr, *args, **kwargs)
    self.itr.clear_buffer()
    return val

# --------------------------------------------------------------------------- #
