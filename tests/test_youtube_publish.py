"""The upload spec, its gates and its ledger.

No test here reaches the network: the upload call is injected, exactly as
`cast_bust.render` is.  The project rule is that no test may spend a credit, and
an upload is worse than a spend -- it is public and it is not undoable.
"""
import json

import pytest

from studio import youtube_publish as yp

TITLE = '"You Have Been in Afghanistan, I Perceive" — A Study in Scarlet Ep.1'


def test_the_spec_carries_what_the_api_needs():
    got = yp.spec(TITLE, "a description", ["sherlock holmes"], synthetic=True)
    assert got["snippet"]["title"] == TITLE
    assert got["snippet"]["categoryId"] == yp.CATEGORY_FILM
    assert got["status"]["privacyStatus"] == "private"
    assert got["status"]["containsSyntheticMedia"] is True
    assert got["status"]["selfDeclaredMadeForKids"] is False


def test_synthetic_has_no_default_and_must_be_stated():
    """The AI disclosure is a declaration to the platform, not copy."""
    with pytest.raises(TypeError):
        yp.spec(TITLE, "d", [], privacy="private")


def test_a_title_over_the_wall_is_refused():
    with pytest.raises(ValueError, match="100"):
        yp.spec("x" * 101, "d", [], synthetic=True)


def test_an_empty_title_is_refused():
    with pytest.raises(ValueError, match="needs a title"):
        yp.spec("   ", "d", [], synthetic=True)


def test_angle_brackets_are_refused_because_the_api_refuses_them():
    with pytest.raises(ValueError, match="angle brackets"):
        yp.spec("Watson <the doctor>", "d", [], synthetic=True)


def test_a_description_over_the_wall_is_refused():
    with pytest.raises(ValueError, match="5000"):
        yp.spec(TITLE, "x" * 5001, [], synthetic=True)


def test_tags_over_the_wall_are_refused():
    with pytest.raises(ValueError, match="500"):
        yp.spec(TITLE, "d", ["x" * 60] * 10, synthetic=True)


def test_an_unknown_privacy_is_refused():
    with pytest.raises(ValueError, match="privacy"):
        yp.spec(TITLE, "d", [], synthetic=True, privacy="secret")


# ---- gates -----------------------------------------------------------------

CLEAN = dict(qc={"passed": True, "sha8": "abc12345"}, dq_failed=[], privacy="private",
             watched="abc12345", digest="abc12345", already=None)
"""A clean episode's qc report names the very bytes being uploaded.

`sha8` joined this fixture on 2026-09-13, after ep03 went public against a report
written about the PREVIOUS cut. See `test_qc_measured_this_cut.py`."""


def test_a_clean_episode_has_no_refusals():
    assert yp.refusals(**CLEAN) == []


def test_a_failed_qc_refuses():
    assert any("passed:false" in r for r in yp.refusals(**{**CLEAN, "qc": {"passed": False}}))


def test_failed_takes_refuse_even_though_qc_only_warns():
    """Episode 2 today: the cut is sound and 14 of 19 takes are not."""
    out = yp.refusals(**{**CLEAN, "dq_failed": ["T03", "T05", "T08", "T10", "T12"]})
    assert any("5 takes failed DQ" in r for r in out)


def test_an_unwatched_master_refuses_when_it_would_be_seen():
    out = yp.refusals(**{**CLEAN, "watched": "", "privacy": "unlisted", "audited": True})
    assert any("watch the file" in r for r in out)


def test_a_watched_hash_for_a_different_cut_refuses():
    out = yp.refusals(**{**CLEAN, "watched": "deadbeef", "privacy": "public", "audited": True})
    assert any("does not match" in r for r in out)


def test_anything_but_private_refuses_while_unaudited():
    assert any("forces private" in r for r in yp.refusals(**{**CLEAN, "privacy": "public"}))


def test_an_already_uploaded_master_refuses():
    out = yp.refusals(**{**CLEAN, "already": {"video_id": "abc", "at": "2026-09-12"}})
    assert any("already uploaded as abc" in r for r in out)


# ---- ledger ----------------------------------------------------------------

def test_the_key_changes_with_the_cut_but_not_with_a_rerun():
    a = yp.upload_key("book", 1, "aaaaaaaa")
    assert a == yp.upload_key("book", 1, "aaaaaaaa")
    assert a != yp.upload_key("book", 1, "bbbbbbbb")
    assert a != yp.upload_key("book", 2, "aaaaaaaa")


def test_the_ledger_round_trips(tmp_path):
    key = yp.upload_key("book", 1, "aaaaaaaa")
    assert yp.uploaded(tmp_path, key) is None
    yp.record(tmp_path, {"key": key, "video_id": "XYZ", "at": "2026-09-12"})
    assert yp.uploaded(tmp_path, key)["video_id"] == "XYZ"


def test_the_ledger_appends_rather_than_replaces(tmp_path):
    yp.record(tmp_path, {"key": "a", "video_id": "1"})
    yp.record(tmp_path, {"key": "b", "video_id": "2"})
    rows = [json.loads(l) for l in (tmp_path / yp.LEDGER).read_text(encoding="utf-8").splitlines() if l]
    assert [r["video_id"] for r in rows] == ["1", "2"]


def test_sha8_is_stable_and_content_addressed(tmp_path):
    a, b = tmp_path / "a.mp4", tmp_path / "b.mp4"
    a.write_bytes(b"same"); b.write_bytes(b"same")
    assert yp.sha8(a) == yp.sha8(b) and len(yp.sha8(a)) == 8
    b.write_bytes(b"different")
    assert yp.sha8(a) != yp.sha8(b)


# ---- automation: the gate scales with irreversibility ----------------------

def test_a_private_upload_needs_no_human_because_it_publishes_nothing():
    """A private video is invisible and deletable, so the machine gates suffice
    and the chain can end in an upload with nobody watching. Requiring a human
    here would mean the pipeline could never run unattended, which is how a
    safety gate becomes a switched-off safety gate."""
    assert yp.refusals(**{**CLEAN, "watched": "", "privacy": "private"}) == []


def test_going_public_still_needs_a_human_who_watched_it():
    """This is the irreversible act: seen, indexed and archived in seconds."""
    out = yp.refusals(**{**CLEAN, "watched": "", "privacy": "public", "audited": True})
    assert any("watch the file" in r for r in out)


def test_unlisted_needs_a_human_too():
    out = yp.refusals(**{**CLEAN, "watched": "", "privacy": "unlisted", "audited": True})
    assert any("watch the file" in r for r in out)


def test_public_is_refused_while_the_project_is_unaudited():
    out = yp.refusals(**{**CLEAN, "privacy": "public", "audited": False})
    assert any("forces private" in r for r in out)


def test_public_is_allowed_once_audited_and_watched():
    assert yp.refusals(**{**CLEAN, "privacy": "public", "audited": True}) == []


def test_the_machine_gates_still_bite_when_unattended():
    """Unattended does not mean ungated: a failed QC or a failed take still stops
    a private upload, because the point is to never ship a known fault."""
    assert yp.refusals(**{**CLEAN, "watched": "", "qc": {"passed": False}})
    assert yp.refusals(**{**CLEAN, "watched": "", "dq_failed": ["T03"]})
    assert yp.refusals(**{**CLEAN, "watched": "", "already": {"video_id": "x", "at": "y"}})
