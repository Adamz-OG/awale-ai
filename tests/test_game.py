import random

import pytest

from awale.board import TOTAL_SEEDS, initial_board
from awale.game import (
    GameRecord,
    GameState,
    MatchResult,
    minimax_agent,
    play,
    play_game,
    play_match,
    random_agent,
    random_opening,
)
from awale.rules import IllegalMoveError, legal_moves


def test_new_game() -> None:
    state = GameState()
    assert state.board == initial_board()
    assert (state.player, state.captured, state.ply) == (0, (0, 0), 0)
    assert not state.over
    assert state.leader is None


def test_play_updates_player_captures_and_ply() -> None:
    board = (0, 0, 0, 0, 0, 3, 2, 1, 1, 0, 0, 4)
    state = play(GameState(board, 0, (5, 1), 7), 5)
    assert state.board == (0,) * 11 + (4,)
    assert (state.player, state.captured, state.ply) == (1, (12, 1), 8)
    assert state.leader == 0


def test_play_refuses_illegal_moves() -> None:
    with pytest.raises(IllegalMoveError):
        play(GameState((0,) * 6 + (4,) * 6, 1), 6)
    with pytest.raises(IllegalMoveError):
        play(GameState((1, 0, 0, 0, 1, 1) + (0,) * 6), 4)


def test_leader_and_end() -> None:
    finished = GameState((0,) * 6 + (1,) * 6, 0, (10, 20))
    assert finished.over
    assert finished.leader == 1


def test_random_games_keep_every_seed_and_replay_exactly() -> None:
    for seed in range(20):
        record = play_game(random_agent(seed), random_agent(seed + 100))
        state = GameState()
        for pit in record.moves:
            assert pit in [m.pit for m in legal_moves(state.board, state.player)]
            state = play(state, pit)
            assert sum(state.board) + sum(state.captured) == TOTAL_SEEDS
        assert state == record.final
        assert record.finished == state.over


def test_games_stop_at_the_move_limit() -> None:
    record = play_game(random_agent(1), random_agent(2), max_plies=10)
    assert record == GameRecord(record.moves, record.final, False)
    assert len(record.moves) == record.final.ply == 10


def test_minimax_agent_plays_the_search_move() -> None:
    agent = minimax_agent(3)
    board = (1, 7, 2, 7, 2, 0, 0, 3, 4, 2, 2, 5)
    assert agent(GameState(board)) == 3


def test_random_opening_is_reproducible_and_legal() -> None:
    first = random_opening(random.Random(5), 4)
    assert first == random_opening(random.Random(5), 4)
    assert first.ply == 4
    long = random_opening(random.Random(5), 1000)
    assert long.over and long.ply < 1000


def test_match_counts_every_game() -> None:
    result = play_match(minimax_agent(1), random_agent(3), openings=3, seed=4)
    assert result.games == 6
    assert sum(result.wins) + result.draws == 6
    assert result.stopped == 0
    assert 0 < sum(result.seeds) <= 6 * TOTAL_SEEDS


def test_deeper_search_wins_more() -> None:
    result = play_match(minimax_agent(4), minimax_agent(1), openings=4, seed=1)
    assert result.wins[0] > result.wins[1]
    assert result.seeds[0] > result.seeds[1]


def test_the_search_beats_random_play() -> None:
    result = play_match(minimax_agent(2), random_agent(9), openings=5, seed=2)
    assert result.wins[0] >= 9


def test_match_result_needs_a_valid_side_and_openings() -> None:
    record = play_game(random_agent(1), random_agent(2), max_plies=4)
    result = MatchResult()
    result.add(record, 1)
    assert (result.games, result.stopped) == (1, 1)
    with pytest.raises(ValueError):
        result.add(record, 2)
    with pytest.raises(ValueError, match="opening"):
        play_match(random_agent(1), random_agent(2), openings=0)
