"""Back-test the episode time model on delivered episodes, leave one out (2026-10-21_ep02_proof DESIGN 4.7, P7).

    uv run --no-sync python scripts/proof/time_backtest.py [--episodes delivered | jekyll:1 wotw:24 ...]
        [--target jekyll:1] [--target-plan <ep02 home>] [--library <real library>] [--out-dir <proof folder>]

Read-only, CPU, seconds.  It opens NAMED files per episode (timing.jsonl, clock.jsonl, repair.jsonl,
plan.json, placed.json, takes/r2v/shots.json) and the library's vlm_calls.jsonl, never a walk.  It writes
`<out>/TIME_BACKTEST_iterN.md` (its full path on the first line, never overwritten) and the Q5 rows
`<out>/results/time_backtest.json` that confidence.py reads.  Any input under a sandbox is refused, exit 2.

The episode set is PRE-REGISTERED before any error was computed (2026-10-21): Jekyll ep01 (the one
episode of the current era) and WotW ep25 (the clean run the step shares were priced on) with its two
neighbours ep24 and ep26.  Pass: total |error| <= 0.15 on >= 3 of the 4 held-out episodes.  That verdict is
kept as registered; the counted row is the leave-one-out over EVERY delivered episode with full records
(`--episodes delivered`, the default), at the same 3-in-4 rate, and each episode left out is named with
why.  `--target-plan` (SR-2's ch2 plan) adds ep02's predicted p90 clock row (AUDIT A6)."""
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
         "wotw": "20260827135508_the-war-of-the-worlds", "scarlet": "20260822113400_a-study-in-scarlet"}
PREREGISTERED = ("jekyll:1", "wotw:24", "wotw:25", "wotw:26")
DELIVERED = "delivered"
MAX_EPISODE = 40
"""epNN probed by name up to here per book, never a walk."""
REQUIRED = ("timing", "plan", "placed", "shots")
OUT = ROOT / "docs" / "audit" / "2026-10-21_ep02_proof"
SUB09 = {"takes": "render", "take_render": "render", "take_dq": "checks", "take_content": "checks",
         "take_eye": "checks", "strip": "checks", "face_refine": "refine"}
REFINE_ERA = {e.name: e.refine for e in tm.ERAS}
NAMED = {"timing": "timing.jsonl", "clock": "clock.jsonl", "repair": "repair.jsonl", "plan": "plan.json",
         "placed": "placed.json", "shots": "takes/r2v/shots.json"}


def home_of(library: Path, spec: str, books: dict | None = None) -> tuple[str, Path]:
    book, n = spec.split(":")
    folder = (books or BOOKS).get(book, book)
    return f"{book}:ep{int(n):02d}", library / folder / "episodes" / f"ep{int(n):02d}"


def unscorable(home: Path) -> str | None:
    """Why an episode with full records cannot be scored (no reviewed era map, a stage the map lacks, no
    first master), or None."""
    try:
        rows = load(home)["timing"]
        era = tm.era_for(rows)
    except (tm.UnmappedStage, OSError, ValueError, KeyError) as why:
        return str(why).strip("'\"")
    if missing := tm.unmapped(rows, era):
        return f"stages not in the reviewed {era.name} map: {', '.join(missing[:6])}"
    return None if tm.first_master_end(rows) is not None else "no first master (no dossier row)"


def delivered(library: Path, books: dict | None = None) -> tuple[list[str], dict[str, str]]:
    """(every episode with full records the back-test can score, {each one it cannot: why}), by name."""
    specs, excluded = [], {}
    for key, folder in (books or BOOKS).items():
        for n in range(1, MAX_EPISODE + 1):
            home = Path(library) / folder / "episodes" / f"ep{n:02d}"
            if not home.is_dir() or not all((home / NAMED[k]).is_file() for k in REQUIRED):
                continue
            why = unscorable(home)
            specs += [] if why else [f"{key}:{n}"]
            excluded.update({f"{key}:{n}": why} if why else {})
    return specs, excluded


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
    refine = era.refine and tm.refine_clocked(first)
    ep = tm.Episode(name=name, era=era.name, refine=refine, measured=tm.measured(first, era, refine),
                    inputs=tm.inputs_from(rec["shots"], rec["placed"], rec["plan"]),
                    clock_s=tm.clock_to_first_master(rec["clock"], end), contended=tm.contended(first, era),
                    evidence=tuple(str(rec["paths"][k]) for k in ("timing", "plan", "placed", "shots")),
                    apart_s=sum(float(r.get("seconds") or 0) for r in apart),
                    uncovered_s=tm.uncovered_s(rec["clock"], rows, end) if rec["clock"] else None)
    return ep, first


