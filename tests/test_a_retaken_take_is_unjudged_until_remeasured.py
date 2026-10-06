"""A retaken T??.mp4 must not outlive its verdicts: qc found T00, T14 and
T18-T21 'unjudged' -- mp4 newer than its .dq.json/.content.json -- because
step 09's judged() checked existence only.  A take counts as judged only when
the dq verdict names EXACTLY these bytes (take_sha8) and the content verdict
is no older than the take."""
from __future__ import annotations

import hashlib
import json
import os
import time

from scripts.episode import step_09_shoot as shoot


def room(tmp_path, body=b"take-bytes"):
    t = tmp_path / "T03.mp4"
    t.write_bytes(body)
    sha8 = hashlib.sha256(body).hexdigest()[:8]
    (tmp_path / "T03.dq.json").write_text(json.dumps({"take_sha8": sha8}), encoding="utf-8")
    (tmp_path / "T03.content.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    return t


def test_matching_sha_and_fresh_content_is_judged(tmp_path):
    t = room(tmp_path)
    assert shoot.judged([t]) is True


def test_changed_bytes_unjudge_the_take(tmp_path):
    t = room(tmp_path)
    t.write_bytes(b"RETAKEN bytes")                       # sha moves, dq verdict is stale
    now = time.time()
    os.utime(t.with_suffix(".content.json"), (now + 5, now + 5))
    assert shoot.dq_current(t) is False
    assert shoot.judged([t]) is False


def test_a_content_verdict_older_than_the_take_is_stale(tmp_path):
    t = room(tmp_path)
    old = time.time() - 600
    os.utime(t.with_suffix(".content.json"), (old, old))
    assert shoot.content_current(t) is False
    assert shoot.judged([t]) is False


def test_a_missing_verdict_is_still_unjudged(tmp_path):
    t = room(tmp_path)
    t.with_suffix(".dq.json").unlink()
    assert shoot.judged([t]) is False
    room(tmp_path).with_suffix(".content.json").unlink()
    assert shoot.judged([t]) is False


def test_the_sha_rule_matches_take_dqs_own(tmp_path):
    """step_09 inlines the sha8 (take_dq's module-level model loads are heavy);
    the two spellings must never drift."""
    t = tmp_path / "x.bin"
    t.write_bytes(b"the same bytes")
    assert shoot.sha8(t) == hashlib.sha256(b"the same bytes").hexdigest()[:8]
