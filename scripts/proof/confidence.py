"""The proof report: what the harness measured, counted by rules, per question (2026-10-21_ep02_proof DESIGN 5, P7).

    uv run --no-sync python scripts/proof/confidence.py [--results <dir>] [--out-dir <dir>] [--transcript <dir>]

Reads every `results/*.json` (a list of rows, or {"rows": [...]}) and `scripts/proof/questions.yaml`, and
writes `CONFIDENCE_iterN.md` under docs/audit/2026-10-21_ep02_proof/ with its full path as the first line,
a new N every run, never an overwrite.  Confidence here is a pass count over n DISTINCT points with its
Wilson lower bound, from checks that ran the real pipeline code; never an agent's opinion.  The rules of
DESIGN 5.1 are enforced here, each with a test:
- n is `n_distinct` (distinct points or distinct recovery traces), never rows or reruns; a row without it
  counts nothing;
- a quality or compliance row with any `canned` answer is mechanism;
- a row measured by an instrument whose gate failed (`instrument_state: failed`) is INSTRUMENT FAILED and
  contributes nothing;
- a row of a time question (Q5, Q7) whose evidence lies under a sandbox, or whose clock is `recorded`, is
  REFUSED with its path (R15);
- a question flagged `cap_uncalibrated_shape` (Q6) is capped at PARTIAL until the ComfyUI transcript exists;
- `compliance` rows print apart (Q8-compliance) and never upgrade a REAL-RUN question;
- a percentage is never printed: every rate is a count over n."""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

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


ROW_LISTS = ("rows", "proof_rows")
"""Where a results file keeps its rows: a bare list, or one of these keys beside the suite's own summary."""


def rows_in(data) -> list[dict]:
    if isinstance(data, list):
        return data
    return [r for key in ROW_LISTS for r in data.get(key) or []]


