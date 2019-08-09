#!/usr/bin/env python
# -*- mode: python; eval: (no-pyformat-mode) -*-
"""
Given a list of 4-letter words, create a 4x4 crossword -- a 4x4 grid
where every row and every column is a valid word. In fact, produce
every such grid.

https://en.m.wikipedia.org/wiki/Word_square

With --test, it should print:

--
a b c
b c a
c a b
--
c a b
a b c
b c a
--
b c a
c a b
a b c

"""

# --------------------------------------------------------------------------- #

from __future__ import absolute_import, division, with_statement

import contextlib
import logging
import math
import optparse
import urllib

# --------------------------------------------------------------------------- #

logging.basicConfig(format='[%(asctime)s '
                    '%(funcName)s:%(lineno)s %(levelname)-5s] '
                    '%(message)s')

DEFAULT_SIZE = 4

# --------------------------------------------------------------------------- #

def main():
    (opts, args) = getopts()

    if opts.test:
        words = ['abc', 'bca', 'cab']
        opts.start = 0
    elif opts.words:
        words = opts.words
    else:
        words = get_words()

    if opts.board:
        board = Board.from_string(opts.board)
    else:
        board = Board(rows=opts.size, cols=opts.size)

    logging.debug("Board = %s", board)
    logging.debug("Empties = %s", list(iter_empties(board)))
    print_solutions(solve(words, board), start=opts.start, num=opts.num)


def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--start', type=int, default=10000)
    parser.add_option('--num', type=int, default=1)
    parser.add_option('--board')
    parser.add_option('--size', type=int, default=4)
    parser.add_option('--words', action='append')
    parser.add_option('--test', action='store_true')
    parser.add_option('--verbose',  action='store_true')
    parser.add_option('--log_level',
                      help="The level to log at")
    (opts, args) = parser.parse_args()

    if opts.verbose:
        logat(logging.DEBUG)

    if opts.log_level is not None:
        logat(opts.log_level)


    if opts.words:
        opts.words = [word for group in opts.words for word in group.split(",")]
    return (opts, args)

def logat(level):
    if isinstance(level, basestring):
        level = getattr(logging, level.upper())
    logging.getLogger().setLevel(level)
    logging.info("Setting log level to %s", level)

# --------------------------------------------------------------------------- #

