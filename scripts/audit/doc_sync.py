#!/usr/bin/env python
"""Fix commits that changed runtime code and wrote nothing down -- an advisory report, never a hook.

    uv run python scripts/audit/doc_sync.py [<rev-range>]     # default: the last 40 commits

A commit that changes `studio/` or `scripts/episode/` is a fix commit.  It is documented when it
also changes the episode skill's GATES.md or LESSONS (index or archive), or when its message carries
the trailer `Docs: none (<reason>)`.  Every other fix commit is listed, newest first.  The report
always exits 0: a heuristic that blocked a commit would also block the autopilot's own (Jekyll
Kawajiri ep01 retro, P16: of the 12 commits that fixed ep01's failures on 2026-10-18, one touched
a skill doc).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ("studio/", "scripts/episode/")
SKILL = ".claude/skills/episode/"
DOCS = (SKILL + "GATES.md", SKILL + "LESSONS.md", SKILL + "LESSONS_ARCHIVE.md")
TRAILER = re.compile(r"^Docs: none \(\s*\S[^)]*\)\s*$", re.MULTILINE)
DEFAULT_RANGE = "HEAD~40..HEAD"


def touches_runtime(paths: list[str]) -> bool:
    return any(p.startswith(RUNTIME) for p in paths)


def touches_docs(paths: list[str]) -> bool:
    return any(p in DOCS for p in paths)


def excused(body: str) -> bool:
    """`Docs: none (<reason>)` on a line of its own; a bare `Docs: none` gives no reason."""
    return bool(TRAILER.search(body))


def undocumented(paths: list[str], body: str) -> bool:
    return touches_runtime(paths) and not touches_docs(paths) and not excused(body)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout


def files_of(sha: str) -> list[str]:
    return [l for l in git("show", "--name-only", "--format=", sha).splitlines() if l.strip()]


def body_of(sha: str) -> str:
    return git("show", "-s", "--format=%B", sha)


def listed(shas: list[str]) -> list[str]:
    """The shas, in the order given, whose commit is an undocumented fix commit."""
    return [sha for sha in shas if undocumented(files_of(sha), body_of(sha))]


def report_line(sha: str) -> str:
    return f"{sha} {git('show', '-s', '--format=%s', sha).strip()[:100]}"


def main(argv: list[str]) -> int:
    span = argv[1] if len(argv) > 1 else DEFAULT_RANGE
    shas = git("rev-list", "--abbrev-commit", span).split()
    rows = listed(shas)
    print(f"doc_sync {span}: {len(rows)} of {len(shas)} commits changed runtime code with no GATES/LESSONS "
          f"line and no 'Docs: none (reason)' trailer (advisory)")
    for sha in rows:
        print("  " + report_line(sha))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
