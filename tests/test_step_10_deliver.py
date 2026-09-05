"""Step 10 of the trailer stage: the manifest and the Telegram send.

The manifest is the retrospect's input: every rung taken and every number
measured, in one file beside the master.  The send climbs x3 and then the
file stays in the library with the manifest saying `undelivered`.  No
network is touched: the sender is a faked subprocess.
"""
from __future__ import annotations

import json
import subprocess

import pytest

from scripts.trailer import step_10_deliver as step
from studio import db
from studio.learnings import Learning, record
from studio.trailer_run import RunContext

QC = {"cuts": 30, "cuts_on_beat": 0.9, "cuts_on_downbeat": 0.4, "cuts_on_L0": 1.0,
      "on_cap_fraction": 0.05, "title_on_downbeat": True, "integrated_lufs": -14.2,
      "true_peak": -1.3, "unbound_shots": 0, "line_over_bed_lu": [6.1], "grid": "metre",
      "cue_cut": {"cuts_on_events": 0.95, "section_changes_cut": 1.0, "cuts_inside_sustain": 0,
                  "long_shots_on_sustains": 1.0, "lines_in_troughs": 1.0}}


@pytest.fixture()
def ctx(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    codex_id = db.insert_codex(conn, "Scarlet", codex_id="20260901000010")
    book = tmp_path / "20260901000010_scarlet"
    context = RunContext(conn, codex_id, book, logs_root=tmp_path / "logs")
    context.out_dir.mkdir(parents=True)
    (context.out_dir / "TRAILER-scarlet.mp4").write_bytes(b"mp4")
    (context.out_dir / "qc.json").write_text(json.dumps(QC), encoding="utf-8")
    record(context.learnings_path, Learning(step="07", gate="identity", measured=0.2,
                                            threshold=0.363, action="reroll_seed"))
    context.open_step("10")
    return context


@pytest.fixture()
def sender(monkeypatch):
    state = {"codes": [0], "calls": []}

    def send(master, caption):
        state["calls"].append({"master": master, "caption": caption})
        return state["codes"].pop(0)
    monkeypatch.setattr(step, "send", send)
    return state


def manifest_of(ctx):
    return json.loads((ctx.out_dir / "manifest.json").read_text(encoding="utf-8"))


class TestRun:
    def test_manifest_carries_every_rung_and_number(self, ctx, sender):
        step.run(ctx.codex_id, ctx)
        doc = manifest_of(ctx)
        assert doc["master"] == "trailer/main/TRAILER-scarlet.mp4"
        assert doc["qc"]["integrated_lufs"] == -14.2 and doc["floor_pass"] is True
        assert doc["flags"] == []
        assert [r["action"] for r in doc["learnings"]] == ["reroll_seed"]
        assert doc["rungs_by_step"] == {"07": 1}
        assert doc["delivery"] == {"status": "delivered", "attempts": 1,
                                   "file": "TRAILER-scarlet.mp4"}
        assert sender["calls"][0]["master"].name == "TRAILER-scarlet.mp4"
        assert "-14.2" in sender["calls"][0]["caption"]

    def test_a_master_over_the_bot_limit_sends_a_shrunk_copy(self, ctx, sender, monkeypatch):
        """Scarlet run 6b: the master was 52,473,989 bytes, 45 KB over the
        Bot API's 50 MiB upload cap; three sends died with a TLS EOF and the
        run went 'undelivered'.  A 39 MB re-encode went through first time."""
        (ctx.out_dir / "TRAILER-scarlet.mp4").write_bytes(b"0" * (step.TELEGRAM_LIMIT + 1))
        shrunk = []

        def shrink(master, dest):
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(b"small"); shrunk.append(master.name); return dest
        monkeypatch.setattr(step, "shrink", shrink)
        step.run(ctx.codex_id, ctx)
        doc = manifest_of(ctx)
        assert shrunk == ["TRAILER-scarlet.mp4"]
        assert sender["calls"][0]["master"].name == "telegram.mp4"
        assert doc["delivery"] == {"status": "delivered", "attempts": 1, "file": "work/telegram.mp4"}
        assert doc["master"] == "trailer/main/TRAILER-scarlet.mp4"

    def test_a_send_that_keeps_failing_leaves_the_file_undelivered(self, ctx, sender):
        sender["codes"] = [3, 3, 3]
        step.run(ctx.codex_id, ctx)
        doc = manifest_of(ctx)
        assert doc["delivery"]["status"] == "undelivered" and doc["delivery"]["attempts"] == 3
        assert len(sender["calls"]) == 3
        actions = [r["action"] for r in doc["learnings"]]
        assert actions == ["reroll_seed"] + ["send"] * 3 + ["undelivered"]

    def test_a_flagged_master_names_its_misses_in_the_caption(self, ctx, sender):
        (ctx.out_dir / "qc.json").write_text(json.dumps(dict(QC, cuts_on_downbeat=0.1)),
                                             encoding="utf-8")
        step.run(ctx.codex_id, ctx)
        assert manifest_of(ctx)["flags"] == ["cuts_on_downbeat"]
        assert "cuts_on_downbeat" in sender["calls"][0]["caption"]

    def test_without_qc_the_manifest_still_ships(self, ctx, sender):
        (ctx.out_dir / "qc.json").unlink()
        step.run(ctx.codex_id, ctx)
        doc = manifest_of(ctx)
        assert doc["qc"] is None and doc["floor_pass"] is None and "qc_missing" in doc["flags"]


class TestCaption:
    def test_names_the_book_the_numbers_and_the_rungs(self):
        caption = step.caption_for("A Study in Scarlet", QC, ["cuts_on_beat"], {"07": 2})
        assert caption.startswith("A Study in Scarlet")
        assert "cuts_on_beat" in caption and "07: 2" in caption and "-1.3" in caption


class TestShrink:
    def test_the_copy_is_a_playable_file_under_the_limit(self, tmp_path):
        source = tmp_path / "m.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                        "testsrc=size=320x180:rate=24:duration=1", "-c:v", "libx264",
                        "-crf", "1", str(source)], check=True)
        copy = step.shrink(source, tmp_path / "work/telegram.mp4")
        assert copy.exists() and copy.stat().st_size < source.stat().st_size
        assert copy.stat().st_size <= step.TELEGRAM_LIMIT