def split09(first: list[dict]) -> str:
    """Step 09's measured render / checks / refine; with overlapped lanes only the 09 total, since netting a
    lane out of its parent can leave a sub-step negative, and a negative minute is no measure."""
    got = {"render": 0.0, "checks": 0.0, "refine": 0.0}
    for r in first:
        if r["stage"] in SUB09:
            got[SUB09[r["stage"]]] += float(r.get("seconds") or 0)
    if any(r.get("within") == "takes" for r in first):
        return (f"09 total {sum(got.values()) / 60:.1f} min (OVERLAPPED lanes: a sub-step split is netting, "
                "not a measure, so none is printed)")
    return " / ".join(f"{k} {v / 60:.1f}" for k, v in got.items()) + " min"


def fit_line(fit: dict) -> str:
    """The VL read fit as the predictor uses it; a refused negative slope is said, with the median it uses."""
    if "refused_b" in fit:
        return (f"VL fit over {fit['n']} logged reads: slope {fit['refused_b']:.3f} s per token REFUSED (b < 0 is "
                f"no model: it prices a long read at or below zero); a read is priced at the median "
                f"{fit['median_s']:.1f} s.")
    return (f"VL fit over {fit['n']} logged reads: seconds = {fit['a']:.2f} + {fit['b']:.3f} x tokens "
            f"({tm.vl_read_s(fit):.1f} s at the median {fit['tokens']:.0f} tokens).")


def scope_lines(episodes: list[tm.Episode], results: list[dict]) -> list[str]:
    """What the back-test scores against what Q5 asks: timing-row seconds, not the clock to the first master."""
    each = [f"{e.name}: timing rows {hours(r['measured_s'])}, clock {hours(e.clock_s)}"
            for e, r in zip(episodes, results) if e.clock_s is not None]
    return ["SCOPE: this back-test scores the first pass's timing-row seconds.  Q5 asks about the machine clock "
            "to the first master (clock.jsonl) against 6 h; the difference is drive overhead and killed runs "
            "(the uncovered-clock gap below).  So this back-test does not predict the 6 h quantity"
            + (f" ({'; '.join(each)})." if each else "."), ""]


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
    out += ["", f"EVERY SCORED EPISODE: {v['within']} of {v['n']} held-out episodes within 0.15 (the counted row; "
            f"it needs the registered rate, {tm.NEED} in {tm.HELD_OUT})",
            f"Band (information, not the verdict): measured at or under the predicted p90 on {under} of {v['n']}.", ""]
    return out


def pre_lines(ctx: dict) -> list[str]:
    """The pre-registered verdict on its own 4 episodes, and the episodes the default run left out."""
    pre = ctx.get("pre")
    out = [f"VERDICT (pre-registered, its 4 episodes only): {'PASS' if pre['passed'] else 'FAIL'} -- {pre['within']} "
           f"of {pre['n']} within 0.15 (needs {tm.NEED} of {tm.HELD_OUT})", ""] if pre else []
    excluded = ctx.get("excluded") or {}
    out += ["Excluded (full records, not scorable): " + "; ".join(f"{k} ({v})" for k, v in excluded.items()), ""] \
        if excluded else []
    return out


def step_error_lines(results: list[dict]) -> list[str]:
    got = tm.step_errors(results)
    out = ["Per step: within 0.15 of its own measure, over the held-out episodes that measured it", "",
           "| step | within | signed error per episode |", "|---|---|---|"]
    for s, e in got.items():
        each = ", ".join(f"{k} {v:+.2f}" for k, v in e["errors"].items() if v is not None)
        out.append(f"| {s} | {e['within']} of {e['n']} | {each} |")
    return out + [""]


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
            + ("; its refine rows carry no GPU clock, so the measure and the prior both leave the refine out "
               "(the first-pass refine Gap carries it)" if REFINE_ERA[e.era] and not e.refine else "")
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
             "", f"Episodes scored: {', '.join(e.name for e in ctx['episodes'])}.  {fit_line(ctx['fit'])}  "
             f"Gap shares are taken on {ctx['target'].name}'s inputs (ep02's plan does not exist until SR-2).", ""]
    lines += scope_lines(ctx["episodes"], ctx["results"])
    lines += base_lines(ctx["episodes"]) + loo_lines(ctx["results"], ctx["episodes"]) + pre_lines(ctx)
    lines += step_lines(ctx["results"], ctx["episodes"], ctx["firsts"]) + step_error_lines(ctx["results"])
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


def context(library: Path, specs: list[str], target: str, books: dict | None = None) -> dict:
    loaded = [(name, load(home)) for name, home in map(lambda s: home_of(library, s, books), specs)]
    built = [episode(name, rec) for name, rec in loaded]
    episodes, firsts = [b[0] for b in built], [b[1] for b in built]
    fit = tm.vl_fit(tm.read_jsonl(library / "vlm_calls.jsonl"))
    results = tm.leave_one_out(episodes, tm.vl_read_s(fit))
    t = [e.name for e in episodes].index(home_of(library, target, books)[0]) if target in specs else 0
    every = [r for _, rec in loaded for r in rec["timing"]]
    found = tm.gaps([r for f in firsts for r in f], every, episodes[t].inputs,
                    [e.uncovered_s for e in episodes if e.uncovered_s is not None]) + tm.unseen_steps(episodes)
    denom = tm.share_denominator(found, results[t]["p90_s"])
    return {"episodes": episodes, "firsts": firsts, "fit": fit, "results": results, "target": episodes[t],
            "shared": tm.shares(found, results[t]["p90_s"]), "denom": denom, "sha": head_sha()}


