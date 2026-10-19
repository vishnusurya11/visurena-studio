"""cut/master_layout.json names what made the master's bytes (upscale, encoder), the book video
ignores keys it does not read, and assemble's inner steps land on the clock within 'assemble'
(P09, Jekyll Kawajiri ep01: one 'assemble' row hid bed, sfx, mix and cut)."""
from __future__ import annotations

import json

from scripts.episode import assemble
from studio import book_compilation as bc, episode_clock, episode_home
from studio import youtube_publish as yp


def test_the_layout_names_the_encoder(tmp_path):
    master = tmp_path / "master_r2v.mp4"
    master.write_bytes(b"short")
    assemble.record_layout(tmp_path, master, main=3369, card=107, upscale="av3", encoder="cuda")
    row = json.loads((tmp_path / bc.LAYOUT).read_text(encoding="utf-8"))[yp.sha8(master)]
    assert row["encoder"] == "cuda" and row["upscale"] == "av3"


def test_an_unnamed_encoder_adds_no_key(tmp_path):
    master = tmp_path / "master_r2v.mp4"
    master.write_bytes(b"short")
    assemble.record_layout(tmp_path, master, main=3369, card=107)
    assert "encoder" not in json.loads((tmp_path / bc.LAYOUT).read_text(encoding="utf-8"))[yp.sha8(master)]


def test_the_book_video_ignores_layout_keys_it_does_not_know():
    layout = {"abcd1234": {"main": 100, "card": 7, "chip": 3, "encoder": "cuda", "upscale": "av3", "future": [1]}}
    assert bc.recorded_split(layout, "abcd1234") == (100, 7)


def test_an_inner_step_is_a_row_within_assemble(tmp_path):
    with assemble.within(tmp_path, 1, "mix", "lines and bed"):
        pass
    row = json.loads(episode_clock.path(tmp_path, 1).read_text(encoding="utf-8").splitlines()[-1])
    assert row["stage"] == "mix" and row["within"] == "assemble" and row["note"] == "lines and bed"


def test_main_times_bed_sfx_mix_and_cut():
    import inspect
    body = inspect.getsource(assemble.main)
    for stage in ("bed", "sfx", "mix", "cut"):
        assert f'within(book, number, "{stage}"' in body, stage


def test_the_log_says_the_paste_is_at_cut_scale():
    import inspect
    assert "pasted at cut scale, before the one upscale" in inspect.getsource(assemble.face_paste_wrap)


def test_the_expected_frames_go_to_a_master_that_takes_them(monkeypatch):
    monkeypatch.setattr(assemble.master_upscale, "master", lambda *a, expected_frames=None, **k: None)
    assert assemble.expected_of(4215) == {"expected_frames": 4215}


def test_the_expected_frames_wait_for_a_master_that_does_not(monkeypatch):
    monkeypatch.setattr(assemble.master_upscale, "master", lambda *a, **k: None)
    assert assemble.expected_of(4215) == {}
