"""Benchmark: search cost by depth and playing strength by depth.

Usage::

    python benchmarks/benchmark.py            # tables in the terminal
    python benchmarks/benchmark.py --json out.json

The positions and the match openings come from fixed seeds, so the results
can be reproduced.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from awale.board import Board, initial_board  # noqa: E402
from awale.game import minimax_agent, play_match  # noqa: E402
from awale.rules import legal_moves  # noqa: E402
from awale.search import Searcher  # noqa: E402

METHODS = {
    "minmax": {"pruning": False},
    "alphabeta_unordered": {"pruning": True, "ordering": False},
    "alphabeta": {"pruning": True, "ordering": True},
}
MAX_MINMAX_DEPTH = 7
MAX_UNORDERED_DEPTH = 10


def positions(count: int, seed: int = 2026) -> list[tuple[Board, int]]:
    """Start position plus positions reached by 10 to 40 random moves."""
    rng = random.Random(seed)
    found = [(initial_board(), 0)]
    while len(found) < count:
        board, player = initial_board(), 0
        for _ in range(rng.randint(10, 40)):
            moves = legal_moves(board, player)
            if not moves:
                break
            board, player = rng.choice(moves).board, 1 - player
        if legal_moves(board, player):
            found.append((board, player))
    return found


def measure_search(depths: range, count: int) -> list[dict[str, float | int]]:
    """Average nodes and time per move for every method and depth."""
    sample = positions(count)
    rows: list[dict[str, float | int]] = []
    for depth in depths:
        row: dict[str, float | int] = {"depth": depth}
        reference = None
        for name, options in METHODS.items():
            if _too_slow(name, depth):
                continue
            searcher = Searcher(**options)
            nodes, start, results = 0, time.perf_counter(), []
            for board, player in sample:
                result = searcher.search(board, player, depth)
                nodes += result.nodes
                results.append((result.move, result.score))
            reference = reference or results
            assert results == reference, f"{name} disagrees at depth {depth}"
            row[f"{name}_nodes"] = nodes / len(sample)
            row[f"{name}_ms"] = 1000 * (time.perf_counter() - start) / len(sample)
        rows.append(row)
        print(_format_search(row), flush=True)
    return rows


def _too_slow(name: str, depth: int) -> bool:
    if name == "minmax":
        return depth > MAX_MINMAX_DEPTH
    return name == "alphabeta_unordered" and depth > MAX_UNORDERED_DEPTH


def measure_strength(depths: list[int], openings: int) -> list[dict[str, float | int]]:
    """Each depth plays against depth 1 (greedy), from the same openings."""
    rows: list[dict[str, float | int]] = []
    greedy = minimax_agent(1)
    for depth in depths:
        start = time.perf_counter()
        result = play_match(minimax_agent(depth), greedy, openings=openings, seed=7)
        rows.append(
            {
                "depth": depth,
                "games": result.games,
                "wins": result.wins[0],
                "draws": result.draws,
                "losses": result.wins[1],
                "seeds_for": result.seeds[0] / result.games,
                "seeds_against": result.seeds[1] / result.games,
                "seconds": time.perf_counter() - start,
            }
        )
        print(_format_strength(rows[-1]), flush=True)
    return rows


def _format_search(row: dict[str, float | int]) -> str:
    parts = [f"depth {row['depth']:>2}"]
    for name in METHODS:
        if f"{name}_nodes" in row:
            parts.append(
                f"{name}: {row[f'{name}_nodes']:>10,.0f} nodes "
                f"{row[f'{name}_ms']:>9.2f} ms"
            )
    return " | ".join(parts)


def _format_strength(row: dict[str, float | int]) -> str:
    return (
        f"depth {row['depth']} vs 1: {row['wins']}-{row['draws']}-{row['losses']} "
        f"({row['seeds_for']:.1f} vs {row['seeds_against']:.1f} seeds) "
        f"in {row['seconds']:.0f} s"
    )


def main() -> None:
    """Parse arguments, run both benchmarks and print or save the results."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--positions", type=int, default=50, help="positions per depth")
    parser.add_argument("--max-depth", type=int, default=12, help="deepest search")
    parser.add_argument("--openings", type=int, default=20, help="openings per match")
    parser.add_argument("--json", type=Path, help="also save results as JSON")
    args = parser.parse_args()

    search = measure_search(range(1, args.max_depth + 1), args.positions)
    strength = measure_strength([2, 4, 6, 8], args.openings)
    if args.json:
        data = {"search": search, "strength": strength}
        args.json.write_text(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
