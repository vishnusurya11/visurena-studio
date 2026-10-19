"""scripts/episode/face_refine.py with round 2 of the face-blur fix wired in (2026-10-19): the take's
tracks come from strong faces, weak faces and bodies (`take_tracks`), a lost face re-acquires only
its own head, each soft face's run is its hysteresis span on H3's grid inside its shot with one
frozen side (`run_of`), a small face is pasted softly, and the gate logs drift, eyes and the anime
identity terms beside facenet.  Engine, detector, embedder and the anime reader are fakes; the
videos are synthetic (tests/test_face_refine_renders_through_a_fake_comfy.py's room)."""
from __future__ import annotations

import json

import numpy as np
import pytest

from scripts.episode import face_refine as cli
from studio import face_refine as fr
from studio import face_track as ft
from tests.test_face_refine_renders_through_a_fake_comfy import FRAMES, Engine, Room, detect_one, embed


def box(cx, cy, h=30.0):
    return (cx - h / 2, cy - h / 2, cx + h / 2, cy + h / 2)


def frames(n=60, side=768):
    return [np.full((side, side, 3), 90, np.uint8) for _ in range(n)]


def rows(boxes, score=0.9, kind=None):
    return [{"box": list(b), "score": score} | ({"kind": kind} if kind else {}) for b in boxes]


# ---- the take's tracks ------------------------------------------------------------------------

def test_a_body_never_lengthens_a_face_track():
    """ep01 T01: a body-estimated face moved Utterson's track onto Enfield; weak faces alone gave
    T06's Hyde his frames 0-17, so bodies only make far figures."""
    dets = {t: rows([box(500, 300, 40)]) for t in range(30, 60, 3)}
    for t in range(0, 30, 3):
        dets[t] = rows([(470, 270, 530, 670)], kind="person")
    tracks, _ = cli.take_tracks(frames(), dets, [])
    assert [ft.life(t) for t in tracks] == [(30, 57)]


def test_a_take_tracks_faces_and_a_far_figure_the_face_model_missed():
    dets = {t: rows([box(500, 300, 40)]) + rows([(90, 200, 150, 380)], kind="person") for t in range(0, 60, 3)}
    tracks, sources = cli.take_tracks(frames(), dets, [])
    assert sources == ["face", "body"] and len(tracks) == 2


def test_a_weak_face_lengthens_its_track():
    dets = {t: rows([box(500, 300, 40)], score=0.9 if t < 30 else 0.4) for t in range(0, 60, 3)}
    tracks, _ = cli.take_tracks(frames(), dets, [])
    assert [ft.life(t) for t in tracks] == [(0, 57)]


def test_a_lone_weak_face_is_no_track():
    dets = {t: rows([box(500, 300, 40)], score=0.4) for t in range(0, 60, 3)}
    assert cli.take_tracks(frames(), dets, [])[0] == []


def test_a_lost_face_is_reacquired_only_by_a_head_more_like_its_own_than_anyone_elses():
    """ep01 round 1's eleven re-acquires: the same person read 0.48-1.00 against the track's latest
    head, another person present 0.46-0.89, so no single line splits them (T07's child 0.48, T01's
    Utterson 0.68).  A head is re-acquired when it reads at least as much like the track's own latest
    head as like any other person's present then, and over a floor of 0.4."""
    fr_ = frames(12)
    for f in fr_:
        f[60:140, 60:140] = (20, 20, 20)
        f[60:140, 300:380] = (200, 140, 60)
    same = cli.Same(fr_)
    dark = [(0, box(100, 110, 40)), (3, box(100, 110, 40))]
    brown = [(0, box(340, 110, 40)), (3, box(340, 110, 40))]
    assert same(dark, box(100, 110, 40), 9, [brown]) and not same(dark, box(340, 110, 40), 9, [brown])
    assert not same(dark, box(340, 110, 40), 9, [])            # under the floor with nobody else about
    assert cli.REACQUIRE_FLOOR == 0.4
    later = [(15, box(100, 110, 40))]                           # her own next piece is no rival
    assert same(dark, box(100, 110, 40), 9, [later]) and cli.RIVAL_GAP == ft.EVERY


# ---- the run of one soft face --------------------------------------------------------------------

def test_a_push_in_is_cropped_only_while_its_face_is_soft():
    track = [(t, box(384, 384, 60 + t)) for t in range(0, 174, 3)]
    run = cli.run_of(track, 174, 768, 768, [])
    assert run.start == 0 and run.frames % 17 == 5 and run.frames < 174
    assert run.life[1] <= run.start + run.frames - 1 and {s for _, _, s in run.windows} == {run.side}


def test_a_run_never_crosses_a_hard_cut():
    track = [(t, box(300, 300, 40)) for t in range(60, 100, 3)]
    run = cli.run_of(track, 200, 768, 768, [100])
    assert run.start + run.frames <= 100 and run.life[0] >= run.start


def test_a_small_face_is_pasted_softly_and_says_so():
    run = cli.run_of([(t, box(300, 300, 30)) for t in range(0, 60, 3)], 60, 768, 768, [])
    assert run.soft and run.face_px == pytest.approx(30.0)


# ---- the whole refine ---------------------------------------------------------------------------

class Anime:
    def __init__(self, terms):
        self.terms, self.asked = terms, []

    def __call__(self, sheet, src, ref):
        self.asked.append((sheet.shape, len(src), len(ref)))
        return self.terms


def run(world, engine, anime=None):
    return cli.refine(world.book, 1, None, engine=engine, detect=detect_one, loose=detect_one, embed=embed,
                      within="", anime=anime)


def test_the_track_file_says_how_its_crop_is_pasted(tmp_path):
    w = Room(tmp_path)
    run(w, Engine(tmp_path))
    person = json.loads((w.room / "refine.json").read_text())["T00"]["people"][0]
    track = json.loads((w.room / person["track"]).read_text())
    assert track["soft"] and track["side"] == ft.MIN_SIDE and track["face_px"] == pytest.approx(30.7, abs=0.1)
    assert {s for _, _, s in track["windows"]} == {track["side"]} and track["source"] == "face" and track["lost"] == 0


def test_the_gate_logs_drift_and_eyes(tmp_path):
    w = Room(tmp_path)
    run(w, Engine(tmp_path))
    m = json.loads((w.room / "refine.json").read_text())["T00"]["people"][0]["measures"]
    assert m["drift"] is not None and m["drift"] < fr.DRIFT_MAX and "eye_src" in m and "eye_ref" in m


def test_the_anime_terms_are_read_and_rule_identity(tmp_path):
    w, anime = Room(tmp_path), Anime({"ccip_src": 0.05, "ccip_ref": 0.15, "clip_src": 0.8, "clip_ref": 0.8})
    run(w, Engine(tmp_path), anime)
    entry = json.loads((w.room / "refine.json").read_text())["T00"]
    assert anime.asked and anime.asked[0][1] == anime.asked[0][2] == cli.ID_SAMPLES
    assert entry["status"] == "unrefined" and "ccip" in entry["people"][0]["why"]
    assert entry["people"][0]["measures"]["ccip_ref"] == 0.15


def test_no_anime_reader_leaves_the_terms_unread(tmp_path):
    w = Room(tmp_path)
    run(w, Engine(tmp_path))
    m = json.loads((w.room / "refine.json").read_text())["T00"]["people"][0]["measures"]
    assert m["ccip_src"] is None and m["clip_ref"] is None
