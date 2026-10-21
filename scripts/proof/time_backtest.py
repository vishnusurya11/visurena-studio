"""Back-test the episode time model on delivered episodes, leave one out (2026-10-21_ep02_proof DESIGN 4.7, P7).

    uv run --no-sync python scripts/proof/time_backtest.py [--episodes jekyll:1 wotw:24 wotw:25 wotw:26]
        [--target jekyll:1] [--library <real library>] [--out-dir docs/audit/2026-10-21_ep02_proof]

Read-only, CPU, seconds.  It opens NAMED files per episode (timing.jsonl, clock.jsonl, repair.jsonl,
plan.json, placed.json, takes/r2v/shots.json) and the library's vlm_calls.jsonl, never a walk.  It writes
`<out>/TIME_BACKTEST_iterN.md` (its full path on the first line, never overwritten) and the Q5 rows
`<out>/results/time_backtest.json` that confidence.py reads.  Any input under a sandbox is refused, exit 2.

The episode set is PRE-REGISTERED before any error was computed (2026-10-21): Jekyll ep01 (the one
episode of the current era) and WotW ep25 (the clean run the step shares were priced on) with its two
neighbours ep24 and ep26.  Pass: total |error| <= 0.15 on >= 3 of the 4 held-out episodes."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import episode_capacity, settings  # noqa: E402
from studio.rehearsal import time_model as tm  # noqa: E402

BOOKS = {"jekyll": "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde",
         "wotw": "20260827135508_the-war-of-the-worlds"}
PREREGISTERED = ("jekyll:1", "wotw:24", "wotw:25", "wotw:26")
OUT = ROOT / "docs" / "audit" / "2026-10-21_ep02_proof"
SUB09 = {"takes": "render", "take_render": "render", "take_dq": "checks", "take_content": "checks",
         "take_eye": "checks", "strip": "checks", "face_refine": "refine"}
NAMED = {"timing": "timing.jsonl", "clock": "clock.jsonl", "repair": "repair.jsonl", "plan": "plan.json",
         "placed": "placed.json", "shots": "takes/r2v/shots.json"}


def home_of(library: Path, spec: str) -> tuple[str, Path]:
    book, n = spec.split(":")
    return f"{book}:ep{int(n):02d}", library / BOOKS.get(book, book) / "episodes" / f"ep{int(n):02d}"


def load(home: Path) -> dict:
    """The named records of one episode (an absent clock or repair file reads empty)."""
    p = {k: home / v for k, v in NAMED.items()}
    tm.refuse_sandbox(p.values())
    js = {k: json.loads(p[k].read_text(encoding="utf-8")) for k in ("plan", "placed", "shots")}
    return {**js, "paths": p, **{k: tm.read_jsonl(p[k]) for k in ("timing", "clock", "repair")}}


def episode(name: str, rec: dict) -> tuple[tm.Episode, list[dict]]:
    """The scored episode and its first-pass rows."""
    rows = rec["timing"]
    era = tm.era_for(rows)
    first, apart = tm.first_pass(rows, tm.repair_windows(rec["repair"]))
    end = tm.first_master_end(rows)
    ep = tm.Episode(name=name, era=era.name, refine=era.refine, measured=tm.measured(first, era),
                    inputs=tm.inputs_from(rec["shots"], rec["placed"], rec["plan"]),
                    clock_s=tm.clock_to_first_master(rec["clock"], end), contended=tm.contended(first, era),
                    evidence=tuple(str(rec["paths"][k]) for k in ("timing", "plan", "placed", "shots")),
                    apart_s=sum(float(r.get("seconds") or 0) for r in apart),
                    uncovered_s=tm.uncovered_s(rec["clock"], rows, end) if rec["clock"] else None)
    return ep, first


def split09(first: list[dict]) -> str:
    """Step 09's measured render / checks / refine, or why the split is not a measure."""
    got = {"render": 0.0, "checks": 0.0, "refine": 0.0}
    for r in first:
        if r["stage"] in SUB09:
            got[SUB09[r["stage"]]] += float(r.get("seconds") or 0)
    lanes = any(r.get("within") == "takes" for r in first)
    text = " / ".join(f"{k} {v / 60:.1f}" for k, v in got.items())
    return text + (" min (OVERLAPPED lanes: the split is netting, only the 09 total is a measure)" if lanes else " min")


