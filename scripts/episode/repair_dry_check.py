#!/usr/bin/env python
"""The repair rerun's DRY CHECK: what an owner's repair of a delivered episode would do, before it launches.

    uv run --no-sync python scripts/episode/repair_dry_check.py <codex_id> <n> [--steps=09]

No GPU, no ComfyUI, no write to the episode (it lists the episode's files before and after and says so).
It reports:
  - the repair window the next drive runs on (a backed leftover continues; an unbacked one is closed at
    drive start; else the owner's redo of `--steps` is assumed) and whether the owner's order still stands;
  - step 09's render pass, take by take, built exactly as takes_r2v builds its cards and asked its own
    question (takes_r2v.wants_render over take_currency.held_in): `current`, `frozen` (the repair keeps
    the delivered or measured bytes) or `render` (and why) -- a launch is right only when this says 0 --
    and the same pass on a relaunch after the drive ends (the closed repair row governs);
  - the terminal's best-draw swaps: a take an archived draw beats is KEPT when frozen, else it SWAPS;
  - the dq / content / eye passes, the refine owed and the tiny-face rung, each priced against the repair
    cap (and against the episode's own clock, for contrast);
  - the batch the early round and the batched rung would render, each asked of its own decider
    (take_overlap.early_cures, take_ladder.still_curable / route / batch_for) on the episode's records
    under the window -- never inferred from a counter (incident 2, 2026-10-19 12:29 PDT) -- and the
    ladder.json rounds the next launch counts;
  - what steps 10-13 would do;
  - THE LAUNCH'S VERDICT (`preflight`, deadline retro item 1, 2026-10-20): drive.py runs it before any GPU
    second and refuses (exit 2) when a delivered take would be written without a named owner order -- by
    the render pass, the early round, the batched rung, the terminal swap, or past the freeze.  This
    command exits 1 on the same verdict.

INCIDENT 2026-10-19 11:18 PDT: RERUN.md said "every take is current" without reading the files; the
launch queued all 28 of Jekyll HEL ep01's takes over P03's reworded prompts.  A rerun's "nothing renders"
claim is proven by this check on the real episode before the launch (LESSONS).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import episode_home, repair_clock, run_budget, work_orders  # noqa: E402
from studio import take_currency as tc  # noqa: E402

STEP = "09"
TAKES = Path("takes") / "r2v"
CHECK_RESERVE_S = 550.0
"""studio/face_refine.CHECK_RESERVE_S: a refine or a rung runs only while a full measuring pass fits after it."""


# ---- one take ------------------------------------------------------------------------------

def take_state(c: dict, take: Path, home: Path, window: dict | None, pictures: list,
               canvas: tuple[int, int], records: dict) -> tuple[str, str]:
    """(current | frozen | render, why): takes_r2v.wants_render over take_currency.held_in under `window`
    -- the render pass's own question, never a copy of it (skeptic minor 2) -- with stale_why's reason."""
    from scripts.episode import takes_r2v
    built = c.get("prompt") or ""
    held = lambda: tc.held_in(window, built, take, home, pictures, canvas)  # noqa: E731
    if takes_r2v.wants_render(c, take, records, None, held):
        return "render", render_why(c, take, records, tc.stale_why(built, take, pictures, canvas))
    why = tc.stale_why(built, take, pictures, canvas)
    if why is None:
        return "current", "words, pictures and canvas are the card's"
    froze = tc.frozen_in(window, take, home)
    return "frozen", f"{froze} bytes {tc.sha8_of(take)} kept by the repair (stale by {why} under today's rule)"


def render_why(c: dict, take: Path, records: dict, stale: str | None) -> str:
    """Why the render pass renders this card: no take, no record of its grouping, or the stale input."""
    rec = records.get(int(c["index"]))
    if not take.exists():
        return "no take on disk"
    if rec is None or rec.get("shots") != c["shots"]:
        return "no shots.json record for this grouping"
    return f"stale: {stale}"


def closed_form(window: dict) -> dict:
    """The row `repair_clock.close` writes for this window: what governs a relaunch after the drive ends."""
    return {**window, "closed_at": time.time(), "spent_s": 0.0}


def count_line(rows: dict[int, tuple[str, str]]) -> str:
    """`step 09 renders N take(s) (T..): a current, b frozen, c render`."""
    renders = [i for i, (state, _) in sorted(rows.items()) if state == "render"]
    counts = {s: sum(1 for st, _ in rows.values() if st == s) for s in ("current", "frozen", "render")}
    named = ", ".join(f"T{i:02d}" for i in renders) or "none"
    return (f"step 09 renders {len(renders)} take(s) ({named}): "
            + ", ".join(f"{n} {s}" for s, n in counts.items()))


# ---- the window and the order ----------------------------------------------------------------

def window_now(conn, home: Path, steps: list[str]) -> tuple[dict | None, str]:
    """The window the next drive runs on, and how it was found; nothing is written."""
    window = repair_clock.read(home)
    if window is not None and repair_clock.backed(conn, home, window):
        return window, f"open and backed by the owner receipt(s) {window['orders']}: the drive continues it"
    said = (f"open ({window['orders']}) but no owner receipt backs it: the drive start closes it; "
            if window is not None else "")
    if not repair_clock.delivered(home):
        return None, said + "not delivered (no manifest.json): no repair window, the episode's own clock"
    orders = work_orders.owner_receipts(conn, home) or {s: 0 for s in steps}
    assumed = {"opened_at": time.time(), "cap_s": repair_clock.cap_for(list(orders)), "steps": sorted(orders),
               "orders": dict(orders)}
    return assumed, said + f"assumed: the owner's redo of {', '.join(sorted(orders))} opens it at launch"


def order_needed(conn, home: Path, steps: list[str], redo: set[str], pending: list) -> str | None:
    """None when the owner's redo of `steps` still stands (still on the unit's redo list with an owner
    receipt, or pending); else what to write."""
    receipts = work_orders.owner_receipts(conn, home)
    owed = all(s in redo and s in receipts for s in steps)
    queued = all(any(r["kind"] == "redo" and r["step_id"] == s and r["by"] == "owner" for r in pending)
                 for s in steps)
    if owed or queued:
        return None
    return f"a new owner redo order for {', '.join(steps)} (studio_cli.py redo ...) before the launch"


def order_line(conn, home: Path, steps: list[str], redo: set[str], pending: list) -> str:
    receipts = work_orders.owner_receipts(conn, home)
    held = ", ".join(f"{s} by order #{receipts[s]}" for s in steps if s in receipts) or "none"
    need = order_needed(conn, home, steps, redo, pending)
    return (f"owner order: redo list {sorted(redo) or '[]'}; owner receipts {held}; pending {len(pending)}; "
            + ("no new order is needed: the taken order is still owed" if need is None else f"NEEDED: {need}"))


# ---- the prices --------------------------------------------------------------------------------

def budget_of(home: Path, window: dict | None):
    """The budget the drive would run on, on a frozen clock: the repair's, or the episode's own."""
    from studio.run_budget import EPISODE_CEILING_SECONDS, EPISODE_SHARES, OWNER_LIMIT_SECONDS, Budget
    if window is not None:
        return repair_clock.budget(home, window, clock=lambda: 0.0), repair_clock.spent(home, window)
    b = Budget(EPISODE_CEILING_SECONDS, EPISODE_SHARES, clock=lambda: 0.0, limit=OWNER_LIMIT_SECONDS)
    spent = run_budget.spent_before(home)
    b.charge(spent)
    return b, spent


def priced(home: Path, window: dict | None, refine_s: float, rung_s: float) -> dict:
    """Whether the refine, then one tiny-face draw after it, leave the reserve (face_refine.cut's rule)."""
    b, spent = budget_of(home, window)
    owed = b.owed_after(STEP)
    refine = b.leaves_reserve(STEP, refine_s + CHECK_RESERVE_S)
    b.charge(refine_s if refine else 0.0)
    rung = b.leaves_reserve(STEP, rung_s + CHECK_RESERVE_S)
    return {"spent_s": spent, "limit_s": b.limit, "owed_after_s": owed, "refine": refine, "rung": rung,
            "after_rung_s": spent + (refine_s if refine else 0.0) + rung_s + CHECK_RESERVE_S + owed}


def price_line(name: str, got: dict, refine_s: float, rung_s: float) -> str:
    word = lambda ok: "runs" if ok else "CUT"  # noqa: E731
    return (f"{name}: {got['spent_s']:.0f} s spent of {got['limit_s']:.0f} s; refine {refine_s:.0f} s "
            f"{word(got['refine'])}; then one tiny-face draw {rung_s:.0f} s {word(got['rung'])} "
            f"({got['after_rung_s']:.0f} s with the 550 s check reserve and {got['owed_after_s']:.0f} s owed "
            f"after 09)")


# ---- no writes ---------------------------------------------------------------------------------

def snapshot(home: Path) -> dict[str, tuple[int, int]]:
    """{relative name: (size, mtime_ns)} of the episode's own files and its takes' (two flat listings)."""
    out = {}
    for room in (Path(home), Path(home) / TAKES):
        for p in sorted(room.glob("*")) if room.is_dir() else []:
            if p.is_file():
                st = p.stat()
                out[p.relative_to(home).as_posix()] = (st.st_size, st.st_mtime_ns)
    return out


def changed(before: dict, after: dict) -> list[str]:
    return sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))


