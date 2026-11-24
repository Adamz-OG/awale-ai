"""The interface asked by the assignment, on boards stored as two lists.

The assignment works on a mutable board ``[[a..f], [g..l]]`` and four
functions: :func:`play`, :func:`is_end`, :func:`enum` and :func:`suggest`.
They are kept here with the same signatures, on top of the immutable
implementation of :mod:`awale.rules` and :mod:`awale.search`.
"""

from __future__ import annotations

from awale import rules, search
from awale.board import from_rows

Rows = list[list[int]]


def play(board: Rows, player: int, cell: int) -> int:
    """Play ``cell`` for ``player``, update ``board`` in place, return the capture."""
    move = rules.apply_move(from_rows(board), player, cell)
    board[0][:] = move.board[:6]
    board[1][:] = move.board[6:]
    return move.captured


def is_end(board: Rows, player: int) -> bool:
    """Whether the game is over when it is ``player``'s turn."""
    return rules.is_end(from_rows(board), player)


def enum(board: Rows, player: int, depth: int) -> list[tuple[list[int], int]]:
    """Every line of at most ``depth`` plies with its final score."""
    lines = search.enumerate_lines(from_rows(board), player, depth)
    return [(list(moves), score) for moves, score in lines]


def suggest(board: Rows, player: int, depth: int) -> int:
    """Best cell for ``player``, looking ``depth`` plies ahead."""
    return search.suggest(from_rows(board), player, depth)
