"""G-EYE: `--watched=<sha8>` is a claim, and the rubric on disk is its evidence.

Episode 9 passed 28/28 takes at 100.0 and looked worse than episodes 4-7 on
shadow, board fidelity, repetition and story (`docs/analysis/ep08_ep09_why_worse.md`).
The publish ladder's `--watched` flag was satisfied by an agent that had looked
at six frames.  So the flag is accepted only against `review/eye_<sha8>.json`:
every rubric field answered, no `n` without a `waived_because`, the sha the
rubric describes equal to the sha being uploaded.

No test here spends, renders on a GPU or reaches the network.  The one video is
two seconds of ffmpeg's own test pattern.
"""
import json
import subprocess
from pathlib import Path

import pytest

from scripts.episode import eye_review as er
from scripts.publish import youtube_upload
from studio import episode_home, youtube_publish as yp

DIGEST = "abc12345"


def filled(answers: dict[str, str] | None = None, *, notes: str = "watched it end to end",
           digest: str = DIGEST, waived: dict[str, str] | None = None) -> dict:
    """A rubric a person filled: every field `y` unless `answers` says otherwise."""
    rubric = er.blank_rubric(digest, "master_r2v.mp4", f"contact_{digest}.png", 5.0, 24)
    for field, _q in er.RUBRIC:
        rubric["rubric"][field]["answer"] = (answers or {}).get(field, "y")
        rubric["rubric"][field]["waived_because"] = (waived or {}).get(field, "")
    rubric["notes"] = notes
    return rubric


# ---- the builder -------------------------------------------------------------

@pytest.fixture(scope="module")
def clip(tmp_path_factory) -> Path:
    """Two seconds of testsrc, 128x128 at 24 fps -- the only video these tests touch."""
    out = tmp_path_factory.mktemp("clip") / "master_r2v.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", "testsrc=duration=2:size=128x128:rate=24",
                    "-pix_fmt", "yuv420p", str(out)], check=True)
    return out


def test_the_length_is_read_off_ffmpeg_without_ffprobe(clip):
    assert er.seconds_of(clip) == pytest.approx(2.0, abs=0.1)


def test_a_frame_every_five_seconds_while_the_grid_holds_them():
    assert er.sample_times(120.0) == [i * 5.0 for i in range(24)]


def test_a_long_master_widens_the_step_to_fit_the_grid():
    """180 s is 36 frames at 5 s; the 5x6 grid holds 30, so the step becomes 6 s."""
    times = er.sample_times(180.0)
    assert len(times) == 30 and times[1] == 6.0 and times[-1] < 180.0


def test_the_builder_writes_the_contact_sheet_and_a_blank_rubric(clip, tmp_path):
    from PIL import Image

    contact, rubric = er.build(tmp_path, clip, DIGEST, every=0.5)
    assert contact == tmp_path / "review" / f"contact_{DIGEST}.png"
    assert rubric == tmp_path / "review" / f"eye_{DIGEST}.json"
    assert Image.open(contact).size == (er.COLS * er.CELL, er.ROWS * er.CELL)
    got = json.loads(rubric.read_text(encoding="utf-8"))
    assert got["sha8"] == DIGEST and got["frames"] == 4
    assert all(got["rubric"][f]["answer"] == "" for f, _q in er.RUBRIC)
    assert set(got["rubric"]) == {"shadow", "faces", "board", "repeats", "story"}


def test_rebuilding_never_blanks_a_filled_rubric(clip, tmp_path):
    _c, path = er.build(tmp_path, clip, DIGEST, every=0.5)
    path.write_text(json.dumps(filled()), encoding="utf-8")
    er.build(tmp_path, clip, DIGEST, every=0.5)
    assert json.loads(path.read_text(encoding="utf-8"))["rubric"]["shadow"]["answer"] == "y"


# ---- the acceptance ------------------------------------------------------------

PATH = Path("review/eye_abc12345.json")


def test_a_blank_rubric_refuses_naming_every_field():
    blank = er.blank_rubric(DIGEST, "m", "c", 5.0, 24)
    out = er.refusals(blank, DIGEST, PATH)
    assert out and "unanswered" in out[0]
    for field in ("shadow", "faces", "board", "repeats", "story", "notes"):
        assert field in out[0]


def test_one_unanswered_field_refuses():
    out = er.refusals(filled({"board": ""}), DIGEST, PATH)
    assert len(out) == 1 and "board" in out[0] and "unanswered" in out[0]


def test_empty_notes_refuse():
    """A reviewer who watched it has something to say."""
    out = er.refusals(filled(notes="   "), DIGEST, PATH)
    assert out and "notes" in out[0]


def test_all_y_accepts():
    assert er.refusals(filled(), DIGEST, PATH) == []


def test_an_n_without_a_waiver_refuses():
    out = er.refusals(filled({"shadow": "n"}), DIGEST, PATH)
    assert len(out) == 1 and "shadow" in out[0] and "waived_because" in out[0]


def test_an_n_with_a_waiver_accepts_and_the_waiver_is_recorded():
    rubric = filled({"shadow": "n"}, waived={"shadow": "noon on the alkali plain; owner accepts"})
    assert er.refusals(rubric, DIGEST, PATH) == []
    assert er.waivers(rubric) == {"shadow": "noon on the alkali plain; owner accepts"}


def test_a_waiver_beside_a_y_is_not_a_waiver():
    assert er.waivers(filled(waived={"shadow": "stray text"})) == {}