# ---- the report --------------------------------------------------------------------------------

STEP_09_ARGV = ["--from-refs", "--no-ends"]
"""The modes step 09 launches takes_r2v in (step_09_shoot.shoot): the cards are built under them."""


def as_step_09(takes_r2v) -> None:
    """takes_r2v's module modes set exactly as its __main__ sets them from step 09's argv."""
    for setter in (takes_r2v._set_no_ends, takes_r2v._set_from_refs, takes_r2v._set_pin_panel,
                   takes_r2v._set_tiny_face):
        setter(STEP_09_ARGV)


def render_rows(codex: str, number: int, home: Path, window: dict | None) -> dict[int, tuple[str, str]]:
    """Every card as takes_r2v.main builds it (same road: opened + cards), each take's state."""
    from scripts.episode import takes_r2v
    as_step_09(takes_r2v)
    book, episode = takes_r2v.opened(codex, number)
    built, room = takes_r2v.cards(book, episode, number), home / TAKES
    records = {r["index"]: r for r in episode_home.read_json(room / "shots.json")} if (room / "shots.json").exists() else {}
    return {int(c["index"]): take_state(c, room / f"T{int(c['index']):02d}.mp4", home, window,
                                        takes_r2v.card_pictures(c, book, number), (takes_r2v.W, takes_r2v.H), records)
            for c in built}


