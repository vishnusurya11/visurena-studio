"""A redrawn base re-tags the plans written before it (Jekyll ep05 repair, 2026-10-28).

A plan tags a person with fragments quoted from their row ("the doctor (thick iron-grey hair, long
black frock coat)", `cast_refs.tag`), and `cast_alias.owner_of` binds the tag by those fragments.
A redrawn base changes the row; the old fragments then bind nobody and step 06 refuses every take
of that person.  Each fragment is replaced by the same clause of the same layer in the new look."""
from __future__ import annotations

import copy

from studio import cast_alias


def clauses(text: str) -> list[str]:
    return [c.strip() for c in (text or "").split(",") if c.strip()]


def mapping(old: dict[str, str], new: dict[str, str]) -> dict[str, str]:
    """{old clause: new clause} for every clause a layer changed, matched by layer and position."""
    out = {}
    for layer, was in old.items():
        now = clauses(new.get(layer, ""))
        for i, clause in enumerate(clauses(was)):
            if i < len(now) and now[i] != clause:
                out[clause] = now[i]
    return out


def retag_text(text: str, table: dict[str, str], his) -> str:
    """Every tag `his(fragments)` owns swapped through `table`; other tags and prose untouched."""
    def one(m) -> str:
        frags = [f.strip() for f in m.group("frags").split(",") if f.strip()]
        if not his(frags):
            return m.group(0)
        return f"{m.group('said')} ({', '.join(table.get(f, f) for f in frags)})"
    return cast_alias.TAG.sub(one, text)


def retag(doc, old: dict[str, str], new: dict[str, str], his):
    """The plan with every tag of the redrawn person (`his(fragments)`, read against the OLD rows)
    re-worded from the old look's layers to the new one's."""
    table = mapping(old, new)

    def walk(x):
        if isinstance(x, str):
            return retag_text(x, table, his)
        if isinstance(x, dict):
            return {k: walk(v) for k, v in x.items()}
        if isinstance(x, list):
            return [walk(v) for v in x]
        return x
    return walk(copy.deepcopy(doc))
