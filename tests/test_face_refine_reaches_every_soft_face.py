"""The face refine reaches every soft face (owner 2026-10-19: "why our fix skipped those
shots? fix that").  Jekyll ep01 refined 2 of the 28 takes; the owner's blurry takes (T01, T06,
T07, T08, T13, T15) are all in the worst nine by face height
(docs/audit/2026-10-19_face_blur/pipeline_audit.md section 2).

- the plan size is no gate (a medium holds a 64 px face, T26) and a face is soft under 120 px
  (a 60-110 px face of 768 draws a 5-10 px eye; H3's token is 32 px);
- the take is judged by its smallest tracked face, never by face-at-end (T06 pushes in from
  60 to 233 px: its last frame read 0.30);
- T01 had no refine.json row because the rule of the 2026-10-18 run barred every hard row but
  the warp's, and T01 failed only `gait`;
- F2's denoise follows the face: 0.45 at 60 px (T08/T18, kept by the owner), +0.05 per halving.

Fixtures (tests/fixtures/ep01_replay/): face_blur/cards.json (ep01 prompts.json + plan.json
sizes), face_blur/face_samples.json (the audit's face_yolov8m heights at 20/50/80 % of every
take, conf >= 0.6 counted), P07/dq_warp.json (the stored dq rows)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import face_refine as fr
from studio import face_track as ft

FIX = Path(__file__).parent / "fixtures" / "ep01_replay"
CONF = 0.6
"""The audit counted a face at confidence >= 0.6 (pipeline_audit.md section 2)."""


def cards() -> list[dict]:
    return json.loads((FIX / "face_blur" / "cards.json").read_text("utf-8"))


def dq_of(row: dict) -> dict:
    """A stored P07 row as the dq record the selection reads."""
    gates = [{"name": name, "ok": False, "hard": True} for name in row["hard_failed"]]
    return {"passed": row["passed"], "gates": gates, "measures": {"warp": row["warp"] or {}}}


def dqs() -> dict[int, dict]:
    rows = json.loads((FIX / "P07" / "dq_warp.json").read_text("utf-8"))
    return {int(k[1:]): dq_of(v) for k, v in rows.items()}


def sample_track(samples: list[dict]) -> list:
    """The take's smallest confident face at each sampled frame, as one track."""
    out = []
    for s in samples:
        heights = [f["h"] for f in s["faces"] if f["conf"] >= CONF]
        if heights:
            h = float(min(heights))
            out.append((s["f"], (0.0, 0.0, h, h)))
    return out


def take_px() -> dict[int, float | None]:
    """Each take's smallest face, read as the run reads a track (ft.track_px)."""
    samples = json.loads((FIX / "face_blur" / "face_samples.json").read_text("utf-8"))
    return {int(k[1:]): (ft.track_px(tr) if (tr := sample_track(v)) else None) for k, v in samples.items()}


def picks() -> list[int]:
    cs = cards()
    sizes = {c["index"]: s for c in cs for s in c["sizes"][:1]}
    chosen = fr.selected([c | {"shots": [c["index"]]} for c in cs], sizes, dqs(), taken={c["index"]: 1 for c in cs})
    px = take_px()
    return [i for i in chosen if fr.soft(px[i])]


# ---- the ep01 replay --------------------------------------------------------------------

def test_the_ep01_replay_refines_the_eleven_soft_takes_and_skips_the_close_ups():
    assert picks() == [1, 5, 6, 8, 10, 13, 15, 18, 20, 23, 26]


def test_the_insert_and_the_faceless_card_stay_out_though_their_faces_are_small():
    px = take_px()
    assert px[7] < fr.SMALL_FACE_PX and px[27] < fr.SMALL_FACE_PX
    assert 7 not in picks() and 27 not in picks()


def test_a_one_sample_dip_is_not_the_takes_face():
    """T09 reads 255, 162 and 119 px: the running median keeps it a 162 px close-up."""
    assert take_px()[9] == pytest.approx(162.0)


