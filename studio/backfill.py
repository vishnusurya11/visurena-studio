"""The backfill: the work-order row a unit's FILES imply (decision 2026-09-25,
"Migration, zero loss"; plan row C8).

Pure derivation, nothing here runs a step.  For every (book, department, unit)
on disk the registry's `out:` globs say which steps have written, the
department's deliverable (the manifest, or the pre-manifest episode pair of a
master under cut/ and a qc_r2v.json that passed) says `done`, a
plan.deferred.json with no signed plan says `deferred`, and anything else is
`blocked` at the last step with an output.  Verdicts and flags come from
studio.verdict_rows, GPU seconds from studio.timing_sum, attempts and clocks
from the events when the unit has any, else from file mtimes (noted).

A row the files do not settle -- a folder outside the unit grammar, a live
run, a hand-signed verdict, a published unit with no qc file -- is LISTED with
its reason and written only with force.  A row whose run is live is never
written at all.  Every path is book-relative posix; the library root is the
caller's and is never stored.
"""
from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from studio import db, manifest, registry, timing_sum, verdict_rows

SOURCE = "backfill"
LIVE_WINDOW = timedelta(hours=6)
PUBLISH_STAGE = "publish"
UNIT_GRAMMAR = {"episode": re.compile(r"^ep\d\d$")}
"""The unit names a department's runner would produce (episode_run.unit_of)."""
TS = "%Y-%m-%dT%H:%M:%SZ"
PUBLISH_CAVEAT = "stage 'publish' is not in the registry: no view; written only with --with-publish"


# --- what the disk says -------------------------------------------------------


def number_of(unit: str) -> int | None:
    """The chapter number an episode unit names; None for a book-level unit."""
    found = re.match(r"^ep(\d+)$", unit)
    return int(found.group(1)) if found else None


def units_of(book_dir: Path, stage: str) -> list[str]:
    """The units a book's folders name for a department: every folder under
    episodes/ for the episode stage (the grammar is checked later, so a stray
    folder is listed, not lost), 'main' when the department's folder exists;
    a stage that declares no outputs has nothing to derive from."""
    book = Path(book_dir)
    if not any(registry.outputs_of(stage, s["id"]) for s in registry.steps(stage)):
        return []
    if stage == "episode":
        root = book / "episodes"
        return sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []
    return ["main"] if (book / stage).is_dir() else []


def step_outputs(book_dir: Path, stage: str, unit: str) -> dict[str, tuple[bool, list[str]]]:
    """Per registry step: (every declared output has a file, the files found)."""
    out: dict[str, tuple[bool, list[str]]] = {}
    for step in registry.steps(stage):
        patterns = registry.outputs_of(stage, step["id"], unit)
        found = [manifest.matched(book_dir, [p]) for p in patterns]
        files = sorted({rel for hits in found for rel in hits})
        out[step["id"]] = (bool(patterns) and all(found), files)
    return out


def legacy_deliverable(book_dir: Path, home: str) -> str | None:
    """The pre-manifest episode pair: a master under cut/ (master_r2v.mp4
    first, else a master_iterN) beside a qc_r2v.json that passed."""
    book = Path(book_dir)
    masters = manifest.matched(book, [f"{home}/cut/master_r2v.mp4", f"{home}/cut/master_iter*.mp4"])
    qc = book / home / "qc_r2v.json"
    if not masters or not qc.exists():
        return None
    try:
        passed = json.loads(qc.read_text(encoding="utf-8")).get("passed")
    except (OSError, ValueError):
        return None
    preferred = [m for m in masters if m.endswith("/master_r2v.mp4")]
    return (preferred or masters)[0] if passed else None


def deliverable_of(book_dir: Path, stage: str, unit: str, home: str) -> str | None:
    """The department's deliverable as the registry names it (the manifest),
    else, for an episode from before the manifest, the legacy pair."""
    found = verdict_rows.deliverable(book_dir, stage, unit)
    if found or stage != "episode":
        return found
    return legacy_deliverable(book_dir, home)


def last_step(stage: str, outputs: dict[str, tuple[bool, list[str]]]) -> str | None:
    """The last step with an output of THIS unit on disk: a step whose outputs
    are all book-level (bind's refs.json, the places every episode shares)
    cannot say where one unit stands, so only `{unit}`-templated outputs
    count -- unless the stage templates nothing, when every output does."""
    templated = {step_id for step_id in outputs
                 if any("{unit}" in p for p in registry.outputs_of(stage, step_id))}
    last = None
    for step_id, (_all, files) in outputs.items():
        if files and (step_id in templated or not templated):
            last = step_id
    return last


