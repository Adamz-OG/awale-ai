"""Board representation: 12 pits stored in sowing order.

The board is an immutable tuple of 12 integers. Index ``i`` belongs to
player ``i // 6`` and is that player's pit ``i % 6``. Indices follow the
counter-clockwise sowing order, so the pit after ``i`` is always
``(i + 1) % 12``::

        l   k   j   i   h   g        <- player 2 (indices 11 .. 6)
        a   b   c   d   e   f        <- player 1 (indices 0 .. 5)

Players are numbered 0 and 1 in the code and shown as 1 and 2 to people.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

Board = tuple[int, ...]
"""Seeds in each of the 12 pits, in sowing order."""

PITS_PER_SIDE = 6
PITS = 2 * PITS_PER_SIDE
INITIAL_SEEDS = 4
TOTAL_SEEDS = PITS * INITIAL_SEEDS
PLAYERS = (0, 1)
LABELS = "abcdefghijkl"


class BoardError(ValueError):
    """Raised for a malformed board, player or pit."""


def initial_board() -> Board:
    """Return the starting position: 4 seeds in every pit."""
    return (INITIAL_SEEDS,) * PITS


def make_board(cells: Sequence[int]) -> Board:
    """Validate 12 seed counts and return them as a board."""
    board = tuple(cells)
    if len(board) != PITS:
        raise BoardError(f"a board has {PITS} pits, got {len(board)}")
    if any(not isinstance(seeds, int) or seeds < 0 for seeds in board):
        raise BoardError("seed counts must be non-negative integers")
    return board


def from_rows(rows: Sequence[Sequence[int]]) -> Board:
    """Build a board from two rows ``[[a..f], [g..l]]``, as in the assignment."""
    if len(rows) != 2 or any(len(row) != PITS_PER_SIDE for row in rows):
        raise BoardError("expected two rows of 6 pits")
    return make_board([*rows[0], *rows[1]])


def to_rows(board: Board) -> list[list[int]]:
    """Return the board as two mutable rows ``[[a..f], [g..l]]``."""
    return [list(board[:PITS_PER_SIDE]), list(board[PITS_PER_SIDE:])]


def check_player(player: int) -> None:
    """Raise :class:`BoardError` unless ``player`` is 0 or 1."""
    if not isinstance(player, int) or player not in PLAYERS:
        raise BoardError(f"player must be 0 or 1, got {player!r}")


def pit_index(player: int, pit: int) -> int:
    """Index in the board of ``player``'s pit number ``pit`` (0 to 5)."""
    check_player(player)
    if not 0 <= pit < PITS_PER_SIDE:
        raise BoardError(f"pit must be between 0 and 5, got {pit!r}")
    return player * PITS_PER_SIDE + pit


def side(board: Board, player: int) -> Board:
    """Return the 6 pits of ``player``, from left to right in sowing order."""
    start = player * PITS_PER_SIDE
    return board[start : start + PITS_PER_SIDE]


def label(player: int, pit: int) -> str:
    """Letter of a pit, from ``a`` (player 1, pit 0) to ``l`` (player 2, pit 5)."""
    return LABELS[pit_index(player, pit)]


def parse_pit(text: str, player: int) -> int:
    """Read a pit given as a letter of ``player``'s row or a number from 1 to 6."""
    value = text.strip().lower()
    if value.isdigit() and 1 <= int(value) <= PITS_PER_SIDE:
        return int(value) - 1
    if len(value) == 1 and value in LABELS:
        index = LABELS.index(value)
        if index // PITS_PER_SIDE == player:
            return index % PITS_PER_SIDE
    letters = LABELS[player * PITS_PER_SIDE : (player + 1) * PITS_PER_SIDE]
    raise BoardError(f"choose a pit from {letters[0]} to {letters[-1]} or 1 to 6")


def parse_board(text: str) -> Board:
    """Parse 12 integers, rows ``a..f`` then ``g..l``, separated by anything."""
    numbers = [int(token) for token in re.findall(r"-?\d+", text)]
    return make_board(numbers)


def render(board: Board) -> str:
    """Draw the board as text, player 2 on top, as in the assignment figures."""
    top = board[PITS - 1 : PITS_PER_SIDE - 1 : -1]
    bottom = board[:PITS_PER_SIDE]
    rule = "+" + "----+" * PITS_PER_SIDE

    def cells(values: Sequence[int]) -> str:
        return "|" + "".join(f"{value:>3} |" for value in values)

    def letters(text: str) -> str:
        return " " + "".join(f"{char:>3}  " for char in text)

    return "\n".join(
        [
            letters(LABELS[PITS - 1 : PITS_PER_SIDE - 1 : -1]) + "   player 2",
            rule,
            cells(top),
            rule,
            cells(bottom),
            rule,
            letters(LABELS[:PITS_PER_SIDE]) + "   player 1",
        ]
    )