def test_a_rubric_for_a_different_cut_refuses():
    """The ep03 shape again: reviewed f5ddd2a3, uploading f8bf7814."""
    out = er.refusals(filled(digest="f5ddd2a3"), "f8bf7814", PATH)
    assert out and "f5ddd2a3" in out[0] and "f8bf7814" in out[0]


def test_answers_are_read_case_and_space_insensitively():
    assert er.refusals(filled({"story": " Y "}), DIGEST, PATH) == []


def test_a_missing_rubric_refuses_with_the_path_to_fill(tmp_path):
    stops, rubric = er.verdict(tmp_path, DIGEST, DIGEST)
    assert rubric == {} and len(stops) == 1
    assert str(tmp_path / "review" / f"eye_{DIGEST}.json") in stops[0]


def test_a_watched_sha_that_is_not_this_cut_refuses(tmp_path):
    """--watched=deadbeef against a master at abc12345: no eye_deadbeef.json,
    and the refusal names the file for THIS cut."""
    episode_home.write_json(er.rubric_path(tmp_path, DIGEST), filled())
    stops, _r = er.verdict(tmp_path, "deadbeef", DIGEST)
    assert stops and f"eye_{DIGEST}.json" in stops[0]


# ---- the publisher's acceptance path ------------------------------------------

def test_no_flag_makes_no_claim(tmp_path):
    assert youtube_upload.eye_stops(tmp_path, "", DIGEST) == ([], {})


def test_the_flag_without_the_file_is_refused(tmp_path):
    stops, eye = youtube_upload.eye_stops(tmp_path, DIGEST, DIGEST)
    assert stops and eye == {} and "eye_review.py" in stops[0]


def test_the_flag_with_a_filled_rubric_is_accepted_and_ledgered(tmp_path):
    rubric = filled({"repeats": "n"}, waived={"repeats": "the wide is the same room twice, on purpose"})
    rubric["reviewed_by"] = "owner"
    episode_home.write_json(er.rubric_path(tmp_path, DIGEST), rubric)
    stops, eye = youtube_upload.eye_stops(tmp_path, DIGEST, DIGEST)
    assert stops == []
    assert eye == {"sha8": DIGEST, "reviewed_by": "owner",
                   "waived": {"repeats": "the wide is the same room twice, on purpose"},
                   "flags": {}}


def library(tmp_path: Path, clip: Path) -> tuple[Path, str]:
    """A book with one episode whose QC passed on the very bytes on disk."""
    book = tmp_path / "20260101000000_book"
    home = book / "episodes" / "ep01"
    (home / "cut").mkdir(parents=True)
    master = home / "cut" / "master_r2v.mp4"
    master.write_bytes(clip.read_bytes())
    digest = yp.sha8(master)
    (home / "qc_r2v.json").write_text(json.dumps({"passed": True, "sha8": digest}), encoding="utf-8")
    (home / "youtube.json").write_text(json.dumps({"title": "Ep 1", "description": "d",
                                                  "synthetic": True}), encoding="utf-8")
    # A REAL EPISODE HAS A TAKES ROOM: the upload refuses one with no record of
    # which takes exist (audit 2026-09-22, item 6), so this one has a judged take.
    room = home / "takes" / "r2v"
    room.mkdir(parents=True)
    (room / "shots.json").write_text(json.dumps([{"index": 0}]), encoding="utf-8")
    (room / "T00.mp4").write_bytes(b"mp4")
    for kind in ("dq", "content"):
        (room / f"T00.{kind}.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    return book, digest


def test_the_dry_run_refuses_watched_until_the_rubric_is_filled(tmp_path, clip, monkeypatch, capsys):
    book, digest = library(tmp_path, clip)
    monkeypatch.setattr(episode_home, "book_dir", lambda _id: book)
    argv = ["youtube_upload.py", book.name, "1", "--dry-run", f"--watched={digest}"]
    with pytest.raises(SystemExit):
        youtube_upload.main(argv, send=lambda *a: pytest.fail("never reached"))
    assert f"eye_{digest}.json" in capsys.readouterr().out

    er.build(book / "episodes" / "ep01", book / "episodes" / "ep01" / "cut" / "master_r2v.mp4",
             digest, every=0.5)
    path = er.rubric_path(book / "episodes" / "ep01", digest)
    path.write_text(json.dumps(filled(digest=digest)), encoding="utf-8")
    # AND THE DIRECTOR SIGNED THIS CUT (publish lock, root cause 2026-09-26)
    (book / "episodes" / "ep01" / "review" / "director_signoff.md").write_text(
        f"# ep01 {digest}\n\n## Watched\nfull size, with sound\n\n## Take strips\nall read\n\n"
        f"## Coverage\nto the last paragraph\n\n## Flags\nnone open\n", encoding="utf-8")
    youtube_upload.main(argv, send=lambda *a: pytest.fail("never reached"))
    assert "all gates pass" in capsys.readouterr().out


def test_an_override_cannot_stand_in_for_the_rubric(tmp_path, clip, monkeypatch, capsys):
    """--override waives the two QUALITY gates; the eye review IS the human."""
    book, digest = library(tmp_path, clip)
    monkeypatch.setattr(episode_home, "book_dir", lambda _id: book)
    argv = ["youtube_upload.py", book.name, "1", "--dry-run", f"--watched={digest}",
            "--override=owner said ship it"]
    with pytest.raises(SystemExit):
        youtube_upload.main(argv, send=lambda *a: pytest.fail("never reached"))
    assert f"eye_{digest}.json" in capsys.readouterr().out
