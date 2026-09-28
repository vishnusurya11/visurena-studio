"""The book-level voice caster runs from the episode runner.

ep14 (2026-09-28), the first episode since the runner with new speakers: step
04 called cast_voices.py through ctx.run_script, which appends the episode
number, and argparse refused "unrecognized arguments: 14".
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("cast_voices_runner", ROOT / "scripts/cast/cast_voices.py")
cv = importlib.util.module_from_spec(_spec)
sys.modules["cast_voices_runner"] = cv
_spec.loader.exec_module(cv)


def test_the_episode_number_the_runner_appends_is_accepted():
    args = cv.parser().parse_args(["20260827135508_the-war-of-the-worlds", "14", "--only=narrators_brother"])
    assert args.codex_id.endswith("worlds") and args.only == "narrators_brother"


def test_the_book_alone_still_parses():
    assert cv.parser().parse_args(["book"]).codex_id == "book"
