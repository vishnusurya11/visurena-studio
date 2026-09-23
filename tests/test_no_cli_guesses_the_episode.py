"""No command under scripts/episode guesses which episode it writes.

Guard for audit item 7: every CLI that took an episode number fell back to 1
when it was missing. They all go through `episode_home.episode_arg` now, and
this keeps a new one from growing the old default back.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUESS = re.compile(r"(?:argv|args)\b.*\belse\s+1\b")


def test_no_episode_cli_falls_back_to_episode_one():
    hits = []
    for path in sorted((ROOT / "scripts" / "episode").glob("*.py")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if GUESS.search(line):
                hits.append(f"{path.name}:{n}: {line.strip()}")
    assert not hits, "a CLI guesses the episode:\n" + "\n".join(hits)