def checks_lines(home: Path) -> list[str]:
    """The dq cache (bytes and measuring code), the content verdicts, the eye, the retake ladder."""
    from scripts.episode import step_09_shoot as s09, take_dq
    from studio import step_attempts, step_caps, take_ladder
    room, code = home / TAKES, take_dq.measures_sha8()
    takes = s09.takes_of(room)
    dq = {t.name: episode_home.read_json(t.with_suffix(".dq.json")) if t.with_suffix(".dq.json").exists() else {}
          for t in takes}
    bytes_ok = [n for n, d in dq.items() if d.get("take_sha8") == tc.sha8_of(room / n)]
    code_ok = [n for n, d in dq.items() if d.get("measures_sha8") == code]
    content = [t.name for t in takes if s09.content_current(t)]
    ctx = SimpleNamespace(home=home)
    return [f"dq: {len(bytes_ok)}/{len(takes)} records on these bytes; {len(code_ok)}/{len(takes)} on today's "
            f"measuring code ({code}) -- the others re-measure (a check, never a render)",
            f"content: {len(content)}/{len(takes)} verdicts no older than their take",
            f"eye: a signed verdict for these bytes {'stands' if s09.signed_for(ctx, room) else 'is re-read (the retry stamp or new bytes)'}",
            f"retake cap: {step_attempts.count(home, take_ladder.RETAKES)}/{step_caps.rounds(take_ladder.RETAKES)} "
            f"episode rounds in attempts.json (a counter: what renders is the deciders' batch below)"]


# ---- the ladder's own deciders (incident 2, 2026-10-19 12:29 PDT) --------------------------------

