"""The proof report: what the harness measured, counted by rules, per question (2026-10-21_ep02_proof DESIGN 5, P7).

    uv run --no-sync python scripts/proof/confidence.py [--results <dir>] [--out-dir <dir>] [--transcript <dir>]

Reads every `results/*.json` (a list of rows, or {"rows": [...]}) and `scripts/proof/questions.yaml`, and
writes `CONFIDENCE_iterN.md` under docs/audit/2026-10-21_ep02_proof/ with its full path as the first line,
a new N every run, never an overwrite.  Confidence here is a pass count over n DISTINCT points with its
Wilson lower bound, from checks that ran the real pipeline code; never an agent's opinion.  The rules of
DESIGN 5.1 are enforced here, each with a test:
- n is `n_distinct` (distinct points or distinct recovery traces), never rows or reruns; a row without it
  counts nothing; rows of one check (and kind) in ONE file count once, at their largest n_distinct and failed
  if any failed; a check two results files hold counts from the newest file only, the older named, except
  across rehearsal scenarios (each file names its `scenario`: another scenario is another point, never a
  rerun) and except a time row R15 refuses, which supersedes nothing;
- a gate is one instrument's row: it answers every question that names it, whichever question wrote it;
  while a gate is shut the question is REAL-RUN and only a check the map marks `ungated` can fail it (the
  rest ran on what the recordings do not cover);
- a quality or compliance row with any stand-in answer (canned, substituted, a canned worker or Claude
  answer, a scripted verdict: asserts.STAND_INS) is mechanism;
- a row measured by an instrument whose gate failed (`instrument_state: failed`) is INSTRUMENT FAILED and
  contributes nothing;
- a time MEASURE (kind quality or baseline) of a time question (Q5, Q7) counts only with clock `measured` and
  evidence whose every path is absolute and outside any sandbox; any other is REFUSED with its path (R15, fail
  closed).  A PASSING gap row says a step was measured, so it is held to the same rule.  A mechanism row
  (A-caps: did a cap fire) or a failing gap row measures no duration, so a sandbox under it is no refusal and
  its failure still fails the question;
- a failed row with no per-point pass count is never given an invented k: its points print beside the count
  as failed with unknown passes, and no Wilson bound is printed over the rest;
- a question flagged `cap_uncalibrated_shape` (Q6) is capped at PARTIAL until the ComfyUI transcript holds a
  pair for every contract route (`fake_comfy.shape_state`);
- a suite summary with no rows is adapted into rows by a named adapter (incidents.json: classes handled by a
  PASSING scenario, the rest open gaps; preconditions_ch2.json: gaps with a named outcome, the rest open gaps);
- `compliance` rows print apart (Q8-compliance) and never upgrade a REAL-RUN question;
- a percentage is never printed: every rate is a count over n."""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio.rehearsal.asserts import stands_in  # noqa: E402
from studio.rehearsal.fake_comfy import shape_state  # noqa: E402
from studio.rehearsal.time_model import under_sandbox  # noqa: E402

OUT = ROOT / "docs" / "audit" / "2026-10-21_ep02_proof"
QUESTIONS = Path(__file__).resolve().parent / "questions.yaml"
TRANSCRIPT = ROOT / "tests" / "fixtures" / "proof" / "comfy_transcript"
ROW_KEYS = frozenset({"check", "question", "passed", "n_points", "n_distinct", "evidence", "match_classes",
                      "instrument", "instrument_state", "kind"})
Z = 1.96


def wilson_lb(k: int, n: int, z: float = Z) -> float:
    """The Wilson score interval's lower bound for k passes over n (0 for no points)."""
    if n <= 0:
        return 0.0
    p = k / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - spread) / (1 + z * z / n)


ROW_LISTS = ("proof_rows", "rows")
"""Where a results file keeps its rows: a bare list, or the first of these keys it holds, beside the suite's
own summary (face_replay keeps per-face data under `rows` beside its `proof_rows`)."""