def hours(s: float | None) -> str:
    return "n/a" if s is None else f"{s / 3600:.2f} h"


def head_sha() -> str:
    out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return out.stdout.strip() or "unknown"


def base_lines(episodes: list[tm.Episode]) -> list[str]:
    k, n = tm.base_rate(episodes)
    each = ", ".join(f"{e.name} first master {hours(e.clock_s)}" for e in episodes if e.clock_s is not None)
    return [f"BASE RATE: {k} of {n} clocked episodes under 6 h" + (f" ({each})" if each else ""), ""]


def loo_lines(results: list[dict], episodes: list[tm.Episode]) -> list[str]:
    v = tm.verdict(results)
    out = ["## Leave one out (total, first pass)", "",
           "| held out | measured | predicted p50 | predicted p90 | error | within 0.15 | studio capacity model |",
           "|---|---|---|---|---|---|---|"]
    for r, e in zip(results, episodes):
        cap = episode_capacity.projected_hours(e.inputs.shots) * 3600
        out.append(f"| {r['episode']} | {hours(r['measured_s'])} | {hours(r['pred_s'])} | {hours(r['p90_s'])} "
                   f"| {r['error']:+.3f} | {'yes' if abs(r['error']) <= tm.TOLERANCE else 'NO'} "
                   f"| {hours(cap)} ({(cap - r['measured_s']) / r['measured_s']:+.3f}) |")
    under = sum(1 for r in results if r["measured_s"] <= r["p90_s"])
    out += ["", f"VERDICT (pre-registered): {'PASS' if v['passed'] else 'FAIL'} -- {v['within']} of {v['n']} "
            f"held-out episodes within 0.15 (needs {tm.NEED} of {tm.HELD_OUT})",
            f"Band (information, not the verdict): measured at or under the predicted p90 on {under} of {v['n']}.", ""]
    return out


def step_lines(results: list[dict], episodes: list[tm.Episode], firsts: list[list[dict]]) -> list[str]:
    mae = tm.step_mae(results)
    out = ["## Per step (minutes)", "", "| step | MAE | " + " | ".join(e.name for e in episodes) + " |",
           "|---|---|" + "---|" * len(episodes)]
    for s in tm.STEPS:
        cells = [f"{r['measured'][s] / 60:.1f} m / {r['pred'].get(s, (0.0, 0.0))[0] / 60:.1f} p"
                 + (f" ({len(e.contended[s])} CONTENDED)" if e.contended.get(s) else "")
                 for r, e in zip(results, episodes)]
        out.append(f"| {s} | {mae.get(s, 0.0):.1f} | " + " | ".join(cells) + " |")
    out += ["", "m = measured, p = predicted p50.  Step 09 split per episode:"]
    out += [f"- {e.name}: {split09(f)}; apart (after the first master or in a repair window) {hours(e.apart_s)}"
            for e, f in zip(episodes, firsts)]
    return out + [""]


def gap_lines(shared: list[tuple[tm.Gap, float | None]], denom: float) -> list[str]:
    out = ["## UNMEASURED steps (R16): p90 share", "", "| step | name | measured | p90 bound | share | source |",
           "|---|---|---|---|---|---|"]
    for g, s in shared:
        bound = "UNKNOWN" if g.p90_s is None else f"{g.p90_s:.0f} s of {denom:.0f} s"
        share = "UNKNOWN" if s is None else f"{s:.3f}"
        out.append(f"| {g.step} | {g.name} | {'yes' if g.measured else 'NO: ' + g.why} | {bound} | {share} | {g.source} |")
    blocked = [g.name for g, s in shared if not g.measured and (s is None or s > tm.SHARE_LIMIT)]
    out.append("")
    out.append(f"Q5 cannot be PROVEN: {len(blocked)} unmeasured step(s) over 0.05 of the p90 or unbounded "
               f"({', '.join(blocked)})" if blocked else "No unmeasured step holds more than 0.05 of the p90.")
    return out + [""]


