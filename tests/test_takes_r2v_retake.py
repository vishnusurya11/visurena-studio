"""F1 (ep10 synthesis): one batched retake round per master, with a written reason.

Episode 10 ordered ten renders in four waves; nine were reviewer-driven, three
waves were one or two takes, and 30.8 min of GPU never reached the picture. The
argument handling is pure, so it is tested without a book, a GPU or a plan.
"""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "takes_r2v_retake", Path(__file__).resolve().parents[1] / "scripts" / "episode" / "takes_r2v.py")
tr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tr)


def test_the_retake_list_is_read_off_the_command_line():
    assert tr.retake_list(["takes_r2v.py", "book", "10", "--retake=3,4,15", "--approved"]) == [3, 4, 15]
    assert tr.retake_list(["takes_r2v.py", "book", "10"]) == []


def test_the_why_is_read_off_the_command_line_spaces_and_all():
    argv = ["takes_r2v.py", "book", "10", "--retake=15", "--why=T15 coherence 0.45 HARD"]
    assert tr.retake_why(argv) == "T15 coherence 0.45 HARD"
    assert tr.retake_why(["takes_r2v.py", "book", "10"]) == ""


def test_a_retake_without_a_why_is_refused():
    said = tr.retake_refusal([3, 4], why="", last=False)
    assert said and "--why=" in said


def test_a_round_of_one_take_is_refused_unless_declared_the_last():
    said = tr.retake_refusal([15], why="coherence 0.45 HARD", last=False)
    assert said and "--last" in said
    assert tr.retake_refusal([15], why="coherence 0.45 HARD", last=True) is None


def test_a_batched_round_with_a_why_passes():
    assert tr.retake_refusal([3, 4, 5, 15], why="six motions, 851d52a", last=False) is None


def test_no_retake_needs_no_why():
    assert tr.retake_refusal([], why="", last=False) is None


def test_the_why_lands_on_each_retaken_card():
    c = {"index": 15, "seed": 91000}
    tr.mark_retake(c, tries=2, why="coherence 0.45 HARD")
    assert c["retake_why"] == "coherence 0.45 HARD"
    assert c["tries"] == 2 and c["seed"] == 91000 + 101 * 2
