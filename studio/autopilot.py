"""The autopilot's pure core: an episode's state is a function of disk.

Decision 2026-10-06 (architecture/decisions/2026-10-06_autopilot_and_brain.md):
the pipeline was already a Python job, `drive.py`; what stopped was the
layer above it, a Claude session that watched the log, read a deferral and
ended its turn.  ep19 sat for hours between four launches that way.  So the
lifetime lives in Python, and every tick is `derive(signals) -> Derived`
over what drive.jsonl, the lock, the process table, uploads.jsonl, the
episode home and the last log say.  Nothing here spawns, reads a socket or
writes a file (two helpers read a ledger and replace a JSON atomically);
the supervisor and the CLI own the side effects and build `Signals`.

The one invariant (tests/test_autopilot_derives_state_from_disk.py): after
any tick on any fixture the state is one of the enum and the reason is
non-empty.  Silence is never a state.  PARKED is a record, never a wait.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from studio import episode_drive, run_budget
from studio.command_center import procs, vitals

RELAUNCH_CAP = 2
"""Stops a plain retry may answer before the brain reads the stop (H3: ep19
refused three plan runs in a row before the wall; the third is a question)."""
CURE_CAP = 2
"""Cures (a `redo`, a refs run, an engine restart) per episode before the brain."""
BRAIN_ATTEMPTS = 3
"""Brain sessions per episode; the fourth stop parks it (ops §3)."""
ENGINE_RESTARTS = 2
"""ComfyUI restarts per episode before PARK(engine) (ops §2)."""
CRASHES_BEFORE_BRAIN = 3
"""A `start` row with no `end` after it is a crash; three ask the brain."""
KINDS = {"completed", "retry", "cure", "wait", "brain", "park", "held", "quota"}


class State(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PUBLISHED = "PUBLISHED"
    NEEDS_BRAIN = "NEEDS_BRAIN"
    BRAIN_RUNNING = "BRAIN_RUNNING"
    WAIT_TREE = "WAIT_TREE"
    WAIT_QUOTA = "WAIT_QUOTA"
    """The usage window is shut: no brain call, a relaunch past its reset (group R A1,
    2026-10-22: a shut window parked episodes brain_exhausted after three brain asks)."""
    PARKED = "PARKED"
    PAUSED = "PAUSED"
    COMPLETE = "COMPLETE"
    HELD_PUBLISH = "HELD_PUBLISH"
    """A finished master step 13 holds at G-STANDING: a deliberate hold, never a
    park (retro 2026-10-20 item 7: ep01 parked twice on it and needed retry + resume)."""


@dataclass
class Signals:
    """What one tick read from disk for episode N (ops §3, the signal column)."""
    drive_rows: list[dict]              # episodes/epNN/drive.jsonl
    exit_code: int | None               # drive.py's exit, when the supervisor saw it
    lock: dict | None                   # library/.autopilot/gpu.lock body
    proc_alive: bool                    # the lock's pid runs drive.py for this episode
    uploads_rows: list[dict]            # library/<book>/uploads.jsonl
    parked_rows: list[dict]             # library/<book>/autopilot/parked.jsonl
    home_files: set[str]                # names under episodes/epNN ('plan.json', ...)
    log_tail: str                       # last lines of the last drive_runNN.log
    porcelain: str                      # git status --porcelain
    engine_up: bool                     # ComfyUI answered /system_stats
    clock_spent_s: float                # timing.jsonl sum
    brain_attempts: int                 # episodes/epNN/brain/attempt_NN.json count
    brain_verdict: dict | None          # the verdict written after the last end row
    paused: bool                        # series.json paused or the STOP file
    head_sha: str | None                # git rev-parse HEAD
    media_spent_usd: float              # spend.unit_spent
    failed_sha: str | None = None       # the commit the last drive row names (P13)
    code_dirty: bool = False            # a runtime file is modified or untracked (P13)
    standing: bool = False              # library/<book>/publish/standing.json is signed


@dataclass
class Derived:
    state: State
    reason: str
    order: tuple[str, str | None] | None = None
    packet: dict = field(default_factory=dict)


# --- the ledger ---------------------------------------------------------------

def crashes(drive_rows: list[dict]) -> int:
    """`start` rows with no `end` before the next `start`: the driver died
    (console closed, reboot) and nothing recorded the stop (ops §1 item 9)."""
    count, open_run = 0, False
    for row in drive_rows:
        if row.get("event") == "start":
            count += open_run
            open_run = True
        elif row.get("event") == "end":
            open_run = False
    return count + open_run


QUOTA_ERRORS = ("RateLimited", "LimitWait")
"""The run-row error words of a shut usage window (studio.llm.LimitWait)."""


def stops(drive_rows: list[dict]) -> int:
    """`end` rows with a non-zero code: how many times this episode has
    already stopped and been answered -- the counter every cap reads.  A
    boundary pause (C3 #7) and a shut usage window (group R A1) are no stop."""
    count, quota = 0, False
    for row in drive_rows:
        if row.get("event") == "run":
            quota = str(row.get("error") or "").endswith(QUOTA_ERRORS)
        elif row.get("event") == "end" and row.get("code") not in (0, None):
            count += not (row.get("paused_at_boundary") or quota)
    return count


def last_row(drive_rows: list[dict], event: str) -> dict | None:
    rows = [r for r in drive_rows if r.get("event") == event]
    return rows[-1] if rows else None


def exit_code(s: Signals) -> int | None:
    """The supervisor's own observation first; the ledger's last `end` row
    otherwise; None while the run has not ended -- and after a crash, whose
    `start` has no `end` (an older run's code is not this run's)."""
    if s.exit_code is not None:
        return s.exit_code
    end = last_row(s.drive_rows, "end")
    return None if end is None or crashed(s.drive_rows) else int(end.get("code", 1))


def crashed(drive_rows: list[dict]) -> bool:
    """The last `start` has no `end` after it."""
    for row in reversed(drive_rows):
        if row.get("event") == "end":
            return False
        if row.get("event") == "start":
            return True
    return False


def failed_sha(drive_rows: list[dict]) -> str | None:
    """The commit the newest ledger row that names one ran on: the code a
    failure was caused BY, which is not the code HEAD holds now (P13)."""
    shas = [str(r["sha"]) for r in drive_rows if r.get("sha")]
    return shas[-1] if shas else None


def head_moved(s: Signals) -> bool:
    """The failure belongs to a commit that is no longer HEAD: a fix landed since."""
    return bool(s.failed_sha and s.head_sha and s.failed_sha != s.head_sha)


def tree_dirty(s: Signals) -> bool:
    return bool(s.code_dirty) or episode_drive.dirty(s.porcelain)


def last_line(tail: str) -> str:
    lines = [ln.strip() for ln in (tail or "").splitlines() if ln.strip()]
    return lines[-1] if lines else ""


# --- the hand-back table -------------------------------------------------------

def _speech_gap(tail: str, home: set[str]) -> tuple[str, str, tuple | None]:
    """H6: a gap the trim left is the writer's to fix (redo 02) until takes
    exist; once rendered a recut would orphan them, so it parks."""
    if "takes" in home:
        return ("park", "speech_gap_rendered", None)
    return ("cure", "speech_gap", ("redo", "02"))


def _deferred_plan(tail: str, home: set[str]) -> tuple[str, str, tuple | None]:
    """H3 / H5: a CAST BOUND note wants the refs runner; any other plan
    deferral retries (each relaunch runs cure_aside_first for $0)."""
    # every refusal shape the battery and the bind step print -- a list, 'not
    # bound', 'no sheet for' -- and never the clean 'all bound' line (A71)
    refused = re.search(r"CAST BOUND\s*:\s*(?:\[|no sheet)|not bound|unbound", tail)
    if refused and "all bound" not in tail:
        return ("cure", "cast_unbound", ("refs", "04"))      # a refusal, never the clean 'all bound' line
    return ("retry", "plan_deferred", None)


QUOTA_LINE = re.compile(r"usage window (\S+) shut until (\S+)")
"""studio.llm.LimitWait's message: the window and the epoch it opens, or `unknown`."""


def quota_of(tail: str) -> tuple[str, float | None] | None:
    """(window, resets_at) off the last shut-window line; an unsaid epoch is None."""
    hits = QUOTA_LINE.findall(tail or "")
    if not hits:
        return None
    window, until = hits[-1]
    try:
        return window, float(until)
    except ValueError:
        return window, None


TABLE: list[tuple[str, object]] = [
    (r"EPISODE completed", ("completed", "completed", None)),
    (r"^studio\.llm\.OverBudget:", ("park", "over_budget", None)),
    # a shut usage window waits for its reset, never a brain turn (group R A1, 2026-10-22)
    (QUOTA_LINE.pattern, ("quota", "quota: {line}", None)),
    (r"REFUSED to start: the working tree is dirty", ("wait", "tree_dirty", None)),
    (r"title card could not be baked", ("brain", "title_card", None)),
    (r"HELD: ", ("wait", "held", None)),
    # no standing publish approval is the owner's own hold, not a fault (retro 2026-10-20 item 7)
    (r"^OWNER G-STANDING \|", ("held", "held_publish", None)),
    (r"^OWNER (\S+) \|", ("park", "escalated: {1}", None)),
    (r"DEFERRED PLAN \|", _deferred_plan),
    (r"ComfyUI's queue stayed busy", ("cure", "queue_busy", ("comfy_restart", None))),
    # a job the engine never finished (ep27 18:18Z: a grid hung an hour, /queue dead)
    (r"StillRunning: \S+ still running after \d+s", ("cure", "engine_hung", ("comfy_restart", None))),
    (r"REFUSED: the takes wait on the panels", ("cure", "takes_wait_on_panels", ("redo", "08"))),
    # the upload door's split voice is the record step's (ep21, 2026-10-08: the
    # brain read it as step 09's terminal and parked the episode)
    (r"speaker_check: .+ is not one voice", ("cure", "split_voice", ("redo", "04"))),
    # the same bytes refused again: nothing a relaunch changes -- the brain's
    (r"REFUSED: qc FAIL in \S+ for these exact bytes", ("brain", "qc_fail", None)),
    # a NEW master refused: the cut and take steps re-run themselves on a refused
    # master (a quiet cue lifted, an unjudged take measured); retry first (ep21,
    # ep24: the brain parked these as gates that gave up)
    (r"REFUSED: qc FAIL", ("retry", "qc_fail", None)),
    (r"REFUSED: qc\.py left no report", ("retry", "qc_no_report", None)),
    (r"speech gap", _speech_gap),
    (r"REFUSED: the plan has no shots", ("park", "no_shots", None)),
    (r"REFUSED: no (panels|takes) under", ("retry", "no_render_output", None)),
    (r"INVALID VERDICT", ("park", "invalid_verdict", None)),
    # the closed SAFETY list stops a spent-clock episode (C3_verdict #5 (v), gate_policy.SAFETY)
    (r"^(?:SystemExit: |RuntimeError: )?SAFETY: ", ("park", "safety: {line}", None)),
    (r"REFUSED: the takes want .* ceiling leaves", ("retry", "ceiling_refused_render", None)),
    (r"is NOT public", ("retry", "not_public", None)),
    (r"left no ledger row", ("retry", "no_ledger_row", None)),
    (r"vanished: the engine restarted|EngineLost|ConnectionError|RemoteDisconnected",
     ("retry", "engine_transient", None)),
    # another process held the studio database a moment (ep27, 2026-10-10)
    (r"OperationalError: database is locked", ("retry", "db_locked", None)),
    (r"google\.auth\.exceptions\.RefreshError|invalid_grant",
     ("park", "youtube_token_expired: run `uv run python scripts/publish/youtube_auth.py` (owner consent), then retry", None)),
    # Jekyll ep07 retro S5: a plan.json that fails the contract is a hand's fault, never a brain cure
    (r"ValidationError: \d+ validation errors? for Episode", ("park", "plan_contract: {line}", None)),
    (r"DEFERRED", ("brain", "deferred: {line}", None)),
    (r"REFUSED", ("brain", "refused: {line}", None)),
    (r"Traceback", ("brain", "failed: {line}", None)),
]
"""Ordered: the first pattern that matches the tail (multiline, any line)
wins.  Each H-row of the integrator's §4 table is one entry; a value is a
(kind, reason, order) triple or a function of (tail, home) for the rows whose
answer depends on what is on disk."""


def classify(tail: str, home_files: set[str]) -> tuple[str, str, tuple[str, str | None] | None]:
    """(kind, reason, order) for a drive log's last lines; `brain` with the
    last line when no row knows the words (H15's fallback)."""
    text = tail or ""
    for pattern, answer in TABLE:
        hit = re.search(pattern, text, flags=re.MULTILINE)
        if not hit:
            continue
        if callable(answer):
            return answer(text, home_files)
        kind, reason, order = answer
        reason = reason.replace("{line}", _said(text, pattern)).replace("{1}", hit.group(1) if hit.groups() else "")
        return (kind, reason, order)
    return ("brain", "unclassified: " + (last_line(text) or "the log is empty"), None)


def _said(text: str, pattern: str) -> str:
    """The line the fault was announced on: the last line that carries the
    pattern's word, else the log's last line (a traceback ends on its error)."""
    if pattern == "Traceback":
        return last_line(text)
    lines = [ln.strip() for ln in text.splitlines() if re.search(pattern, ln)]
    said = lines[-1] if lines else last_line(text)
    return re.sub(r"^(SystemExit|RuntimeError): ", "", said)


# --- the state machine --------------------------------------------------------

def episode_rows(rows: list[dict]) -> list[dict]:
    """The rows that name a chapter: a book-level row (book_compilation's
    episode='compilation') is another unit, and an int() on it stopped every
    tick from 2026-10-10 23:24Z."""
    return [r for r in rows if str(r.get("episode", "")).isdigit()]


def public_episodes(uploads_rows: list[dict]) -> set[int]:
    """The chapters live in public, rows read in order: a public upload adds one, a `deleted` row
    (the owner took the video down, Jekyll ep05 2026-10-28) removes it until a later upload."""
    live: set[int] = set()
    for r in episode_rows(uploads_rows):
        if r.get("deleted"):
            live.discard(int(r["episode"]))
        elif r.get("privacy") == "public":
            live.add(int(r["episode"]))
    return live


def published(uploads_rows: list[dict], n: int) -> bool:
    return n in public_episodes(uploads_rows)


REFUSAL_SIG = re.compile(r"G-[A-Z]+ T\d\d|stands at shot_\d\d")
"""The refusal lines a cure must move: `G-DEAD T10`, `stands at shot_07` (Jekyll ep07 retro S4)."""


def refusal_sig(tail: str) -> str:
    """The stop's refusal lines, sorted and joined; the last line when it names none."""
    hits = sorted(set(REFUSAL_SIG.findall(tail or "")))
    return "|".join(hits) if hits else last_line(tail or "")


def cure_spent(events: list[dict], n: int, order: dict, sig: str) -> bool:
    """This order already ran on episode N from a stop with this same signature: it moved nothing."""
    return any(r.get("event") == "brain_cure" and r.get("episode") == n and r.get("order") == order
               and r.get("sig") == sig for r in events)


NUDGE_EVERY_S = 6 * 3600.0
"""How often a finished, unpublished, parked episode is told again (Jekyll ep07: six silent days)."""
RETRY_S = 600.0
"""A nudge whose send failed is tried again this soon, never every tick."""


def nudge_due(drive_rows: list[dict], standing: bool, is_public: bool, told: list[tuple[float, bool]],
              now: float) -> bool:
    """A parked episode the chain carried to step 13 with standing approval is told until someone
    acts: at once, then every NUDGE_EVERY_S; a failed send again after RETRY_S.  `told` is (ts, sent)."""
    run = last_row(drive_rows, "run")
    if not (standing and run and str(run.get("step")) == "13") or is_public:
        return False
    if not told:
        return True
    at, sent = told[-1]
    return now - at >= (NUDGE_EVERY_S if sent else RETRY_S)


def parked(parked_rows: list[dict], n: int) -> dict | None:
    rows = [r for r in parked_rows if int(r.get("episode", -1)) == n]
    return rows[-1] if rows else None


def packet(s: Signals, n: int, reason: str) -> dict:
    """What the brain and the parked row get: relative names, the ledger's
    last run row, the fault line.  Never a path with a drive letter."""
    run = last_row(s.drive_rows, "run") or {}
    return {"episode": f"ep{n:02d}", "home": f"episodes/ep{n:02d}", "reason": reason,
            "exit_code": exit_code(s), "drive_row": {k: run[k] for k in ("n", "sha", "outcome") if k in run},
            "last_line": last_line(s.log_tail), "home_files": sorted(s.home_files),
            "brain_attempts": s.brain_attempts, "clock_spent_s": s.clock_spent_s,
            "media_spent_usd": s.media_spent_usd, "crashes": crashes(s.drive_rows),
            "failed_sha": s.failed_sha, "head": s.head_sha}


def _idle(s: Signals, n: int, reason: str, order=None) -> Derived:
    """A launch is wanted: the one deliberate wait is the owner's own dirty
    tree (a brain that commits his WIP is worse than a pause)."""
    if tree_dirty(s):
        return Derived(State.WAIT_TREE, "tree_dirty", None, packet(s, n, reason))
    if not s.engine_up:
        reason += " (engine down)"
    return Derived(State.IDLE, reason, order, packet(s, n, reason))


def _brain(s: Signals, n: int, reason: str) -> Derived:
    """The brain is asked at most BRAIN_ATTEMPTS times; then the episode parks.
    Never on a dirty tree (wait) or on a failure a newer commit may have fixed
    (one relaunch per new HEAD): Jekyll ep01 parked three episodes that way (P13)."""
    if tree_dirty(s):
        return Derived(State.WAIT_TREE, "tree_dirty", None, packet(s, n, reason))
    if head_moved(s):
        return _idle(s, n, "head_moved")
    if s.brain_attempts >= BRAIN_ATTEMPTS:
        return Derived(State.PARKED, "brain_exhausted", None, packet(s, n, reason))
    return Derived(State.NEEDS_BRAIN, reason, None, packet(s, n, reason))


def _verdict(s: Signals, n: int) -> Derived:
    """The brain is trusted by its file and git, never its prose: relaunch only
    when the verdict names HEAD and the tree is clean after it."""
    v = s.brain_verdict or {}
    said = v.get("verdict")
    if said in ("retry", "cure"):
        # ep21 (2026-10-07): a triage answer short of a fix is a launch order; the
        # in-process tick placed any cure order already.  Re-read, it must not
        # become another brain turn.
        return _idle(s, n, f"brain_{said}")
    if said != "relaunch":
        return _brain(s, n, f"brain: {said or 'no verdict'}")
    if tree_dirty(s):
        return Derived(State.WAIT_TREE, "tree_dirty", None, packet(s, n, "brain_relaunch"))
    if v.get("commit") != s.head_sha:
        return _brain(s, n, "brain: head is not the verdict's commit")
    return _idle(s, n, "brain_relaunch")


def _over_budget(s: Signals, n: int) -> Derived:
    """The $3 media wall (ops §3): a signed plan with no aside relaunches ONCE
    (the rest of the chain is $0 local); anything else parks.  ep19 had the
    aside, so it parks."""
    signed = "plan.json" in s.home_files and "plan.deferred.json" not in s.home_files
    failed = sum(1 for r in s.drive_rows if r.get("event") == "run" and r.get("outcome") in ("failed", "overbudget"))
    if signed and failed <= 1:
        return _idle(s, n, "over_budget_signed_plan")
    return Derived(State.PARKED, "over_budget", None, packet(s, n, "over_budget"))


def _answer(s: Signals, n: int, kind: str, reason: str, order) -> Derived:
    """A classified stop becomes a state; retries and cures are capped by the
    ledger's stop count, then the brain reads the stop."""
    if kind == "completed":
        return _brain(s, n, "no_upload_row")
    if kind == "wait" and reason == "tree_dirty" and not tree_dirty(s):
        # the end row is history; the tree is read every tick (2026-10-18: an hour on a clean tree)
        return _idle(s, n, "tree_clean")
    if kind == "wait":
        return Derived(State.WAIT_TREE if reason == "tree_dirty" else State.PAUSED, reason, None, packet(s, n, reason))
    if kind == "park":
        return Derived(State.PARKED, reason, None, packet(s, n, reason))
    if kind == "held":
        return _held(s, n)
    if kind == "brain":
        return _brain(s, n, reason)
    if kind == "quota":
        return Derived(State.WAIT_QUOTA, reason, None, packet(s, n, reason))
    cap = RELAUNCH_CAP if kind == "retry" else CURE_CAP
    if stops(s.drive_rows) > cap:
        return _brain(s, n, f"{kind}_exhausted: {reason}")
    return _idle(s, n, reason, order)


HELD_WHY = "held_publish: sign publish/standing.json (book-relative) to let step 13 upload"


def _held(s: Signals, n: int) -> Derived:
    """G-STANDING: HELD_PUBLISH until the owner signs; signed, the drive runs step 13 again."""
    if s.standing:
        return _idle(s, n, "standing_signed")
    return Derived(State.HELD_PUBLISH, HELD_WHY, None, packet(s, n, "held_publish"))


def _ended(s: Signals, n: int) -> Derived:
    """The run ended with a code: 0 wants the public row, 1 and 2 are read
    from the log through the table, the wall and the clock first."""
    if exit_code(s) == 0:
        return _brain(s, n, "no_upload_row")
    if re.match(r"^studio\.llm\.OverBudget:", last_line(s.log_tail)):
        return _over_budget(s, n)
    return _answer(s, n, *classify(s.log_tail, s.home_files))


def boundary_exit(s: Signals) -> bool:
    """The last drive stopped at a boundary (C3_verdict #7): a paused series
    reads PAUSED above; a resumed one relaunches, never counted as a stop."""
    end = last_row(s.drive_rows, "end")
    return bool(end and end.get("paused_at_boundary")) and not crashed(s.drive_rows)


CLOCK_LOOP = 3
"""Consecutive spent-clock stops (C3_verdict #5 (e)) before the episode parks:
a backstop against a relaunch loop, not a policy -- a spent clock relaunches."""


def clock_loop(s: Signals) -> bool:
    """The last CLOCK_LOOP drives each ended non-zero on a spent clock, and the
    tail is no SAFETY stop (that one parks by its own name)."""
    if s.clock_spent_s < run_budget.EPISODE_CEILING_SECONDS or "SAFETY: " in (s.log_tail or ""):
        return False
    ends = [r for r in s.drive_rows if r.get("event") == "end"][-CLOCK_LOOP:]
    return len(ends) == CLOCK_LOOP and all(r.get("code") not in (0, None) and r.get("clock_spent") for r in ends)


def named_park(s: Signals, n: int) -> Derived | None:
    """The table's own park for the last stop (the token, SAFETY, a plan contract), else None.
    Jekyll ep07: an expired token hid 6 days behind `clock_loop`; a named park outranks it."""
    kind, reason, _order = classify(s.log_tail, s.home_files)
    if kind != "park":
        return None
    return Derived(State.PARKED, reason, None, packet(s, n, reason))


def _clock_loop_park(s: Signals, n: int) -> Derived:
    """The backstop park, naming the last stop's classified cause so a reader can act on it."""
    _kind, reason, _order = classify(s.log_tail, s.home_files)
    return Derived(State.PARKED, f"clock_loop: {reason}", None, packet(s, n, "clock_loop"))


def derive(s: Signals, n: int) -> Derived:
    """One episode's state from one tick's signals (ops §3, every row).
    Order: the brakes and the records, the live process, the brain's verdict,
    the clock, a crash, then the exit code through the hand-back table."""
    if s.paused:
        return Derived(State.PAUSED, "paused", None, packet(s, n, "paused"))
    if published(s.uploads_rows, n):
        return Derived(State.PUBLISHED, "published", None, packet(s, n, "published"))
    if (row := parked(s.parked_rows, n)) is not None:
        return Derived(State.PARKED, f"parked: {row.get('reason', '?')}", None, packet(s, n, "parked"))
    if s.proc_alive:
        return Derived(State.RUNNING, "drive alive", None, packet(s, n, "running"))
    if s.brain_verdict is not None:
        return _verdict(s, n)
    if not s.drive_rows:
        return _idle(s, n, "launch")
    if boundary_exit(s):
        return _idle(s, n, "boundary_resume")
    if clock_loop(s):
        return named_park(s, n) or _clock_loop_park(s, n)
    if crashed(s.drive_rows) and s.exit_code is None:
        return _idle(s, n, "relaunch") if crashes(s.drive_rows) < CRASHES_BEFORE_BRAIN else _brain(s, n, "crash_loop")
    return _ended(s, n)


# --- pause leases and moved judge code (retro 2026-10-20 items 7, 12) ------------------

LEASE_S = {"retro": 2 * 3600.0, "autopilot": 2 * 3600.0}
"""How long a pause holds before it is said again, by who set it (V7: a retro pause
expires at 2 h).  An owner's pause holds until he says otherwise, or for his hours."""


def lease(by: str, why: str, now: float, hours: float | None = None, sha: str | None = None) -> dict:
    """{by, why, since, expires, sha}: who paused, why, and when the pause is owed a look."""
    held = hours * 3600.0 if hours is not None else LEASE_S.get(by)
    return {"by": by, "why": why, "since": now, "expires": None if held is None else now + held, "sha": sha}


def lease_expired(held: dict | None, now: float) -> bool:
    """Past its `expires`; a pause with no lease (one from before leases) never expires."""
    return bool(held) and held.get("expires") is not None and now >= float(held["expires"])


def may_resume(held: dict | None, now: float, head: str | None) -> bool:
    """Only a pause the autopilot set itself, only past its lease, and only once a
    commit landed since (the brake waits on a fix); never an owner's or a retro's."""
    if not held or held.get("by") != "autopilot" or not lease_expired(held, now):
        return False
    return bool(head and held.get("sha") and not str(head).startswith(str(held["sha"])))


JUDGE_CODE = re.compile(r"^(studio/judges/|studio/measure/|studio/\w*(?:_gates?|_dq|_currency|judged|gate_policy)\.py$"
                        r"|scripts/episode/\w*(?:_check|_dq|qc|eye_review)\.py$|gates\.yaml$)")
"""A file whose change can turn a verdict already on disk: the judges, the measures,
the gates, the dq and content checks, qc and gates.yaml."""


def invalidated_checks(names: list[str]) -> list[str]:
    """The checks a diff's judge code invalidates, by name, sorted (retro item 12)."""
    hits = {Path(n.strip()).stem if n.strip().endswith(".py") else Path(n.strip()).name
            for n in names if JUDGE_CODE.search(n.strip().replace("\\", "/"))}
    return sorted(hits)


# --- the lock, the series, the status ---------------------------------------------

def stale_lock(lock: dict | None, proc_rows: list[procs.ProcInfo], codex: str, n: int) -> bool:
    """A lock is stale when its pid is gone, runs another command line, or
    started after the lock did (a reused id after a reboot).  No lock is not
    stale: there is nothing to recover."""
    if not lock:
        return False
    mine = [p for p in proc_rows if p.pid == lock.get("drive_pid")]
    hit = procs.find_drive(mine, codex, n)
    return not vitals.pid_alive(hit, lock.get("started"))


def next_unit(chapters: list[int], uploads_rows: list[dict], parked_rows: list[dict], last: int | None) -> int | None:
    """The lowest chapter with no public upload and no parked row, capped at
    `last` (book.json episodes); None means the series is complete."""
    done = public_episodes(uploads_rows) | {int(r["episode"]) for r in parked_rows}
    left = [c for c in chapters if c not in done and (last is None or c <= last)]
    return min(left) if left else None


def status(derived: Derived, s: Signals, series: dict, now: str | None = None) -> dict:
    """status.json (ops §5): the contract keys, rewritten every tick.  `series`
    carries what the supervisor knows beyond one episode (pids, heartbeat,
    engine counters, events); every path in it is book-relative."""
    run = last_row(s.drive_rows, "run") or {}
    start = last_row(s.drive_rows, "start") or {}
    sha = str(start.get("sha") or run.get("sha") or "")[:8]
    n = int(derived.packet.get("episode", "ep00")[2:]) if derived.packet else series.get("n")
    return {
        "ts": now or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "supervisor_pid": series.get("supervisor_pid"),
        "heartbeat_age_s": series.get("heartbeat_age_s"),
        "engine": {"up": s.engine_up, "queue_running": series.get("queue_running", 0),
                   "restarts_today": series.get("restarts_today", 0)},
        "series": {k: series.get(k) for k in ("book", "first", "last", "published", "parked", "next", "state")},
        "episode": {"n": n, "state": derived.state.value, "reason": derived.reason, "order": derived.order,
                    "drive_pid": (s.lock or {}).get("drive_pid"), "sha": sha, "run": run.get("n"),
                    "step": run.get("step"), "clock_spent_s": s.clock_spent_s,
                    "media_spent_usd": s.media_spent_usd, "brain_attempts": s.brain_attempts},
        "last_events": list(series.get("last_events") or [])[-5:],
    }


# --- the two file helpers ----------------------------------------------------------

def read_jsonl(path: Path | str) -> list[dict]:
    """The rows of a ledger; a missing file is no rows, a bad line is skipped
    (a row half-written at a crash must not take the ledger with it)."""
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    return rows


def write_json_atomic(path: Path | str, doc: dict) -> Path:
    """tmp + os.replace: a reader sees the old status or the new one, never a
    torn file (the board polls status.json while the supervisor writes it)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
    return path
