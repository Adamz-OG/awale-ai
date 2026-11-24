"""Awale game engine and MinMax AI with alpha-beta pruning.

Basic use::

    >>> from awale import initial_board, suggest
    >>> suggest(initial_board(), player=0, depth=6)
    0
"""

from awale.board import Board, BoardError, from_rows, initial_board, render, to_rows
from awale.game import GameState, play_game, play_match
from awale.rules import IllegalMoveError, Move, is_end, legal_moves
from awale.search import Searcher, SearchResult, enumerate_lines, suggest

__all__ = [
    "Board",
    "BoardError",
    "GameState",
    "IllegalMoveError",
    "Move",
    "SearchResult",
    "Searcher",
    "enumerate_lines",
    "from_rows",
    "initial_board",
    "is_end",
    "legal_moves",
    "play_game",
    "play_match",
    "render",
    "suggest",
    "to_rows",
]
__version__ = "1.0.0"