def load_results(folder: Path) -> list[dict]:
    """Every row of every results file, each tagged with the file it came from."""
    rows = []
    for path in sorted(Path(folder).glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        rows += [{**r, "_file": path.name} for r in rows_in(data)]
    return rows


def rowless_files(folder: Path) -> list[str]:
    """The results files that hold no proof rows (a suite's summary): read, named, never counted."""
    return [p.name for p in sorted(Path(folder).glob("*.json"))
            if not rows_in(json.loads(p.read_text(encoding="utf-8")))]


def load_questions(path: Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def shape_calibrated(folder: Path) -> bool:
    """The fake ComfyUI's shape is calibrated once SR-5 has recorded a transcript there."""
    return Path(folder).is_dir() and any(Path(folder).iterdir())


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
    """A canned dependency: 'canned' in a class list, or a canned count above 0 in a class map."""
    if isinstance(classes, dict):
        return bool(classes.get("canned"))
    return "canned" in (classes or [])


def instrument_failed(row: dict) -> bool:
    return str(row.get("instrument_state", "")).strip().lower() in ("failed", "instrument failed")


def uncalibrated(row: dict) -> bool:
    return "uncalibrated" in str(row.get("instrument_state", "")).lower()


def engine_shape_ok(transcript: bool, rows: list[dict]) -> bool:
    """Calibrated only with a recorded transcript AND no row stamped by an uncalibrated fake."""
    return transcript and not any(uncalibrated(r) and "shape" in str(r.get("instrument_state")) for r in rows)


def time_refusal(row: dict) -> str:
    """Why a time row is no evidence: a clock the fake recorded, or evidence under a sandbox."""
    paths = [str(p) for p in row.get("evidence") or []]
    if row.get("clock") == "recorded":
        return f"clock recorded by the fake engine, never a measure ({', '.join(paths)})"
    boxed = [p for p in paths if under_sandbox(p)]
    return f"evidence under a sandbox: {', '.join(boxed)}" if boxed else ""


def contribution(row: dict, spec: dict) -> tuple[str, str]:
    """(what the row counts as, why): refused, instrument_failed, or its (possibly demoted) kind."""
    if row.get("n_distinct") is None:
        return "refused", f"no n_distinct: n is distinct points, never rows or reruns ({row.get('_file', '?')})"
    if spec.get("time") and (why := time_refusal(row)):
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


# ---- the status of a question ----

def gate_misses(spec: dict, rows: list[dict]) -> list[str]:
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


def failing(spec: dict, by: dict) -> list[dict]:
    gates = set(spec.get("gates") or [])
    return [r for kind in ("quality", "mechanism") for r in by.get(kind, [])
            if not r["passed"] and r["check"] not in gates]


def short_of_proof(spec: dict, by: dict) -> str:
    """What keeps a question that nothing fails from PROVEN, in words; '' when nothing does."""
    misses = check_misses(spec, by)
    gaps = [r["check"] for r in by.get("gap", []) if not r["passed"]]
    loose = [r["check"] for k in ("quality", "mechanism") for r in by.get(k, [])
             if uncalibrated(r)]
    parts = [("short: " + ", ".join(misses)) if misses else "", ("open gap: " + ", ".join(gaps)) if gaps else "",
             ("uncalibrated instrument: " + ", ".join(loose)) if loose else ""]
    return "; ".join(p for p in parts if p) or ("" if by.get("quality") else "no quality row")


def decide(spec: dict, by: dict, rows: list[dict], shape_ok: bool) -> tuple[str, str]:
    if spec.get("real_run"):
        return "REAL-RUN", "no recording can answer it"
    if bad := failing(spec, by):
        return "FAILING", "failing: " + ", ".join(r["check"] for r in bad)
    if gates := gate_misses(spec, rows):
        return "REAL-RUN", "gate not passed: " + ", ".join(gates)
    if why := short_of_proof(spec, by):
        return "PARTIAL", why
    if spec.get("cap_uncalibrated_shape") and not shape_ok:
        return "PARTIAL", "capped: the fake ComfyUI's shape is uncalibrated until SR-5 records a transcript"
    return "PROVEN", "every check passes at its minimum, calibrated, no canned answer under a quality check"


def status(spec: dict, rows: list[dict], shape_ok: bool) -> dict:
    by = bucket(spec, rows)
    state, why = decide(spec, by, rows, shape_ok)
    k, n = tally(by.get("quality", []))
    return {"status": state, "why": why, "k": k, "n": n, "lb": wilson_lb(k, n), "refused": by.get("refused", []),
            "instrument_failed": by.get("instrument_failed", []), "mechanism": tally(by.get("mechanism", [])),
            "compliance": tally(by.get("compliance", [])), "quality": by.get("quality", []),
            "gaps": by.get("gap", []), "baselines": by.get("baseline", [])}


def evaluate(qmap: dict, rows: list[dict], shape_ok: bool) -> dict[str, dict]:
    return {q: status(spec, [r for r in rows if r.get("question") == q], shape_ok)
            for q, spec in qmap["questions"].items()}


# ---- the report ----

def count(k: int, n: int) -> str:
    if n <= 0:
        return "no counted points"
    return f"{k}/{n} distinct points (Wilson lower bound {wilson_lb(k, n):.3f})"


def summary(qmap: dict, got: dict) -> list[str]:
    out = ["| Q | question | status | quality passes | why |", "|---|---|---|---|---|"]
    for q, spec in qmap["questions"].items():
        g = got[q]
        out.append(f"| {q} | {spec['title']} | **{g['status']}** | {count(g['k'], g['n'])} | {g['why']} |")
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


def evidence_lines(g: dict) -> list[str]:
    out = [row_line(r) for r in g["quality"]]
    out += [f"- INSTRUMENT FAILED: {r['check']} ({r.get('instrument')}): contributes nothing"
            for r in g["instrument_failed"]]
    out += [f"- REFUSED: {r.get('check', '?')}: {why}" for r, why in g["refused"]]
    out += [f"- open gap: {r['check']}" + (f" (p90 share {r['p90_share']:.3f})" if r.get("p90_share") is not None
                                           else " (p90 share UNKNOWN)") for r in g["gaps"] if not r["passed"]]
    out += [f"- baseline: {r['check']} {k_of(r) or 0} of {n_of(r)}" for r in g["baselines"]]
    return out


def section(q: str, spec: dict, g: dict, runs: dict) -> list[str]:
    out = [f"## {q} {spec['title']}: {g['status']}", "", f"Why: {g['why']}.", "",
           f"Quality: {count(g['k'], g['n'])}.  Mechanism exercised: {g['mechanism'][0]}/{g['mechanism'][1]} "
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
             "Fake ComfyUI shape: " + ("calibrated (a recorded transcript exists)." if ctx["shape_ok"] else
                                       "uncalibrated (no recorded transcript; SR-5): every Q6 row is capped at PARTIAL."),
             "Rules (DESIGN 5.1, in code): n is distinct points; canned makes a row mechanism; a failed instrument "
             "counts nothing; a sandbox or recorded clock is refused for Q5 and Q7; no rate without its count.", ""]
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
    qmap, rows = load_questions(args.questions), load_results(args.results)
    shape_ok = engine_shape_ok(shape_calibrated(args.transcript), rows)
    path = next_path(args.out_dir)
    ctx = {"rows": rows, "results": args.results, "shape_ok": shape_ok, "rowless": rowless_files(args.results)}
    write_new(path, report(path, qmap, evaluate(qmap, rows, shape_ok), ctx))
    print(path)
    print(path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
