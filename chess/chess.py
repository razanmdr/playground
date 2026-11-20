"""
Chess rules engine (movement and captures only).

Scope: 8x8 board, two sides taking turns, six piece types with their move
rules, captures, path blocking (only the Knight jumps).
Out of scope: check/checkmate, castling, promotion, en passant.

Coordinates are (row, col), both 0-7. Row 0 is Black's back rank (top),
row 7 is White's (bottom). White moves "up" (row decreases).
"""
from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

BOARD_SIZE = 8


# ---------------------------------------------------------------- domain types
class Color(Enum):
    WHITE = "White"
    BLACK = "Black"

    @property
    def opponent(self) -> "Color":
        return Color.BLACK if self is Color.WHITE else Color.WHITE

    @property
    def forward(self) -> int:
        """Row delta towards the opponent."""
        return -1 if self is Color.WHITE else 1

    @property
    def pawn_start_row(self) -> int:
        return 6 if self is Color.WHITE else 1


@dataclass(frozen=True)
class Position:
    row: int
    col: int

    def is_on_board(self) -> bool:
        return 0 <= self.row < BOARD_SIZE and 0 <= self.col < BOARD_SIZE

    def __add__(self, delta: tuple[int, int]) -> "Position":
        return Position(self.row + delta[0], self.col + delta[1])


@dataclass(frozen=True)
class Move:
    src: Position
    dst: Position

    @property
    def d_row(self) -> int:
        return self.dst.row - self.src.row

    @property
    def d_col(self) -> int:
        return self.dst.col - self.src.col


# ---------------------------------------------------------------------- pieces
class Piece(ABC):
    symbol: str = "??"
    name: str = "Piece"

    def __init__(self, color: Color):
        self.color = color

    def __str__(self) -> str:
        return self.symbol.upper() if self.color is Color.WHITE else self.symbol.lower()

    @abstractmethod
    def can_move(self, move: Move, board: "Board") -> bool:
        """Geometry + path rules only. Turn, ownership and own-capture are checked elsewhere."""


class SlidingPiece(Piece):
    """Rook, Bishop, Queen: any distance along fixed directions, cannot jump."""
    directions: tuple[tuple[int, int], ...] = ()

    def can_move(self, move: Move, board: "Board") -> bool:
        return unit_step(move) in self.directions and board.is_path_clear(move.src, move.dst)


class Rook(SlidingPiece):
    symbol, name = "RK", "Rook"
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))


class Bishop(SlidingPiece):
    symbol, name = "BS", "Bishop"
    directions = ((1, 1), (1, -1), (-1, 1), (-1, -1))


class Queen(SlidingPiece):
    symbol, name = "QU", "Queen"
    directions = Rook.directions + Bishop.directions


class Knight(Piece):
    symbol, name = "KN", "Knight"

    def can_move(self, move: Move, board: "Board") -> bool:
        return {abs(move.d_row), abs(move.d_col)} == {1, 2}   # jumps: no path check


class King(Piece):
    symbol, name = "KI", "King"

    def can_move(self, move: Move, board: "Board") -> bool:
        return max(abs(move.d_row), abs(move.d_col)) == 1


class Pawn(Piece):
    symbol, name = "PW", "Pawn"

    def can_move(self, move: Move, board: "Board") -> bool:
        fwd = self.color.forward
        target = board.get(move.dst)
        if move.d_col == 0:                                  # push: target must be empty
            if target is not None:
                return False
            if move.d_row == fwd:
                return True
            return (move.d_row == 2 * fwd and move.src.row == self.color.pawn_start_row
                    and board.is_path_clear(move.src, move.dst))
        return abs(move.d_col) == 1 and move.d_row == fwd and target is not None  # capture


PIECES = {cls.symbol: cls for cls in (Rook, Knight, Bishop, Queen, King, Pawn)}


def unit_step(move: Move) -> Optional[tuple[int, int]]:
    """(dr, dc) normalised to -1/0/1 for straight or diagonal moves, else None."""
    dr, dc = move.d_row, move.d_col
    if (dr, dc) == (0, 0) or (dr and dc and abs(dr) != abs(dc)):
        return None
    sign = lambda x: (x > 0) - (x < 0)
    return sign(dr), sign(dc)


# ----------------------------------------------------------------------- board
class Board:
    BACK_RANK = (Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook)

    def __init__(self):
        self._grid: list[list[Optional[Piece]]] = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]

    @classmethod
    def standard(cls) -> "Board":
        b = cls()
        for col, piece_cls in enumerate(cls.BACK_RANK):
            b.set(Position(0, col), piece_cls(Color.BLACK))
            b.set(Position(1, col), Pawn(Color.BLACK))
            b.set(Position(6, col), Pawn(Color.WHITE))
            b.set(Position(7, col), piece_cls(Color.WHITE))
        return b

    @classmethod
    def from_rows(cls, rows: list[str]) -> "Board":
        """Build a board from 8 strings of 8 two-letter codes ('--' = empty, upper = White)."""
        b = cls()
        for r, line in enumerate(rows):
            for c, code in enumerate(line.split()):
                if code != "--":
                    color = Color.WHITE if code.isupper() else Color.BLACK
                    b.set(Position(r, c), PIECES[code.upper()](color))
        return b

    def get(self, pos: Position) -> Optional[Piece]:
        return self._grid[pos.row][pos.col]

    def set(self, pos: Position, piece: Optional[Piece]) -> None:
        self._grid[pos.row][pos.col] = piece

    def move_piece(self, move: Move) -> Optional[Piece]:
        """Apply a move without validation. Returns the captured piece, if any."""
        captured = self.get(move.dst)
        self.set(move.dst, self.get(move.src))
        self.set(move.src, None)
        return captured

    def is_path_clear(self, src: Position, dst: Position) -> bool:
        """True if every square strictly between src and dst is empty."""
        step = unit_step(Move(src, dst))
        if step is None:
            return False
        cur = src + step
        while cur != dst:
            if self.get(cur) is not None:
                return False
            cur = cur + step
        return True

    def rows(self) -> list[list[str]]:
        return [[str(p) if p else "--" for p in row] for row in self._grid]

    def render(self) -> str:
        lines = ["    " + "  ".join(f"{c} " for c in range(BOARD_SIZE))]
        lines += [f"{r}   " + "  ".join(row) for r, row in enumerate(self.rows())]
        return "\n".join(lines)


