import pytest

from awale.board import PITS, Board, BoardError, initial_board
from awale.rules import (
    IllegalMoveError,
    apply_move,
    capture,
    has_seeds,
    is_end,
    legal_moves,
    play_legal,
    sow,
)
from helpers import mirror, random_positions

POSITIONS = random_positions(400, seed=11)


def board_with(**pits: int) -> Board:
    """Empty board with some pits filled, by letter: ``board_with(a=3, g=1)``."""
    cells = [0] * PITS
    for letter, seeds in pits.items():
        cells["abcdefghijkl".index(letter)] = seeds
    return tuple(cells)


def naive_sow(board: Board, start: int) -> tuple[list[int], int]:
    """Reference sowing, one seed at a time, written independently."""
    cells = list(board)
    seeds, cells[start], index = cells[start], 0, start
    while seeds:
        index = (index + 1) % PITS
        cells[index] += 1
        seeds -= 1
    return cells, index


# ---------------------------------------------------------------- sowing


def test_sow_from_the_start_position() -> None:
    cells, last = sow(initial_board(), 0, 0)
    assert cells == [0, 5, 5, 5, 5, 4] + [4] * 6
    assert last == 4


def test_sow_goes_from_player_two_back_to_player_one() -> None:
    cells, last = sow(initial_board(), 1, 5)
    assert cells == [5, 5, 5, 5, 4, 4] + [4, 4, 4, 4, 4, 0]
    assert last == 3


def test_twelve_seeds_make_a_full_lap_and_refill_the_pit() -> None:
    cells, last = sow(board_with(c=12), 0, 2)
    assert cells == [1] * PITS
    assert last == 2


def test_more_than_twelve_seeds() -> None:
    cells, last = sow(board_with(k=16), 1, 4)
    assert cells == [2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2]
    assert last == 2


def test_sow_rejects_empty_and_unknown_pits() -> None:
    with pytest.raises(IllegalMoveError, match="empty"):
        sow(board_with(a=1), 0, 1)
    with pytest.raises(BoardError):
        sow(initial_board(), 0, 6)
    with pytest.raises(BoardError):
        sow(initial_board(), 2, 0)


def test_sow_matches_a_one_seed_at_a_time_reference() -> None:
    for board, _ in POSITIONS:
        for index in range(PITS):
            if board[index]:
                assert sow(board, index // 6, index % 6) == naive_sow(board, index)


# -------------------------------------------------------------- captures


def test_capture_chain_of_two_and_three() -> None:
    move = apply_move(board_with(f=3, g=2, h=1, i=1), 0, 5)
    assert move.captured == 3 + 2 + 2
    assert move.board == board_with()


def test_capture_chain_stops_at_a_pit_of_four() -> None:
    move = apply_move(board_with(f=3, g=3, h=1, i=1), 0, 5)
    assert move.captured == 4
    assert move.board == board_with(g=4)


def test_capture_never_enters_the_players_own_row() -> None:
    cells = list(board_with(e=2, f=3, g=2))
    assert capture(cells, 0, 6) == 2
    assert cells == list(board_with(e=2, f=3))


def test_no_capture_in_own_row_or_with_one_or_four_seeds() -> None:
    assert apply_move(board_with(a=2, c=1), 0, 0).captured == 0
    assert apply_move(board_with(f=1, h=1), 0, 5).captured == 0
    assert apply_move(board_with(f=1, g=3), 0, 5).captured == 0


def test_player_two_captures_in_player_one_row() -> None:
    move = apply_move(board_with(k=16), 1, 4)
    assert move.captured == 6
    assert move.board == (0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 2)


def test_seeds_are_conserved_and_captures_are_two_or_more() -> None:
    for board, player in POSITIONS:
        for move in legal_moves(board, player):
            assert sum(move.board) + move.captured == sum(board)
            assert move.captured == 0 or move.captured >= 2


def test_captured_pits_form_a_run_in_the_opponent_row() -> None:
    for board, player in POSITIONS:
        for index in range(player * 6, player * 6 + 6):
            if not board[index]:
                continue
            sown, last = sow(board, player, index % 6)
            after = list(sown)
            capture(after, player, last)
            emptied = [i for i in range(PITS) if after[i] != sown[i]]
            assert all(sown[i] in (2, 3) and after[i] == 0 for i in emptied)
            if emptied:
                assert emptied == list(range(emptied[0], last + 1))
                assert emptied[0] // 6 == 1 - player


# ------------------------------------------------------------ legal moves


def test_empty_pits_are_not_moves() -> None:
    assert [move.pit for move in legal_moves(board_with(b=1, e=2, g=3), 0)] == [1, 4]


def test_a_move_that_starves_the_opponent_is_forbidden() -> None:
    assert [move.pit for move in legal_moves(board_with(e=1, f=1), 0)] == [5]


def test_capturing_the_last_seeds_counts_as_starving() -> None:
    assert [move.pit for move in legal_moves(board_with(a=1, f=1, g=1), 0)] == [0]


def test_if_every_move_starves_they_are_all_allowed() -> None:
    assert [move.pit for move in legal_moves(board_with(b=1, d=1), 0)] == [1, 3]


def test_no_move_without_seeds() -> None:
    assert legal_moves(board_with(g=5), 0) == []


def test_legal_moves_validates_the_player() -> None:
    with pytest.raises(BoardError):
        legal_moves(initial_board(), 2)


def test_feeding_moves_are_preferred_whenever_possible() -> None:
    for board, player in POSITIONS:
        moves = legal_moves(board, player)
        non_empty = [pit for pit in range(6) if board[player * 6 + pit]]
        feeding = [m for m in moves if has_seeds(m.board, 1 - player)]
        assert [m.pit for m in moves] == sorted(m.pit for m in moves)
        assert set(m.pit for m in moves) <= set(non_empty)
        assert feeding == moves or not feeding
        if not feeding:
            assert [m.pit for m in moves] == non_empty


def test_rules_are_symmetric_between_players() -> None:
    for board, player in POSITIONS:
        moves = legal_moves(board, player)
        mirrored = legal_moves(mirror(board), 1 - player)
        assert [(m.pit, m.captured) for m in moves] == [
            (m.pit, m.captured) for m in mirrored
        ]
        assert [mirror(m.board) for m in moves] == [m.board for m in mirrored]


# ------------------------------------------------------------ end of game


def test_is_end_only_looks_at_the_player_to_move() -> None:
    board = board_with(b=1, c=2, e=4)
    assert not is_end(board, 0)
    assert is_end(board, 1)
    assert not is_end(initial_board(), 1)


def test_is_end_validates_the_player() -> None:
    with pytest.raises(BoardError):
        is_end(initial_board(), -1)


def test_play_legal_explains_why_a_move_is_refused() -> None:
    assert play_legal(board_with(e=1, f=1), 0, 5).board == board_with(e=1, g=1)
    with pytest.raises(IllegalMoveError, match="empty"):
        play_legal(board_with(e=1, f=1), 0, 0)
    with pytest.raises(IllegalMoveError, match="without seeds"):
        play_legal(board_with(e=1, f=1), 0, 4)
    with pytest.raises(IllegalMoveError, match="pit must be"):
        play_legal(initial_board(), 0, 6)
