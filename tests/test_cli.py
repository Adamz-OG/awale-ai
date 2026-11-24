import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from awale import cli
from awale.cli import main
from awale.game import GameState
from awale.rules import legal_moves

SRC = Path(__file__).resolve().parents[1] / "src"


def feed(monkeypatch: pytest.MonkeyPatch, answers: list[str]) -> None:
    """Answer ``input()`` calls with ``answers``, then end of file."""
    replies: Iterator[str] = iter(answers)

    def fake_input(prompt: str = "") -> str:
        try:
            return next(replies)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr("builtins.input", fake_input)


def test_suggest_on_the_start_position(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["suggest", "--depth", "4"]) == 0
    out = capsys.readouterr().out
    assert "player 1 to move, depth 4" in out
    assert "best move : a" in out
    assert "score     : +0" in out


def test_suggest_with_a_board_and_all_scores(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["suggest", "1 7 2 7 2 0 / 0 3 4 2 2 5", "-d", "4", "--all"]) == 0
    out = capsys.readouterr().out
    assert "best move : d" in out
    assert "score     : +5" in out
    assert "all moves : a: +0  b: -3  c: -2  d: +5  e: +0" in out


def test_suggest_for_player_two(capsys: pytest.CaptureFixture[str]) -> None:
    assert (
        main(["suggest", "0 0 0 1 1 0  2 0 0 0 0 0", "--player", "2", "-d", "1"]) == 0
    )
    out = capsys.readouterr().out
    assert "best move : g" in out


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["suggest", "1 2 3"], "12 pits"),
        (["suggest", "0 0 0 0 0 0 4 4 4 4 4 4"], "game is over"),
        (["suggest", "--depth", "0"], "depth"),
        (["match", "1", "1", "--openings", "0"], "opening"),
    ],
)
def test_errors_are_reported_without_traceback(
    argv: list[str], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(argv) == 1
    assert message in capsys.readouterr().err


def test_match(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["match", "3", "1", "--openings", "2", "--seed", "1"]) == 0
    out = capsys.readouterr().out
    assert "depth 3 (A) against depth 1 (B): 4 games" in out
    assert "A wins" in out and "per game" in out


def test_ask_move_retries_until_the_move_is_legal(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    feed(monkeypatch, ["z", "g", "e", "f"])
    state = GameState((0, 0, 0, 0, 1, 1) + (0,) * 6)
    assert cli._ask_move(state) == 5
    out = capsys.readouterr().out
    assert out.count("choose a pit") == 2
    assert "without seeds" in out


@pytest.mark.parametrize("answers", [["q"], ["QUIT"], []])
def test_ask_move_lets_the_player_quit(
    monkeypatch: pytest.MonkeyPatch, answers: list[str]
) -> None:
    feed(monkeypatch, answers)
    assert cli._ask_move(GameState()) is None


def test_play_can_be_abandoned(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    feed(monkeypatch, ["a", "q"])
    assert main(["play", "--depth", "2"]) == 0
    out = capsys.readouterr().out
    assert "AI plays" in out
    assert out.rstrip().endswith("game abandoned")


@pytest.mark.parametrize("human", ["1", "2"])
def test_a_full_game_against_the_ai(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], human: str
) -> None:
    def first_legal_move(state: GameState) -> int:
        return legal_moves(state.board, state.player)[0].pit

    monkeypatch.setattr(cli, "_ask_move", first_legal_move)
    assert main(["play", "--depth", "3", "--human", human]) == 0
    last = capsys.readouterr().out.rstrip().splitlines()[-1]
    assert last in {"you win", "the AI wins", "draw"}


def test_outcome_messages() -> None:
    board = (0,) * 12
    assert cli._outcome(GameState(board, 0, (20, 28)), human=1) == "you win"
    assert cli._outcome(GameState(board, 0, (20, 28)), human=0) == "the AI wins"
    assert cli._outcome(GameState(board, 0, (24, 24)), human=0) == "draw"


def test_module_entry_point() -> None:
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    result = subprocess.run(
        [sys.executable, "-m", "awale", "suggest", "-d", "2"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert "best move" in result.stdout
