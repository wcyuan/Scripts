#!/usr/bin/env python
"""
Solitaire Chess

Several chess pieces are arranged on a four-by-four board.
On each move, you can move any of the pieces, but it must capture
another piece.  Continue until there are no more capturing moves left.
If there is only one piece on the board, you win, otherwise you lose.

>>> b = Board(rows=4, cols=4,
...           pieces_str="B,1,0+P,0,0+B,0,1+N,1,1+N,2,2+P,3,3+R,2,1+R,3,2")
>>> print b
--
. . R P
. R N .
B N . .
P B . .
>>> (moves) = do_search(b)
>>> print b
--
. . . R
. . . .
. . . .
. . . .
>>> print moves  # doctest: +NORMALIZE_WHITESPACE
(True, [(Rook(), (3, 2), (3, 3)), (Rook(), (2, 2), (3, 2)),
        (Bishop(), (1, 0), (3, 2)), (Bishop(), (0, 1), (1, 0)),
        (Rook(), (2, 1), (2, 2)), (Pawn(), (1, 1), (2, 2)),
        (Pawn(), (0, 0), (1, 1))])

"""

# ------------------------------------------------------------- #

import itertools
import logging
import optparse
import sys

# ------------------------------------------------------------- #

DEFAULT_SIZE = 4
DEFAULT_N_PIECES = 6
LIST_SEP = '+'
PIECE_SEP = ','

def main():
    opts = getopts()
    board = Board(rows=opts.rows, cols=opts.cols, pieces_str=opts.pieces)

    if opts.generate:
        board = generate_random_puzzle(board, npieces=opts.npieces)

    print board

    if opts.generate:
        raw_input()

    boardcopy = board.copy()
    moves = do_search(board)
    print board
    print moves
    for (piece, loc, end) in reversed(moves[1]):
        boardcopy.capture(piece, loc, end)
        print boardcopy

