"""Step 01's bind (build_pack.book_dir) and step 04's new-voice cast (cast_voices.book_dir) find the
SANDBOX book when VISURENA_LIBRARY names a sandbox, in a child process the way a drive runs them.

The first window's ep02 bind looked in the real library (`no book matching '99991021000000'`,
2026-10-21 17:45 PDT); e68e66c fixed build_pack, and the proof of it set `build_pack.LIBRARY` by
hand, so `settings.library_root()` under the variable was never run.  cast_voices spelled
`Path("library")` (cwd-relative), the same fault, on the path S0b and F14 take at step 04."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from studio.rehearsal import activate, fence, sandbox
from tests.proof_sandbox_fixture import env_for, tiny_sandbox

REPO = Path(__file__).resolve().parents[1]
CHILD = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
from scripts.refs import build_pack
from scripts.cast import cast_voices
codex = sys.argv[2]
print(json.dumps({"bind": str(build_pack.book_dir(codex)), "voices": str(cast_voices.book_dir(codex))}))
'''


def child_env(box: Path) -> dict:
    """The env a drive's step child carries: the library, the rehearsal boot first, the parent's verdict."""
    env = {k: v for k, v in os.environ.items() if k not in ("VISURENA_LIBRARY", "PYTHONPATH", "COMFY_URL")}
    return {**env, **env_for(box), "PYTHONPATH": str(fence.BOOT), activate.CLEARED: f"{int(time.time())}|{box}"}


def found(box: Path) -> dict:
    out = subprocess.run([sys.executable, "-c", CHILD, str(REPO), sandbox.book_name()[:14]], capture_output=True,
                         text=True, cwd=REPO, env=child_env(box), timeout=180)
    assert out.returncode == 0, out.stderr[-3000:]
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_both_steps_find_the_book_under_the_sandbox_library(tmp_path):
    box = tiny_sandbox(tmp_path, comfy_host="http://127.0.0.1:18188")
    got, book = found(box), box / "library" / sandbox.book_name()
    assert not (box / "tripwire.jsonl").exists()
    assert Path(got["bind"]).resolve() == book.resolve()
    assert Path(got["voices"]).resolve() == book.resolve()
