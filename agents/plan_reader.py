"""Plan reader -- the critic that LISTS what a plan does (episode 02_05); code judges.

Handed the chapter's text, the chapter's rows numbered, and the plan as
PLAIN TEXT with the writer's rationale stripped (`why`, `turn`, `section`,
and the plan's own `answer`: the critic finds the turn and the answer, it is
never told them), it returns a `PlanReading` in a closed shape --
`studio.judges.plan` judges it.  It is never asked whether the plan is
right.  Asked k=3 times; the judge requires agreement on the turn and takes
the union of the claims.

THE FAMILY RULE (decision 2026-09-24, judges §1.1): the critic runs on a
model family other than the writer's, or it grades its own prose.
models.yaml configures ONE family today (every tier is the same OpenAI
model), so this critic reuses `workhorse`; the flip is a `critic` tier on a
second provider with a key and a listed rate, and this constant.  Temperature
is a tier param in models.yaml, not a code setting.  Book-neutral: nothing
here names a book, a character or an episode.
"""
from __future__ import annotations

from pathlib import Path

from studio import llm
from studio.judges.plan import PlanReading  # noqa: F401  (the reading, re-exported)

TIER = "workhorse"
K = 3
RETRIES = 2
"""One re-ask on a schema violation, then it surfaces: the critic never loops."""
SKILL_PATH = Path(__file__).parent / "skills" / "plan_reader.md"
STRIPPED = ("why", "turn", "section")
"""The writer's rationale: what persuades a judge, so the critic never sees it."""
SHOT_FIELDS = ("setup", "size", "faces", "extras", "source", "frame", "motion", "camera",
               "at_rest", "end", "changed")


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _flat(value) -> str:
    return ", ".join(str(v) for v in value) if isinstance(value, list) else str(value)


def shot_text(shot: dict) -> str:
    """One shot as prose fields, the rationale left out, the empties left out."""
    kept = [(k, shot.get(k)) for k in SHOT_FIELDS if k not in STRIPPED]
    body = "; ".join(f"{k}={_flat(v)}" for k, v in kept if v not in (None, "", [], 0))
    return f"shot {shot.get('index')}: {body}"


def plain_text(doc: dict) -> str:
    """The plan as plain text for the critic: the question, the setups with their
    cast, every shot's picture, every line -- and no `why`, `turn`, `section`
    or `answer`."""
    head = [f"title: {doc.get('title', '')}", f"question: {doc.get('question', '')}",
            f"protagonist: {doc.get('protagonist', '')}"]
    setups = [f"setup {name}: cast {_flat(s.get('cast', []))}; {s.get('described', '')}"
              for name, s in (doc.get("setups") or {}).items()]
    shots = [shot_text(s) for s in doc.get("shots") or []]
    lines = [f"line {ln.get('index')} ({ln.get('kind')}, {ln.get('speaker')}, on shot {ln.get('shot')}): "
             f"{ln.get('text', '')}" for ln in doc.get("lines") or []]
    return "\n".join(head + setups + shots + lines)


def prompt_for(plan_text: str, chapter_rows: list[str], chapter_text: str | None = None) -> str:
    rows = "\n".join(f"{i}: {row}" for i, row in enumerate(chapter_rows)) or "(none listed)"
    parts = [load_skill()]
    if chapter_text:
        parts.append(f"--- THE CHAPTER ---\n{chapter_text}")
    parts += [f"--- THE CHAPTER'S ROWS, NUMBERED ---\n{rows}", f"--- THE PLAN ---\n{plan_text}",
              "Return the reading."]
    return "\n\n".join(parts)


def _tally(total: dict | None, one: dict) -> None:
    if total is None:
        return
    for key in ("input_tokens", "output_tokens", "total_tokens"):
        total[key] = total.get(key, 0) + one.get(key, 0)
    total["tier"] = one.get("tier", TIER)


def read(plan_text: str, chapter_rows: list[str], k: int = K, *, chapter_text: str | None = None,
         usage: dict | None = None, _agent=None) -> list[PlanReading]:
    """k readings of one plan through the gateway; a schema violation is re-asked once."""
    prompt = prompt_for(plan_text, chapter_rows, chapter_text)
    out = []
    for _ in range(k):
        one: dict = {}
        out.append(llm.structured(TIER, prompt, PlanReading, retries=RETRIES, usage=one, _agent=_agent))
        _tally(usage, one)
    return out
