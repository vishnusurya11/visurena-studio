"""Upscale last, once (owner 2026-10-18), and judged before it (Jekyll ep03 retro #2, 2026-10-27).

ep03: upscale (av3 4x, 3.1 min) 11:26 -> qc 11:29 -> master eye 11:32 -> retake -> upscale AGAIN 11:46 ->
qc -> master eye.  Every master round paid the 4x.  Now step 10 makes the finished picture at the cut's own
scale (face paste baked in, card, chip, loudness; no upscale), step 11's QC and master eye judge THAT file,
and the upscale runs once on the cut that was judged, its sound copied, never re-encoded.  The QC report and
the rubric are carried to the master's sha8 only while `cut/upscaled.json` says these master bytes were
made from the judged cut's bytes; any other master is upscaled again from the judged cut.

What the eye needs from full resolution: nothing it judges.  MEASURED on ep03's master (frame at 20 s):
the face box is 0.134 of the height at 3072 and at 768; MTCNN takes 1.34 s a frame at 3072, 0.13 s at
768.  The face strip (log only) shows crops as the viewer sees them, so it runs on the master after the
upscale.  No GPU, no ffmpeg in these tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import master_upscale as mu, youtube_publish as yp


# ---- the cut-scale pass ----------------------------------------------------------------------

def test_the_cut_pass_pastes_and_never_upscales_or_asks_for_the_card(tmp_path, monkeypatch):
    seen = {}

    def streamed(listing, out, width, height, up, fps, upscaler, encoder="cpu", paste=None,
                 expected_frames=None, args=None):
        seen.update(up=up, frame=upscaler("f"), paste=paste, args=args, expected=expected_frames)
        return expected_frames
    monkeypatch.setattr(mu, "streamed", streamed)
    monkeypatch.setattr(mu, "card_free", lambda *a, **k: pytest.fail("the cut pass asked for the card"))
    wrap = lambda up: (lambda f: f)                               # noqa: E731
    out = mu.master(tmp_path / "final.txt", tmp_path / "cut.mp4", 768, 768, mu.AT_CUT, 24, wrap=wrap,
                    expected_frames=3444)
    assert out == tmp_path / "cut.mp4" and seen["up"].factor == 1 and seen["frame"] == "f"
    assert seen["paste"] is not None and seen["args"] == mu.CUT_ENCODE and seen["expected"] == 3444
    assert not (tmp_path / mu.USED_FILE).exists(), "the cut pass is no upscale: QC must not read one"


def test_the_cut_encode_is_finer_than_the_delivered_one():
    crf = lambda args: int(args[args.index("-crf") + 1])          # noqa: E731
    assert crf(mu.CUT_ENCODE) < crf(mu.ENCODE)


def test_the_encoder_takes_the_cut_args(tmp_path):
    argv = mu.encode_argv(tmp_path / "l.txt", tmp_path / "o.mp4", 768, 768, 24, args=mu.CUT_ENCODE)
    assert argv[argv.index("-crf") + 1] == mu.CUT_ENCODE[mu.CUT_ENCODE.index("-crf") + 1]


def test_the_cut_is_named_beside_its_master(tmp_path):
    assert mu.cut_of(tmp_path / "cut" / "master_r2v.mp4") == tmp_path / "cut" / "cut_r2v.mp4"
    assert mu.cut_of(tmp_path / "cut" / "master.mp4") == tmp_path / "cut" / "cut.mp4"


def test_the_upscaled_picture_takes_the_judged_cuts_sound_unchanged(tmp_path):
    argv = mu.with_sound_of(tmp_path / "pic.mp4", tmp_path / "cut.mp4", tmp_path / "out.mp4")
    assert argv[argv.index("-map") + 1] == "0:v" and "1:a" in argv
    assert argv[argv.index("-c") + 1] == "copy" and "aac" not in argv


# ---- provenance: which cut a master was made from ------------------------------------------------

def made(tmp_path, master=b"upscaled", cut=b"judged cut", frames=(3444, 3444)):
    room = tmp_path / "cut"
    room.mkdir(exist_ok=True)
    (room / "master_r2v.mp4").write_bytes(master)
    (room / "cut_r2v.mp4").write_bytes(cut)
    mu.record_made(room / "master_r2v.mp4", room / "cut_r2v.mp4", "av3", *frames)
    return room / "master_r2v.mp4", room / "cut_r2v.mp4"


def test_a_master_names_the_cut_it_was_made_from(tmp_path):
    master, cut = made(tmp_path)
    assert mu.made_from(master) == yp.sha8(cut)


def test_another_file_at_the_masters_name_was_made_from_nothing(tmp_path):
    master, _cut = made(tmp_path)
    master.write_bytes(b"a master from somewhere else")
    assert mu.made_from(master) == ""


def test_a_master_that_lost_frames_was_not_made_from_the_cut(tmp_path):
    master, _cut = made(tmp_path, frames=(3440, 3444))
    assert mu.made_from(master) == ""


def test_the_record_keeps_every_master_it_made(tmp_path):
    master, cut = made(tmp_path)
    first = yp.sha8(master)
    made(tmp_path, master=b"upscaled again", cut=b"a recut")
    doc = json.loads((tmp_path / "cut" / mu.MADE).read_text(encoding="utf-8"))
    assert set(doc) == {first, yp.sha8(master)} and doc[first]["upscale"] == "av3"


# ---- assemble: the cut for the judges, then the one upscale ----------------------------------------

FIX = Path(__file__).parent / "fixtures" / "ep03_master_retake"


@pytest.fixture
def book(tmp_path, monkeypatch):
    """A book with ep03's plan, its judged cut and that cut's layout row; ffmpeg and the GPU faked."""
    import shutil
    from scripts.episode import assemble
    from studio import episode_home
    root = tmp_path / "book"
    home = episode_home.home(root, 3)
    (home / "cut").mkdir(parents=True)
    (home / "takes" / "work").mkdir(parents=True)
    shutil.copy(FIX / "plan.json", home / "plan.json")
    cut = home / "cut" / "cut_r2v.mp4"
    cut.write_bytes(b"the judged cut")
    assemble.record_layout(home / "cut", cut, main=3337, card=107, upscale="cut")
    monkeypatch.setattr(episode_home, "book_dir", lambda codex: root)
    monkeypatch.setattr(assemble, "video_frames", lambda p: 3444)
    monkeypatch.setattr(assemble.video_encoder, "encoder_for", lambda job: "cpu")
    monkeypatch.setattr(mu, "resolved", lambda env=None: (mu.CHOICES["av3"], ""))
    ran = []

    def upscale(listing, out, width, height, up, fps, **kw):
        ran.append({"listing": Path(listing).read_text(encoding="utf-8"), "size": (width, height), "up": up, **kw})
        Path(out).write_bytes(b"4x picture")
        return out

    def ffmpeg(argv, check=False, **kw):
        ran.append({"argv": argv})
        Path(argv[-1]).write_bytes(b"4x picture + the cut's sound")
    monkeypatch.setattr(mu, "master", upscale)
    monkeypatch.setattr(assemble.subprocess, "run", ffmpeg)
    return home, cut, ran


def test_the_upscale_reads_only_the_judged_cut_and_copies_its_sound(book):
    from scripts.episode import assemble
    home, cut, ran = book
    master = assemble.upscale_cut("20260827135504", 3, "r2v")
    assert master == home / "cut" / "master_r2v.mp4" and master.read_bytes() == b"4x picture + the cut's sound"
    assert ran[0]["listing"] == f"file '{cut.as_posix()}'\n" and ran[0]["up"] == mu.CHOICES["av3"]
    assert ran[0]["wrap"] is None, "the paste was baked into the judged cut; none after the upscale"
    assert ran[0]["cuts"] == [3337, 3444] and ran[0]["expected_frames"] == 3444
    assert ran[1]["argv"] == mu.with_sound_of(home / "takes" / "work" / "upscaled_picture.mp4", cut, ran[1]["argv"][-1])


def test_the_upscaled_master_is_kept_numbered_laid_out_and_traced_to_its_cut(book):
    from scripts.episode import assemble
    from studio import book_compilation as bc
    home, cut, _ran = book
    master = assemble.upscale_cut("20260827135504", 3, "r2v")
    assert (home / "cut" / "master_iter1.mp4").read_bytes() == master.read_bytes()
    row = json.loads((home / "cut" / bc.LAYOUT).read_text(encoding="utf-8"))[yp.sha8(master)]
    assert (row["main"], row["card"], row["upscale"]) == (3337, 107, "av3")
    assert mu.made_from(master) == yp.sha8(cut)


def test_no_judged_cut_is_no_upscale(book):
    from scripts.episode import assemble
    home, cut, ran = book
    cut.unlink()
    with pytest.raises(SystemExit, match="no judged cut"):
        assemble.upscale_cut("20260827135504", 3, "r2v")
    assert ran == []


def test_the_cut_report_feeds_the_cue_lifts_before_a_recut_at_cut():
    from scripts.episode import assemble
    assert assemble.report_engine("r2v", at_cut=True) == "r2v_cut"
    assert assemble.report_engine("r2v", at_cut=False) == "r2v"


# ---- QC on the judged cut ------------------------------------------------------------------------

EP03_CUT_MEANS = [1.136, 1.305, 0.937, 1.002, 0.597, 1.362, 1.001, 1.029, 0.846, 0.941, 1.112, 0.95, 1.318, 1.162,
                  1.079, 1.342, 1.149, 0.813, 1.002, 1.289, 0.927, 0.886, 0.603, 1.305, 0.5, 0.758, 0.861, 1.22]
"""MEASURED 2026-10-27: ep03's own work room through `at_cut_pass` (mixed + card + chip, 9 takes pasted,
CRF 8), every segment against its take by the edit gate: 0.50-1.36, offset 0, cuts 27/27, tail 3444/3444.
Under the unrecorded cap (1.0) 11 of 28 failed: a cut-scale QC needs its own cap."""


def test_qc_reads_the_judged_cut_under_its_own_cap():
    from studio import edit_gate
    cap = edit_gate.segment_cap("cut")
    assert all(m <= cap for m in EP03_CUT_MEANS) and cap < edit_gate.segment_cap("av3")
    assert edit_gate.hold_least("cut") == edit_gate.HOLD_FRAMES, "no temporal denoise at cut scale"


def test_qc_at_cut_measures_the_cut_and_writes_the_cut_report(tmp_path):
    from scripts.episode import qc
    from studio import episode_home
    assert qc.measured_path(tmp_path, 3, "r2v", at_cut=True) == episode_home.cut_dir(tmp_path, 3) / "cut_r2v.mp4"
    assert qc.measured_path(tmp_path, 3, "r2v", at_cut=False) == episode_home.master_path(tmp_path, 3, "r2v")
    assert qc.report_path(tmp_path, 3, "r2v", at_cut=True).name == "qc_r2v_cut.json"
    assert qc.report_path(tmp_path, 3, "r2v", at_cut=False).name == "qc_r2v.json"


def test_a_cut_report_names_no_upscale_even_beside_an_old_masters_record(tmp_path):
    from scripts.episode import qc
    (tmp_path / mu.USED_FILE).write_text(json.dumps({"asked": "av3", "used": "lanczos", "fallback": True}),
                                         encoding="utf-8")
    assert qc.upscale_for(tmp_path, at_cut=True)["recorded"] is False
    assert qc.upscale_for(tmp_path, at_cut=False)["used"] == "lanczos"
