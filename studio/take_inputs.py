"""G-TAKE-INPUTS: was this take rendered from the pictures the plan stages NOW?

Jekyll HEL ep01 iter4 (audit 2026-10-15, docs/audit/2026-10-15_jekyll_ep01_ref_audit/
01_staged_refs.md): `T06.graph.json` staged the SUPERSEDED lace-bonnet girl sheet
(`sheet_front_b54219a4.png`) and a panel no longer on disk.  `take_dq --attempts`
kept that roll (95) over four rolls of the current sheet (10-40), because the rank
was (passed, score) and nothing asked whether the winner's inputs were still the
episode's.  The master shipped it.  A score ranks renders of the same inputs,
never across a changed input.

The record is already on disk: every LoadImage name in `T<NN>.graph.json` is
content-addressed (`<stem>_<md5[:8]><suffix>`, `studio.comfy.staged_name`), so the
comparison with `{staged_name(p) for p in card_pictures(card)}` is exact and
needs no GPU.  A stale name whose md5[:8] matches a file in its picture's own
`superseded/` room is named so.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

from studio import take_currency

ROW = "inputs"
SUPERSEDED = "superseded"


@dataclass
class Inputs:
    """One take's verdict: current, and if not, which names say why."""
    current: bool
    staged: list[str] = field(default_factory=list)
    stale: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    superseded: list[str] = field(default_factory=list)
    unknown_provenance: bool = False
    reworded: bool = False
    """Rendered from other words than the card's now (Jekyll ep01 iter7 T06: the ranker kept the iter6
    render, made before the plan's cure, over the cured one)."""

    def said(self) -> str:
        """`current`, or the reasons: unknown provenance, older words, stale names, missing names."""
        if self.current:
            return "current"
        parts = ["unknown provenance (no graph of its own)"] if self.unknown_provenance else []
        if self.reworded:
            parts.append("rendered from older words than the card's")
        if self.stale:
            parts.append("stale " + ", ".join(n + (" (superseded)" if n in self.superseded else "")
                                              for n in self.stale))
        if self.missing:
            parts.append("missing " + ", ".join(self.missing))
        return "; ".join(parts) or "not current"


def md5_8(path: Path) -> str:
    """The content suffix `staged_name` gives a file."""
    return hashlib.md5(Path(path).read_bytes()).hexdigest()[:8]


def digest_of(name: str) -> str:
    """The md5[:8] a staged name carries: `sheet_front_b54219a4.png` -> `b54219a4`."""
    return Path(name).stem.rsplit("_", 1)[-1]


def wanted_names(pictures: list) -> set[str]:
    """What a render of these pictures stages NOW.  A picture not on disk is
    wanted under a name no graph can hold, so it always reads missing."""
    from studio.comfy import staged_name
    return {staged_name(p) if Path(p).is_file() else f"{Path(p).name} (not on disk)" for p in pictures}


def superseded_by_digest(pictures: list) -> dict[str, Path]:
    """md5[:8] -> file, over each current picture's own `superseded/` room only
    (refs/characters/<id>/superseded/): a few files, never a tree walk."""
    out: dict[str, Path] = {}
    for room in {Path(p).parent / SUPERSEDED for p in pictures}:
        if room.is_dir():
            out.update({md5_8(f): f for f in room.iterdir() if f.is_file()})
    return out


def check(take: Path, pictures: list, built: str | None = None) -> Inputs:
    """G-TAKE-INPUTS for one take file against the CURRENT card pictures.  With the card's words
    (`built`), `reworded` says whether the take rendered from other words -- a report row only:
    `current` stays the pictures' verdict (craft ruling A2, advisory under freeze)."""
    staged = take_currency.staged_images(take)
    want = wanted_names(pictures)
    stale, missing = sorted(staged - want), sorted(want - staged)
    unknown = take_currency.provenance_unknown(take)
    old = superseded_by_digest(pictures) if stale else {}
    return Inputs(current=not (unknown or stale or missing), staged=sorted(staged), stale=stale,
                  missing=missing, superseded=[n for n in stale if digest_of(n) in old],
                  unknown_provenance=unknown, reworded=built is not None and reworded_from(take, built))


def reworded_from(take: Path, built: str) -> bool:
    """The take's own graph recorded other words than `built` (whitespace is not a word)."""
    said = take_currency.recorded_prompt(take)
    return said is not None and said.strip() != (built or "").strip()


def built_prompts(take_dir: Path) -> dict[int, str]:
    """{take: the card's words now}, off the last build's `prompts.json`; {} when there is none."""
    path = Path(take_dir) / "prompts.json"
    if not path.is_file():
        return {}
    import json
    return {int(c["index"]): c.get("prompt") or "" for c in json.loads(path.read_text(encoding="utf-8"))}


# --- stale words: a kept take's RECORDED prompt under today's HARD rules (craft ruling A2) -----------

UNRECORDED = ("l16_dialogue_tail",)
"""HARD rules that read what a recorded prompt does not keep: the second each spoken line ends."""
SPOKEN = re.compile(r"<d>\[English\] (.*?)</d>", re.S)