class Trie(object):
    """
    A Trie is a tree-like structure for storing strings, usually,
    though it can be used to store many things.  The value to be
    stored usually determines where it should be stored in the tree.
    Usually, the Trie stores strings.  Each node of the tree has edges
    corresponding to each letter.  The value is the path through the
    tree that you take to determine which node stores the value.
    """
    def __init__(self, values=None, value_to_path=None):
        """
        Create a new Trie.  If we are seeded with some values, insert those.
        """
        self.children = {}
        self.value = None
        if value_to_path is None:
            self.value_to_path_func = self._default_value_to_path
        else:
            self.value_to_path_func = value_to_path
        if values is not None:
            for value in values:
                self.insert(value)

    @classmethod
    def _default_value_to_path(cls, value):
        """
        Where should we store a particular value (if the user doesn't
        insert us with a particular path).  We just treat the value as
        an iterable, if possible.  Otherwise, we convert it to a string.
        >>> Trie._default_value_to_path('abc')
        'abc'
        >>> Trie._default_value_to_path(3)
        '3'
        """
        try:
            iter(value)
            return value
        except TypeError:
            return str(value)

    def insert(self, value, path=None):
        """
        Insert a value.
        """
        if path is None:
            path = self.value_to_path_func(value)
        if not path:
            self.value = value
            return self
        else:
            if path[0] not in self.children:
                self.children[path[0]] = Trie()
            self.children[path[0]].insert(value, path[1:])
            return self

    def subtrie(self, path, create=False):
        """
        Given a path, return the subtrie rooted at the end of that path.
        If the subtrie doesn't exist in the trie, return None.  If
        create is true, then it will create the path if necessary.
        >>> print str(Trie(['agb', 'agbas', 'basd', 'agbsdfa']).
        ... subtrie('agb', create=False))
        agb
         a : None
          s : agbas
         s : None
          d : None
           f : None
            a : agbsdfa
        """
        if not path:
            return self
        if path[0] not in self.children:
            if not create:
                return None
            self.children[path[0]] = Trie()
        return self.children[path[0]].subtrie(path[1:], create=create)

    def setdefault(self, path, default):
        """
        Get the value at the end of a particular path.  If there is no
        value there, set it to the given default
        >>> t = Trie(['agb', 'agbas', 'basd'])
        >>> t.setdefault('foo', []).append('bar')
        >>> t.setdefault('foo', []).append('baz')
        >>> t.get('foo')
        ['bar', 'baz']
        """
        subtrie = self.subtrie(self.value_to_path_func(path), create=True)
        if subtrie.value is None:
            subtrie.value = default
        return subtrie.value

    def get(self, path, default=None):
        """
        Get the value at the end of a particular path.  If there is no
        value there, return None.
        >>> t = Trie(['agb', 'agbas', 'basd'])
        >>> t.get('agb')
        'agb'
        >>> t.get('foo')
        >>> t.get('foo', 'bar')
        'bar'
        """
        subtrie = self.subtrie(self.value_to_path_func(path), create=False)
        return default if subtrie is None else subtrie.value

    def to_string(self, depth=0):
        """
        Return a string representation of a Trie.
        >>> print str(Trie(['agb', 'agbas', 'basd']))
        None
         a : None
          g : None
           b : agb
            a : None
             s : agbas
         b : None
          a : None
           s : None
            d : basd
        """
        retval = str(self.value)
        for sub in self.children:
            retval += '\n{0}{1} : {2}'.format(
                ' ' * (depth+1), # indent
                sub,
                self.children[sub].to_string(depth+1))
        return retval

    def __iter__(self):
        """
        Iterate through the keys of the Trie, sorted.
        Converts keys into strings and concatenates them.
        >>> list(Trie(['zasdf', 'agb', 'agbas', 'basd']))
        ['agb', 'agbas', 'basd', 'zasdf']
        >>> t = Trie()
        >>> t.insert(range(3), path='abc')
        Trie(['abc'])
        >>> list(t)
        ['abc']
        """
        if self.value is not None:
            yield ""
        for sub in sorted(self.children):
            for key in self.children[sub]:
                yield str(sub) + str(key)

    def itervalues(self):
        """
        Iterate through the values in the Trie, sorted.
        >>> list(Trie(['zasdf', 'agb', 'agbas', 'basd']).itervalues())
        ['agb', 'agbas', 'basd', 'zasdf']
        >>> t = Trie()
        >>> t.insert(range(3), path='abc')
        Trie(['abc'])
        >>> list(t.itervalues())
        [[0, 1, 2]]
        """
        if self.value is not None:
            yield self.value
        for sub in sorted(self.children):
            for value in self.children[sub].itervalues():
                yield value

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        """
        If the Trie has fewer than 6 elements, print a string that will
        reconstruct the Trie.  Otherwise, print the default repr.
        >>> Trie(['agb', 'agbas', 'basd'])
        Trie(['agb', 'agbas', 'basd'])
        >>> Trie(range(3))
        Trie(['0', '1', '2'])
        >>> Trie(range(9)) # doctest: +ELLIPSIS
        <crossword.Trie object at ...>
        """
        itr = iter(self)
        nvals = tuple(next(itr) for _ in xrange(6))
        if len(nvals) < 6:
            return '{cn}({lst})'.format(cn=self.__class__.__name__,
                                        lst=list(self))
        else:
            return super(Trie, self).__repr__()

# ------------------------------------------------------------- #