def rows_in(data) -> list[dict]:
    """The proof rows: dicts that name a check; a suite's own data under a row key is never a row."""
    if isinstance(data, dict):
        data = next((data[k] for k in ROW_LISTS if k in data), None) or []
    return [r for r in data if isinstance(r, dict) and "check" in r]


def once(group: list[dict]) -> dict:
    """Rows of one (question, check, kind) in ONE file counted once: the row with the most distinct points,
    failed if any of them failed, and then with no pass count (never invented)."""
    top = max(group, key=lambda r: int(r.get("n_distinct") or -1))
    said = {**top, "_rows": len(group)}
    if top.get("passed") and not all(r.get("passed") for r in group):
        said = {k: v for k, v in said.items() if k != "n_pass"} | {"passed": False}
    return said


def counted_once(rows: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        groups.setdefault((r.get("question"), r.get("check"), r.get("kind", "quality")), []).append(r)
    return [once(g) for g in groups.values()]


def file_rows(folder: Path) -> list[dict]:
    """Every row of every results file, each check counted once per file, tagged with its file and the
    rehearsal scenario the file names (None for any other suite)."""
    rows = []
    for path in sorted(Path(folder).glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        run = data.get("scenario") if isinstance(data, dict) else None
        rows += counted_once([{**r, "_file": path.name, "_run": run} for r in rows_in(data)])
    return rows


def counted_once_names(folder: Path) -> list[str]:
    return sorted(f"{r['check']} ({r['_file']}, {r['_rows']} rows)" for r in file_rows(folder) if r["_rows"] > 1)


def time_refused(row: dict, time_qs: frozenset) -> bool:
    """A time claim of a time question that R15 refuses: it prints REFUSED and supersedes nothing."""
    return row.get("question") in time_qs and time_claim(row) and bool(time_refusal(row))


def superseded(rows: list[dict], folder: Path, time_qs: frozenset = frozenset()) -> list[dict]:
    """The rows of a (question, check, scenario) that a NEWER results file also holds: an earlier run, never
    added (n is distinct points, never reruns).  Newest is by mtime, then by name; a refused time row takes no
    part, so it can hide no real row."""
    live = [r for r in rows if not time_refused(r, time_qs)]
    age = {f: ((Path(folder) / f).stat().st_mtime, f) for f in {r["_file"] for r in live}}
    key = lambda r: (r.get("question"), r.get("check"), r.get("_run"))  # noqa: E731
    newest: dict[tuple, str] = {}
    for r in live:
        if key(r) not in newest or age[r["_file"]] > age[newest[key(r)]]:
            newest[key(r)] = r["_file"]
    return [r for r in live if newest[key(r)] != r["_file"]]


def superseded_names(folder: Path, time_qs: frozenset = frozenset()) -> list[str]:
    return sorted({f"{r['check']} ({r['_file']})" for r in superseded(file_rows(folder), folder, time_qs)})


def load_results(folder: Path, time_qs: frozenset = frozenset()) -> list[dict]:
    """The rows of the newest run of every check, then the adapted summaries."""
    rows = file_rows(folder)
    old = {id(r) for r in superseded(rows, folder, time_qs)}
    kept = [r for r in rows if id(r) not in old]
    return kept + adapted(Path(folder), kept)


def time_questions(qmap: dict) -> frozenset:
    return frozenset(q for q, spec in qmap["questions"].items() if spec.get("time"))


def rowless_files(folder: Path) -> list[str]:
    """The results files that hold no proof rows and no adapter (a suite's summary): named, never counted."""
    return [p.name for p in sorted(Path(folder).glob("*.json"))
            if p.name not in ADAPTERS and not rows_in(json.loads(p.read_text(encoding="utf-8")))]


# ---- the summaries P2 writes, adapted into rows ----

NO_SCENARIO = ("UNCOVERED", "NOT_A_FAULT")
NAMED_OUTCOMES = ("jit", "park")


def summary_row(check: str, kind: str, passed: bool, k: int, n: int, tried: int, evidence: str, detail: str) -> dict:
    return {"check": check, "question": "Q6", "passed": passed, "n_points": tried, "n_distinct": n, "n_pass": k,
            "evidence": [evidence], "match_classes": {}, "instrument": "files", "instrument_state": "n/a",
            "kind": kind, "detail": detail}


def open_gap(name: str, items: list[str], evidence: str) -> list[dict]:
    """One open gap row naming every item, or none when nothing is open."""
    return [summary_row(f"unmeasured:{name}", "gap", False, 0, 1, 1, evidence, ", ".join(items))] if items else []


def scenario_ran(classes: dict, rows: list[dict]) -> tuple[dict, dict]:
    """(class -> scenario for every mapped class, scenario -> its rows in the results)."""
    mapped = {c: v.get("scenario") for c, v in classes.items() if v.get("scenario") not in NO_SCENARIO}
    by = {s: [r for r in rows if r.get("check") == s] for s in set(mapped.values())}
    return mapped, by


def incident_rows(summary: dict, rows: list[dict]) -> list[dict]:
    """DESIGN 4.5: a recorded class is handled only when its scenario ran and every row of it PASSED (a
    mechanism row: the scenarios run on fake engines); unreproduced and unrun classes are open gaps."""
    classes, src = summary.get("classes") or {}, "results/incidents.json"
    mapped, by = scenario_ran(classes, rows)
    ran = {c: s for c, s in mapped.items() if by[s]}
    failed = [c for c, s in ran.items() if not all(r.get("passed") for r in by[s])]
    recorded, handled = int(summary.get("recorded", len(classes))), len(ran) - len(failed)
    detail = f"handled {handled} of {recorded} recorded classes" + (
        f"; scenario failed: {', '.join(failed)}" if failed else "")
    cov = summary_row("incident_coverage", "mechanism", not failed, handled, len(ran), recorded, src, detail)
    unreproduced = [c for c, v in classes.items() if v.get("scenario") == "UNCOVERED"]
    unrun = [f"{c} ({s})" for c, s in mapped.items() if c not in ran]
    return ([cov] + open_gap("incident classes no scenario reproduces", unreproduced, src)
            + open_gap("incident classes whose scenario has not run", unrun, src))


def precondition_rows(audit: dict) -> list[dict]:
    """DESIGN 4.3: the ch2 gaps with a rule-named outcome (a just-in-time ref step or a named park) over EVERY
    gap (AUDIT A8: the unknown and the owner's are in the denominator); F14 tests the handling.  A gap with no
    named outcome, an owner's precondition (series.json) and props not yet listed are open."""
    gaps, src = audit.get("gaps") or [], "results/preconditions_ch2.json"
    named = [g for g in gaps if g.get("outcome") in NAMED_OUTCOMES]
    unknown = [f"{g.get('what')} ({g.get('outcome')})" for g in gaps if g.get("outcome") not in NAMED_OUTCOMES]
    props = audit.get("props") or {}
    unknown += [f"props ({props.get('why')})"] if props.get("status") == "REAL-RUN" else []
    parks = sum(g["outcome"] == "park" for g in named)
    detail = (f"{len(named)} of {len(gaps)} ch2 gaps have a named outcome ({parks} parks, {len(named) - parks} "
              "just-in-time ref steps); F14 tests the handling")
    row = summary_row("preconditions_ch2", "mechanism", True, len(named), len(gaps), len(gaps), src, detail)
    return [row] + open_gap("ch2 preconditions with no named outcome", unknown, src)


ADAPTERS = {"incidents.json": incident_rows, "preconditions_ch2.json": lambda data, rows: precondition_rows(data)}
"""A summary file a suite writes with no rows, and the function that turns it into rows: (data, rows) -> rows."""


def adapted(folder: Path, rows: list[dict]) -> list[dict]:
    out = []
    for name, adapt in ADAPTERS.items():
        path = folder / name
        data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
        if isinstance(data, dict) and not rows_in(data):
            out += [{**r, "_file": name} for r in adapt(data, rows)]
    return out


def load_questions(path: Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def shape_calibrated(folder: Path) -> bool:
    """Calibrated once SR-5 has recorded a pair for EVERY contract route there, never on a partial capture."""
    return shape_state(Path(folder)) == "calibrated"


# ---- the counting rules ----

def n_of(row: dict) -> int:
    return int(row["n_distinct"])


def k_of(row: dict) -> int | None:
    """Passes over the row's distinct points: `n_pass`; all of them for a passed row that gives none; None
    (unknown, never invented) for a failed row that does not say how many of its points passed."""
    if "n_pass" in row:
        return int(row["n_pass"])
    return n_of(row) if row.get("passed") else None


def has_canned(classes) -> bool:
    """A stand-in dependency (asserts.STAND_INS: canned, substituted, a canned worker or Claude answer, a
    scripted verdict): in a class list, or a count above 0 in a class map (AUDIT A2, A4)."""
    return stands_in(classes)


def instrument_failed(row: dict) -> bool:
    return str(row.get("instrument_state", "")).strip().lower() in ("failed", "instrument failed")


def uncalibrated(row: dict) -> bool:
    return "uncalibrated" in str(row.get("instrument_state", "")).lower()


def engine_shape_ok(transcript: bool, rows: list[dict]) -> bool:
    """Calibrated only with a recorded transcript AND no row stamped by an uncalibrated fake."""
    return transcript and not any(uncalibrated(r) and "shape" in str(r.get("instrument_state")) for r in rows)


TIME_KINDS = ("quality", "baseline")
"""The kinds that measure a duration.  A mechanism row counts whether a cap fired and a failing gap row
declares a blocker: neither is a clock, and refusing either could only hide a failure or a blocker.  A
PASSING gap row claims its step was measured, so it is a time claim too."""


def time_claim(row: dict) -> bool:
    kind = row.get("kind", "quality")
    return kind in TIME_KINDS or (kind == "gap" and bool(row.get("passed")))


def time_refusal(row: dict) -> str:
    """Why a time measure is no evidence (R15, fail closed): '' only for clock `measured` with evidence whose
    every path is absolute and outside any sandbox."""
    paths = [str(p) for p in row.get("evidence") or []]
    if row.get("clock") != "measured":
        return f"clock {row.get('clock', 'not stated')!r}, never a measure ({', '.join(paths) or 'no evidence'})"
    if not paths:
        return "no evidence path: a time measure names the real record it read"
    loose = [p for p in paths if not os.path.isabs(p)]
    if loose:
        return f"relative evidence, which any sandbox could hold: {', '.join(loose)}"
    boxed = [p for p in paths if under_sandbox(p)]
    return f"evidence under a sandbox: {', '.join(boxed)}" if boxed else ""


def contribution(row: dict, spec: dict) -> tuple[str, str]:
    """(what the row counts as, why): refused, instrument_failed, or its (possibly demoted) kind."""
    if row.get("n_distinct") is None:
        return "refused", f"no n_distinct: n is distinct points, never rows or reruns ({row.get('_file', '?')})"
    if spec.get("time") and time_claim(row) and (why := time_refusal(row)):
        return "refused", why
    if instrument_failed(row):
        return "instrument_failed", f"INSTRUMENT FAILED: {row.get('instrument')}"
    kind = row.get("kind", "quality")
    if kind in ("quality", "compliance") and has_canned(row.get("match_classes")):
        return "mechanism", "rests on a canned answer"
    return kind, ""


def bucket(spec: dict, rows: list[dict]) -> dict[str, list]:
    by: dict[str, list] = {}
    for r in rows:
        kind, why = contribution(r, spec)
        by.setdefault(kind, []).append((r, why) if kind == "refused" else r)
    return by


def tally(rows: list[dict]) -> tuple[int, int]:
    known = [r for r in rows if k_of(r) is not None]
    return sum(k_of(r) for r in known), sum(n_of(r) for r in known)


def unknown_points(rows: list[dict]) -> int:
    """The distinct points of failed rows that never said how many passed: printed beside the count."""
    return sum(n_of(r) for r in rows if k_of(r) is None)


# ---- the status of a question ----

def gate_misses(spec: dict, rows: list[dict]) -> list[str]:
    """The gates with no passing, unrefused row; `rows` is EVERY row, since a gate answers each question
    that names it, whichever question wrote it."""
    return [g for g in spec.get("gates") or [] if not any(
        r["check"] == g and r.get("passed") and contribution(r, spec)[0] != "refused" for r in rows)]


def check_misses(spec: dict, by: dict) -> list[str]:
    """The required checks with no passing row of their kind at their distinct-point minimum."""
    misses = []
    for c in spec.get("checks") or []:
        got = [r for r in by.get(c.get("kind", "quality"), []) if r["check"] == c["check"]]
        n = sum(n_of(r) for r in got)
        if not got or not all(r["passed"] for r in got) or n < c["min_n"]:
            misses.append(f"{c['check']} {n} of {c['min_n']}")
    return misses


def failing(spec: dict, by: dict, shut: bool = False) -> list[dict]:
    """The failed counted rows; while a gate is shut only a check the map marks `ungated` can fail the
    question (the rest ran on what the recordings do not cover: DESIGN 5.2, Q1 REAL-RUN below its gates)."""
    gates = set(spec.get("gates") or [])
    free = {c["check"] for c in spec.get("checks") or [] if c.get("ungated")}
    return [r for kind in ("quality", "mechanism") for r in by.get(kind, [])
            if not r["passed"] and r["check"] not in gates and (not shut or r["check"] in free)]


def shut_why(spec: dict, by: dict, shut: list[str]) -> str:
    held = [r["check"] for r in failing(spec, by) if r not in failing(spec, by, True)]
    return "gate not passed: " + ", ".join(shut) + (
        f"; failing behind the shut gate (not answerable from recordings): {', '.join(held)}" if held else "")


def short_of_proof(spec: dict, by: dict) -> str:
    """What keeps a question that nothing fails from PROVEN, in words; '' when nothing does."""
    misses = check_misses(spec, by)
    gaps = [r["check"] for r in by.get("gap", []) if not r["passed"]]
    loose = [r["check"] for k in ("quality", "mechanism") for r in by.get(k, [])
             if uncalibrated(r)]
    parts = [("short: " + ", ".join(misses)) if misses else "", ("open gap: " + ", ".join(gaps)) if gaps else "",
             ("uncalibrated instrument: " + ", ".join(loose)) if loose else ""]
    return "; ".join(p for p in parts if p) or ("" if by.get("quality") else "no quality row")


def decide(spec: dict, by: dict, every: list[dict], shape_ok: bool) -> tuple[str, str]:
    if spec.get("real_run"):
        return "REAL-RUN", "no recording can answer it"
    shut = gate_misses(spec, every)
    if bad := failing(spec, by, bool(shut)):
        return "FAILING", "failing: " + ", ".join(r["check"] for r in bad)
    if shut:
        return "REAL-RUN", shut_why(spec, by, shut)
    if why := short_of_proof(spec, by):
        return "PARTIAL", why
    if spec.get("cap_uncalibrated_shape") and not shape_ok:
        return "PARTIAL", "capped: the fake ComfyUI's shape is uncalibrated until SR-5 records a transcript"
    return "PROVEN", "every check passes at its minimum, calibrated, no canned answer under a quality check"


def status(spec: dict, rows: list[dict], shape_ok: bool, every: list[dict] | None = None) -> dict:
    """The question's status from its own rows; its gates are read over `every` row (default: its own)."""
    by = bucket(spec, rows)
    state, why = decide(spec, by, rows if every is None else every, shape_ok)
    k, n = tally(by.get("quality", []))
    return {"status": state, "why": why, "k": k, "n": n, "lb": wilson_lb(k, n),
            "unknown": unknown_points(by.get("quality", [])), "refused": by.get("refused", []),
            "instrument_failed": by.get("instrument_failed", []), "mechanism": tally(by.get("mechanism", [])),
            "compliance": tally(by.get("compliance", [])), "quality": by.get("quality", []),
            "gaps": by.get("gap", []), "baselines": by.get("baseline", []),
            "mechanism_rows": by.get("mechanism", []), "compliance_rows": by.get("compliance", [])}


def evaluate(qmap: dict, rows: list[dict], shape_ok: bool) -> dict[str, dict]:
    return {q: status(spec, [r for r in rows if r.get("question") == q], shape_ok, rows)
            for q, spec in qmap["questions"].items()}


# ---- the report ----

def count(k: int, n: int, unknown: int = 0) -> str:
    """k/n with its Wilson bound; failed points with unknown passes print beside it, and then no bound."""
    said = "no counted points" if n <= 0 else f"{k}/{n} distinct points"
    if unknown:
        return said + f" + {unknown} failed points with unknown passes (no bound over a part of the points)"
    return said if n <= 0 else said + f" (Wilson lower bound {wilson_lb(k, n):.3f})"


def summary(qmap: dict, got: dict) -> list[str]:
    out = ["| Q | question | status | quality passes | why |", "|---|---|---|---|---|"]
    for q, spec in qmap["questions"].items():
        g = got[q]
        out.append(f"| {q} | {spec['title']} | **{g['status']}** | {count(g['k'], g['n'], g['unknown'])} | {g['why']} |")
    return out + [""]


def row_line(r: dict) -> str:
    k = k_of(r)
    said = f"{k}/{n_of(r)} distinct" if k is not None else f"over {n_of(r)} distinct (passes per point not reported)"
    return (f"- {r['check']} ({r.get('kind', 'quality')}): {'pass' if r.get('passed') else 'FAIL'} "
            f"{said} of {r.get('n_points', '?')} tried; {r.get('_file', '?')}"
            + "".join(f"; {r[k]}" for k in ("note", "detail") if r.get(k)))


def staged(spec: dict, runs: dict) -> list[str]:
    out = []
    for sid in spec.get("staged") or []:
        r = runs[sid]
        note = f" ({r['machine_note']})" if r.get("machine_note") else ""
        out.append(f"- {sid}: {r['what']}; machine about {r['machine_min']} min{note}; "
                   f"{'owner go required' if r.get('owner_go') else 'no owner go needed'}")
    return out


def gap_line(r: dict) -> str:
    """A time gap prints its share of the p90; any other gap prints what it names."""
    if "p90_share" in r:
        said = " (p90 share UNKNOWN)" if r["p90_share"] is None else f" (p90 share {r['p90_share']:.3f})"
    else:
        said = f": {r['detail']}" if r.get("detail") else ""
    return f"- open gap: {r['check']}{said}"


def evidence_lines(g: dict) -> list[str]:
    out = [row_line(r) for k in ("quality", "mechanism_rows", "compliance_rows") for r in g.get(k, [])]
    out += [f"- INSTRUMENT FAILED: {r['check']} ({r.get('instrument')}): contributes nothing"
            for r in g["instrument_failed"]]
    out += [f"- REFUSED: {r.get('check', '?')}: {why}" for r, why in g["refused"]]
    out += [gap_line(r) for r in g["gaps"] if not r["passed"]]
    out += [f"- baseline: {r['check']} {k_of(r) or 0} of {n_of(r)}" for r in g["baselines"]]
    return out


def section(q: str, spec: dict, g: dict, runs: dict) -> list[str]:
    out = [f"## {q} {spec['title']}: {g['status']}", "", f"Why: {g['why']}.", "",
           f"Quality: {count(g['k'], g['n'], g['unknown'])}.  Mechanism exercised: {g['mechanism'][0]}/{g['mechanism'][1]} "
           "distinct points (never counted toward the question).", ""]
    if spec.get("compliance_apart"):
        out += [f"{q}-compliance (kind compliance, printed apart, never upgrades {q}): "
                f"{g['compliance'][0]}/{g['compliance'][1]} distinct points.", ""]
    if spec.get("baseline"):
        out += [f"Baseline: {spec['baseline']}.", ""]
    out += evidence_lines(g) or ["- no rows yet"]
    if g["status"] in ("REAL-RUN", "PARTIAL") and spec.get("staged"):
        out += ["", "The staged real runs that would answer it:"] + staged(spec, runs)
    return out + [""]


def head_sha() -> str:
    out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return out.stdout.strip() or "unknown"


def report(path: Path, qmap: dict, got: dict, ctx: dict) -> str:
    files = sorted({r["_file"] for r in ctx["rows"]})
    known = set(qmap["questions"])
    loose = [r for r in ctx["rows"] if r.get("question") not in known]
    lines = [str(path), "", f"# Proof-backed confidence ({datetime.now().astimezone():%Y-%m-%d %H:%M %Z}, "
             f"HEAD {head_sha()})", "",
             f"Results read: {ctx['results']} ({len(ctx['rows'])} rows from {', '.join(files) or 'no files'}"
             + (f"; no proof rows in {', '.join(ctx['rowless'])}" if ctx.get("rowless") else "") + ").",
             "Superseded by a newer results file (an earlier run, never counted): "
             + (", ".join(ctx["superseded"]) if ctx.get("superseded") else "none") + ".",
             "Several rows of one check in one file, counted once: "
             + (", ".join(ctx["once"]) if ctx.get("once") else "none") + ".",
             "Fake ComfyUI shape: " + ("calibrated (a recorded transcript exists)." if ctx["shape_ok"] else
                                       "uncalibrated (no recorded transcript; SR-5): every Q6 row is capped at PARTIAL."),
             "Rules (DESIGN 5.1, in code): n is distinct points; canned makes a row mechanism; a failed instrument "
             "counts nothing; a Q5/Q7 time measure counts only with a measured clock and absolute evidence outside "
             "any sandbox; mechanism rows still count and can fail; no rate without its count.", ""]
    lines += summary(qmap, got)
    for q, spec in qmap["questions"].items():
        lines += section(q, spec, got[q], qmap["staged_runs"])
    if loose:
        lines += [f"Rows naming no question in the map: {len(loose)} (never counted)."]
    return "\n".join(lines) + "\n"


def next_path(out: Path) -> Path:
    n = 1
    while (out / f"CONFIDENCE_iter{n}.md").exists():
        n += 1
    return out / f"CONFIDENCE_iter{n}.md"


def write_new(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--results", type=Path, default=OUT / "results")
    ap.add_argument("--out-dir", type=Path, default=OUT)
    ap.add_argument("--transcript", type=Path, default=TRANSCRIPT)
    ap.add_argument("--questions", type=Path, default=QUESTIONS)
    args = ap.parse_args(argv)
    qmap = load_questions(args.questions)
    time_qs = time_questions(qmap)
    rows = load_results(args.results, time_qs)
    shape_ok = engine_shape_ok(shape_calibrated(args.transcript), rows)
    path = next_path(args.out_dir)
    ctx = {"rows": rows, "results": args.results, "shape_ok": shape_ok, "rowless": rowless_files(args.results),
           "superseded": superseded_names(args.results, time_qs), "once": counted_once_names(args.results)}
    write_new(path, report(path, qmap, evaluate(qmap, rows, shape_ok), ctx))
    print(path)
    print(path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