def ladder_lines(home: Path, window: dict | None) -> list[str]:
    """The early round and the batched rung, each asked of the very function step 09 asks, on the
    episode's records under `window`: the dry check said "spent: no ladder render" off a counter while
    the early round queued frozen T01.  Nothing is written."""
    room, since = Path(home) / TAKES, run_budget.clock_reset_epoch(home)
    ctx = SimpleNamespace(home=Path(home), budget=budget_of(home, window)[0])
    return [rounds_line(room, since), early_line(ctx, room, since, window)] + rung_lines(ctx, room, since, window)


def measured_takes(room: Path) -> list[int]:
    """The takes with a dq record: what step 09's CPU lane hands the early round."""
    return sorted(int(t.stem[1:3]) for t in Path(room).glob("T??.mp4") if t.with_suffix(".dq.json").exists())


def batch_word(batch: dict) -> str:
    """`batch none`, or `batch T01, T07` with each early cure named."""
    named = [f"T{i:02d}" + (f" ({c[0]})" if isinstance(c, tuple) else "") for i, c in sorted(batch.items())]
    return "batch " + (", ".join(named) or "none")


def rounds_line(room: Path, since: float) -> str:
    """ladder.json as the next launch counts it (take_ladder.counted): a round no byte landed for is none."""
    from studio import take_ladder
    rounds = take_ladder.rounds_on_file(room)
    live = take_ladder.counted(room, rounds)
    void = [f"{r.get('why')} ({', '.join(f'T{int(i):02d}' for i in r.get('takes') or r.get('faults') or {})}): "
            f"landed nothing, not counted" for r in rounds if r not in live]
    return (f"ladder.json: {len(rounds)} round(s) on file, {len(live)} counted, "
            f"{take_ladder.rounds_of(room, since)} since the retry stamp; uncounted: {'; '.join(void) or 'none'}")


def early_line(ctx, room: Path, since: float, window: dict | None) -> str:
    """take_overlap.early_cures over every measured take, then early_affordable: the round the CPU lane queues."""
    from studio import take_overlap
    takes = measured_takes(room)
    cures = take_overlap.early_cures(room, takes, since, window=window)
    paid = "" if not cures else ("; affordable" if take_overlap.early_affordable(ctx, len(cures))
                                 else "; unaffordable: not queued")
    return f"early round (take_overlap.early_cures over {len(takes)} dq record(s)): {batch_word(cures)}{paid}"


def rung_lines(ctx, room: Path, since: float, window: dict | None) -> list[str]:
    """route -> batch_for: the batched rung as judged_gate's climb would take it.  A climb a counter closed
    (still_curable's own two) takes no rung, and the router's batch is printed beside it all the same, so
    the line shows what the freeze empties, not only what the counter does (skeptic round, incident 2)."""
    from studio import take_ladder
    verdict, source = recorded_verdict(room)
    head = f"take ladder (take_ladder.route -> batch_for over {source}): "
    routed = take_ladder.route(verdict, room, try_i=take_ladder.rounds_of(room, since) + 1, window=window)
    if closed := climb_closed(ctx.home, room, since):
        alone = ", ".join(f"T{i:02d}" for i in take_ladder.renderable(routed, room, [])) or "none"
        return [head + f"batch none (the climb is closed: {closed}; route -> batch_for alone: {alone})",
                frozen_line(room, verdict, window)]
    *_, kept, why = take_ladder.batch_for(ctx, take_ladder.BATCH, routed, [], records_of(room), since)
    return [head + batch_word(kept) + (f" ({why})" if why else ""), frozen_line(room, verdict, window)]


def climb_closed(home: Path, room: Path, since: float) -> str:
    """The counter that closes the climb before any rung (take_ladder.still_curable's two), or ''."""
    from studio import step_attempts, step_caps, take_ladder
    n = take_ladder.rounds_of(room, since)
    if n >= take_ladder.ROUNDS_CAP:
        return f"ladder.json {n}/{take_ladder.ROUNDS_CAP} counted rounds since the retry stamp"
    if take_ladder.episode_spent(home):
        return (f"attempts.json retakes {step_attempts.count(home, take_ladder.RETAKES)}/"
                f"{step_caps.rounds(take_ladder.RETAKES)} spent")
    return ""


