#!/usr/bin/env python
"""
A script to solve the N-queen problem by brute force

http://en.wikipedia.org/wiki/Eight_queens_puzzle

Finds a solution in about 7 seconds:

Q x x x x x x x
x x x x Q x x x
x x x x x x x Q
x x x x x Q x x
x x Q x x x x x
x x x x x x Q x
x Q x x x x x x
x x x Q x x x x

"""

# ------------------------------------------------------------- #

import itertools
import logging
import optparse
import sys

# ------------------------------------------------------------- #

DEFAULT_SIZE = 8

def main():
    opts = getopts()
    board = Board(rows=opts.rows, cols=opts.cols)
    do_search(board, nqueens=opts.nqueens)
    print board

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--rows', type=int, default=DEFAULT_SIZE)
    parser.add_option('--cols', type=int, default=DEFAULT_SIZE)
    parser.add_option('--nqueens', type=int, default=DEFAULT_SIZE)
    parser.add_option('-n', type=int)
    parser.add_option('--verbose', action='store_true')
    opts, args = parser.parse_args()
    if len(args) != 0:
        raise ValueError("Too many arguments: {0}".format(args))
    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    if opts.n is not None:
        opts.rows = opts.n
        opts.cols = opts.n
        opts.nqueens = opts.n
    return opts

# ------------------------------------------------------------- #

class FieldMixin(object):
    """
    A Mixin that applies to classes that have a few key attributes
    that determine all the other behavior.  Those attributes have to
    be settable as keyword arguments in the __init__ function.  In
    that case, if you put the names of those attributes in _flds, then
    this Mixin will provide repr, cmp, and hash functions.
    """
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
    >>> b = Board().add_queen((3, 5))
    >>> b == eval(repr(b))
    True
    >>> b
    Board(rows = 8,
          cols = 8,
          queens = [(3, 5)])

    >>> print b
    --
    . . x . . x . .
    . . . x . x . x
    . . . . x x x .
    x x x x x Q x x
    . . . . x x x .
    . . . x . x . x
    . . x . . x . .
    . x . . . x . .

    """
    EMPTY = '.'
    ATTACKED = 'x'
    QUEEN = 'Q'

    def __init__(self, rows=DEFAULT_SIZE, cols=DEFAULT_SIZE, queens=None):
        super(Board, self).__init__()
        self.rows = rows
        self.cols = cols
        self.board = []
        self.queens = [] if queens is None else queens
        self.reset_board()

    def __str__(self):
        return '--\n' + '\n'.join(' '.join(self._get((r, c)) for c in xrange(self.cols))
                                  for r in xrange(self.rows))

    @property
    def _flds(self):
        return ('rows', 'cols', 'queens')

    def _loc_to_idx(self, loc):
        (row, col) = loc
        return row * self.cols + col

    def _get(self, loc):
        idx = self._loc_to_idx(loc)
        try:
            return self.board[idx]
        except IndexError:
            (tp, value, traceback) = sys.exc_info()
            value = 'Index {0} out of range: {1}'.format(idx, value)
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

    def reset_board(self):
        self.board = [self.EMPTY] * (self.rows * self.cols)
        for queen in self.queens:
            self.add_queen(queen)
        return self

    def set_empty(self, loc):
        self.board[self._loc_to_idx(loc)] = self.EMPTY
        return self

    def add_queen(self, loc):
        if loc not in self.queens:
            self.queens.append(loc)
        self._set(loc, self.QUEEN)
        for attack in self.attacks(loc):
            self._set(attack, self.ATTACKED)
        return self

    def remove_queen(self, loc):
        if loc in self.queens:
            queens = [q for q in self.queens if q != loc]
            self.queens = queens
            self.reset_board()
        return self

    def is_empty(self, loc):
        return self._get(loc) == self.EMPTY

    def all_locs(self):
        return ((row, col)
                for row in xrange(self.rows)
                for col in xrange(self.cols))

    def empty_locs(self):
        return (loc for loc in self.all_locs()
                if self.is_empty(loc))

    def attacks(self, loc):
        """
        >>> b = Board(8, 8)
        >>> tuple(b.attacks((0, 0)))
        ((1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7))
        """
        (row, col) = loc
        rd_st = min(row, col)
        rd_ed = min(self.rows - row - 1, self.cols - col - 1) + rd_st + 1
        ld_st = min(row, self.cols - col - 1)
        ld_ed = min(self.rows - row - 1, col) + ld_st + 1
        return itertools.chain(
            ((r, col) for r in xrange(self.rows) if r != row),
            ((row, c) for c in xrange(self.cols) if c != col),
            ((row - rd_st + ii, col - rd_st + ii) for ii in xrange(rd_ed)
             if ii != rd_st),
            ((row - ld_st + ii, col + ld_st - ii) for ii in xrange(ld_ed)
             if ii != ld_st)
            )

def do_search(board, nqueens=8):
    if len(board.queens) == nqueens:
        return True
    empties = tuple(board.empty_locs())
    if len(empties) == 0:
        return False
    for empty in empties:
        board.add_queen(empty)
        logging.debug(board)
        if do_search(board, nqueens=nqueens):
            return True
        board.remove_queen(empty)
    return False

# ------------------------------------------------------------- #

if __name__ == '__main__':
    main()

# ------------------------------------------------------------- #
