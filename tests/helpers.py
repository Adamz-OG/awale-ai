"""Shared helpers: reproducible random positions and board symmetry."""

from __future__ import annotations

import random

from awale.board import PITS, TOTAL_SEEDS, Board, initial_board
from awale.rules import legal_moves

Position = tuple[Board, int]


def played_position(rng: random.Random, plies: int) -> Position:
    """Position reached by ``plies`` random legal moves from the start."""
    board, player = initial_board(), 0
    for _ in range(plies):
        moves = legal_moves(board, player)
        if not moves:
            break
        board, player = rng.choice(moves).board, 1 - player
    return board, player


def scattered_position(rng: random.Random) -> Position:
    """Any spread of at most 48 seeds, including big pits of 12 seeds or more."""
    seeds = rng.randint(1, TOTAL_SEEDS)
    cells = [0] * PITS
    weights = [rng.random() ** 3 for _ in range(PITS)]
    for index in rng.choices(range(PITS), weights=weights, k=seeds):
        cells[index] += 1
    return tuple(cells), rng.randint(0, 1)


def random_positions(count: int, seed: int) -> list[Position]:
    """Mix of realistic and arbitrary positions where a move is possible."""
    rng = random.Random(seed)
    positions: list[Position] = []
    while len(positions) < count:
        if rng.random() < 0.5:
            position = played_position(rng, rng.randint(0, 60))
        else:
            position = scattered_position(rng)
        if legal_moves(*position):
            positions.append(position)
    return positions


def mirror(board: Board) -> Board:
    """Swap the two rows: player 1's pits become player 2's and back."""
    return board[6:] + board[:6]