def frozen_line(room: Path, verdict, window: dict | None) -> str:
    """The faulted takes the repair froze: in no batch, kept flagged at the terminal."""
    from studio import take_ladder
    kinds: dict[int, set[str]] = {}
    for f in verdict.faults:
        kinds.setdefault(take_ladder.index_of(f.where), set()).add(f.kind)
    named = [f"T{i:02d} ({', '.join(sorted(k))})" for i, k in sorted(kinds.items())
             if take_ladder.frozen_here(room, i, window)]
    return f"frozen and faulted (no cure batch; the terminal keeps them, keep_best flagged): {', '.join(named) or 'none'}"


def recorded_verdict(room: Path):
    """(the verdict the ladder would climb on, where it came from): the eye signed for these bytes when one
    is, else the dq rows alone (the next launch re-reads the eye; its dq rows are these)."""
    from studio import eye_verdict, take_overlap
    from studio.judges.verdict import Fault, Verdict
    takes = sorted(Path(room).glob("T??.mp4"))
    doc = eye_verdict.current(room, takes) if takes else None
    if doc and isinstance(doc.get("faults"), list):
        faults = [Fault(**f) for f in doc["faults"]]
        return (Verdict(judge="take_eye", version="1", passed=not faults, faults=faults, confidence=1.0,
                        reads=len(takes)), f"the signed eye_{doc.get('sha8')}.json")
    return take_overlap.dq_verdict(room, measured_takes(room)), "the dq rows (no eye signed for these bytes)"


def records_of(room: Path) -> dict[int, dict]:
    path = Path(room) / "shots.json"
    return {r["index"]: r for r in episode_home.read_json(path)} if path.exists() else {}


def rung_price(book: Path, number: int, home: Path, owed: dict[int, float]) -> tuple[float, str]:
    """One tiny-face draw of the refine-owed Spark take with the most planned people: the rung is decided
    by the refine's own refusals, so this prices its worst single draw."""
    from scripts.episode import tiny_face
    room, plan = home / TAKES, episode_home.read_json(home / "plan.json")
    cards = {int(c["index"]): c for c in episode_home.read_json(room / "prompts.json")}
    spark = {i: tiny_face.planned(plan, cards[i].get("shots") or [i]) for i in owed
             if i in cards and tiny_face.on_spark(cards[i])}
    if not spark:
        return 0.0, "no refine-owed take on the Spark graph: the rung cannot draw"
    worst = max(spark, key=lambda i: (len(spark[i]), -i))
    faces = max(1, len(spark[worst]))
    return tiny_face.price(1, faces), (f"worst single draw T{worst:02d} ({faces} planned people); "
                                       f"owed now: {sorted(tiny_face.owed(home)) or 'none until the refine refuses a 20-40 px face'}")


def refine_lines(codex: str, number: int, home: Path, window: dict | None) -> list[str]:
    from scripts.episode import face_refine as cli
    book = episode_home.book_dir(codex)
    owed = cli.owed(book, number)
    refine_s = sum(owed.values())
    rung_s, rung_said = rung_price(book, number, home, owed)
    lines = [f"refine owed: {len(owed)} take(s) {', '.join(f'T{i:02d}' for i in sorted(owed))} priced {refine_s:.0f} s",
             f"tiny-face rung: {rung_said}; priced {rung_s:.0f} s"]
    if window is not None:
        lines.append(price_line("repair clock", priced(home, window, refine_s, rung_s), refine_s, rung_s))
    lines.append(price_line("episode clock (no repair window)", priced(home, None, refine_s, rung_s), refine_s, rung_s))
    return lines


def downstream_lines(codex: str, number: int, home: Path) -> list[str]:
    """Steps 10-13: done now, and what the repair makes them do."""
    import importlib
    from studio import standing_approval
    book = episode_home.book_dir(codex)
    ctx = SimpleNamespace(book_dir=book, number=number, home=home, extra=[], stage="episode", unit=f"ep{number:02d}")
    said = {"10": "re-cuts when a take or refine.json is newer than the master (the refine writes refine.json), "
                  "then one av3 upscale; the new master is cut/master_iter"
                  f"{1 + max([0] + [int(p.stem[11:]) for p in (home / 'cut').glob('master_iter*.mp4') if p.stem[11:].isdigit()])}.mp4",
            "11": "QC and the master eye on the new master's bytes",
            "12": "delivers: manifest.json names the new QC sha",
            "13": ("PARKS on G-STANDING (no publish/standing.json): nothing uploads" if not standing_approval.ok(book)
                   else "WOULD UPLOAD: publish/standing.json is present")}
    out = []
    for step, mod in (("10", "step_10_edit"), ("11", "step_11_qc"), ("12", "step_12_deliver"), ("13", "step_13_publish")):
        try:
            done = bool(importlib.import_module(f"scripts.episode.{mod}").done(ctx))
        except Exception as why:                          # noqa: BLE001 -- a dry check reports, never stops
            done = f"unknown ({type(why).__name__})"
        out.append(f"step {step}: done now {done}; {said[step]}")
    return out