def getopts():
    parser = optparse.OptionParser()
    parser.add_option('--pieces')
    parser.add_option('--rows', type=int, default=DEFAULT_SIZE)
    parser.add_option('--cols', type=int, default=DEFAULT_SIZE)
    parser.add_option('-n', type=int)
    parser.add_option('--verbose', action='store_true')
    parser.add_option('--generate', action='store_true')
    parser.add_option('--npieces', type=int, default=DEFAULT_N_PIECES)
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
        """
        Returns a list of all the locations that this piece is allowed to
        move.  This is the same as attacks, except for pawns which
        move differently when capturing.
        """
        return cls.attacks(board, loc, white=white)

    @classmethod
    def attacks(cls, board, loc, white=True):
        """
        Returns a list of all the locations that this piece is allowed to
        move, including capturing.  This is the same as moves, except
        for pawns which move differently when capturing.
        """
        return [loc for loc in cls.raw_attacks(board, loc, white=white)
                if board.is_on_board(loc)]


    @classmethod
    def moved_from(cls, board, loc, white=True):
        """
        Returns a list of all the locations that this piece may have moved from.

        Defaults to just the list of moves, since for most pieces,
        moves are symmetric.
        """
        return cls.moves(board, loc, white=white)

    @classmethod
    def attacked_from(cls, board, loc, white=True):
        """
        Returns a list of all the locations that this piece may have
        attacked from

        Defaults to just the list of attacks, since for most pieces,
        attacks are symmetric.
        """
        return cls.attacks(board, loc, white=white)

    @classmethod
    def raw_attacks(cls, board, loc, white=True):
        """
        This is a list of all the locations that the piece is attacking,
        but the locations might be off the board.  It will be filtered
        before being returned by the attacks method.
        """
        raise NotImplementedError

    @classmethod
    def attack_to(cls, board, loc, direction):
        """
        This is a helper function for creating the list of locations that
        the piece is attacking.  It will keep moving in a given
        direction and include all the locations that it passes until
        it reaches another piece or the edge of the board.
        """
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
    def valid(cls, board, locs):
        return [loc for loc in locs if board.is_on_board(loc)]

    @classmethod
    def moves(cls, board, loc, white=True):
        """
        This isn't quite right.  This returns the places where the piece
        is allowed to move without capturing.  We should probably
        include the places it is allowed to move including capturing.
        """
        (row, col) = loc
        new_row = row + (1 if white else -1)
        return cls.valid(board, [(new_row, col)])

    @classmethod
    def moved_from(cls, board, loc, white=True):
        """
        This isn't quite right.  This returns the places where the piece
        is allowed to move without capturing.  We should probably
        include the places it is allowed to move including capturing.
        """
        (row, col) = loc
        new_row = row + (-1 if white else 1)
        return cls.valid(board, [(new_row, col)])

    @classmethod
    def raw_attacks(cls, board, loc, white=True):
        """
        Returns the places where the piece can move with capturing.
        However, we can only move there if we are capturing, and this
        doesn't check to make sure that the move would actually be a
        capture.  And if we did do that, I don't think we have a way
        to check capturing "en passant"

        """
        (row, col) = loc
        new_row = row + (1 if white else -1)
        return cls.valid(board, [(new_row, col+i) for i in (1, -1)])

    @classmethod
    def attacked_from(cls, board, loc, white=True):
        """
        Returns the places where the piece can move with capturing.
        However, we can only move there if we are capturing, and this
        doesn't check to make sure that the move would actually be a
        capture.  And if we did do that, I don't think we have a way
        to check capturing "en passant"

        """
        (row, col) = loc
        new_row = row + (-1 if white else 1)
        return cls.valid(board, [(new_row, col+i) for i in (1, -1)])

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
    EMPTY = '.'

    def __init__(self, rows=DEFAULT_SIZE, cols=DEFAULT_SIZE,
                 pieces=None, pieces_str=None):
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
        if pieces is not None:
            self.pieces = sorted(pieces)
        elif pieces_str is not None:
            pieces = [val.split(PIECE_SEP)
                      for val in pieces_str.split(LIST_SEP)]
            self.pieces = [
                (self.char_to_piece(char), (int(row), int(col)))
                for (char, row, col) in pieces]
        else:
            self.pieces = []
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

    def copy(self):
        return eval(repr(self))

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

    def move(self, piece, start, end, force=False):
        if not force:
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
        board.move(piece, end, loc, force=True)
        board.add_piece(captured, end)
    return (False, None)

def generate_random_puzzle(board, npieces):
    import random
    valid = board.valid_pieces()
    # Exclude Queens, they make things too easy.
    valid = [v for v in valid if v != Queen()]
    started_with_pieces = len(board.pieces) > 0
    while len(board.pieces) < npieces:
        if len(board.pieces) < 1:
            row = random.randrange(board.rows)
            col = random.randrange(board.cols)
            piece = random.sample(valid, 1)[0]
            logging.debug("Adding new {0} to {1}".format(piece, (row, col)))
            logging.debug(board)
            board.add_piece(piece, (row, col))
        else:
            for (piece, loc) in random.sample(board.pieces, len(board.pieces)):
                locs = piece.attacked_from(board, loc)
                if len(locs) <= 0:
                    continue
                orig_loc = random.sample(locs, 1)[0]
                new_piece = random.sample(valid, 1)[0]
                logging.debug("Moving {0} from {1} to {2}".
                              format(piece, loc, orig_loc))
                board.move(piece, loc, orig_loc, force=True)
                board.add_piece(new_piece, loc)
                break
            else:
                if started_with_pieces:
                    # no valid moves for any pieces, start over with an
                    # empty board
                    logging.debug("No valid moves, starting over")
                    board = Board(rows=board.rows, cols=board.cols)
                    started_with_pieces = False
                else:
                    raise ValueError("Unable to place {0} pieces on board".
                                     format(npieces))

    return board

# ------------------------------------------------------------- #

if __name__ == '__main__':
    main()

# ------------------------------------------------------------- #
