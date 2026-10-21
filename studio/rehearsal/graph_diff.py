"""The brick's test, as code (2026-10-21_ep02_proof DESIGN 0, R1): the take graph a rehearsal
builds, diffed field by field against the RECORDED graph of the same index and try count, each
difference attributed to a commit or to the try count.

A field is one literal input of one node (`<node>.<class_type>.<input>`) plus the node class
multiset; links are wiring, not fields.  A difference is explained by (a) a commit since the
recording, in the take code, read-only over the REAL repo, whose hunk SETS that field to that
literal (`git log -G '<input|class|node>...[:=] <value>'`; only a changed prompt phrase of 8+
characters may stand alone, by `-S`) -- a commit that merely moved a `True` or a `2` somewhere
explains nothing -- or (b) a seed that moved by
101 per try (`takes_r2v.mark_retake`).  What is left is UNEXPLAINED: the regression measure is
their count over n takes, and each one is listed with its field.  Never run inside a fenced
rehearsal process: the fence refuses git outside <sandbox>/git; the harness runs this after."""
from __future__ import annotations

import difflib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from studio import settings

TAKE_CODE = ("scripts/episode/takes_r2v.py", "studio/take_ladder.py", "scripts/episode/face_refine.py",
             "studio/face_refine.py", "studio/episode_take_prompt.py", "studio/comfy.py", "studio/take_phases.py")
"""The code a take graph is built from: where a commit that explains a field must have landed."""
SEED_STEP = 101
"""takes_r2v.mark_retake: a retake's seed is the card's plus 101 x its try count."""
PHRASE_MIN = 8
"""A changed prompt phrase this long is specific enough for `git log -S` alone; anything shorter
(and every number or boolean) must sit on a line that names its field (`-G '<name>.*<value>'`)."""
SHOWN = 160
"""Characters of a value kept in a report row (a prompt is thousands)."""
NO_GRAPH = "<no recorded graph>"
Git = Callable[..., str]