def report(conn, codex: str, number: int, steps: list[str]) -> list[str]:
    home = episode_home.home(episode_home.book_dir(codex), number)
    window, how = window_now(conn, home, steps)
    redo = work_orders.redo_steps(conn, codex, "episode", f"ep{number:02d}")
    pending = work_orders.pending_orders(conn, codex, "episode", f"ep{number:02d}")
    rows = render_rows(codex, number, home, window)
    lines = [f"repair window: {how}" + (f"; cap {window['cap_s']:.0f} s" if window else ""),
             order_line(conn, home, steps, redo, pending), "", count_line(rows)]
    lines += [f"  T{i:02d} {state:7} {why}" for i, (state, why) in sorted(rows.items())]
    lines += [relaunch_line(render_rows(codex, number, home, closed_form(window)) if window else rows)]
    return lines + [""] + checks_lines(home) + ladder_lines(home, window) + swap_block(home, window) + [""] + \
        refine_lines(codex, number, home, window) + [""] + downstream_lines(codex, number, home)


def relaunch_line(rows: dict[int, tuple[str, str]]) -> str:
    """Step 09 on a relaunch after this drive ends (receipt cleared, window closed into repair.jsonl)."""
    return "relaunch after the drive ends (the closed repair row governs): " + count_line(rows)


def swap_block(home: Path, window: dict | None) -> list[str]:
    """The terminal's best-draw swaps: keep_best_draws runs on every take the new eye faults, so every
    take an archived draw beats is named, measured from its own dq record (take_ladder.recorded_draw)."""
    from studio import take_ladder
    said = swap_lines(home, window, take_ladder.recorded_draw)
    return [f"terminal best-draw swaps (if the eye faults the take): {len(said)} candidate(s)"] + said


def swap_lines(home: Path, window: dict | None, runner) -> list[str]:
    """One line per take whose archived draw beats it (take_ladder.pick_best; nothing moves): KEPT when
    the repair froze its bytes, else SWAPS."""
    return [f"  {take.stem} best draw attempts/{best.name} ({measure(scored[best])}) over the take "
            f"({measure(scored[take])}): " + (f"KEPT, {froze} bytes frozen" if froze else "SWAPS")
            for take, best, scored, froze in swaps(home, window, runner)]


def swaps(home: Path, window: dict | None, runner) -> list[tuple]:
    """(take, best draw, scores, why frozen or None) for every take an archived draw beats."""
    from studio import take_ladder
    room, out = Path(home) / TAKES, []
    for take in sorted(room.glob("T??.mp4")):
        scored = take_ladder.scored_draws(room, int(take.stem[1:3]), runner)
        best = take_ladder.pick_best(room, int(take.stem[1:3]), runner, scored)
        if best is not None:
            out.append((take, best, scored, tc.frozen_in(window, take, home)))
    return out


def measure(m: dict) -> str:
    return f"hard {m['hard']}, Se {m.get('Se')}"


# ---- the launch refuses (deadline retro item 1, 2026-10-20) -------------------------------------------
# Every drive launch of a delivered episode runs this (drive.py) and refuses when a delivered take would be
# written without a named owner order.  All three stopped repair launches of ep01 (2026-10-19 11:18, 12:29,
# 13:54 PDT) were found by launching: this check existed, read counters, and nothing called it (RC2).

