"""`uv add` strips the music and voice groups from the lock unless `uv sync
--all-groups` follows.  The lock must still name one package from every group."""
import re
from pathlib import Path

LOCK = Path(__file__).resolve().parents[1] / "uv.lock"
ONE_PER_GROUP = {"music": "beat-this", "voice": "resemblyzer",
                 "measures": ("facenet-pytorch", "easyocr")}


def _locked() -> set[str]:
    return set(re.findall(r'^name = "([^"]+)"', LOCK.read_text(encoding="utf-8"), re.M))


def test_the_lock_carries_every_dependency_group():
    names = _locked()
    for group, package in ONE_PER_GROUP.items():
        for one in ((package,) if isinstance(package, str) else package):
            assert one in names, f"uv.lock lost the {group} group: no {one}"
