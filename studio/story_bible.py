"""`story.md`: the one file a fresh window reads to learn what this episode is,
where it got to, and what was already decided.

From sw-workflow (screenwriting-skills), read 2026-09-12: keep the project's
state in one file so the work resumes across sessions; on resuming, read only
the current stage, the settled decisions and the decision log, say them back in
three sentences, and do NOT re-open a settled decision unless the owner
overturns it.

Ours splits the page in half for one reason.  The FACTS -- which stage, how many
takes, which paths -- go stale the moment anything runs, so they are
regenerated from disk every time.  The JUDGEMENT -- what was settled, why, what
happens next -- cannot be derived from disk at all, so it is kept verbatim
through every regeneration.  A generated file nobody trusts and a hand-written
file nobody updates both fail; splitting them fails neither way.

Armstrong footnotes his scripts only where the reason for a change is not
self-evident, and observes that the distribution of the footnotes is itself
information: the episodes that shot smoothly have none.  The decision log works
the same way.  Log the choice whose reason a stranger could not reconstruct,
and where the log is thick is where the pipeline is unsettled.
"""
from __future__ import annotations

import re

WHAT = "## What this is"
WHERE = "## Where it got to"
SETTLED = "## Settled — do not re-open without the owner"
DECISIONS = "## Decisions, oldest first"
NEXT = "## Next"

GENERATED = (WHAT, WHERE)
KEPT = (SETTLED, DECISIONS, NEXT)

PLACEHOLDER = "- (nothing written here yet)"
NO_NEXT = "- (next step not written)"

HEADING = re.compile(r"^## .*$", re.MULTILINE)


def _facts(facts: dict) -> str:
    """The half that is read off disk, so it is always true and never argued with."""
    pages = ", ".join(facts.get("pages") or []) or "none yet"
    return (
        f"{WHAT}\n\n"
        f"- **{facts.get('title', 'untitled')}**\n"
        f"- The question it answers: {facts.get('question') or '(none declared)'}\n"
        f"- {facts.get('shots', 0)} shots, {facts.get('lines', 0)} lines, "
        f"{facts.get('seconds', 0):.2f} s of picture\n\n"
        f"{WHERE}\n\n"
        f"- Stage: {facts.get('stage', 'unknown')}\n"
        f"- Takes: {facts.get('takes_done', 0)} of {facts.get('takes_total', 0)}\n"
        f"- Master: {facts.get('master') or '(not cut yet)'}\n"
        f"- Pages: {pages}\n")


def render(facts: dict, kept: dict | None = None) -> str:
    """The whole page: regenerated facts, then whatever judgement we were given."""
    kept = kept or {}
    body = [f"# {facts.get('title', 'untitled')}\n", _facts(facts)]
    for heading, empty in ((SETTLED, PLACEHOLDER), (DECISIONS, PLACEHOLDER), (NEXT, NO_NEXT)):
        body.append(f"{heading}\n\n{kept.get(heading, empty).strip()}\n")
    return "\n".join(body)


def parse(text: str) -> dict:
    """The hand-written sections, by heading.  The generated ones are dropped:
    re-reading them would let a stale fact outlive the disk it came from."""
    out, heading, lines = {}, None, []
    for line in (text or "").splitlines():
        if HEADING.match(line):
            if heading in KEPT:
                out[heading] = "\n".join(lines).strip()
            heading, lines = line.strip(), []
        elif heading:
            lines.append(line)
    if heading in KEPT:
        out[heading] = "\n".join(lines).strip()
    return {k: v for k, v in out.items() if k in KEPT}


def merge(existing: str, facts: dict) -> str:
    """Refresh the facts, keep every word of the judgement."""
    return render(facts, parse(existing))


def decide(text: str, when: str, what: str, why: str) -> str:
    """Append one decision: the date, what changed, and why.

    The why is the whole value. Without it the next window reads a rule it
    cannot evaluate, and either obeys it superstitiously or reverses it."""
    kept = parse(text)
    log = kept.get(DECISIONS, "").strip()
    if log == PLACEHOLDER:
        log = ""
    entry = f"- **{when}** {what} — {why}"
    kept[DECISIONS] = f"{log}\n{entry}".strip()
    title = next((l[2:] for l in text.splitlines() if l.startswith("# ")), "untitled")
    return render({**_read_facts(text), "title": title}, kept)


def _read_facts(text: str) -> dict:
    """The generated half back as a dict, so `decide` can rewrite the page
    without going to disk.  Only the fields that appear on the page."""
    facts: dict = {}
    for line in (text or "").splitlines():
        if line.startswith("- Stage: "):
            facts["stage"] = line.removeprefix("- Stage: ")
        elif line.startswith("- Takes: "):
            done, _, total = line.removeprefix("- Takes: ").partition(" of ")
            facts["takes_done"], facts["takes_total"] = _int(done), _int(total)
        elif line.startswith("- Master: "):
            facts["master"] = line.removeprefix("- Master: ").replace("(not cut yet)", "")
        elif line.startswith("- Pages: "):
            pages = line.removeprefix("- Pages: ")
            facts["pages"] = [] if pages == "none yet" else [p.strip() for p in pages.split(",")]
        elif line.startswith("- The question it answers: "):
            question = line.removeprefix("- The question it answers: ")
            facts["question"] = "" if question == "(none declared)" else question
        elif match := re.match(r"- (\d+) shots, (\d+) lines, ([\d.]+) s", line):
            facts["shots"], facts["lines"] = int(match[1]), int(match[2])
            facts["seconds"] = float(match[3])
    return facts


def _int(text: str) -> int:
    digits = re.sub(r"\D", "", text or "")
    return int(digits) if digits else 0


def last_decision(text: str) -> str:
    log = parse(text).get(DECISIONS, "").strip()
    lines = [l for l in log.splitlines() if l.strip().startswith("-") and l.strip() != PLACEHOLDER]
    return lines[-1].strip("- ").strip() if lines else "nothing decided yet"


def restate(text: str) -> str:
    """What a fresh window says back before it does anything: what this is,
    where it got to, what was last decided.  Three sentences, no more."""
    facts = _read_facts(text)
    title = next((l[2:] for l in text.splitlines() if l.startswith("# ")), "untitled")
    return (f"This is {title}. "
            f"It is at {facts.get('stage', 'an unknown stage')}, with "
            f"{facts.get('takes_done', 0)} of {facts.get('takes_total', 0)} takes rendered. "
            f"The last thing decided was {last_decision(text)}.")
