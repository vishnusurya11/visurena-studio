"""The upload request, its gates, and the ledger that stops a second copy.

Publishing is the one step in this pipeline that cannot be undone by deleting a
file: a public video is seen, indexed and archived within seconds.  So it is
gated harder than a spend, and every gate here is a REFUSAL rather than a
warning, except the ones marked advisory.

Two facts from Google's own docs decide the shape (verified 2026-09-12):

  * `videos.insert` from an UNVERIFIED API project is forced to private
    whatever `privacyStatus` you send, and the call still returns 200 with a
    video id.  So `private` is the default and the honest value to record; the
    remedy for public is a compliance audit, not a flag.
  * AI disclosure is `status.containsSyntheticMedia`.  It is a declaration to
    the platform, not copy, so it is never generated -- the spec refuses to
    build without it being stated.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

TITLE_MAX, DESCRIPTION_MAX, TAGS_MAX = 100, 5000, 500
PRIVACIES = ("private", "unlisted", "public")
CATEGORY_FILM = "1"
"""YouTube's "Film & Animation" category id."""


def sha8(path: Path) -> str:
    """The first 8 hex of the file's sha256: what `--watched` is checked against."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()[:8]


def spec(title: str, description: str, tags: list[str], *, synthetic: bool,
         privacy: str = "private", category: str = CATEGORY_FILM,
         made_for_kids: bool = False) -> dict:
    """The `videos.insert` body, validated against the API's own limits.

    `synthetic` is keyword-only and has no default on purpose: the AI-disclosure
    declaration is the owner's, and a script that guessed it wrong risks a
    manually applied label and, repeated, removal."""
    if not title.strip():
        raise ValueError("a video needs a title")
    if len(title) > TITLE_MAX:
        raise ValueError(f"title is {len(title)} characters; YouTube's wall is {TITLE_MAX}")
    if "<" in title or ">" in title:
        raise ValueError("angle brackets are refused by the API in a title")
    if len(description) > DESCRIPTION_MAX:
        raise ValueError(f"description is {len(description)} characters; the wall is {DESCRIPTION_MAX}")
    if sum(len(t) + 1 for t in tags) > TAGS_MAX:
        raise ValueError(f"tags total over {TAGS_MAX} characters")
    if privacy not in PRIVACIES:
        raise ValueError(f"privacy is one of {PRIVACIES}, got {privacy!r}")
    return {"snippet": {"title": title, "description": description,
                        "tags": list(tags), "categoryId": category},
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": made_for_kids,
                       "containsSyntheticMedia": synthetic}}


# ---- the ledger ------------------------------------------------------------

LEDGER = "uploads.jsonl"


def ledger_path(book: Path) -> Path:
    return Path(book) / LEDGER


def uploaded(book: Path, key: str) -> dict | None:
    """The record for this upload key, or None.  The key is book+episode+sha,
    so a re-cut master is a DIFFERENT upload and a re-run of the same one is
    not -- which is the only honest way to tell a fix from a duplicate."""
    path = ledger_path(book)
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("key") == key:
                return row
    return None


def record(book: Path, row: dict) -> Path:
    path = ledger_path(book)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def upload_key(book_id: str, episode: int, digest: str) -> str:
    return f"{book_id}/ep{episode:02d}/{digest}"


# ---- the gates -------------------------------------------------------------

def waived(qc: dict, dq_failed: list[str], *, override: str) -> dict | None:
    """What an override actually waived, for the ledger.  None when nothing was.

    An override nobody can read afterwards is indistinguishable from a bug, so
    the reason and the numbers it covered are recorded beside the upload."""
    if not override.strip():
        return None
    return {"reason": override.strip(), "qc_passed": bool(qc.get("passed")),
            "dq_failed": list(dq_failed)}


def refusals(qc: dict, dq_failed: list[str], *, privacy: str, watched: str,
             digest: str, already: dict | None, audited: bool = False,
             override: str = "") -> list[str]:
    """Every reason NOT to upload.  Empty means go.

    THE GATE SCALES WITH IRREVERSIBILITY.  A PRIVATE upload publishes nothing:
    it is invisible, deletable, and reversible in one click, so the machine
    gates carry it alone and the chain can end in an upload unattended.  Going
    PUBLIC is the act that cannot be taken back -- seen, indexed and archived in
    seconds -- so that is where the human belongs, and only there.

    Demanding a human for every network call would make the pipeline
    un-automatable, and an un-automatable safety gate is a gate somebody
    eventually comments out.

    `qc.py` deliberately does not fail on the take roll-up -- "the money is
    spent; the cut still needs a picture" -- which is right when asking "is this
    the best cut of what we rendered" and wrong when asking "is this fit for
    strangers".  The same measurement is advisory at G5 and hard here."""
    out = []
    # DOES THE REPORT DESCRIBE THIS FILE?  Also a fact, also no override -- you
    # cannot waive a measurement that was never taken.  MEASURED 2026-09-13:
    # qc_r2v.json was written at 19:49 about sha8 f5ddd2a3, the master was re-cut
    # at 20:02 as f8bf7814 after a take was swapped, and it went public at 20:04
    # against a report that had never seen it.  Had that report said PASS, an
    # unmeasured cut would have shipped with no override at all.
    if (measured := qc.get("sha8")) != digest:
        out.append(f"qc measured {measured or 'no recorded'} sha8, this cut is {digest}; "
                   f"re-run qc on the file you are uploading")
    # `already` is NOT a judgement, it is a fact, so no override reaches it: waiving
    # it puts a second copy of the same cut on the channel.
    if already:
        out.append(f"already uploaded as {already.get('video_id')} on {already.get('at')}; "
                   f"the master has not changed since")
    # The two QUALITY gates, and the only two an override covers.  Both answer
    # "is this the best cut we could make"; only the owner, having watched it,
    # can answer "is this good enough to show strangers".
    knowing = bool(override.strip())
    if not qc.get("passed") and not knowing:
        out.append("qc says passed:false -- fix the cut before anyone sees it")
    if dq_failed and not knowing:
        out.append(f"{len(dq_failed)} takes failed DQ ({', '.join(dq_failed[:4])}"
                   f"{'...' if len(dq_failed) > 4 else ''})")
    if privacy != "private":
        if watched != digest:
            out.append(f"--watched={watched or '(absent)'} does not match the master's sha8 "
                       f"{digest}; {privacy} is seen by strangers, so watch the file first")
        if not audited:
            out.append(f"privacy {privacy!r}: an unverified API project forces private anyway, so "
                       f"anything else records a falsehood. Pass --audited once the compliance "
                       f"audit is granted, or publish later with videos.update")
    return out


