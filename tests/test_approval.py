"""No paid picture without the owner's word, for that picture.

Owner, 2026-09-11: a go given for six storyboard sheets was spent on a seventh
picture, the episode title, that nobody had approved.  The gate exists so the
mistake is impossible rather than merely regretted.
"""
import pytest

from studio import approval


@pytest.fixture(autouse=True)
def no_live_hold(tmp_path, monkeypatch):
    """A hold on the real repo is a real instruction to the real machine, and no
    test may either read it or be steered by it.  Every test here gets its own."""
    monkeypatch.setattr(approval, "HOLD", tmp_path / "RENDER_HOLD")


def test_a_paid_call_is_refused_without_approval():
    with pytest.raises(approval.NotApproved) as raised:
        approval.require("title", "the episode 1 title card", 0.20, approved=False)
    said = str(raised.value)
    assert "REFUSED" in said and "title: the episode 1 title card — $0.20" in said


def test_an_approved_call_goes_through():
    approval.require("title", "the episode 1 title card", 0.20, approved=True)


def test_an_unknown_kind_is_a_mistake_not_a_spend():
    with pytest.raises(ValueError):
        approval.require("posters", "whatever", 1.0, approved=True)


def test_a_bare_approval_covers_the_kind_asked_for():
    assert approval.approved_for("title", ["title.py", "20260822113400", "1", "--approved"])
    assert not approval.approved_for("title", ["title.py", "20260822113400", "1"])


def test_an_approval_named_for_one_kind_never_covers_another():
    argv = ["seq_boards.py", "20260822113400", "1", "--approved=sheets"]
    assert approval.approved_for("sheets", argv)
    assert not approval.approved_for("title", argv)
    assert not approval.approved_for("cast", argv)


def test_the_plan_line_is_itemised_so_the_owner_can_say_yes_to_a_number():
    assert approval.plan_line("sheets", "6 sheets for episode 1", 0.99) == "sheets: 6 sheets for episode 1 — $0.99"


def test_a_gpu_render_is_refused_without_approval():
    """Owner 2026-09-12: "do not run anything in comfyui, especially the title card,
    until asked".  The GPU is the owner's machine and their queue, so a render asks
    for itself, exactly as a paid picture does."""
    with pytest.raises(approval.NotApproved) as raised:
        approval.require("render", "the title card's 4 s animation on ComfyUI", 0.0, approved=False)
    assert "REFUSED" in str(raised.value) and "render" in str(raised.value)
    approval.require("render", "19 takes on ComfyUI", 0.0, approved=True)


def test_an_image_approval_never_buys_a_render():
    argv = ["seq_boards.py", "20260822113400", "1", "--approved=sheets"]
    assert not approval.approved_for("render", argv)


def test_a_hold_stops_everything_even_with_an_approval(tmp_path, monkeypatch):
    """Owner, 2026-09-12: "only kill your jobs and stop them from running again
    until I ask".  An approval already typed on a command line that is already
    running cannot be untyped, and the machine cannot always be reached to stop
    the script.  A file can: while it is there, nothing starts.
    """
    hold = tmp_path / "RENDER_HOLD"
    monkeypatch.setattr(approval, "HOLD", hold)
    approval.require("render", "19 takes on ComfyUI", 0.0, approved=True)  # no hold yet
    hold.write_text("the owner is using the GPU", encoding="utf-8")
    for kind in ("render", "title", "sheets"):
        with pytest.raises(approval.NotApproved) as raised:
            approval.require(kind, "whatever it was about to do", 0.20, approved=True)
        assert "HELD" in str(raised.value) and "RENDER_HOLD" in str(raised.value)


def test_the_hold_says_who_put_it_there(tmp_path, monkeypatch):
    hold = tmp_path / "RENDER_HOLD"
    monkeypatch.setattr(approval, "HOLD", hold)
    hold.write_text("comfy_studio is on the GPU", encoding="utf-8")
    with pytest.raises(approval.NotApproved) as raised:
        approval.require("render", "one take", 0.0, approved=True)
    assert "comfy_studio is on the GPU" in str(raised.value)


def test_lifting_the_hold_is_deleting_the_file(tmp_path, monkeypatch):
    hold = tmp_path / "RENDER_HOLD"
    monkeypatch.setattr(approval, "HOLD", hold)
    hold.write_text("held", encoding="utf-8")
    hold.unlink()
    approval.require("render", "one take", 0.0, approved=True)
