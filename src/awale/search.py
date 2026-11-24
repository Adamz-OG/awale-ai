"""Game tree search: enumeration of lines, MinMax and alpha-beta.

Scores follow the assignment: the *score* of a line of play is the number of
seeds captured by player 1 minus the number captured by player 2. Player 1
maximises it, player 2 minimises it.

Internally the search uses the *negamax* form of MinMax: the value of a
position is the best capture difference that the player to move can secure,
seen from that player's side. Because a score is a sum of captures, the
value of a move is what it captures minus the value of the position it
leaves to the opponent, so one function serves both players.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from awale.board import TOTAL_SEEDS, Board, check_player
from awale.rules import IllegalMoveError, Move, legal_moves

INFINITY = TOTAL_SEEDS + 1
"""Larger than any reachable score."""

Line = tuple[tuple[int, ...], int]
"""A sequence of pits played and its final score."""


@dataclass(frozen=True, slots=True)
class SearchResult:
    """Best move found by a search."""

    move: int
    """Pit to play, from 0 to 5 in the player's own row."""
    score: int
    """Expected score (player 1 minus player 2) if both sides play well."""
    depth: int
    """Number of plies searched."""
    nodes: int
    """Number of positions visited."""


def enumerate_lines(board: Board, player: int, depth: int) -> Iterator[Line]:
    """Iterate over every legal line of at most ``depth`` plies, with its score.

    This is the backtracking enumeration of the assignment: a line stops
    early when the player to move has no seed left. Lines come in pit order.
    """
    check_player(player)
    _check_depth(depth, minimum=0)
    return _lines(board, player, depth, 0, [])


def _lines(
    board: Board, player: int, depth: int, score: int, path: list[int]
) -> Iterator[Line]:
    moves = legal_moves(board, player) if depth else []
    if not moves:
        yield tuple(path), score
        return
    sign = 1 if player == 0 else -1
    for move in moves:
        path.append(move.pit)
        yield from _lines(
            move.board, 1 - player, depth - 1, score + sign * move.captured, path
        )
        path.pop()


class Searcher:
    """Depth-limited MinMax search, with or without alpha-beta pruning.

    ``pruning=False`` gives plain MinMax, which visits the whole tree.
    ``pruning=True`` cuts the branches that cannot change the result and,
    with ``ordering=True``, searches capturing moves first so that cuts
    happen sooner. All settings return the same best move and score.
    """

    def __init__(self, *, pruning: bool = True, ordering: bool = True) -> None:
        """Choose the search method."""
        self.pruning = pruning
        self.ordering = ordering
        self.nodes = 0

    def search(self, board: Board, player: int, depth: int) -> SearchResult:
        """Return the best move of ``player`` looking ``depth`` plies ahead.

        Ties go to the lowest pit. Raises :class:`IllegalMoveError` when the
        game is over.
        """
        moves = self._root_moves(board, player, depth)
        best_pit, best = moves[0].pit, -INFINITY
        for move in moves:
            value = self._child_value(move, player, depth, best, INFINITY)
            if value > best:
                best_pit, best = move.pit, value
        return SearchResult(best_pit, _score(best, player), depth, self.nodes)

    def evaluate_moves(self, board: Board, player: int, depth: int) -> dict[int, int]:
        """Exact score of every legal move, like the top row of a MinMax tree."""
        moves = self._root_moves(board, player, depth)
        return {
            move.pit: _score(
                self._child_value(move, player, depth, -INFINITY, INFINITY), player
            )
            for move in moves
        }

    def value(self, board: Board, player: int, depth: int) -> int:
        """Best capture difference for ``player`` (to move) over ``depth`` plies."""
        check_player(player)
        _check_depth(depth, minimum=0)
        self.nodes = 0
        return self._value(board, player, depth, -INFINITY, INFINITY)

    def _root_moves(self, board: Board, player: int, depth: int) -> list[Move]:
        check_player(player)
        _check_depth(depth, minimum=1)
        moves = legal_moves(board, player)
        if not moves:
            raise IllegalMoveError(f"player {player} has no seed: the game is over")
        self.nodes = 1
        return moves

    def _child_value(
        self, move: Move, player: int, depth: int, alpha: int, beta: int
    ) -> int:
        """Value of ``move`` for ``player``, searched in the window (alpha, beta)."""
        gain = move.captured
        reply = self._value(
            move.board, 1 - player, depth - 1, gain - beta, gain - alpha
        )
        return gain - reply

    def _value(
        self, board: Board, player: int, depth: int, alpha: int, beta: int
    ) -> int:
        if self.pruning:
            return self._alphabeta(board, player, depth, alpha, beta)
        return self._minimax(board, player, depth)

    def _minimax(self, board: Board, player: int, depth: int) -> int:
        self.nodes += 1
        moves = legal_moves(board, player) if depth else []
        if not moves:
            return 0
        return max(
            move.captured - self._minimax(move.board, 1 - player, depth - 1)
            for move in moves
        )

    def _alphabeta(
        self, board: Board, player: int, depth: int, alpha: int, beta: int
    ) -> int:
        """Negamax with alpha-beta pruning (fail-soft).

        The result is exact when it lies strictly between ``alpha`` and
        ``beta``; otherwise it is a bound on the same side as the window.
        """
        self.nodes += 1
        moves = legal_moves(board, player) if depth else []
        if not moves:
            return 0
        if self.ordering:
            moves.sort(key=_captures_first)
        best = -INFINITY
        for move in moves:
            gain = move.captured
            value = gain - self._alphabeta(
                move.board, 1 - player, depth - 1, gain - beta, gain - alpha
            )
            if value > best:
                best = value
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
        return best


def suggest(board: Board, player: int, depth: int) -> int:
    """Best pit for ``player`` with alpha-beta search of ``depth`` plies."""
    return Searcher().search(board, player, depth).move


def _captures_first(move: Move) -> int:
    return -move.captured


def _score(value: int, player: int) -> int:
    """Convert a value seen by ``player`` into a player 1 minus player 2 score."""
    return value if player == 0 else -value


def _check_depth(depth: int, minimum: int) -> None:
    if not isinstance(depth, int) or depth < minimum:
        raise ValueError(f"depth must be an integer >= {minimum}, got {depth!r}")
