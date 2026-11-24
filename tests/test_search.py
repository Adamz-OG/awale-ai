from collections import defaultdict

import pytest

from awale.board import Board, BoardError, from_rows, initial_board
from awale.rules import IllegalMoveError, legal_moves
from awale.search import Line, Searcher, enumerate_lines, suggest
from helpers import mirror, random_positions

POSITIONS = random_positions(150, seed=23)

# Worked example of the assignment (Figure 5): player 1 to move.
EXAMPLE = from_rows([[1, 7, 2, 7, 2, 0], [0, 3, 4, 2, 2, 5]])


def reference_score(board: Board, player: int, depth: int) -> int:
    """Classic MinMax on the score, written independently of the negamax code."""
    moves = legal_moves(board, player) if depth else []
    if not moves:
        return 0
    sign = 1 if player == 0 else -1
    scores = [
        sign * move.captured + reference_score(move.board, 1 - player, depth - 1)
        for move in moves
    ]
    return max(scores) if player == 0 else min(scores)


def reference_move(board: Board, player: int, depth: int) -> int:
    """Lowest pit among the moves with the best MinMax score."""
    sign = 1 if player == 0 else -1
    scores = {
        move.pit: sign * move.captured
        + reference_score(move.board, 1 - player, depth - 1)
        for move in legal_moves(board, player)
    }
    best = max(scores.values()) if player == 0 else min(scores.values())
    return min(pit for pit, score in scores.items() if score == best)


def score_from_lines(lines: list[Line], player: int) -> int:
    """MinMax computed on the tree rebuilt from the enumerated lines."""
    if len(lines) == 1 and not lines[0][0]:
        return lines[0][1]
    branches: dict[int, list[Line]] = defaultdict(list)
    for moves, score in lines:
        branches[moves[0]].append((moves[1:], score))
    values = [score_from_lines(branch, 1 - player) for branch in branches.values()]
    return max(values) if player == 0 else min(values)


# ------------------------------------------------------------ enumeration


def test_enumeration_of_the_assignment_example() -> None:
    lines = dict(enumerate_lines(EXAMPLE, 0, 4))
    assert len(lines) == 596
    assert lines[(3, 1, 5, 2)] == 5


def test_depth_zero_and_finished_games_give_one_empty_line() -> None:
    assert list(enumerate_lines(initial_board(), 0, 0)) == [((), 0)]
    finished = (0,) * 6 + (4,) * 6
    assert list(enumerate_lines(finished, 0, 3)) == [((), 0)]


def test_depth_one_lines_are_the_legal_moves() -> None:
    for board, player in POSITIONS[:40]:
        sign = 1 if player == 0 else -1
        expected = [((m.pit,), sign * m.captured) for m in legal_moves(board, player)]
        assert list(enumerate_lines(board, player, 1)) == expected


def test_every_line_is_legal_and_correctly_scored() -> None:
    for board, player in POSITIONS[:40]:
        for moves, score in enumerate_lines(board, player, 3):
            current, side, total = board, player, 0
            for pit in moves:
                move = next(m for m in legal_moves(current, side) if m.pit == pit)
                total += move.captured if side == 0 else -move.captured
                current, side = move.board, 1 - side
            assert total == score
            assert len(moves) == 3 or not legal_moves(current, side)


def test_enumeration_validates_its_arguments_immediately() -> None:
    with pytest.raises(ValueError, match="depth"):
        enumerate_lines(initial_board(), 0, -1)
    with pytest.raises(BoardError):
        enumerate_lines(initial_board(), 3, 2)


# ------------------------------------------------------------------ MinMax


def test_scores_of_the_assignment_example() -> None:
    scores = Searcher().evaluate_moves(EXAMPLE, 0, 4)
    assert scores == {0: 0, 1: -3, 2: -2, 3: 5, 4: 0}
    result = Searcher().search(EXAMPLE, 0, 4)
    assert (result.move, result.score, result.depth) == (3, 5, 4)


@pytest.mark.parametrize("depth", [1, 2, 3, 4])
def test_all_search_methods_match_a_reference_minmax(depth: int) -> None:
    methods = [
        Searcher(pruning=False),
        Searcher(pruning=True, ordering=False),
        Searcher(pruning=True, ordering=True),
    ]
    for board, player in POSITIONS:
        expected = (
            reference_move(board, player, depth),
            reference_score(board, player, depth),
        )
        for searcher in methods:
            result = searcher.search(board, player, depth)
            assert (result.move, result.score) == expected