# ---- which master, and which QC belongs to it -------------------------------

MASTERS = (("r2v", "master_r2v.mp4", "qc_r2v.json"), ("i2v", "master.mp4", "qc.json"))
"""Each delivered master with the QC report that measured IT.

An episode can hold more than one: episode 1 has `master.mp4` at 2:54 whose
`qc.json` passed, beside a `master_r2v.mp4` whose `qc_r2v.json` did not.  Taking
the masters in a fixed order and the QC from wherever picks the wrong pair, and
publishing an experiment that never passed is the one mistake that cannot be
taken back."""


def deliverable(home, engine: str = "") -> tuple:
    """(engine, master, qc path) -- the pair whose QC PASSED.

    Refuses rather than guesses when none passed or several did: an ambiguous
    choice here is resolved with `--engine`, by a person."""
    from pathlib import Path as _P

    home = _P(home)
    # THE CUT ROOM.  This built `home / master` and masters moved to `home/cut/`
    # in the layout change, while the QC report stayed at the episode root -- so
    # the pair came apart and a passing episode 4 was reported as "no master has
    # a QC that passed", which reads as a bad cut.
    found = [(name, home / "cut" / master, home / qc) for name, master, qc in MASTERS
             if (home / "cut" / master).exists()]
    if engine:
        picked = [f for f in found if f[0] == engine]
        if not picked:
            raise SystemExit(f"no {engine} master in {home}")
        return picked[0]
    passed = []
    for name, master, qc in found:
        if qc.exists() and json.loads(qc.read_text(encoding="utf-8")).get("passed"):
            passed.append((name, master, qc))
    if len(passed) == 1:
        return passed[0]
    if not passed:
        raise SystemExit(f"no master in {home} has a QC that passed "
                         f"({', '.join(n for n, _m, _q in found) or 'none found'}); "
                         f"fix the cut, or name one with --engine=<r2v|i2v>")
    raise SystemExit(f"{len(passed)} masters passed QC in {home}; name one with --engine=")


# ---- the title -------------------------------------------------------------

SERIES = "Sherlock Holmes"
"""The character, not the author or the channel.

It leads because it is the search term. A viewer looking for this work types
"Sherlock Holmes" long before they type "A Study in Scarlet", and never types
the chapter title -- which is what the first five uploads led with."""

ELLIPSIS = "…"


def elided(text: str, room: int) -> str:
    """`text` cut to `room` characters at a word boundary, ending in an ellipsis.

    Cutting inside a word ("Reminiscen…") reads as a bug rather than as an
    abbreviation, so the cut lands on the last space or comma that fits."""
    if len(text) <= room:
        return text
    kept = text[:max(0, room - len(ELLIPSIS))]
    kept = kept[:max(0, kept.rstrip().rfind(" "))].rstrip(" ,")
    return kept + ELLIPSIS


def series_title(book: str, episode: int, total: int, chapter: str) -> str:
    """`Sherlock Holmes: A Study in Scarlet — Ep 04/14 — "What John Rance..."`.

    The serial and the position come first because that is what a truncated
    search result shows; the chapter is what gives when the 100-character wall
    is reached, never the other way round."""
    if not chapter.strip():
        raise ValueError("a title needs its chapter name")
    if not 1 <= episode <= total:
        raise ValueError(f"episode {episode} of {total} is not in the series")
    lead = f"{SERIES}: {book} — Ep {episode:02d}/{total:02d} — "
    return f'{lead}"{elided(chapter.strip(), TITLE_MAX - len(lead) - 2)}"'