def state_of(book_dir: Path, home: str, deliverable: str | None, last: str | None) -> tuple[str, str | None]:
    """(state, step_id): `done` when the deliverable exists; `deferred` on a
    plan.deferred.json with no signed plan beside it; else `blocked` -- at
    the last step with an output either way."""
    if deliverable:
        return "done", last
    folder = Path(book_dir) / home
    if (folder / "plan.deferred.json").exists() and not (folder / "plan.verdict.json").exists():
        return "deferred", last
    return "blocked", last


def verdicts_of(book_dir: Path, stage: str, unit: str) -> dict[str, dict]:
    """Every gate the department's steps sign, from the newest file of each."""
    merged: dict[str, dict] = {}
    for step in registry.steps(stage):
        merged.update(verdict_rows.step_rows(book_dir, stage, step["id"], unit))
    return merged


def mtimes(book_dir: Path, files: list[str]) -> tuple[str | None, str | None]:
    """(earliest, latest) modification time of the files that exist, UTC."""
    book = Path(book_dir)
    stamps = sorted((book / rel).stat().st_mtime for rel in files if (book / rel).exists())
    if not stamps:
        return None, None
    first, last = (datetime.fromtimestamp(t, timezone.utc).strftime(TS) for t in (stamps[0], stamps[-1]))
    return first, last


def timestamps(book_dir: Path, files: list[str], events: dict, done: bool) -> tuple[dict, bool]:
    """started_at / finished_at from the events when the unit has any, else
    from the files' mtimes; the bool says the mtimes were used."""
    if events.get("started_at"):
        return {"started_at": events["started_at"],
                "finished_at": events.get("finished_at") if done else None}, False
    first, last = mtimes(book_dir, files)
    return {"started_at": first, "finished_at": last if done else None}, True


def note_of(verdicts: dict, done: bool, from_mtime: bool) -> str | None:
    """The row's note: a done unit no judge ever signed (pre-judge episodes)
    and clocks read off mtimes; None when neither applies."""
    parts = []
    if done and not verdicts:
        parts.append("grandfathered: no verdict file")
    if from_mtime:
        parts.append("ts:mtime")
    return "; ".join(parts) or None


def derive_unit(book_dir: Path, codex_id: str, stage: str, unit: str, events_status: dict) -> dict | None:
    """The work-order row the unit's files imply; None for a stage that
    declares no outputs (nothing on disk answers for it)."""
    outputs = step_outputs(book_dir, stage, unit)
    if not any(registry.outputs_of(stage, s) for s in outputs):
        return None
    home = manifest.home_of(stage, unit)
    deliverable = deliverable_of(book_dir, stage, unit, home)
    state, step_id = state_of(book_dir, home, deliverable, last_step(stage, outputs))
    files = [rel for _all, hits in outputs.values() for rel in hits]
    verdicts = verdicts_of(book_dir, stage, unit)
    stamps, from_mtime = timestamps(book_dir, files, events_status, state == "done")
    return {"codex_id": codex_id, "stage": stage, "unit": unit, "number": number_of(unit),
            "state": state, "step_id": step_id,
            "progress": f"{sum(done for done, _ in outputs.values())}/{len(outputs)}",
            "attempts": events_status.get("attempts", 0), "flags": verdict_rows.flags(book_dir, unit),
            "gpu_seconds": timing_sum.gpu_seconds_of(Path(book_dir) / home), "deliverable": deliverable,
            "verdicts": json.dumps(verdicts, sort_keys=True), **stamps, "source": SOURCE,
            "note": note_of(verdicts, state == "done", from_mtime)}


# --- what the events say --------------------------------------------------------


def is_live(ts: str, event: str, now: datetime | None = None) -> bool:
    """A `started` with no terminal event after it, inside the window."""
    if event != "started":
        return False
    when = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return (now or db.utc_now()) - when < LIVE_WINDOW


def events_summary(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str,
                   now: datetime | None = None) -> dict:
    """The unit's events folded: latest event per step, attempts (passes: one
    per run_id that started), the first start, the final step's last
    completion, the last event and whether it is live.  {} with no events."""
    rows = list(conn.execute(
        "SELECT event_ts, step_id, event, run_id FROM events"
        " WHERE codex_id = ? AND stage = ? AND unit = ? ORDER BY event_ts, id", (codex_id, stage, unit)))
    if not rows:
        return {}
    started = [r for r in rows if r["event"] == "started"]
    final = db._final_step_id(stage)
    finished = [r["event_ts"] for r in rows if r["event"] == "completed" and r["step_id"] == final]
    last = rows[-1]
    return {"status": {r["step_id"]: r["event"] for r in rows}, "attempts": len({r["run_id"] for r in started}),
            "started_at": started[0]["event_ts"] if started else None,
            "finished_at": finished[-1] if finished else None,
            "last": {"ts": last["event_ts"], "event": last["event"], "run_id": last["run_id"]},
            "live": is_live(last["event_ts"], last["event"], now)}


