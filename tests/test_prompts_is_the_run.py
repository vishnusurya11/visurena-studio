"""A dry run is the same computation as the real run, minus the spending.

`takes_r2v.main` rebinds the module's canvas from the plan --

    W, H = canvas.size(episode.aspect)

-- and `takes_r2v.prompts` did not.  So `--prompts`, the FREE preview you check
before committing GPU hours, built every card at the module default.

MEASURED on episode 4, 2026-09-13: the plan declares `1:1`, the preview cards
said 768x1344, and the graph that actually ran said 768x768.  The preview was
describing a different episode's shape.

Nothing was lost this time, because the thing being checked was the take budget
and `frames` does not depend on the canvas.  The fault is that it COULD have
been: a preview that differs from the run by even one line of setup is a
different program, and its job is to be the run.

The guard is not "prompts sets W and H too" -- that is the same duplication one
line further on.  It is that both entry points take the same road into `cards`.
"""
import json

import pytest

from studio import canvas


def test_the_two_entry_points_share_their_setup():
    """No setup line may live in one entry point and not the other."""
    import inspect

    from scripts.episode import takes_r2v as tr
    body = inspect.getsource(tr.prompts) + inspect.getsource(tr.main)
    # the canvas is read from the plan, in ONE place, not once per entry point
    assert body.count("canvas.size(") <= 1, "each entry point rebinds the canvas for itself"


@pytest.mark.parametrize("aspect,size", [("1:1", (768, 768)), ("9:16", (768, 1344))])
def test_a_preview_card_carries_the_plans_own_canvas(tmp_path, aspect, size, monkeypatch):
    from scripts.episode import takes_r2v as tr

    seen = {}

    def fake_cards(book, episode, number):
        seen["wh"] = (tr.W, tr.H)
        return []

    monkeypatch.setattr(tr, "cards", fake_cards)
    monkeypatch.setattr(tr.episode_home, "book_dir", lambda _id: tmp_path)
    monkeypatch.setattr(tr.episode_home, "load_plan",
                        lambda b, n: type("E", (), {"aspect": aspect, "long_shots": lambda self: [],
                                                    "still_motions": lambda self: []})())
    monkeypatch.setattr(tr.episode_home, "takes_dir", lambda b, n, e: tmp_path)
    tr.prompts("book", 4)
    assert seen["wh"] == size == canvas.size(aspect)