def test_minmax_on_the_enumerated_tree_gives_the_same_score() -> None:
    for board, player in POSITIONS[:60]:
        lines = list(enumerate_lines(board, player, 3))
        assert (
            score_from_lines(lines, player) == Searcher().search(board, player, 3).score
        )


def test_best_line_is_not_the_minmax_score() -> None:
    """Taking the best line assumes the opponent helps: it overestimates."""
    gaps = 0
    for board, player in POSITIONS:
        sign = 1 if player == 0 else -1
        best_line = max(sign * score for _, score in enumerate_lines(board, player, 3))
        minmax = sign * Searcher().search(board, player, 3).score
        assert best_line >= minmax
        gaps += best_line > minmax
    assert gaps > len(POSITIONS) // 4


def test_evaluate_moves_agrees_with_search() -> None:
    for board, player in POSITIONS[:60]:
        scores = Searcher().evaluate_moves(board, player, 3)
        assert scores == Searcher(pruning=False).evaluate_moves(board, player, 3)
        result = Searcher().search(board, player, 3)
        best = max(scores.values()) if player == 0 else min(scores.values())
        assert result.score == best
        assert result.move == min(pit for pit, s in scores.items() if s == best)


def test_search_is_symmetric_between_players() -> None:
    for board, player in POSITIONS[:80]:
        result = Searcher().search(board, player, 4)
        mirrored = Searcher().search(mirror(board), 1 - player, 4)
        assert (mirrored.move, mirrored.score) == (result.move, -result.score)


def test_value_is_seen_from_the_player_to_move() -> None:
    searcher = Searcher()
    assert searcher.value(EXAMPLE, 0, 4) == 5
    assert searcher.value(EXAMPLE, 0, 0) == 0
    assert searcher.value((0,) * 6 + (4,) * 6, 0, 5) == 0
    for board, player in POSITIONS[:40]:
        sign = 1 if player == 0 else -1
        assert searcher.value(board, player, 3) == sign * reference_score(
            board, player, 3
        )


def test_scores_never_exceed_the_seeds_on_the_board() -> None:
    for board, player in POSITIONS:
        assert abs(Searcher().search(board, player, 4).score) <= sum(board)


# ------------------------------------------------------------ efficiency


def test_pruning_never_visits_more_positions() -> None:
    plain, pruned, unordered = (
        Searcher(pruning=False),
        Searcher(),
        Searcher(ordering=False),
    )
    total = {"pruned": 0, "unordered": 0}
    for board, player in POSITIONS:
        plain.search(board, player, 4)
        pruned.search(board, player, 4)
        unordered.search(board, player, 4)
        assert pruned.nodes <= plain.nodes
        assert unordered.nodes <= plain.nodes
        total["pruned"] += pruned.nodes
        total["unordered"] += unordered.nodes
    assert total["pruned"] < total["unordered"]


def test_node_count_of_plain_minmax_is_the_tree_size() -> None:
    searcher = Searcher(pruning=False)
    searcher.search(initial_board(), 0, 2)
    assert searcher.nodes == 1 + 6 + 36


def test_alpha_beta_cuts_most_of_the_tree_at_depth_six() -> None:
    plain, pruned = Searcher(pruning=False), Searcher()
    full = plain.search(initial_board(), 0, 6)
    cut = pruned.search(initial_board(), 0, 6)
    assert (full.move, full.score) == (cut.move, cut.score)
    assert (full.nodes, cut.nodes) == (plain.nodes, pruned.nodes)
    assert cut.nodes * 20 < full.nodes


# ---------------------------------------------------------------- errors


@pytest.mark.parametrize("depth", [0, -2])
def test_search_needs_a_positive_depth(depth: int) -> None:
    with pytest.raises(ValueError, match="depth"):
        Searcher().search(initial_board(), 0, depth)


def test_depth_must_be_an_integer() -> None:
    with pytest.raises(ValueError, match="depth"):
        Searcher().value(initial_board(), 0, 2.5)  # type: ignore[arg-type]


def test_search_rejects_unknown_players_and_finished_games() -> None:
    with pytest.raises(BoardError):
        Searcher().search(initial_board(), 2, 3)
    with pytest.raises(IllegalMoveError, match="game is over"):
        Searcher().search((0,) * 6 + (4,) * 6, 0, 3)


def test_suggest_returns_the_best_pit() -> None:
    assert suggest(EXAMPLE, 0, 4) == 3
    for board, player in POSITIONS[:30]:
        assert suggest(board, player, 3) == reference_move(board, player, 3)