def is_link(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 2 and isinstance(value[0], str) and isinstance(value[1], int)


def fields_of(graph: Mapping) -> dict[str, Any]:
    """{'<node>.<class>.<input>': literal} for every literal input, plus 'classes' (sorted)."""
    out: dict[str, Any] = {}
    nodes = {k: v for k, v in graph.items() if isinstance(v, dict) and "class_type" in v}
    for node, body in nodes.items():
        for name, value in (body.get("inputs") or {}).items():
            if not is_link(value):
                out[f"{node}.{body['class_type']}.{name}"] = value
    out["classes"] = sorted(body["class_type"] for body in nodes.values())
    return out


def diff(old: Mapping, new: Mapping) -> list[dict]:
    """Every field whose value differs (absent on one side reads as None), in field order."""
    keys = sorted(set(old) | set(new))
    return [{"field": k, "old": old.get(k), "new": new.get(k)} for k in keys if old.get(k) != new.get(k)]


def recorded_for(room: Path, index: int, tries: int, kept_tries: int) -> tuple[Path | None, int | None]:
    """(graph, its try count): try t's own graph (kept, or attempts/T##_fail{t+1}); else the kept
    take's as the nearest, so the try count can explain the seed; (None, None) when none exists."""
    kept = Path(room) / f"T{index:02d}.graph.json"
    failed = Path(room) / "attempts" / f"T{index:02d}_fail{tries + 1}.graph.json"
    if tries == kept_tries and kept.is_file():
        return kept, tries
    if failed.is_file():
        return failed, tries
    return (kept, kept_tries) if kept.is_file() else (None, None)


def by_tries(d: Mapping, tries: tuple[int, int]) -> bool:
    """A seed that moved by exactly 101 per try between the recording's try and this one."""
    if not d["field"].endswith(".noise_seed") or tries[0] == tries[1]:
        return False
    try:
        return int(d["new"]) - int(d["old"]) == SEED_STEP * (tries[1] - tries[0])
    except (TypeError, ValueError):
        return False


def changed_runs(old: str, new: str) -> list[str]:
    """The word runs that differ: inserted or replaced in `new`, then deleted from `old`."""
    a, b = old.split(), new.split()
    ops = difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes()
    added = [" ".join(b[j1:j2]) for tag, _, _, j1, j2 in ops if tag in ("replace", "insert")]
    removed = [" ".join(a[i1:i2]) for tag, i1, i2, _, _ in ops if tag == "delete"]
    return added + removed


def phrase(run: str, old: str, new: str) -> str:
    """A changed run widened by one word on the left when it is too short to search alone."""
    if len(run) >= PHRASE_MIN:
        return run
    hit = re.search(r"(\S+\s+)?" + re.escape(run), new) or re.search(r"(\S+\s+)?" + re.escape(run), old)
    return hit.group(0) if hit else run


EDGE = "[^0-9A-Za-z_.]"
ERE_SPECIAL = set(".[]()*+?{}|^$\\")


def ere(text: str) -> str:
    """`text` as a POSIX ERE literal (git -G is extended; Python's re.escape over-escapes for it)."""
    return "".join("\\" + c if c in ERE_SPECIAL else c for c in text)


def icase(word: str) -> str:
    """A case-blind ERE for a name: `cfg` matches CFG = 2 and graph['cfg']."""
    return "".join(f"[{c.lower()}{c.upper()}]" if c.isalpha() else ere(c) for c in word)


def names_of(field: str) -> list[str]:
    """The names a hunk must carry to explain a field: the input (a document's last key), plus a
    graph field's class and its node id when the id is a word (`lora_second`), never a bare number."""
    parts = field.split(".")
    keys = [p for p in re.split(r"[.\[\]]+", field) if p and not p.isdigit() and p != "classes"]
    if len(parts) == 3 and "[" not in field:
        return [p for p in parts if not p.isdigit()]
    return keys[-1:]


def spellings(value: Any) -> list[str]:
    """How a literal is written in code: a boolean in Python and in JSON, anything else as itself."""
    if isinstance(value, bool):
        return [str(value), str(value).lower()]
    return [str(value).strip()[:SHOWN]]


def named(field: str, values: list[str]) -> str | None:
    """A -G pattern for ONE line that SETS the field to the literal: a name, its closing quotes or
    brackets, `=` or `:`, then the literal as a whole word (`CFG = 2`, `'cfg'] = 2`, `"cfg": 2`,
    `cfg=2`); prose like `(8 steps, euler)` is no setting.  None when the field has no name."""
    names = names_of(field)
    if not names or not any(values):
        return None
    n = "(" + "|".join(icase(x) for x in names) + ")"
    v = "(" + "|".join(ere(x) for x in values if x) + f")({EDGE}|$)"
    return f"{n}[]'\"]*[[:space:]]*[:=][[:space:]]*{v}"


def terms(field: str, old: Any, new: Any) -> list[tuple[str, str]]:
    """git pickaxe terms: a changed prompt phrase of PHRASE_MIN+ characters by -S alone; every
    other literal (a number, a boolean, a short string) only on a line that names its field."""
    if isinstance(old, str) and isinstance(new, str):
        found = [w.strip()[:SHOWN] for w in (phrase(r, old, new) for r in changed_runs(old, new)) if w.strip()]
        out = [("-S", w) if len(w) >= PHRASE_MIN else ("-G", named(field, [w])) for w in dict.fromkeys(found)]
    else:
        out = [("-G", named(field, spellings(v))) for v in (new, old) if v is not None and not isinstance(v, (dict, list))]
    return [t for t in out if t[1]][:4]


def commits_for(term: tuple[str, str], since: str, git: Git) -> list[str]:
    """Short shas of commits since `since` that changed `term` in the take code (read-only)."""
    flag, text = term
    out = git("log", "--format=%h", f"--since={since}", f"{flag}{text}", "--", *TAKE_CODE)
    return [line.strip() for line in out.splitlines() if line.strip()]


def shown(value: Any) -> Any:
    return value[:SHOWN] if isinstance(value, str) else value


def attribute(d: Mapping, since: str, tries: tuple[int, int], git: Git) -> dict:
    """The difference with `by`: 'tries', 'commit' (+ commits, literal) or None (UNEXPLAINED)."""
    row = {"field": d["field"], "old": shown(d["old"]), "new": shown(d["new"])}
    if by_tries(d, tries):
        return {**row, "by": "tries"}
    for term in terms(d["field"], d["old"], d["new"]):
        if shas := commits_for(term, since, git):
            return {**row, "by": "commit", "commits": shas[:5], "literal": term[1]}
    return {**row, "by": None}


def take_report(index: int, recorded: Mapping, built: Mapping, since: str, tries: tuple[int, int], git: Git) -> dict:
    """One take: every difference attributed; `unexplained` the fields nothing explains."""
    rows = [attribute(d, since, tries, git) for d in diff(fields_of(recorded), fields_of(built))]
    return {"index": index, "tries": list(tries), "differences": rows,
            "unexplained": [r["field"] for r in rows if r["by"] is None]}


def summary(reports: Iterable[Mapping]) -> dict:
    """The regression measure: unexplained differences over n takes, each listed with its field."""
    reports = list(reports)
    listed = [{"index": r["index"], "field": f} for r in reports for f in r["unexplained"]]
    return {"n": len(reports), "unexplained": len(listed), "listed": listed}


def kept_tries(room: Path) -> dict[int, int]:
    """index -> the kept take's try count, from the room's shots.json records."""
    path = Path(room) / "shots.json"
    rows = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
    return {int(r["index"]): int(r.get("tries") or 0) for r in rows if "index" in r}


def room_report(room: Path, built: Mapping[int, tuple[Mapping, int]], since: str, git: Git) -> list[dict]:
    """Every built take {index: (graph, tries)} against the recorded room; a take with no
    recorded graph is one unexplained difference, never silently skipped."""
    kept, out = kept_tries(room), []
    for index, (graph, tries) in sorted(built.items()):
        path, rec_tries = recorded_for(room, index, tries, kept.get(index, 0))
        if path is None:
            out.append({"index": index, "tries": [None, tries], "differences": [], "unexplained": [NO_GRAPH]})
            continue
        recorded = json.loads(path.read_text(encoding="utf-8"))
        out.append(take_report(index, recorded, graph, since, (rec_tries, tries), git))
    return out


def flatten(doc: Any, prefix: str = "") -> dict[str, Any]:
    """A JSON document as {path: leaf}: `[0].refs[1]`, `plan.shots[2].size`."""
    if isinstance(doc, dict):
        items = [(f"{prefix}.{k}" if prefix else str(k), v) for k, v in doc.items()]
    elif isinstance(doc, list):
        items = [(f"{prefix}[{i}]", v) for i, v in enumerate(doc)]
    else:
        return {prefix: doc}
    out: dict[str, Any] = {}
    for path, value in items:
        out.update(flatten(value, path))
    return out


def doc_report(name: str, recorded: Any, built: Any, since: str, git: Git) -> dict:
    """A deterministic step output (placed.json, prompts.json, shots.json) against ep01's."""
    rows = [attribute(d, since, (0, 0), git) for d in diff(flatten(recorded), flatten(built))]
    return {"doc": name, "differences": rows, "unexplained": [r["field"] for r in rows if r["by"] is None]}


def repo_git(repo: Path = settings.REPO) -> Git:
    """`git -C <repo> ...` for read-only log queries; its stdout ('' on a failed query)."""
    def run(*args: str) -> str:
        done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", check=False)
        return done.stdout if done.returncode == 0 else ""
    return run
