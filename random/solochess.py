#!/usr/bin/env python
"""
Solitaire Chess

Several chess pieces are arranged on a four-by-four board.
On each move, you can move any of the pieces, but it must capture
another piece.  Continue until there are no more capturing moves left.
If there is only one piece on the board, you win, otherwise you lose.

"""

# ------------------------------------------------------------- #

import itertools
import logging
import optparse
import sys

# ------------------------------------------------------------- #

DEFAULT_SIZE = 4
LIST_SEP = '+'
PIECE_SEP = ','

def main():
    opts = getopts()
    board = Board(rows=opts.rows, cols=opts.cols, pieces=opts.pieces)
    print board
    moves = do_search(board)
    print board
    print moves

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--pieces')
    parser.add_option('--rows', type=int, default=DEFAULT_SIZE)
    parser.add_option('--cols', type=int, default=DEFAULT_SIZE)
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
    if opts.pieces is not None:
        pieces = [val.split(PIECE_SEP) for val in opts.pieces.split(LIST_SEP)]
        opts.pieces = [
            (Board.char_to_piece(char), (int(row), int(col)))
            for (char, row, col) in pieces]

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


class Piece(object):
    CHAR = None

    def __repr__(self):
        return '{0}()'.format(self.__class__.__name__)

    def __cmp__(self, other):
        return cmp(type(self), type(other))

    def __str__(self):
        return self.CHAR

    @classmethod
    def is_match(cls, char):
        return char == cls.CHAR

    @classmethod
    def moves(cls, board, loc, white=True):
        return cls.attacks(board, loc, white=white)

    @classmethod
    def attacks(cls, board, loc, white=True):
        return [loc for loc in cls.raw_attacks(board, loc, white=white)
                if board.is_on_board(loc)]

    @classmethod
    def raw_attacks(cls, board, loc, white=True):
        raise NotImplementedError

    @classmethod
    def attack_to(cls, board, loc, direction):
        (row, col) = loc
        (add_r, add_c) = direction
        while True:
            row += add_r
            col += add_c
            if not board.is_on_board((row, col)):
                break
            yield (row, col)
            if not board.is_empty((row, col)):
                break

class Pawn(Piece):
    CHAR = 'P'
    @classmethod
    def moves(cls, board, loc, white=True):
        (row, col) = loc
        new_row = row + (1 if white else -1)
        return [(new_row, col)]
    @classmethod
    def raw_attacks(cls, board, loc, white=True):
        (row, col) = loc
        new_row = row + (1 if white else -1)
        return [(new_row, col+i) for i in (1, -1)]

class King(Piece):
    CHAR = 'K'
    @classmethod
    def raw_attacks(cls, board, loc, white=True):
        (row, col) = loc
        return [(row+i, col+j)
                for i in (1, 0, -1)
                for j in (1, 0, -1)
                if not (i == 0 and j == 0)]

class Rook(Piece):
    CHAR = 'R'
    @classmethod
    def raw_attacks(cls, board, loc, white=True):
        import itertools
        (row, col) = loc
        return itertools.chain(
            cls.attack_to(board, loc, (0, 1)),
            cls.attack_to(board, loc, (0, -1)),
            cls.attack_to(board, loc, (1, 0)),
            cls.attack_to(board, loc, (-1, 0)))

class Knight(Piece):
    CHAR = 'N'
    @classmethod
    def raw_attacks(cls, board, loc, white=True):
        (row, col) = loc
        return ((row+2, col+1),
                (row+2, col-1),
                (row-2, col+1),
                (row-2, col-1),
                (row+1, col+2),
                (row+1, col-2),
                (row-1, col+2),
                (row-1, col-2))

class Bishop(Piece):
    CHAR = 'B'
    @classmethod
    def raw_attacks(cls, board, loc, white=True):
        import itertools
        (row, col) = loc
        return itertools.chain(
            cls.attack_to(board, loc, (1, 1)),
            cls.attack_to(board, loc, (1, -1)),
            cls.attack_to(board, loc, (-1, 1)),
            cls.attack_to(board, loc, (-1, -1)))

class Queen(Piece):
    CHAR = 'Q'
    @classmethod
    def raw_attacks(cls, board, loc, white=True):
        import itertools
        (row, col) = loc
        return itertools.chain(
            cls.attack_to(board, loc, (1, 1)),
            cls.attack_to(board, loc, (1, -1)),
            cls.attack_to(board, loc, (-1, 1)),
            cls.attack_to(board, loc, (-1, -1)),
            cls.attack_to(board, loc, (0, 1)),
            cls.attack_to(board, loc, (0, -1)),
            cls.attack_to(board, loc, (1, 0)),
            cls.attack_to(board, loc, (-1, 0)))