# --- the publish row (no registry stage yet) --------------------------------------


def upload_rows(book_dir: Path, number: int) -> list[dict]:
    """The upload ledger's rows for one episode number, in the order written."""
    path = Path(book_dir) / "uploads.jsonl"
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r for r in rows if r.get("episode") == number]


def publish_row(book_dir: Path, codex_id: str, unit: str) -> dict | None:
    """A `publish` work-order row from the unit's youtube.json and its upload
    rows: the unit is the uploaded master's sha8 at the platform, the note the
    video id and the privacy it ended on; None when nothing was uploaded."""
    number = number_of(unit)
    home = manifest.home_of("episode", unit)
    rows = upload_rows(book_dir, number) if number is not None else []
    uploads = [r for r in rows if r.get("video_id") and r.get("sha8")]
    if not uploads or not (Path(book_dir) / home / "youtube.json").exists():
        return None
    latest = uploads[-1]
    privacy = ([r["privacy"] for r in rows if r.get("privacy")] or ["unknown"])[-1]
    return {"codex_id": codex_id, "stage": PUBLISH_STAGE, "unit": f"{latest['sha8']}@youtube",
            "number": number, "kind": "master", "home": f"publish/{latest['sha8']}@youtube",
            "state": "done", "deliverable": f"{home}/youtube.json", "finished_at": latest.get("at"),
            "note": f"video {latest['video_id']} {privacy}; from {unit}", "source": SOURCE}


# --- the plan: what would be written, and why not --------------------------------


def published_unsettled(home: Path) -> str | None:
    """A unit declared to the platform (youtube.json) whose qc file is missing
    or did not pass (the owner waived it at upload): the files alone cannot
    call it done."""
    if not (home / "youtube.json").exists():
        return None
    qc = home / "qc_r2v.json"
    if not qc.exists():
        return "published but no qc file"
    try:
        passed = json.loads(qc.read_text(encoding="utf-8")).get("passed")
    except (OSError, ValueError):
        passed = None
    return None if passed else "published but qc did not pass"


def ambiguous(book_dir: Path, codex_id: str, stage: str, unit: str, row: dict, events_status: dict) -> str | None:
    """Every reason the row is not written without force, joined; None when
    the files settle it."""
    reasons = []
    grammar = UNIT_GRAMMAR.get(stage)
    if grammar and not grammar.match(unit):
        reasons.append("outside the unit grammar")
    if events_status.get("live"):
        last = events_status["last"]
        reasons.append(f"a live run ({last['run_id']} started {last['ts']}, no terminal event since)")
    hand = [f"{gate} by {str(rec.get('by', ''))[:40]}" for gate, rec in json.loads(row["verdicts"] or "{}").items()
            if not str(rec.get("by", "")).startswith("judge:")]
    if hand:
        reasons.append("hand-signed verdict: " + ", ".join(hand))
    if unsettled := published_unsettled(Path(book_dir) / manifest.home_of(stage, unit)):
        reasons.append(unsettled)
    return "; ".join(reasons) or None


def books_of(library: Path, codex_ids: list[str] | None = None) -> list[tuple[str, Path]]:
    """(codex_id, folder) for every book folder in the library, sorted; a
    codex list narrows it."""
    out = []
    for folder in sorted(Path(library).iterdir()):
        codex = folder.name[:14]
        if folder.is_dir() and codex.isdigit() and (not codex_ids or codex in codex_ids):
            out.append((codex, folder))
    return out


def existing_row(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str) -> sqlite3.Row | None:
    """The row the table has, or None -- also when the DB has no table yet
    (the live one opened read-only before its migration)."""
    try:
        return db.work_order(conn, codex_id, stage, unit)
    except sqlite3.OperationalError:
        return None


def live_run_of(existing) -> str | None:
    """The run_id that owns the row while it is running; None otherwise."""
    if existing is not None and existing["run_id"] and existing["state"] == "running":
        return existing["run_id"]
    return None


