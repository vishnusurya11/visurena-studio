"""Every clock the board prints is the studio's local clock (page experts 2026-10-18, C1):
the run id's stamp, the lease, the orders strip, the Activity rows, Home's 'started' and
the Today feed were UTC slices of ISO strings ('20:35' at 13:35 Seattle).  The stamps are
UTC; the page converts them through one helper, and no template slices a stamp."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from command_center_fixtures import CODEX
from studio.command_center import app as cc_app
from studio.command_center import unit_view as uv

TEMPLATES = Path(uv.__file__).resolve().parent / "templates"
NOW = datetime(2026, 10, 18, 21, 0, tzinfo=timezone.utc)


def local(*ymdhms) -> datetime:
    return datetime(*ymdhms, tzinfo=timezone.utc).astimezone()


def test_a_run_ids_utc_stamp_reads_as_the_local_clock():
    rid = f"{CODEX}__episode__20261018203415"
    assert uv._run_short({"run_id": rid}) == local(2026, 10, 18, 20, 34, 15).strftime("%H:%M")


def test_the_lease_prints_its_local_clock():
    row = {"state": "running", "lease_until": "2026-10-18T20:35:00Z"}
    assert uv.lease(row, NOW)["until"] == local(2026, 10, 18, 20, 35).strftime("%H:%M")


def test_hhmmss_is_local_and_blank_for_junk():
    assert uv.hhmmss("2026-10-18T20:35:07Z") == local(2026, 10, 18, 20, 35, 7).strftime("%H:%M:%S")
    assert uv.hhmmss("") == "" and uv.hhmmss("soon") == ""


def test_the_templates_have_local_clock_filters():
    filters = cc_app.templates.env.filters
    assert filters["hhmm"] is uv.hhmm and filters["day_hhmm"] is uv.day_hhmm


def test_no_template_or_view_slices_a_stamp():
    slices = re.compile(r"\[(5|11):(16|19)\]")
    sources = [*TEMPLATES.glob("*.html"), Path(uv.__file__)]
    hits = [f"{p.name}: {m.group(0)}" for p in sources for m in slices.finditer(p.read_text("utf-8"))]
    assert hits == []


def test_the_viewer_reads_judged_from_the_item_and_opens_aliases():
    # page experts 2026-10-18 (E1): prov.js guessed 'judged' from the sub text
    static = TEMPLATES.parent / "static" / "viewer"
    prov, viewer = (static / "prov.js").read_text("utf-8"), (static / "viewer.js").read_text("utf-8")
    assert "judged = it.judged" in prov and "(x.aliases || []).includes(spec.rel)" in viewer


def test_the_viewer_ladder_converts_its_iso_stamp():
    prov = (TEMPLATES.parent / "static" / "viewer" / "prov.js").read_text("utf-8")
    assert "dhm(l.ts)" not in prov and "dhm(isoT(l.ts))" in prov
