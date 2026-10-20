"""The mandatory read fits a budget, and no anchor the code cites is lost (P16, decision D17).

At HEAD 6572728 the episode skill's mandatory read was about 236 KB (SKILL 49 + GATES 61 + LESSONS
126).  LESSONS.md becomes an index of 8 KB or less, brick first; the full text moves unchanged to
LESSONS_ARCHIVE.md, which keeps every heading and every sha anchor code cites ("LESSONS 3ae4584").

Ratchet (deadline retro 2026-10-20, item 14): the read set stood at 133,112 bytes of a 133,120 cap, so
the live-run and repair protocol MOVED to OPERATOR.md (read when you act, not on every read) and the cap
came down to what is left. No file of the skill holds a CRLF: `Path.write_text` on Windows writes one per
line, and once added 677 bytes to GATES.md; `.gitattributes` keeps the skill and the docs LF on checkout.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".claude" / "skills" / "episode"
INDEX, ARCHIVE = SKILL_DIR / "LESSONS.md", SKILL_DIR / "LESSONS_ARCHIVE.md"
HEADINGS = ROOT / "tests" / "fixtures" / "ep01_replay" / "P16" / "lessons_headings.json"
CITE = re.compile(r"LESSONS[^\n]{0,12}?\b([0-9a-f]{7})\b")
INDEX_MAX, READ_MAX, OPERATOR_MAX = 8 * 1024, 128 * 1024, 14 * 1024
OPERATOR = SKILL_DIR / "OPERATOR.md"
CRLF = bytes([13, 10])


def size(path: Path) -> int:
    return len(path.read_bytes())


def cited_shas() -> set[str]:
    files = [p for d in ("studio", "tests", "scripts") for p in (ROOT / d).rglob("*.py")]
    return {m for p in files for m in CITE.findall(p.read_text(encoding="utf-8", errors="ignore"))}


def test_the_index_is_eight_kb_or_less():
    assert size(INDEX) <= INDEX_MAX


def test_skill_gates_and_index_read_in_the_ratcheted_budget():
    assert size(SKILL_DIR / "SKILL.md") + size(SKILL_DIR / "GATES.md") + size(INDEX) <= READ_MAX


def test_every_sha_the_code_cites_resolves_in_the_archive():
    shas = cited_shas()
    assert "3ae4584" in shas
    assert [s for s in sorted(shas) if s not in ARCHIVE.read_text(encoding="utf-8")] == []


def test_the_archive_keeps_every_heading_of_the_old_lessons():
    archive = ARCHIVE.read_text(encoding="utf-8").splitlines()
    old = json.loads(HEADINGS.read_text(encoding="utf-8"))["headings"]
    assert [h for h in old if h not in archive] == []


def test_the_index_names_every_archive_section():
    index = INDEX.read_text(encoding="utf-8")
    names = [l[3:].split(" (")[0] for l in ARCHIVE.read_text(encoding="utf-8").splitlines() if l.startswith("## ")]
    assert [n for n in names if n not in index] == []


def test_the_index_leads_with_the_bricks():
    head = INDEX.read_text(encoding="utf-8").split("\n## ", 2)
    assert head[1].startswith("The bricks")


def test_the_operator_page_is_its_own_small_read():
    assert 0 < size(OPERATOR) <= OPERATOR_MAX


def test_no_file_of_the_skill_holds_a_crlf():
    assert [p.name for p in sorted(SKILL_DIR.iterdir()) if CRLF in p.read_bytes()] == []


def attr(rel: str, name: str) -> str:
    out = subprocess.run(["git", "check-attr", name, "--", rel], cwd=ROOT, capture_output=True, text=True, check=True)
    return out.stdout.strip().rsplit(": ", 1)[-1]


def test_the_skill_and_the_docs_check_out_lf_and_a_picture_stays_binary():
    for rel in (".claude/skills/episode/SKILL.md", ".claude/skills/episode/OPERATOR.md", "docs/DECISIONS.md"):
        assert attr(rel, "eol") == "lf", rel
    assert attr("docs/images/any.png", "text") == "auto"