class FieldMixin(object):
    """
    A Mixin that applies to classes that have a few key attributes
    that determine all the other behavior.  Those attributes have to
    be settable as keyword arguments in the __init__ function.  In
    that case, if you put the names of those attributes in _flds, then
    this Mixin will provide repr, cmp, and hash functions.
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


class Board(FieldMixin):
    """
    >>> b = Board(rows=4, cols=4, letters={(1, 2): 'A', (1, 1): 'B'})
    >>> b == eval(repr(b))
    True
    >>> b
    Board(rows = 4,
          cols = 4,
          letters = {(1, 2): 'A', (1, 1): 'B'})
    >>> print b
    --
    . . . .
    . B A .
    . . . .
    . . . .
    >>> list(b.get_range((1, 1), (1, 2)))
    ['B', 'A']
    """
    EMPTY = '.'
    BLOCK = '#'

    def __init__(self, rows=DEFAULT_SIZE, cols=DEFAULT_SIZE,
                 letters=None, blocks=None):
        """
        A board is represented as a list of rows x cols values.  Each
        value can either be empty, or it can be blacked out, or it can
        contain a letter.
        A spot on the board is usually referred to by a "location" or
        "loc", which is a (row, col) tuple.
        """
        super(Board, self).__init__()
        self.rows = rows
        self.cols = cols
        self.board = []
        self.letters = letters if letters else {}
        self.blocks = blocks if blocks else set()
        self._reset_board()

    def __str__(self):
        return ('--\n' +
                '\n'.join(' '.join(self._get((r, c)) for c in xrange(self.cols))
                          for r in xrange(self.rows)))

    @property
    def _flds(self):
        return ('rows', 'cols', 'letters', 'blocks')

    def _loc_to_idx(self, loc):
        """
        Translates from a location (a (row, col) tuple) to an index into
        the board, which is just a list of values.
        """
        (row, col) = loc
        return row * self.cols + col

    def _get(self, loc):
        idx = self._loc_to_idx(loc)
        try:
            return self.board[idx]
        except IndexError:
            (tp, value, traceback) = sys.exc_info()
            value = 'Index {0}, from {1} out of range: {2}'.format(idx, loc, value)
            raise tp, value, traceback

    def _set(self, loc, value):
        idx = self._loc_to_idx(loc)
        try:
            self.board[idx] = value
        except IndexError:
            (tp, value, traceback) = sys.exc_info()
            value = 'Index {0} out of range: {1}'.format(idx, value)
            raise tp, value, traceback
        return self

    def _reset_board(self):
        """
        Call this after changing self.queens to recompute which locations
        are being attacked.
        """
        self.board = [self.EMPTY] * (self.rows * self.cols)
        for loc in self.letters:
            self.add_letter(loc, self.letters[loc])
        for loc in self.blocks:
            self.set_block(loc)
        return self

    @classmethod
    def from_string(cls, string):
        rows = string.lower().split()
        num_cols = max(len(r) for r in rows)
        board = Board(rows=len(rows), cols=num_cols)
        for rr in xrange(len(rows)):
            for cc in xrange(len(rows[rr])):
                loc = (rr, cc)
                char = rows[rr][cc]
                if char == cls.BLOCK:
                    board.set_block(loc)
                elif char == cls.EMPTY:
                    pass
                else:
                    board.add_letter(loc, char)
        return board

    def add_letter(self, loc, letter):
        """
        Add a letter to the board at the given location.
        """
        if letter in (self.EMPTY, self.BLOCK):
            raise ValueError("Invalid letter: {0}".format(letter))
        if loc not in self.letters:
            self.letters[loc] = letter
        self._set(loc, letter)
        return self

    def set_block(self, loc):
        """
        Set the given location to be a block
        """
        self._set(loc, self.BLOCK)
        self.blocks.add(loc)

    def clear_loc(self, loc):
        """
        Remove any letter from the given location.
        """
        if self._get(loc) != self.BLOCK:
            self._set(loc, self.EMPTY)
        if loc in self.letters:
            del self.letters[loc]
            #self._reset_board()
        return self

    def is_empty(self, loc):
        return self._get(loc) == self.EMPTY

    def is_block(self, loc):
        return self._get(loc) == self.BLOCK

    def _all_locs(self):
        return ((row, col)
                for row in xrange(self.rows)
                for col in xrange(self.cols))

    def empty_locs(self):
        return (loc for loc in self._all_locs()
                if self.is_empty(loc))

    def get(self, loc):
        return self._get(loc)

    def get_range(self, start_loc, end_loc, incr=None):
        """
        This is a bit hacky, it doesn't handle corner cases well,
        such as if the end_loc is not on the board or is either above
        or to the left of the start_loc.  Use with caution.
        """
        if not incr:
            (srow, scol) = start_loc
            (erow, ecol) = end_loc
            diff = (erow - srow, ecol - scol)
            incr = [int(math.copysign(1, erow-srow)),
                    int(math.copysign(1, ecol-scol))]
            if diff[0] == 0:
                incr[0] = 0
            elif diff[1] == 0:
                incr[1] = 0
            elif diff[0] != diff[1]:
                raise ValueError(
                    "Can't determine increment from {0} to {1}".format(
                        start_loc, end_loc))
        loc = start_loc
        while loc[0] >=0 and loc[0] < self.rows and loc[1] >= 0 and loc[1] < self.cols:
            yield self._get(loc)
            if loc == end_loc:
                break
            loc = (loc[0] + incr[0], loc[1] + incr[1])


# --------------------------------------------------------------------------- #

def iter_empties(board):
    """
    Find empty locs in this order.  By alternating rows/cols somewhat,
    we find conflicts more quickly.
    0, 0

    0, 1
    1, 0
    1, 1

    2, 0
    2, 1
    0, 2
    1, 2
    2, 2

    3, 0
    3, 1
    3, 2
    0, 3
    1, 3
    2, 3
    3, 3
    ...

    """
    maxn = max(board.rows, board.cols)
    maxrow = board.rows - 1
    maxcol = board.cols - 1
    for ii in xrange(maxn):
        max_ii_row = min(ii, maxrow)
        max_ii_col = min(ii, maxcol)
        row = max_ii_row
        if row == ii:
            for col in xrange(max_ii_col):
                if board.is_empty((row, col)):
                    yield (row, col)
        col = max_ii_col
        if col == ii:
            for row in xrange(max_ii_row + 1):
                if board.is_empty((row, col)):
                    yield (row, col)

def next_empty(board):
    """
    Return the next empty location, or None if the board is full.
    """
    try:
        #return next(board.empty_locs())
        return next(iter_empties(board))
    except StopIteration:
        return None

def by_prefix(trie, prefixes):
    """
    Given a list of prefixes and lengths, find all words
    of the given length that start with the given prefix,
    and return all valid next letters
    """
    letters = None
    for prefix in prefixes:
        subtrie = trie.subtrie(prefix)
        if not subtrie:
            print "No possibilities for prefix: ", prefix
            #raise ValueError("No possibilities for prefix: {0}".format(prefix))
            continue
        next_letters = subtrie.children.keys()
        if letters is None:
            letters = set(next_letters)
        else:
            letters.intersection_update(next_letters)
    if letters is None:
        return set()
    return letters

def get_prefix_and_length(board, loc, direction):
  (row, col) = loc
  if direction == "row":
    index = row
    max_index = board.rows
  else:
    index = col
    max_index = board.cols
  prefix = ""
  for temp_index in xrange(index - 1, -1, -1):
    if direction == "row":
      temp_loc = (temp_index, col)
    else:
      temp_loc = (row, temp_index)
    if board.is_block(temp_loc):
      break
    prefix = board.get(temp_loc) + prefix

  length = len(prefix) + 1
  for temp_index in xrange(index + 1, max_index):
    if direction == "row":
      temp_loc = (temp_index, col)
    else:
      temp_loc = (row, temp_index)
    if board.is_block(temp_loc):
      break
    length += 1

  #print board, loc, prefix, length
  return prefix, length

def get_possible_letters(trie_list, board, loc):
    (row, col) = loc
    letters = None
    for direction in ("row", "col"):
      prefix, length = get_prefix_and_length(board, loc, direction)
      if length not in trie_list:
        letters = set()
      elif letters is None:
        letters = set(by_prefix(trie_list[length], [prefix]))
      else:
        letters.intersection_update(by_prefix(trie_list[length], [prefix]))
    return letters

def helper(trie_list, board):
    # Nothing stops us from using the same word in multiple
    # places on the board, such as:
    #   a a h s
    #   a d i t
    #   h i v e
    #   s t e p
    spot = next_empty(board)
    if not spot:
        yield board
        return
    letters = get_possible_letters(trie_list, board, spot)
    if not letters:
        logging.debug("Stuck, no letters for: %s, %s", board, spot)
    for letter in letters:
        board.add_letter(spot, letter)
        for solution in helper(trie_list, board):
            yield solution
        board.clear_loc(spot)

def solve(words, board, nchars=None):
    trie_list = {}
    for word in words:
        trie_list.setdefault(len(word), Trie()).insert(word.lower())
    for solution in helper(trie_list, board):
        yield solution

def get_words():
    #url = ('https://raw.githubusercontent.com/wcyuan/Scripts/master/random/'
    #       '4_letter_enable2k_words.txt')
    url = 'https://www.wordgamedictionary.com/sowpods/download/sowpods.txt'
    #url = 'https://www.wordgamedictionary.com/twl06/download/twl06.txt'
    #url = 'https://www.wordgamedictionary.com/english-word-list/download/english.txt'
    with contextlib.closing(urllib.urlopen(url)) as fd:
        words = [word.rstrip() for word in fd.readlines()
                 if not word.startswith("#")]
    return words

def print_solutions(solutions, start=10000, num=1):
    end = start + num - 1
    nvalues = 0
    for board in solutions:
        nvalues += 1
        if nvalues >= start:
            print board
        if nvalues >= end:
            break

# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    main()

# --------------------------------------------------------------------------- #
