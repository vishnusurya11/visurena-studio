"""take_dq cache (2026-09-29): 8 full 30-take passes cost 2.1 h on ep14 because
the gate decoded every take on every resume.  A T<NN>.dq.json that names the
kept file's bytes (take_sha8) is the measure of those bytes; the pass skips it.
An --attempts round still re-measures (it settles between attempt files)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))

import take_dq  # noqa: E402


def test_a_matching_sha_is_a_cache_hit_and_anything_else_is_not(tmp_path):
    take = tmp_path / "T03.mp4"
    take.write_bytes(b"the very bytes")
    sha = take_dq.take_sha8(take)
    assert len(sha) == 8
    report = {"take_sha8": sha, "score": 85.0}
    (tmp_path / "T03.dq.json").write_text(json.dumps(report), encoding="utf-8")
    assert take_dq.cached(tmp_path, 3, take) == report
    take.write_bytes(b"other bytes")
    assert take_dq.cached(tmp_path, 3, take) is None
    assert take_dq.cached(tmp_path, 4, tmp_path / "T04.mp4") is None


def test_a_verdict_naming_the_bytes_is_current_whatever_the_clocks_say(tmp_path):
    import hashlib
    import os
    from studio import judged
    take = tmp_path / "T03.mp4"
    take.write_bytes(b"the very bytes")
    sha = hashlib.sha256(b"the very bytes").hexdigest()[:8]
    (tmp_path / "T03.dq.json").write_text(json.dumps({"take_sha8": sha}), encoding="utf-8")
    (tmp_path / "T03.content.json").write_text(json.dumps({"faults": []}), encoding="utf-8")
    (tmp_path / "shots.json").write_text(json.dumps([{"index": 3}]), encoding="utf-8")
    late = os.path.getmtime(take) + 60
    os.utime(take, (late, late))                          # the take LOOKS newer than both reports
    assert judged.unjudged_takes(tmp_path, kinds=("dq",)) == []
    assert judged.unjudged_takes(tmp_path, kinds=("dq", "content")) == ["T03"]   # content has no sha