TAKE_NAMED = re.compile(r"\bT(\d{2})\b")
"""How an owner order names a take: `T05` in its note (studio_cli.py redo ... --note "retake T05: hands")."""
DELIVERED_TAKE = re.compile(r"takes/r2v/T(\d{2})\.mp4$")
RENDER_PASS = "render pass (takes_r2v.wants_render)"
EARLY = "early round (take_overlap.early_cures)"
RUNG = "take ladder (take_ladder.route -> batch_for)"
SWAP = "terminal best-draw swap (take_ladder.pick_best)"
FREEZE = "freeze (take_currency.frozen_in: what every T<nn>.mp4 writer asks)"


def owner_orders(conn, home: Path, codex: str, number: int) -> list[dict]:
    """The owner's redo orders this launch carries: receipted beside the episode (K12) or still pending for
    its unit.  An autopilot cure is never one."""
    ids = sorted(set(work_orders.owner_receipts(conn, home).values()))
    marks = ",".join("?" * len(ids))
    taken = [dict(r) for r in conn.execute(f"SELECT * FROM orders WHERE id IN ({marks})", ids)] if ids else []
    pending = [dict(r) for r in work_orders.pending_orders(conn, codex, "episode", f"ep{number:02d}")
               if r["kind"] == "redo" and r["by"] == "owner"]
    return taken + pending


def launch_window(conn, home: Path, orders: list[dict]) -> dict | None:
    """The repair the launch's step 09 runs under: a backed open window; else the one the owner's orders
    open at launch; else the row that governs today (take_currency.governing -- a leftover window no
    receipt backs is closed into that same row at drive start)."""
    window = repair_clock.read(home)
    if window is not None and repair_clock.backed(conn, home, window):
        return window
    steps = {str(o["step_id"]): int(o["id"]) for o in orders if o.get("step_id")}
    if steps:
        return {"opened_at": time.time(), "cap_s": repair_clock.cap_for(list(steps)), "steps": sorted(steps),
                "orders": steps}
    return tc.governing(home)


def delivered_takes(home: Path) -> set[int]:
    """The takes step 12's manifest.json delivered (its `takes/r2v/T<nn>.mp4` rows)."""
    try:
        rows = json.loads((Path(home) / "manifest.json").read_text(encoding="utf-8")).get("inputs") or []
    except (OSError, ValueError, AttributeError):
        return set()
    return {int(m.group(1)) for r in rows if (m := DELIVERED_TAKE.search(str(r.get("path", ""))))}


def would_render(home: Path, window: dict | None, rows: dict[int, tuple[str, str]]) -> dict[str, set[int]]:
    """site -> the takes it would write, each asked of its own decider under `window`; nothing is written."""
    from studio import take_ladder
    room, since = Path(home) / TAKES, run_budget.clock_reset_epoch(home)
    ctx = SimpleNamespace(home=Path(home), budget=budget_of(home, window)[0])
    return {RENDER_PASS: {i for i, (state, _) in rows.items() if state == "render"},
            EARLY: set(early_batch(room, since, window)),
            RUNG: set(rung_batch(ctx, room, since, window)),
            SWAP: {int(t.stem[1:3]) for t, _, _, froze in swaps(home, window, take_ladder.recorded_draw) if not froze},
            FREEZE: unfrozen(home, window)}


def early_batch(room: Path, since: float, window: dict | None) -> dict:
    """The early round's cures over every measured take.  Affordability is the live budget's call, so a take
    in the batch counts even when today's frozen clock could not pay it."""
    from studio import take_overlap
    return take_overlap.early_cures(room, measured_takes(room), since, window=window)


def rung_batch(ctx, room: Path, since: float, window: dict | None) -> dict:
    """The batched rung's batch (route -> batch_for); none when still_curable's counters close the climb."""
    from studio import take_ladder
    if climb_closed(ctx.home, room, since):
        return {}
    routed = take_ladder.route(recorded_verdict(room)[0], room, try_i=take_ladder.rounds_of(room, since) + 1,
                               window=window)
    return take_ladder.batch_for(ctx, take_ladder.BATCH, routed, [], records_of(room), since)[3]


def unfrozen(home: Path, window: dict | None) -> set[int]:
    """Under a repair of 09 or later, the takes on disk the freeze does not hold: their bytes are neither
    the manifest's nor their dq record's, so no writer's guard keeps them."""
    if window is None or min(window.get("steps") or ["00"]) < tc.FREEZE_FROM:
        return set()
    room = Path(home) / TAKES
    return {int(t.stem[1:3]) for t in room.glob("T??.mp4") if tc.frozen_in(window, t, home) is None}