def test_the_added_gpu_fits_the_six_hour_clock():
    """Priced at 11.0 s + 0.558 s per frame per planned face (studio/face_refine.price, the fit
    COSTS.md measured; 110 s per 192 frames priced it at 1,512 s until fleet C A4, 2026-10-22)."""
    by = {c["index"]: c for c in cards()}
    total = sum(fr.price(len(by[i]["faces"]), by[i]["frames"]) for i in picks())
    already = sum(fr.price(len(by[i]["faces"]), by[i]["frames"]) for i in (8, 18))
    assert total == pytest.approx(1671, abs=5)              # 27.9 min, the 11 takes
    assert (total - already) / 60 == pytest.approx(21.2, abs=0.2)


# ---- the rule ----------------------------------------------------------------------------

def test_a_face_is_soft_under_120_px():
    assert fr.SMALL_FACE_PX == 120.0
    assert fr.soft(119.9) and not fr.soft(120.0) and not fr.soft(None)


def test_the_plan_size_is_no_gate():
    card = {"index": 26, "faces": ["a"]}
    dq = {"passed": True, "gates": []}
    assert fr.eligible(card, ["medium"], dq) and fr.eligible(card, ["medium_close"], dq)


def test_face_at_end_is_never_read():
    card = {"index": 6, "faces": ["a"]}
    dq = {"passed": True, "gates": [{"name": "face-at-end", "value": 0.303, "ok": True, "hard": False}]}
    assert fr.eligible(card, ["full"], dq)


def test_a_take_failing_on_score_alone_still_ships_so_its_face_is_refined():
    assert fr.eligible({"index": 3, "faces": ["a"]}, ["wide"], {"passed": False, "gates": []})


def test_a_hard_row_outside_the_bars_still_bars_the_take():
    dq = {"passed": False, "gates": [{"name": "identity", "ok": False, "hard": True}]}
    assert not fr.eligible({"index": 3, "faces": ["a"]}, ["wide"], dq)


def test_a_warp_fail_waits_for_its_one_seed_retake():
    dq = {"passed": False, "gates": [{"name": "warp", "ok": False, "hard": True}],
          "measures": {"warp": {"S": 2.9, "Se": 1.0, "share": 0.9}}}
    card = {"index": 3, "faces": ["a"]}
    assert fr.retake_owed(dq, 0) and not fr.eligible(card, ["wide"], dq, taken=0)
    assert not fr.retake_owed(dq, 1) and fr.eligible(card, ["wide"], dq, taken=1)


# ---- T01: why it had no row -------------------------------------------------------------

def run_time_rule(dq: dict) -> bool:
    """passed_but_warp as it stood for the 2026-10-18 run (41fba62^): only the warp may fail."""
    failed = {g.get("name") for g in dq.get("gates", []) if g.get("hard") and not g.get("ok")}
    return bool(dq.get("passed")) or failed == {"warp"}


def test_t01_was_barred_by_its_gait_row_so_it_never_got_a_row():
    """ep01 attempts.json holds no face_refine.T01 round and refine.json no T01 entry: the take
    was never pending.  Its only hard failure is gait; the run-time rule let only warp fail."""
    t01 = dqs()[1]
    assert {g["name"] for g in t01["gates"]} == {"gait"}
    assert not run_time_rule(t01)
    assert fr.passed_but_warp(t01) and 1 in picks()


# ---- the denoise follows the face ---------------------------------------------------------

def test_the_denoise_is_045_at_the_60_px_point_the_owner_kept():
    assert fr.denoise_for(60.0) == pytest.approx(0.45)


def test_a_smaller_face_gets_a_little_more_denoise_a_bigger_one_less():
    assert fr.denoise_for(30.0) == pytest.approx(0.50)
    assert fr.denoise_for(120.0) == pytest.approx(0.40)
    assert fr.denoise_for(41.0) > fr.denoise_for(55.0) > fr.denoise_for(99.0)


def test_the_denoise_stays_in_its_band():
    assert fr.denoise_for(4.0) == pytest.approx(0.55) and fr.denoise_for(400.0) == pytest.approx(0.40)
    assert fr.denoise_for(None) == fr.DENOISE and fr.denoise_for(0.0) == fr.DENOISE
