"""03_02 (AREA 4): a plan-staged prop with no refs/props/<pid>/sheet.png is
drawn in step 03 -- the first GPU step after a clean battery -- via
build_pack.draw imported directly, so grids and takes always find the sheet
(the thunder_child hand-draw, codified).  done() refuses while a sheet is
missing, so drive.py re-enters idempotently.  A card with no design.sheet_prompt
routes through stage_pick.write_sheet_prompt and the prompt is persisted,
append-only, into the card json.  build_pack is monkeypatched: no GPU, $0."""
from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

from scripts.episode import step_03_places as step
from studio import episode_home, plan_verdict

DOC = {"setups": {"pit": {"described": "The pit.", "props": ["fighting_machine"]},
                  "lane": {"described": "The lane.", "props": []}}}


def book_of(tmp_path, sheet_prompt="A glittering walking engine centered on a plain ground."):
    props = tmp_path / "book" / "analysis" / "props"
    props.mkdir(parents=True)
    design = {"sheet_prompt": sheet_prompt} if sheet_prompt else {}
    (props / "fighting_machine.json").write_text(json.dumps(
        {"id": "fighting_machine", "name": "the Martian fighting-machine", "kind": "machine",
         "profile": {"physical": "A walking engine.", "scale": "Huge.", "design": design}},
        indent=2), encoding="utf-8")
    return tmp_path / "book"


def fake_draw(monkeypatch):
    bp = importlib.import_module("scripts.refs.build_pack")
    drawn = []

    def draw(book, job):
        target = Path(book) / f"refs/{job.kind}/{job.entity}/{job.name}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"png")
        drawn.append(job)
        return target
    monkeypatch.setattr(bp, "draw", draw)
    monkeypatch.setattr(bp, "log", lambda book, job, seconds: None)
    return drawn


def ctx_of(book):
    return SimpleNamespace(book_dir=book, number=None, home=episode_home.home(book, 4),
                           log=lambda *a, **k: None)


def test_missing_sheets_lists_the_staged_pid_until_drawn(tmp_path):
    book = book_of(tmp_path)
    assert step.plan_props(DOC) == ["fighting_machine"]
    assert step.missing_sheets(book, DOC) == ["fighting_machine"]
    sheet = book / "refs" / "props" / "fighting_machine" / "sheet.png"
    sheet.parent.mkdir(parents=True)
    sheet.write_bytes(b"png")
    assert step.missing_sheets(book, DOC) == []


def test_draw_prop_sheets_lands_the_sheet_via_build_pack(tmp_path, monkeypatch):
    book = book_of(tmp_path)
    drawn = fake_draw(monkeypatch)
    step.draw_prop_sheets(ctx_of(book), DOC)
    assert (book / "refs" / "props" / "fighting_machine" / "sheet.png").exists()
    assert [j.entity for j in drawn] == ["fighting_machine"]
    step.draw_prop_sheets(ctx_of(book), DOC)            # idempotent: nothing redrawn
    assert len(drawn) == 1


def test_done_waits_for_the_sheet(tmp_path, monkeypatch):
    book = book_of(tmp_path)
    ctx = ctx_of(book)
    episode_home.write_json(ctx.home / "plan.json", DOC)
    episode_home.write_json(ctx.home / "storyboard" / "cells_from_picture.json",
                            {"plan_sha8": plan_verdict.plan_sha8(ctx.home / "plan.json"),
                             "from_picture": False, "readings": {}})
    assert not step.done(ctx)
    fake_draw(monkeypatch)
    step.draw_prop_sheets(ctx, DOC)
    assert step.done(ctx)


def test_a_card_with_no_sheet_prompt_gets_one_written_and_persisted(tmp_path, monkeypatch):
    book = book_of(tmp_path, sheet_prompt="")
    other = book / "analysis" / "props" / "red_weed.json"
    other.write_text(json.dumps({"id": "red_weed", "profile": {"design": {
        "sheet_prompt": "A red creeper on a plain neutral ground."}}}), encoding="utf-8")
    drawn = fake_draw(monkeypatch)
    said = ("A glittering walking engine centered on a plain neutral ground, every "
            "leg joint and the brazen hood stated, no scene, no people, no text.")
    asked = []
    monkeypatch.setattr(step, "PROMPT", lambda card, examples: asked.append(examples) or said)
    step.draw_prop_sheets(ctx_of(book), DOC)
    assert asked == [["A red creeper on a plain neutral ground."]]
    card = json.loads((book / "analysis" / "props" / "fighting_machine.json")
                      .read_text(encoding="utf-8"))
    assert card["profile"]["design"]["sheet_prompt"] == said
    assert card["name"] == "the Martian fighting-machine"   # every other key kept
    assert [j.prompt for j in drawn] == [said]