def unordered(would: dict[str, set[int]], delivered: set[int], orders: list[dict]) -> dict[str, list[int]]:
    """site -> the delivered takes it would write that no owner order names; {} when the owner redid a step
    before 09 (the takes' inputs moved: every take it re-renders is ordered)."""
    if any(str(o.get("step_id") or "99") < tc.FREEZE_FROM for o in orders):
        return {}
    named = {int(m) for o in orders for m in TAKE_NAMED.findall(o.get("note") or "")}
    return {site: sorted(left) for site, takes in would.items() if (left := (takes & delivered) - named)}


def refusal_lines(left: dict[str, list[int]]) -> list[str]:
    """[] when nothing is left; else the REFUSED line (the autopilot reads it) and one line per site."""
    if not left:
        return []
    takes = sorted({i for site in left.values() for i in site})
    head = (f"REFUSED to start: the dry check lists {len(takes)} delivered take(s) that would be written without "
            f"a named owner order ({', '.join(f'T{i:02d}' for i in takes)}); name them in an owner order or fix "
            f"the decider")
    return [head] + [f"  {site}: {len(got)} take(s) {', '.join(f'T{i:02d}' for i in got)}"
                     for site, got in left.items()]


def refusals(conn, codex: str, number: int) -> list[str]:
    """[] when the launch may go; else what refuses it.  An undelivered episode is never refused."""
    home = episode_home.home(episode_home.book_dir(codex), number)
    if not repair_clock.delivered(home):
        return []
    orders = owner_orders(conn, home, codex, number)
    window = launch_window(conn, home, orders)
    would = would_render(home, window, render_rows(codex, number, home, window))
    return refusal_lines(unordered(would, delivered_takes(home), orders))


def preflight(conn, codex: str, number: int) -> list[str]:
    """What drive.py runs before any GPU second: `refusals`, refused too when the check cannot run or
    writes into the episode (a delivered episode launches only on a dry check that ran clean)."""
    home = episode_home.home(episode_home.book_dir(codex), number)
    before = snapshot(home)
    try:
        said = refusals(conn, codex, number)
    except (Exception, SystemExit) as why:            # noqa: BLE001 -- the render road refuses by SystemExit
        return [cannot_run(why)]
    if moved := changed(before, snapshot(home)):
        return [f"REFUSED to start: the dry check wrote into the episode ({', '.join(moved)})"] + said
    return said


def cannot_run(why: BaseException) -> str:
    """The refusal of a dry check that could not run: fail closed and say what broke."""
    return f"REFUSED to start: the dry check could not run ({type(why).__name__}: {why})"


def launch_preflight(connect, codex: str, number: int) -> list[str]:
    """`preflight` on the connection `connect` opens; a database that will not open refuses the same way,
    so the launch still writes its refused run log and end row (skeptic, package A round 2)."""
    try:
        conn = connect()
    except (Exception, SystemExit) as why:            # noqa: BLE001 -- fail closed
        return [cannot_run(why)]
    return preflight(conn, codex, number)


def main(codex: str, number: int, steps: list[str]) -> int:
    from studio import db
    home = episode_home.home(episode_home.book_dir(codex), number)
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    print(f"DRY CHECK {codex} ep{number:02d} at {head}, {time.strftime('%Y-%m-%d %H:%M')} local; "
          f"owner redo of {', '.join(steps)} assumed", flush=True)
    before, conn = snapshot(home), db.get_connection()
    lines = report(conn, codex, number, steps)
    moved = changed(before, snapshot(home))
    print("\n".join(lines), flush=True)
    print(f"\nepisode untouched: {'yes' if not moved else 'NO -- ' + ', '.join(moved)}", flush=True)
    refused = preflight(conn, codex, number)
    print("\nthe launch: " + ("\n".join(refused) if refused else "goes (no delivered take written unordered)"),
          flush=True)
    return 1 if moved or refused else 0


def steps_arg(argv: list[str]) -> list[str]:
    return next((a.split("=", 1)[1].split(",") for a in argv if a.startswith("--steps=")), [STEP])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], int(sys.argv[2]), steps_arg(sys.argv)))