def pre_registered(ctx: dict, pre: list[str]) -> dict | None:
    """The registered verdict, re-scored on its own episodes alone when the run scored more than them."""
    names = [e.name for e in ctx["episodes"]]
    picked = [names.index(n) for n in pre if n in names]
    if len(picked) != len(pre):
        return None
    if len(picked) == len(names):
        return tm.verdict(ctx["results"])
    return tm.verdict(tm.leave_one_out([ctx["episodes"][i] for i in picked], tm.vl_read_s(ctx["fit"])))


def loo_row(row: dict, ctx: dict) -> dict:
    """The counted back-test row: every scored episode at the registered 3-in-4 rate, the registered verdict said."""
    v, pre = tm.verdict(ctx["results"]), ctx.get("pre")
    rate = v["n"] >= tm.HELD_OUT and v["within"] * tm.HELD_OUT >= tm.NEED * v["n"]
    said = (f"pre-registered {pre['n']}: {pre['within']} of {pre['n']} within 0.15 ({'PASS' if pre['passed'] else 'FAIL'})"
            if pre else "pre-registered episodes not all scored")
    return {**row, "passed": rate and bool(pre and pre["passed"]),
            "detail": f"{v['within']} of {v['n']} delivered episodes within 0.15 (needs {tm.NEED} in {tm.HELD_OUT}); {said}"}


def target_rows(ctx: dict, plan_home: Path | None) -> list[dict]:
    """ep02's predicted p90 clock row, from SR-2's plan, when the plan exists (AUDIT A6)."""
    if plan_home is None:
        return []
    p = {k: Path(plan_home) / NAMED[k] for k in ("plan", "placed", "shots")}
    tm.refuse_sandbox(p.values())
    js = {k: json.loads(v.read_text(encoding="utf-8")) for k, v in p.items()}
    inp, read_s = tm.inputs_from(js["shots"], js["placed"], js["plan"]), tm.vl_read_s(ctx["fit"])
    p90 = sum(v[1] for v in tm.predict(inp, False, tm.fit(ctx["episodes"], read_s), read_s).values())
    uncovered = [e.uncovered_s for e in ctx["episodes"] if e.uncovered_s is not None]
    return [tm.ep02_row(p90 + tm.refine_p90_s(inp), max(uncovered) if uncovered else None, [str(v) for v in p.values()])]


def write_rows(out: Path, ctx: dict) -> Path:
    """The Q5 rows confidence.py reads (results are inputs to the report, rewritten each run)."""
    rows = tm.result_rows(ctx["results"], ctx["shared"], tm.base_rate(ctx["episodes"]), ctx["episodes"])
    rows = [loo_row(rows[0], ctx), *rows[1:], *target_rows(ctx, ctx.get("target_plan"))]
    path = out / "results" / "time_backtest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8", newline="\n")
    return path


def parse(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--episodes", nargs="+", default=[DELIVERED])
    ap.add_argument("--preregistered", nargs="+", default=list(PREREGISTERED))
    ap.add_argument("--books", nargs="+", default=None, help="key=folder pairs (default: the series books)")
    ap.add_argument("--target", default=PREREGISTERED[0])
    ap.add_argument("--target-plan", type=Path, default=None, help="an ep02 home holding SR-2's plan")
    ap.add_argument("--library", type=Path, default=settings.REAL_LIBRARY)
    ap.add_argument("--out-dir", type=Path, default=OUT)
    return ap.parse_args(argv)


def run(args: argparse.Namespace) -> dict:
    """Score the episodes, the registered verdict and the target plan; the rows written."""
    books = dict(b.split("=", 1) for b in args.books) if args.books else None
    tm.refuse_sandbox([args.library / "vlm_calls.jsonl"])
    specs, excluded = delivered(args.library, books) if args.episodes == [DELIVERED] else (args.episodes, {})
    ctx = context(args.library, specs, args.target, books)
    ctx.update(excluded=excluded, target_plan=args.target_plan,
               pre=pre_registered(ctx, [home_of(args.library, s, books)[0] for s in args.preregistered]))
    ctx["rows_path"] = write_rows(args.out_dir, ctx)
    return ctx


def main(argv: list[str] | None = None) -> int:
    args = parse(argv)
    try:
        ctx = run(args)
    except tm.SandboxInput as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    path = next_path(args.out_dir, "TIME_BACKTEST")
    write_new(path, report(path, ctx))
    print(path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
