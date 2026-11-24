"""Full games: game state, players (agents) and matches between AIs."""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field

from awale.board import Board, check_player, initial_board
from awale.rules import has_seeds, legal_moves, play_legal
from awale.search import Searcher

MAX_PLIES = 300
"""Moves after which a game is stopped (seeds can circle forever)."""


@dataclass(frozen=True, slots=True)
class GameState:
    """Position of a game in progress."""

    board: Board = field(default_factory=initial_board)
    player: int = 0
    """Player to move: 0 for player 1, 1 for player 2."""
    captured: tuple[int, int] = (0, 0)
    """Seeds captured so far by each player."""
    ply: int = 0
    """Number of moves already played."""

    @property
    def over(self) -> bool:
        """Whether the player to move has no seed left."""
        return not has_seeds(self.board, self.player)

    @property
    def leader(self) -> int | None:
        """Player with the most captured seeds, or ``None`` if they are level."""
        first, second = self.captured
        if first == second:
            return None
        return 0 if first > second else 1


def play(state: GameState, pit: int) -> GameState:
    """Return the state after ``state.player`` plays ``pit`` (must be legal)."""
    move = play_legal(state.board, state.player, pit)
    captured = list(state.captured)
    captured[state.player] += move.captured
    return GameState(
        move.board, 1 - state.player, (captured[0], captured[1]), state.ply + 1
    )


Agent = Callable[[GameState], int]
"""A player: receives the state and returns the pit to play."""


def minimax_agent(depth: int) -> Agent:
    """AI that plays the alpha-beta MinMax move of the given depth."""
    searcher = Searcher()

    def choose(state: GameState) -> int:
        return searcher.search(state.board, state.player, depth).move

    return choose


def random_agent(seed: int | None = None) -> Agent:
    """Player that picks a legal move at random."""
    rng = random.Random(seed)

    def choose(state: GameState) -> int:
        return rng.choice(legal_moves(state.board, state.player)).pit

    return choose


@dataclass(frozen=True, slots=True)
class GameRecord:
    """Moves and final state of a finished or stopped game."""

    moves: tuple[int, ...]
    final: GameState
    finished: bool
    """False if the game was stopped after ``max_plies`` moves."""


def play_game(
    player_one: Agent,
    player_two: Agent,
    start: GameState | None = None,
    max_plies: int = MAX_PLIES,
) -> GameRecord:
    """Let two agents play from ``start`` until the end or ``max_plies`` moves."""
    state = start or GameState()
    agents = (player_one, player_two)
    moves: list[int] = []
    while not state.over and state.ply < max_plies:
        pit = agents[state.player](state)
        state = play(state, pit)
        moves.append(pit)
    return GameRecord(tuple(moves), state, state.over)


def random_opening(rng: random.Random, plies: int) -> GameState:
    """Start a game with ``plies`` random legal moves, to vary the games."""
    state = GameState()
    for _ in range(plies):
        if state.over:
            break
        state = play(state, rng.choice(legal_moves(state.board, state.player)).pit)
    return state


@dataclass(slots=True)
class MatchResult:
    """Score of a match between agents A and B."""

    games: int = 0
    wins: list[int] = field(default_factory=lambda: [0, 0])
    """Games won by A and by B."""
    draws: int = 0
    seeds: list[int] = field(default_factory=lambda: [0, 0])
    """Seeds captured in total by A and by B."""
    stopped: int = 0
    """Games stopped by the move limit."""

    def add(self, record: GameRecord, a_player: int) -> None:
        """Count one game in which agent A played as ``a_player``."""
        check_player(a_player)
        self.games += 1
        self.stopped += not record.finished
        for agent, player in ((0, a_player), (1, 1 - a_player)):
            self.seeds[agent] += record.final.captured[player]
        leader = record.final.leader
        if leader is None:
            self.draws += 1
        else:
            self.wins[0 if leader == a_player else 1] += 1


def play_match(
    agent_a: Agent,
    agent_b: Agent,
    openings: int,
    opening_plies: int = 2,
    seed: int = 0,
    max_plies: int = MAX_PLIES,
) -> MatchResult:
    """Play each random opening twice, A and B swapping sides."""
    if openings < 1:
        raise ValueError(f"at least one opening is needed, got {openings}")
    rng = random.Random(seed)
    result = MatchResult()
    for _ in range(openings):
        start = random_opening(rng, opening_plies)
        for a_player in (0, 1):
            pair = (agent_a, agent_b) if a_player == 0 else (agent_b, agent_a)
            record = play_game(*pair, start=start, max_plies=max_plies)
            result.add(record, a_player)
    return result