# ------------------------------------------------------------ validation chain
# Each validator returns an error message, or None if the check passes.
# The function name doubles as a machine-readable error code.
Validator = Callable[["Game", Move], Optional[str]]


def on_board(game: "Game", move: Move) -> Optional[str]:
    if not (move.src.is_on_board() and move.dst.is_on_board()):
        return "Coordinates must be between 0 and 7."


def piece_exists(game: "Game", move: Move) -> Optional[str]:
    if game.board.get(move.src) is None:
        return "There is no piece on the first square."


def owned_by_current_player(game: "Game", move: Move) -> Optional[str]:
    if game.board.get(move.src).color is not game.turn:
        return f"That piece does not belong to {game.turn.value}."


def not_same_square(game: "Game", move: Move) -> Optional[str]:
    if move.src == move.dst:
        return "Start and target square are the same."


def not_capturing_own(game: "Game", move: Move) -> Optional[str]:
    target = game.board.get(move.dst)
    if target is not None and target.color is game.turn:
        return "You cannot capture your own piece."


def follows_piece_rules(game: "Game", move: Move) -> Optional[str]:
    piece = game.board.get(move.src)
    if not piece.can_move(move, game.board):
        return f"Illegal move for a {piece.name}."


# Selecting a piece runs the first three checks; playing a move runs all six.
SELECTION_VALIDATORS: tuple[Validator, ...] = (on_board, piece_exists, owned_by_current_player)
DEFAULT_VALIDATORS: tuple[Validator, ...] = SELECTION_VALIDATORS + (
    not_same_square,
    not_capturing_own,
    follows_piece_rules,   # last: assumes every check above passed
)


# ------------------------------------------------------------------------ game
class InvalidMove(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


@dataclass
class Turn:
    """One played move, enough to show it in a history list and to undo it."""
    move: Move
    piece: Piece
    captured: Optional[Piece]
    board_before: Board


class Game:
    def __init__(self, board: Optional[Board] = None, turn: Color = Color.WHITE,
                 validators: tuple[Validator, ...] = DEFAULT_VALIDATORS):
        self.board = board or Board.standard()
        self.turn = turn
        self.validators = validators
        self.history: list[Turn] = []

    def validate(self, move: Move, validators: Optional[tuple[Validator, ...]] = None) -> None:
        for check in validators or self.validators:
            error = check(self, move)
            if error:
                raise InvalidMove(error, check.__name__)

    def validate_selection(self, pos: Position) -> None:
        self.validate(Move(pos, pos), SELECTION_VALIDATORS)

    def legal_destinations(self, src: Position) -> list[Position]:
        moves = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                try:
                    self.validate(Move(src, Position(r, c)))
                    moves.append(Position(r, c))
                except InvalidMove:
                    pass
        return moves

    def play(self, move: Move) -> Optional[Piece]:
        self.validate(move)
        before = copy.deepcopy(self.board)
        piece = self.board.get(move.src)
        captured = self.board.move_piece(move)
        self.history.append(Turn(move, piece, captured, before))
        self.turn = self.turn.opponent
        return captured

    def undo(self) -> bool:
        if not self.history:
            return False
        last = self.history.pop()
        self.board = last.board_before
        self.turn = self.turn.opponent
        return True

    def captured_by(self, color: Color) -> list[Piece]:
        return [t.captured for t in self.history if t.captured and t.piece.color is color]


# ------------------------------------------------------------------------- CLI
def parse_position(text: str) -> Position:
    parts = text.split()
    if len(parts) != 2 or not all(p.lstrip("-").isdigit() for p in parts):
        raise ValueError("Format: 'row col', e.g. 6 4")
    return Position(int(parts[0]), int(parts[1]))


def main() -> None:
    game = Game()
    print("CLI chess. Type 'q' to quit.\n")
    while True:
        print(game.board.render())
        try:
            raw_src = input(f"[{game.turn.value}] From: ").strip()
            if raw_src.lower() == "q":
                break
            raw_dst = input(f"[{game.turn.value}] To:   ").strip()
            if raw_dst.lower() == "q":
                break
            captured = game.play(Move(parse_position(raw_src), parse_position(raw_dst)))
            if captured:
                print(f"{captured} captured!")
        except (ValueError, InvalidMove) as e:
            print(f"Invalid move: {e}")
        except (EOFError, KeyboardInterrupt):
            break
        print()


if __name__ == "__main__":
    main()
