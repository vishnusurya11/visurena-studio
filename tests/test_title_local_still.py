"""The title still can be drawn on the LOCAL model when the paid API cannot.

MEASURED 2026-09-17: the image API returned "You have no credits remaining" and
episode 13 was finished but for its card, which every master needs (the generic
card is 9:16 and a 1:1 episode refuses it).  The local drawer sets the three
lines legibly -- "SHERLOCK HOLMES", "A STUDY IN SCARLET" with SCARLET in red,
"EPISODE N" -- but will not draw the scarlet thread, so the local card is the
fallback and the paid one stays the default.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "episode"))
spec = importlib.util.spec_from_file_location("ep_title_local", ROOT / "scripts" / "episode" / "title.py")
title = importlib.util.module_from_spec(spec)
spec.loader.exec_module(title)


def test_the_local_prompt_asks_for_the_red_thread_and_the_red_word():
    said = title.local_prompt(title.still_prompt("Sherlock Holmes", "A Study in Scarlet", 13, "", "square 1:1"))
    assert "RED" in said and "SCARLET is lettered" in said


def test_the_local_still_is_rendered_and_conformed(tmp_path):
    from PIL import Image

    source = tmp_path / "raw.png"
    Image.new("RGB", (1024, 1024), "black").save(source)
    seen = {}

    def render(prompt, prefix, seed):
        seen.update(prompt=prompt, prefix=prefix, seed=seed)
        return source

    out = title.draw_local("a prompt", tmp_path / "ep13.png", seed=4400, render=render)
    assert out.exists() and Image.open(out).size == (title.W, title.H)
    assert seen["seed"] == 4400 and "a prompt" in seen["prompt"]


def test_a_still_on_disk_is_never_redrawn(tmp_path):
    from PIL import Image

    out = tmp_path / "ep13.png"
    Image.new("RGB", (title.W, title.H), "black").save(out)

    def refuse(*_a, **_k):
        raise AssertionError("redrew a still that was already on disk")

    assert title.draw_local("a prompt", out, seed=1, render=refuse) == out
