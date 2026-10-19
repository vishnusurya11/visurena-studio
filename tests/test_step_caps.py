"""The cap table's own contract (P12): every row has a reader, the step wall is the row sum,
the lines row exists (K1), every step names a model family (K2)."""
import re
from pathlib import Path

from studio import registry, step_caps

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = {"text", "image", "vl", "tts", "video", "none"}


def _source() -> str:
    files = [*(ROOT / "studio").glob("*.py"), *(ROOT / "scripts").rglob("*.py")]
    return "\n".join(f.read_text(encoding="utf-8") for f in files if f.name != "step_caps.py")


def _has_reader(cap, source: str) -> bool:
    if cap.read == "step" or cap.gate:
        return True
    return bool(re.search(r"""step_caps\.(rounds|wall_s|cap)\(\s*["']%s["']""" % cap.name, source))


def test_every_cap_row_has_a_reader():
    source = _source()
    orphans = [c.name for c in step_caps.table().values() if not _has_reader(c, source)]
    assert orphans == []


def test_step_wall_is_still_the_row_sum():
    rows = step_caps.table().values()
    for step_id in {c.step for c in rows}:
        want = sum(c.wall_s * (c.climbs if c.per == "climb" else 1) for c in rows if c.step == step_id)
        assert step_caps.step_wall_s(step_id) == want


def test_the_lines_row_exists():
    row = step_caps.cap("lines")
    assert (row.step, row.per, step_caps.wall_s("lines")) == ("04", "episode", 600.0)


def test_every_step_names_a_family():
    assert {step_caps.family(s["id"]) for s in registry.steps("episode")} <= FAMILIES
    assert step_caps.family("08") == "vl" and step_caps.family("09") == "video"
    assert step_caps.family("99") == "none"


def test_share_min_is_report_only():
    before = step_caps.step_wall_s("09")
    assert step_caps.share_min("09") >= 0.0
    assert step_caps.step_wall_s("09") == before
