"""assemble.kept_of reads the settled mark (contract K5) per take: one narration still in the
verdict no longer hides every other kept take (the latent ladder_kept bug, Jekyll ep01 P09)."""
from __future__ import annotations

import json

from scripts.episode import assemble
from studio import eye_verdict


def fault(where, settled=None, kind="warp"):
    ev = {"settled": settled} if settled else {}
    return {"kind": kind, "where": where, "evidence": ev, "severity": "normal", "note": f"{kind} {where}"}


def sign(folder, faults, names=("T00", "T01", "T02")):
    paths = []
    for n in names:
        if not (folder / f"{n}.mp4").exists():
            (folder / f"{n}.mp4").write_bytes(n.encode())
        paths.append(folder / f"{n}.mp4")
    sha8 = eye_verdict.fingerprint(paths)
    doc = {"sha8": sha8, "verdict": "flagged", "files": [p.name for p in paths], "faults": faults}
    target = eye_verdict.path(folder, sha8)
    target.write_text(json.dumps(doc), encoding="utf-8")
    return target


def test_a_still_does_not_hide_a_kept_take(tmp_path):
    sign(tmp_path, [fault("T00", "still", "content"), fault("T01", "keep_best"), fault("T02", "high")])
    assert set(assemble.kept_of(tmp_path)) == {1, 2}


def test_the_kept_take_carries_its_faults(tmp_path):
    sign(tmp_path, [fault("T01", "keep_best"), fault("T01", "high", "gait")])
    assert [f["kind"] for f in assemble.kept_of(tmp_path)[1]] == ["warp", "gait"]


def test_ladder_kept_is_gone():
    assert not hasattr(assemble, "ladder_kept")
