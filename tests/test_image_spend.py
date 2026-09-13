"""The IMAGE ledger: one line per paid image call, priced from the owner's table.

Separate from `tests/test_spend.py`, which covers the LLM usage ledger. The two
modules briefly shared the name `studio.spend`, and the collision broke
`analysis.py` and `screenplay.py` (2026-09-11).
"""
import json

from studio import image_spend as spend


def test_a_sheet_and_a_still_are_priced_from_the_owners_table():
    assert spend.estimate_usd("gpt-image-2.5-sunburst", "2048x3072", "high") == 0.20
    assert spend.estimate_usd("gpt-image-2.5-sunburst", "1024x1536", "high") == 0.08


def test_an_unlisted_size_is_priced_by_area_against_the_nearest_listed_one():
    assert spend.estimate_usd("gpt-image-2.5-sunburst", "1024x1024", "high") == round(0.08 * 1024 * 1024 / (1024 * 1536), 2)


def test_every_call_writes_one_line_and_the_total_adds_them_up(tmp_path):
    spend.record(tmp_path, "gpt-image-2.5-sunburst", "2048x3072", "high", 1, "storyboard seq_cab_0")
    spend.record(tmp_path, "gpt-image-2.5-sunburst", "1024x1536", "high", 1, "cast sheet")
    rows = [json.loads(l) for l in (tmp_path / "spend.jsonl").read_text(encoding="utf-8").splitlines() if l]
    assert [r["purpose"] for r in rows] == ["storyboard seq_cab_0", "cast sheet"]
    assert spend.total(tmp_path) == 0.28
