"""Rules of the game: sowing, captures, the no-starving rule and the end.

The rules are those of the course assignment:

* the player empties one of their pits and sows its seeds one by one in the
  following pits, counter-clockwise; with 12 seeds or more the sowing goes
  round the board and the emptied pit receives seeds too;
* if the last seed lands in an opponent's pit that then holds 2 or 3 seeds,
  those seeds are captured, and so are the previous pits of the opponent's
  row while they also hold 2 or 3 seeds;
* a move that leaves the opponent without any seed is forbidden, unless
  every possible move does so;
* the game ends when the player to move has no seed left in their row.
"""

from __future__ import annotations

from typing import NamedTuple

from awale.board import PITS, PITS_PER_SIDE, Board, BoardError, pit_index


class IllegalMoveError(ValueError):
    """Raised when a move is not allowed by the rules."""


class Move(NamedTuple):
    """A move and its outcome."""

    pit: int
    """Pit played, from 0 to 5 in the player's own row."""
    board: Board
    """Board after sowing and capturing."""
    captured: int
    """Seeds captured by this move."""


def sow(board: Board, player: int, pit: int) -> tuple[list[int], int]:
    """Sow the seeds of a pit and return the new cells and the last index.

    The emptied pit is part of the cycle: with 12 seeds or more it gets
    seeds back, as required by the assignment.
    """
    start = pit_index(player, pit)
    if board[start] == 0:
        raise IllegalMoveError(f"pit {pit} of player {player} is empty")
    return _sow(board, start)


def capture(cells: list[int], player: int, last: int) -> int:
    """Remove captured seeds from ``cells`` (in place) and return their number.

    Captures start at the pit of the last seed and go backwards while the
    pit is in the opponent's row and holds 2 or 3 seeds.
    """
    low = (1 - player) * PITS_PER_SIDE
    high = low + PITS_PER_SIDE
    captured = 0
    index = last
    while low <= index < high and cells[index] in (2, 3):
        captured += cells[index]
        cells[index] = 0
        index -= 1
    return captured


def apply_move(board: Board, player: int, pit: int) -> Move:
    """Play ``pit`` for ``player`` without checking the no-starving rule."""
    cells, last = sow(board, player, pit)
    captured = capture(cells, player, last)
    return Move(pit, tuple(cells), captured)


def has_seeds(board: Board, player: int) -> bool:
    """Whether ``player`` has at least one seed in their row."""
    start = player * PITS_PER_SIDE
    return any(board[start : start + PITS_PER_SIDE])


def is_end(board: Board, player: int) -> bool:
    """Whether the game is over when it is ``player``'s turn."""
    pit_index(player, 0)  # validates the player
    return not has_seeds(board, player)


def legal_moves(board: Board, player: int) -> list[Move]:
    """All legal moves of ``player``, ordered by pit.

    A move is legal if its pit is not empty and it leaves the opponent at
    least one seed. If no move feeds the opponent, every non-empty pit is
    allowed and the game will end on the next turn.
    """
    start = pit_index(player, 0)
    moves = [
        _play(board, player, start + pit)
        for pit in range(PITS_PER_SIDE)
        if board[start + pit]
    ]
    feeding = [move for move in moves if has_seeds(move.board, 1 - player)]
    return feeding or moves


def play_legal(board: Board, player: int, pit: int) -> Move:
    """Play ``pit`` if it is a legal move, else raise :class:`IllegalMoveError`."""
    try:
        index = pit_index(player, pit)
    except BoardError as error:
        raise IllegalMoveError(str(error)) from None
    if board[index] == 0:
        raise IllegalMoveError(f"pit {pit} is empty")
    for move in legal_moves(board, player):
        if move.pit == pit:
            return move
    raise IllegalMoveError(f"pit {pit} would leave the opponent without seeds")


def _sow(board: Board, start: int) -> tuple[list[int], int]:
    """Sow the non-empty pit at index ``start`` (no validation)."""
    cells = list(board)
    seeds = cells[start]
    cells[start] = 0
    laps, rest = divmod(seeds, PITS)
    if laps:
        cells = [count + laps for count in cells]
    for step in range(1, rest + 1):
        cells[(start + step) % PITS] += 1
    return cells, (start + seeds) % PITS


def _play(board: Board, player: int, start: int) -> Move:
    """Sow and capture from index ``start`` (no validation)."""
    cells, last = _sow(board, start)
    captured = capture(cells, player, last)
    return Move(start % PITS_PER_SIDE, tuple(cells), captured)
