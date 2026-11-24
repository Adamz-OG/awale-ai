import pytest

from awale.compat import enum, is_end, play, suggest
from awale.rules import IllegalMoveError


def test_play_updates_the_rows_in_place() -> None:
    board = [[0, 0, 0, 0, 0, 3], [2, 1, 1, 0, 0, 4]]
    rows = board[0], board[1]
    assert play(board, 0, 5) == 7
    assert board == [[0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 4]]
    assert (board[0], board[1]) == rows  # same list objects


def test_play_on_an_empty_cell_is_an_error() -> None:
    board = [[0, 1, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0]]
    with pytest.raises(IllegalMoveError):
        play(board, 0, 0)
    assert board == [[0, 1, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0]]


def test_is_end() -> None:
    assert is_end([[0] * 6, [3] * 6], 0)
    assert not is_end([[0] * 6, [3] * 6], 1)


def test_enum_returns_lists_and_player_one_scores() -> None:
    board = [[1, 1, 0, 0, 1, 2], [1, 1, 0, 0, 0, 2]]
    assert enum(board, 0, 1) == [([0], 0), ([1], 0), ([4], 0), ([5], 4)]
    assert enum(board, 1, 1) == [([0], 0), ([1], 0), ([5], -4)]
    assert all(isinstance(moves, list) for moves, _ in enum(board, 0, 3))
    assert board == [[1, 1, 0, 0, 1, 2], [1, 1, 0, 0, 0, 2]]


def test_suggest_prefers_the_capture() -> None:
    board = [[0, 0, 0, 0, 0, 3], [2, 1, 1, 0, 0, 4]]
    assert suggest(board, 0, 1) == 5
    assert board == [[0, 0, 0, 0, 0, 3], [2, 1, 1, 0, 0, 4]]
