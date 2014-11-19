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
