import pytest

from awale.board import (
    PITS,
    TOTAL_SEEDS,
    BoardError,
    check_player,
    from_rows,
    initial_board,
    label,
    make_board,
    parse_board,
    parse_pit,
    pit_index,
    render,
    side,
    to_rows,
)


def test_initial_board_has_four_seeds_everywhere() -> None:
    board = initial_board()
    assert board == (4,) * PITS
    assert sum(board) == TOTAL_SEEDS == 48


def test_make_board_accepts_any_sequence() -> None:
    assert make_board([0] * 11 + [7]) == (0,) * 11 + (7,)


@pytest.mark.parametrize(
    "cells",
    [[4] * 11, [4] * 13, [], [4] * 11 + [-1], [4] * 11 + [1.5], [4] * 11 + ["4"]],
)
def test_make_board_rejects_bad_cells(cells: list[object]) -> None:
    with pytest.raises(BoardError):
        make_board(cells)  # type: ignore[arg-type]


def test_rows_round_trip() -> None:
    rows = [[1, 2, 3, 4, 5, 6], [7, 8, 9, 10, 11, 12]]
    board = from_rows(rows)
    assert board == tuple(range(1, 13))
    assert to_rows(board) == rows
    assert to_rows(board) is not to_rows(board)


@pytest.mark.parametrize(
    "rows", [[[0] * 6], [[0] * 6, [0] * 5], [[0] * 6, [0] * 6, [0] * 6]]
)
def test_from_rows_rejects_bad_shapes(rows: list[list[int]]) -> None:
    with pytest.raises(BoardError):
        from_rows(rows)


@pytest.mark.parametrize("player", [-1, 2, 1.0, "0"])
def test_check_player_rejects_unknown_players(player: object) -> None:
    with pytest.raises(BoardError):
        check_player(player)  # type: ignore[arg-type]


def test_pit_index_follows_sowing_order() -> None:
    assert pit_index(0, 0) == 0
    assert pit_index(0, 5) == 5
    assert pit_index(1, 0) == 6
    assert pit_index(1, 5) == 11


@pytest.mark.parametrize(("player", "pit"), [(0, -1), (0, 6), (1, 6), (2, 0)])
def test_pit_index_rejects_out_of_range(player: int, pit: int) -> None:
    with pytest.raises(BoardError):
        pit_index(player, pit)


def test_side_and_labels() -> None:
    board = tuple(range(12))
    assert side(board, 0) == (0, 1, 2, 3, 4, 5)
    assert side(board, 1) == (6, 7, 8, 9, 10, 11)
    assert [label(0, pit) for pit in range(6)] == list("abcdef")
    assert [label(1, pit) for pit in range(6)] == list("ghijkl")


@pytest.mark.parametrize(
    ("text", "player", "pit"),
    [("a", 0, 0), ("F", 0, 5), (" d ", 0, 3), ("g", 1, 0), ("l", 1, 5), ("3", 1, 2)],
)
def test_parse_pit(text: str, player: int, pit: int) -> None:
    assert parse_pit(text, player) == pit


@pytest.mark.parametrize(
    ("text", "player"), [("g", 0), ("a", 1), ("0", 0), ("7", 1), ("", 0), ("ab", 0)]
)
def test_parse_pit_rejects_other_side_and_garbage(text: str, player: int) -> None:
    with pytest.raises(BoardError, match="choose a pit"):
        parse_pit(text, player)


@pytest.mark.parametrize(
    "text",
    [
        "1 7 2 7 2 0 / 0 3 4 2 2 5",
        "1,7,2,7,2,0,0,3,4,2,2,5",
        "[[1,7,2,7,2,0],[0,3,4,2,2,5]]",
    ],
)
def test_parse_board_accepts_several_layouts(text: str) -> None:
    assert parse_board(text) == (1, 7, 2, 7, 2, 0, 0, 3, 4, 2, 2, 5)


@pytest.mark.parametrize("text", ["1 2 3", "4 " * 13, "4 " * 11 + "-4"])
def test_parse_board_rejects_bad_input(text: str) -> None:
    with pytest.raises(BoardError):
        parse_board(text)


def test_render_puts_player_two_on_top_in_reverse_order() -> None:
    lines = render(tuple(range(12))).splitlines()
    assert lines[0].split()[:6] == list("lkjihg")
    assert [int(x) for x in lines[2].strip("|").split("|")] == [11, 10, 9, 8, 7, 6]
    assert [int(x) for x in lines[4].strip("|").split("|")] == [0, 1, 2, 3, 4, 5]
    assert lines[-1].split()[:6] == list("abcdef")
