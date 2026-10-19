"""The units of a step in plain words, partitioned to the plan's total (Jekyll Kawajiri ep01).

The card said "28 of 28" while seven takes were stale and two flagged: counts came from files
and each reader counted its own way.  A bucket is one word; a unit sits in exactly one; the
buckets sum to the total the PLAN names (plan.json), never to the files that happen to exist."""
from __future__ import annotations

WORDS = ("passed", "kept with flags", "running", "to check", "to fix", "to redo", "blocked", "not started")
ORDER = (("running", "running"), ("blocked", "blocked"), ("stale", "to redo"), ("failed", "to fix"))


def _count(value) -> int:
    """A list's length, or a bare count."""
    return len(value) if isinstance(value, list) else int(value or 0)


def plan_totals(plan: dict) -> dict[str, int]:
    """{takes, lines}: the contract totals, read off plan.json's shots and lines."""
    return {"takes": _count(plan.get("shots")), "lines": _count(plan.get("lines"))}


def bucket_of(facts: dict) -> str:
    """The one word for a unit's facts: running, blocked, stale, failed, file, judged, flagged."""
    for key, word in ORDER:
        if facts.get(key):
            return word
    if not facts.get("file"):
        return "not started"
    if not facts.get("judged"):
        return "to check"
    return "kept with flags" if facts.get("flagged") else "passed"


def partition(units: list[tuple[str, dict]], total: int) -> dict[str, int]:
    """{word: n} summing to `total`; units the facts have not met are `not started`."""
    seen = [u for u, _ in units]
    for u in seen:
        if seen.count(u) > 1:
            raise ValueError(f"unit {u} is in two buckets")
    if len(seen) > total:
        raise ValueError(f"{len(seen)} units but the plan total is {total}")
    out = {w: 0 for w in WORDS}
    for _, facts in units:
        out[bucket_of(facts)] += 1
    out["not started"] += total - len(seen)
    return out


def words(buckets: dict[str, int]) -> str:
    """`24 passed · 2 to check`: the buckets that hold units, in the card's order."""
    return " · ".join(f"{buckets[w]} {w}" for w in WORDS if buckets.get(w))