class Board(FieldMixin):
    """
    >>> b = Board(rows=8, cols=8).add_queen((3, 5))
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

    def __init__(self, rows=DEFAULT_SIZE, cols=DEFAULT_SIZE, pieces=None):
        """
        A board is represented as a list of rows x cols values.  Each
        value can either be empty, or it can contain a queen, or it
        can be attacked by a queen.

        A spot on the board is usually referred to by a "location" or
        "loc", which is a (row, col) tuple.

        """
        super(Board, self).__init__()
        self.rows = rows
        self.cols = cols
        self.board = []
        self.pieces = [] if pieces is None else sorted(pieces)
        self._reset_board()

    def __str__(self):
        return ('--\n' +
                '\n'.join(' '.join(str(self.get((r, c)))
                                   for c in xrange(self.cols))
                          for r in xrange(self.rows-1, -1, -1)))

    @property
    def _flds(self):
        return ('rows', 'cols', 'pieces')

    def _loc_to_idx(self, loc):
        """
        Translates from a location (a (row, col) tuple) to an index into
        the board, which is just a list of values.

        >>> b = Board(rows=8, cols=8)
        >>> b._loc_to_idx((0, 0))
        0
        >>> b._loc_to_idx((0, 3))
        3
        >>> b._loc_to_idx((1, 0))
        8
        >>> b._loc_to_idx((1, 4))
        12
        >>> b._loc_to_idx((2, 4))
        20

        """
        (row, col) = loc
        if row < 0 or row >= self.rows:
            raise IndexError("Invalid row {0}, should be 0 <= x < {1}".
                             format(row, self.rows))
        if col < 0 or col >= self.cols:
            raise IndexError("Invalid col {0}, should be 0 <= x < {1}".
                             format(col, self.cols))
        return row * self.cols + col

    def get(self, loc):
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

    def _reset_board(self):
        """
        Call this after changing self.queens to recompute which locations
        are being attacked.
        """
        self.board = [self.EMPTY] * (self.rows * self.cols)
        for (piece, loc) in self.pieces:
            self._set(loc, piece)
        return self

    def is_empty(self, loc):
        return self.get(loc) == self.EMPTY

    @classmethod
    def valid_pieces(cls):
        return (King(), Queen(), Bishop(), Knight(), Rook(), Pawn())

    @classmethod
    def char_to_piece(cls, char):
        if char == cls.EMPTY:
            return cls.EMPTY
        for piece in cls.valid_pieces():
            if piece.is_match(char):
                return piece
        raise ValueError("Invalid piece: {0}".format(char))

    def is_on_board(self, loc):
        (row, col) = loc
        return row >=0 and row < self.rows and col >= 0 and col < self.cols

    @classmethod
    def from_string(cls, string, separator='\n'):
        rows = string.split(separator)
        pieces = [(cls.char_to_piece(char), (ridx, cidx))
                  for (ridx, row) in enumerate(rows)
                  for (cidx, char) in enumerate(row)]
        pieces = [(piece, loc) for (piece, loc) in pieces if piece != cls.EMPTY]
        return cls(rows=len(rows),
                   cols=len(rows[0]),
                   pieces=pieces)

    def add_piece(self, piece, loc):
        assert(self.is_empty(loc))
        self.pieces = sorted(self.pieces + [(piece, loc)])
        self._set(loc, piece)

    def move(self, piece, start, end):
        assert(self.get(start) == piece)
        assert((piece, start) in self.pieces)
        if self.is_empty(end):
            assert(end in piece.moves(self, start))
        else:
            assert(end in piece.attacks(self, start))
        self._set(start, self.EMPTY)
        self._set(end, piece)
        self.pieces = sorted(
            [(pc, loc) for (pc, loc) in self.pieces
             if loc != start and loc != end] + [(piece, end)])

    def capture(self, piece, start, end):
        assert(not self.is_empty(end))
        self.move(piece, start, end)

    def possible_moves(self):
        for (piece, loc) in self.pieces:
            for end in piece.attacks(self, loc):
                if not self.is_empty(end):
                    yield (piece, loc, end)

def do_search(board):
    if len(board.pieces) <= 1:
        return (True, [])
    for (piece, loc, end) in board.possible_moves():
        captured = board.get(end)
        board.capture(piece, loc, end)
        logging.debug(board)
        (res, moves) = do_search(board)
        if res:
            moves.append((piece, loc, end))
            return (True, moves)
        board.move(piece, end, loc)
        board.add_piece(captured, end)
    return (False, None)

# ------------------------------------------------------------- #

if __name__ == '__main__':
    main()

# ------------------------------------------------------------- #