def report(path: Path, ctx: dict) -> str:
    lines = [str(path), "", f"# Time-model back-test ({datetime.now().astimezone():%Y-%m-%d %H:%M %Z}, HEAD {ctx['sha']})",
             "", f"Episodes (pre-registered): {', '.join(e.name for e in ctx['episodes'])}.  VL fit over "
             f"{ctx['fit']['n']} logged reads: seconds = {ctx['fit']['a']:.2f} + {ctx['fit']['b']:.3f} x tokens "
             f"({tm.vl_read_s(ctx['fit']):.1f} s at the median {ctx['fit']['tokens']:.0f} tokens).  "
             f"Gap shares are taken on {ctx['target'].name}'s inputs (ep02's plan does not exist until SR-2).", ""]
    lines += base_lines(ctx["episodes"]) + loo_lines(ctx["results"], ctx["episodes"])
    lines += step_lines(ctx["results"], ctx["episodes"], ctx["firsts"])
    lines += gap_lines(ctx["shared"], ctx["denom"]) + [f"Q5 rows: {ctx['rows_path']}", ""]
    return "\n".join(lines)


def next_path(out: Path, stem: str) -> Path:
    n = 1
    while (out / f"{stem}_iter{n}.md").exists():
        n += 1
    return out / f"{stem}_iter{n}.md"


def write_new(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(text)


def context(library: Path, specs: list[str], target: str) -> dict:
    loaded = [(name, load(home)) for name, home in map(lambda s: home_of(library, s), specs)]
    built = [episode(name, rec) for name, rec in loaded]
    episodes, firsts = [b[0] for b in built], [b[1] for b in built]
    fit = tm.vl_fit(tm.read_jsonl(library / "vlm_calls.jsonl"))
    results = tm.leave_one_out(episodes, tm.vl_read_s(fit))
    t = [e.name for e in episodes].index(home_of(library, target)[0]) if target in specs else 0
    every = [r for _, rec in loaded for r in rec["timing"]]
    found = tm.gaps([r for f in firsts for r in f], every, episodes[t].inputs,
                    [e.uncovered_s for e in episodes if e.uncovered_s is not None]) + tm.unseen_steps(episodes)
    denom = results[t]["p90_s"] + sum(g.p90_s or 0.0 for g in found if not g.measured)
    return {"episodes": episodes, "firsts": firsts, "fit": fit, "results": results, "target": episodes[t],
            "shared": tm.shares(found, results[t]["p90_s"]), "denom": denom, "sha": head_sha()}


def write_rows(out: Path, ctx: dict) -> Path:
    """The Q5 rows confidence.py reads (results are inputs to the report, rewritten each run)."""
    rows = tm.result_rows(ctx["results"], ctx["shared"], tm.base_rate(ctx["episodes"]), ctx["episodes"])
    path = out / "results" / "time_backtest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8", newline="\n")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--episodes", nargs="+", default=list(PREREGISTERED))
    ap.add_argument("--target", default=PREREGISTERED[0])
    ap.add_argument("--library", type=Path, default=settings.REAL_LIBRARY)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    args = ap.parse_args(argv)
    try:
        tm.refuse_sandbox([args.library / "vlm_calls.jsonl"])
        ctx = context(args.library, args.episodes, args.target)
    except tm.SandboxInput as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    ctx["rows_path"] = write_rows(args.out_dir, ctx)
    path = next_path(args.out_dir, "TIME_BACKTEST")
    write_new(path, report(path, ctx))
    print(path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