def plan_unit(conn: sqlite3.Connection, book: Path, codex_id: str, stage: str, unit: str,
              now: datetime | None) -> dict | None:
    """One plan entry: the derived row, why it is ambiguous, what the table holds."""
    events = events_summary(conn, codex_id, stage, unit, now)
    row = derive_unit(book, codex_id, stage, unit, events)
    if row is None:
        return None
    existing = existing_row(conn, codex_id, stage, unit)
    return {"row": row, "ambiguous": ambiguous(book, codex_id, stage, unit, row, events),
            "existing_state": existing["state"] if existing is not None else None,
            "live_run": live_run_of(existing)}


def publish_entry(conn: sqlite3.Connection, row: dict) -> dict:
    """A publish row's plan entry: never ambiguous, always carrying the caveat
    that its stage is not registered."""
    existing = existing_row(conn, row["codex_id"], row["stage"], row["unit"])
    return {"row": row, "ambiguous": None, "caveat": PUBLISH_CAVEAT,
            "existing_state": existing["state"] if existing is not None else None,
            "live_run": live_run_of(existing)}


def plan_stage(conn: sqlite3.Connection, book: Path, codex_id: str, stage: str,
               with_publish: bool, now: datetime | None) -> list[dict]:
    """Every entry one department of one book yields."""
    out = []
    for unit in units_of(book, stage):
        entry = plan_unit(conn, book, codex_id, stage, unit, now)
        if entry:
            out.append(entry)
        if with_publish and stage == "episode" and (row := publish_row(book, codex_id, unit)):
            out.append(publish_entry(conn, row))
    return out


def plan(conn: sqlite3.Connection, library: Path, codex_ids: list[str] | None = None, *,
         with_publish: bool = False, now: datetime | None = None) -> list[dict]:
    """Every (book, department, unit) on disk as a plan entry."""
    return [entry for codex_id, book in books_of(library, codex_ids)
            for stage in registry.stage_names()
            for entry in plan_stage(conn, book, codex_id, stage, with_publish, now)]


# --- writing and listing ----------------------------------------------------------


def writable(entry: dict, force: bool) -> bool:
    """A live run is never overwritten; an ambiguous row only with force."""
    return not entry["live_run"] and (force or not entry["ambiguous"])


def write(conn: sqlite3.Connection, entries: list[dict], force: bool = False) -> int:
    """Upsert the plan's rows through db.upsert_work_order; how many were written."""
    written = 0
    for entry in entries:
        if not writable(entry, force):
            continue
        row = dict(entry["row"])
        codex_id, stage, unit = row.pop("codex_id"), row.pop("stage"), row.pop("unit")
        db.upsert_work_order(conn, codex_id, stage, unit, **row)
        written += 1
    return written


def verdict_words(row: dict) -> str:
    """`GATE=word` per gate, or '-' when nothing is signed."""
    recs = json.loads(row.get("verdicts") or "{}")
    return " ".join(f"{gate}={rec.get('word') or '-'}" for gate, rec in sorted(recs.items())) or "-"


def line_of(entry: dict) -> str:
    """One listing line: the unit, its derived row, and why it would not be written."""
    row = entry["row"]
    tail = (entry["ambiguous"] and f"AMBIGUOUS: {entry['ambiguous']}") or (
        entry["live_run"] and f"SKIP: live run {entry['live_run']}") or entry.get("caveat") or ""
    if entry.get("existing_state"):
        tail = f"{tail} (row: {entry['existing_state']})".strip()
    return (f"{row['codex_id']}  {row['stage']:<8} {row['unit']:<16} {row['state']:<9} "
            f"step {row.get('step_id') or '--':>2}  {verdict_words(row)}  flags {row.get('flags', 0)}  "
            f"gpu {(row.get('gpu_seconds') or 0) / 3600:.1f}h  {tail}").rstrip()


def totals(entries: list[dict]) -> str:
    """The counts under the listing: derivable, ambiguous, live-skipped; by state; by book."""
    by_state = Counter(e["row"]["state"] for e in entries)
    by_book = Counter(e["row"]["codex_id"] for e in entries)
    live = sum(1 for e in entries if e["live_run"])
    amb = sum(1 for e in entries if e["ambiguous"] and not e["live_run"])
    return "\n".join([
        f"rows: {len(entries)}  derivable: {len(entries) - amb - live}  ambiguous: {amb}  live-skipped: {live}",
        "by state: " + (", ".join(f"{s} {n}" for s, n in sorted(by_state.items())) or "-"),
        "by book: " + (", ".join(f"{b} {n}" for b, n in sorted(by_book.items())) or "-")])


def listing(entries: list[dict]) -> str:
    """The dry-run text: a header, one line per unit, the totals."""
    header = "codex           stage    unit             state     step  verdicts  flags  gpu  why not"
    return "\n".join([header, *(line_of(e) for e in entries), "", totals(entries)])
