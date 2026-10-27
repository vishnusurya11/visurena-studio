"""Jekyll ep03 retro #3: the episode shipped over PLAN keep_best, EYE_PANELS keep_best and
MASTER flag while the log said only QC PASS.  Step 13 prints every terminal non-pass gate
before it uploads and records them in the ledger; it reports, never blocks.  $0."""
from __future__ import annotations

import json

from scripts.episode import step_13_publish
from studio.learnings import Learning, record
from tests.test_step_13_publishes_and_polls import channel, episode, fake_send


def _flag(home, gate, action, note="", terminal=True):
    record(home / "learnings.jsonl", Learning(step="06", gate=gate, action=action, terminal=terminal, note=note))


def test_terminal_flags_are_the_last_row_per_gate_and_not_a_pass(tmp_path):
    _flag(tmp_path, "PLAN", "keep_best", "G-STORY shots 2-10")
    _flag(tmp_path, "MASTER", "flag", "lufs")
    _flag(tmp_path, "MASTER", "pass", terminal=False)           # a later pass clears the gate
    _flag(tmp_path, "EYE", "pass", terminal=False)
    flags = step_13_publish.terminal_flags(tmp_path)
    assert flags == [{"gate": "PLAN", "action": "keep_best", "notes": ["G-STORY shots 2-10"]}]


def test_the_notes_are_the_gates_first_three_terminal_rows(tmp_path):
    for i in range(5):
        _flag(tmp_path, "EYE_PANELS", "keep_best", f"note{i}")
    assert step_13_publish.terminal_flags(tmp_path)[0]["notes"] == ["note0", "note1", "note2"]


def test_a_flagged_episode_prints_and_records_its_flags_and_still_publishes(tmp_path, monkeypatch, capsys):
    ctx, book, home, sha8 = episode(tmp_path, monkeypatch)
    _flag(home, "PLAN", "keep_best", "G-STORY shots 2-10")
    step_13_publish.run(ctx, send=fake_send, build_api=lambda: channel(),
                        http=lambda url: (200, "https://www.youtube.com/shorts/vid1"), sleep=lambda s: None)
    out = capsys.readouterr().out.strip().splitlines()
    assert any(ln.startswith("FLAGGED: PLAN keep_best") and "G-STORY" in ln for ln in out)
    assert out[-1] == "https://www.youtube.com/shorts/vid1"
    rows = [json.loads(ln) for ln in (book / "uploads.jsonl").read_text(encoding="utf-8").splitlines()]
    row = next(r for r in rows if r.get("event") == "delivery_flags")
    assert row["sha8"] == sha8 and row["flags"][0]["gate"] == "PLAN"


def test_autopilot_status_names_the_current_episodes_terminal_flags(tmp_path):
    from tests import autopilot_cli_fixtures as fx
    cli, book = fx.load(), fx.book(tmp_path)
    _flag(cli.home_of(book, 2), "MASTER", "flag", "lufs")
    assert cli.flags_of(cli.home_of(book, 2)) == ["MASTER ended flag: lufs"]
    assert cli.flags_of(cli.home_of(book, 3)) == []