def night_of(setup) -> bool:
    """Whether a setup (a plan dict or a Setup) is at night: `house_style.is_night`'s rule."""
    from types import SimpleNamespace
    from studio import house_style
    return house_style.is_night(SimpleNamespace(**setup) if isinstance(setup, dict) else setup)


def recorded_facts(said: str, night: bool = False, frames: int | None = None) -> dict:
    """The lint facts a recorded prompt carries itself: the cast rows it defined, the lines it
    spoke (so a spoken "walked" is not a walk), plus the setup's night and the take's frames."""
    from studio import episode_ref_official as ro
    rows = ro.sections(said).get("subject_definitions", "")
    return {"night": bool(night), "frames": frames, "cast_rows": rows.lower(),
            "lines": [{"text": t} for t in SPOKEN.findall(said)]}


def stale_words(take: Path, night: bool = False, frames: int | None = None) -> list[str]:
    """Today's HARD lint faults on the words this take RENDERED from; none without a graph."""
    from studio import episode_ref_official as ro
    said = take_currency.recorded_prompt(take)
    if said is None:
        return []
    facts = recorded_facts(said, night, frames)
    return [f for rule in ro.RULES if rule.__name__ not in UNRECORDED for f in rule(said, facts)]


def words_line(reworded: int, failing: int, of: int) -> str:
    """`words: 27 of 28 rendered from older words; 8 fail a current HARD rule (advisory under freeze)`."""
    return (f"words: {reworded} of {of} rendered from older words; {failing} fail a current HARD rule "
            f"(advisory under freeze)")


def words(audited: dict[int, Inputs], records: list[dict], book: Path, night: dict[int, bool]) -> dict:
    """The QC provenance block: which audited takes rendered from older words, and which recorded
    prompts fail a HARD rule today.  It never refuses and never re-renders: the owner sees the count."""
    rows = {int(r["index"]): r for r in records}
    fail = {f"T{i:02d}": bad for i in sorted(audited)
            if (bad := stale_words(Path(book) / rows[i]["rel_path"], night.get(i, False),
                                   int(rows[i].get("frames") or 0) or None))}
    reworded = [f"T{i:02d}" for i, v in sorted(audited.items()) if v.reworded]
    return {"of": len(audited), "reworded": reworded, "fail": fail,
            "line": words_line(len(reworded), len(fail), len(audited))}


def card_pictures(rec: dict, book: Path, number: int) -> list[Path]:
    """The pictures a take record's card stages now (takes_r2v.card_pictures:
    the refs from `takes/r2v/shots.json`, then any anchor cells)."""
    from scripts.episode import takes_r2v
    return takes_r2v.card_pictures(rec, Path(book), number)


def audit(records: list[dict], book: Path, number: int, skip=(), built: dict[int, str] | None = None
          ) -> dict[int, Inputs]:
    """Every take record that has a card of references (r2v), except `skip`
    (takes the cut holds as a still, so no frame of theirs is in the master).  With the cards'
    words (`built_prompts`), each verdict also says whether its take was reworded since."""
    return {int(r["index"]): check(Path(book) / r["rel_path"], card_pictures(r, book, number),
                                   (built or {}).get(int(r["index"])))
            for r in records if "refs" in r and int(r["index"]) not in set(skip)}


def refusals(audited: dict[int, Inputs]) -> list[str]:
    """One line per take that is not current: `T06: stale ...; missing ...`."""
    return [f"T{i:02d}: {v.said()}" for i, v in sorted(audited.items()) if not v.current]


def count_line(audited: dict[int, Inputs]) -> str:
    """The number a master report quotes: `inputs: all 23 takes current`."""
    bad = sum(not v.current for v in audited.values())
    return (f"inputs: all {len(audited)} takes current" if not bad
            else f"inputs: {bad} of {len(audited)} takes stale")


def wall(audited: dict[int, Inputs], who: str = "G-TAKE-INPUTS refuses the master") -> None:
    """HARD: refuse while any take was rendered from pictures that are not the
    ones on disk now -- re-render those takes, then cut."""
    if why := refusals(audited):
        raise SystemExit(f"{who} ({count_line(audited)}):\n  " + "\n  ".join(why)
                         + "\nre-render each named take from the current sheets and panel")


def report(audited: dict[int, Inputs]) -> dict:
    """The QC block: ok, the counts, the line, and each stale take's names."""
    from dataclasses import asdict
    stale = {f"T{i:02d}": asdict(v) for i, v in sorted(audited.items()) if not v.current}
    return {"ok": not stale, "of": len(audited), "current": len(audited) - len(stale),
            "line": count_line(audited), "stale": stale}


def row(inputs: Inputs):
    """The take gate's HARD `inputs` row: a stale roll FAILS, so the ladder
    retakes it instead of keeping it; no penalty, the score still compares
    renders of the same inputs."""
    from studio.take_verdict import Gate
    return Gate(ROW, len(inputs.stale) + len(inputs.missing), inputs.current, True, inputs.said())
