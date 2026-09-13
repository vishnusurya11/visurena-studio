"""The title card is two spends wearing one name: a paid picture and a render on
the owner's own ComfyUI.

Owner, 2026-09-12: "do not run anything in comfyui, especially the title card,
until I ask".  So an approval typed for the PICTURE must not start the render:
the two are asked for separately, and `--approved=title` buys the still alone.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _title():
    spec = importlib.util.spec_from_file_location("ep_title", ROOT / "scripts" / "episode" / "title.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_named_title_approval_buys_the_still_and_not_the_render(monkeypatch):
    title = _title()
    asked = {}
    monkeypatch.setattr(title, "main", lambda book, number, approved=False, rendering=False:
                        asked.update(approved=approved, rendering=rendering))
    title._cli(["title.py", "20260822113400", "1", "--approved=title"])
    assert asked == {"approved": True, "rendering": False}


def test_a_bare_approval_buys_both(monkeypatch):
    title = _title()
    asked = {}
    monkeypatch.setattr(title, "main", lambda book, number, approved=False, rendering=False:
                        asked.update(approved=approved, rendering=rendering))
    title._cli(["title.py", "20260822113400", "1", "--approved"])
    assert asked == {"approved": True, "rendering": True}


def test_no_flag_buys_nothing(monkeypatch):
    title = _title()
    asked = {}
    monkeypatch.setattr(title, "main", lambda book, number, approved=False, rendering=False:
                        asked.update(approved=approved, rendering=rendering))
    title._cli(["title.py", "20260822113400", "1"])
    assert asked == {"approved": False, "rendering": False}
