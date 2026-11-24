"""Command line interface: ``awale suggest | play | match``."""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Sequence

from awale.board import BoardError, initial_board, label, parse_board, parse_pit, render
from awale.game import GameState, minimax_agent, play, play_match
from awale.rules import IllegalMoveError
from awale.search import Searcher

DEFAULT_DEPTH = 8


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line tool and return the exit code."""
    args = _build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except (BoardError, IllegalMoveError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="awale", description="Awale game and MinMax AI with alpha-beta pruning."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    suggest = commands.add_parser("suggest", help="best move on a given board")
    suggest.add_argument(
        "board",
        nargs="?",
        help="12 seed counts, row a..f then row g..l (default: start position), "
        'e.g. "1 7 2 7 2 0 / 0 3 4 2 2 5"',
    )
    suggest.add_argument("-p", "--player", type=int, choices=(1, 2), default=1)
    _add_depth(suggest)
    suggest.add_argument(
        "--all", action="store_true", help="also print the score of every move"
    )
    suggest.set_defaults(handler=_run_suggest)

    game = commands.add_parser("play", help="play against the AI in the terminal")
    _add_depth(game)
    game.add_argument(
        "--human", type=int, choices=(1, 2), default=1, help="your side (1 starts)"
    )
    game.set_defaults(handler=_run_play)

    match = commands.add_parser("match", help="AI against AI at two depths")
    match.add_argument("depth_a", type=int, help="depth of AI A")
    match.add_argument("depth_b", type=int, help="depth of AI B")
    match.add_argument(
        "--openings", type=int, default=10, help="random openings, each played twice"
    )
    match.add_argument("--seed", type=int, default=0, help="seed of the openings")
    match.set_defaults(handler=_run_match)
    return parser


def _add_depth(command: argparse.ArgumentParser) -> None:
    command.add_argument(
        "-d",
        "--depth",
        type=int,
        default=DEFAULT_DEPTH,
        help=f"plies searched (default: {DEFAULT_DEPTH})",
    )


def _run_suggest(args: argparse.Namespace) -> int:
    board = parse_board(args.board) if args.board else initial_board()
    player = args.player - 1
    searcher = Searcher()
    start = time.perf_counter()
    result = searcher.search(board, player, args.depth)
    elapsed = time.perf_counter() - start
    print(render(board))
    print()
    print(f"player {args.player} to move, depth {args.depth}")
    print(f"best move : {label(player, result.move)}")
    print(f"score     : {result.score:+d} (seeds of player 1 minus player 2)")
    print(f"nodes     : {result.nodes} in {elapsed:.3f} s")
    if args.all:
        scores = searcher.evaluate_moves(board, player, args.depth)
        line = "  ".join(f"{label(player, pit)}: {s:+d}" for pit, s in scores.items())
        print(f"all moves : {line}")
    return 0


def _run_play(args: argparse.Namespace) -> int:
    human = args.human - 1
    ai = minimax_agent(args.depth)
    state = GameState()
    while not state.over:
        _show(state)
        if state.player == human:
            pit = _ask_move(state)
            if pit is None:
                print("game abandoned")
                return 0
        else:
            pit = ai(state)
            print(f"AI plays {label(state.player, pit)}")
        state = play(state, pit)
    _show(state)
    print(_outcome(state, human))
    return 0


def _ask_move(state: GameState) -> int | None:
    """Read a legal move from the keyboard; ``None`` if the player quits."""
    while True:
        try:
            text = input("your move (letter or 1-6, q to quit): ")
        except EOFError:
            return None
        if text.strip().lower() in {"q", "quit"}:
            return None
        try:
            pit = parse_pit(text, state.player)
            play(state, pit)
        except (BoardError, IllegalMoveError) as error:
            print(f"  {error}")
            continue
        return pit


def _show(state: GameState) -> None:
    print()
    print(render(state.board))
    print(f"captured: player 1 = {state.captured[0]}, player 2 = {state.captured[1]}")


def _outcome(state: GameState, human: int) -> str:
    leader = state.leader
    if leader is None:
        return "draw"
    return "you win" if leader == human else "the AI wins"


def _run_match(args: argparse.Namespace) -> int:
    result = play_match(
        minimax_agent(args.depth_a),
        minimax_agent(args.depth_b),
        openings=args.openings,
        seed=args.seed,
    )
    games = result.games
    print(f"depth {args.depth_a} (A) against depth {args.depth_b} (B): {games} games")
    print(f"A wins  : {result.wins[0]}")
    print(f"B wins  : {result.wins[1]}")
    print(f"draws   : {result.draws}")
    print(
        f"seeds   : {result.seeds[0] / games:.1f} (A) "
        f"vs {result.seeds[1] / games:.1f} (B) per game"
    )
    return 0
