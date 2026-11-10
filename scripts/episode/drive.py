#!/usr/bin/env python
"""Drive one episode to its end, unattended: the ONE way to launch a run.

    uv run python scripts/episode/drive.py <codex_id> <episode>

Refuses a dirty tree (the code is frozen for the episode), records the SHA it
ran in `episodes/epNN/drive.jsonl`, runs `episode.py`, resumes a DEFERRED run,
and tells the owner on Telegram when the run completes, stops, or goes silent
for SILENCE_S (studio/episode_drive).  Ten-agent plan fixes #1 and #2.

THE RE-CHECK CADENCE, in numbers: the drive polls the run's log for growth
every POLL_S (30 s); a log silent for episode_drive.SILENCE_S (20 min) is
reported to the owner ONCE per silence; MAX_RUNS is 6 -- five resumes, and
since judged_gate no longer emits budget deferrals (a spent clock is terminal
in the same run, five-hour verdict) those resumes serve only PLAN deferrals.
A spent clock no longer stops a resume (C3_verdict #5 (iii)); the `end` row
records `clock_spent` for the autopilot's clock_loop backstop.

THE DIRTY-TREE RULE AND THE SIBLING SESSIONS: episode_drive.dirty() refuses
any tracked change or any untracked file OUTSIDE library/, so a sibling
session writing book data under library/<book>/ never blocks a drive, while
any code edit does until it is committed -- one episode runs on one commit
(fix #7), and a drive on moved code says so out loud.

THE DRY CHECK REFUSES (deadline retro item 1, 2026-10-20): a launch of a DELIVERED episode runs
repair_dry_check.preflight first -- the real deciders, never a counter -- and exits 2 with a
`REFUSED to start: the dry check ...` run log when a delivered take would be written without a named
owner order (all three stopped ep01 repair launches of 2026-10-19 were found by launching).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import episode_drive, episode_home, settings  # noqa: E402


def utf8_console() -> None:
    """The console never kills the run: a quoted chapter span can carry any
    character, and Windows hands the drive a cp1252 stdout (ep16, 2026-10-01:
    the deferral summary print raised UnicodeEncodeError and the drive died
    mid-episode).  Logs are opened utf-8 already; this covers the console."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

NOTIFY = Path("D:/Projects/KingdomOfViSuReNa/alpha/comfy_studio/poc/2026-08-25_2k-video-pipeline/scripts/notify_bench.py")
FFMPEG_DIR = "C:/Users/vishn/bin"
POLL_S = 30


def git(*args: str) -> str:
    """HEAD and porcelain: the checkout, or the sandbox's 1-commit repo in a rehearsal, so the
    dirty-tree refusal never reads other builders' edits there.  Children keep cwd=ROOT."""
    return subprocess.run(["git", *args], cwd=settings.git_root(), capture_output=True, text=True,
                          check=True).stdout


def quiet(env=os.environ) -> bool:
    """DRIVE_QUIET=1 (autopilot 2026-10-06): the drive prints only; the
    supervisor owns the owner's channel and says PUBLISHED, PARKED and
    SERIES_COMPLETE once each, so a run never doubles its lines."""
    return env.get("DRIVE_QUIET", "").strip().lower() in ("1", "true", "yes")


def notify(text: str) -> bool:
    """Telegram, through the sibling project's tested script; a failed send is printed, never fatal.
    True only when the script exited 0 (Jekyll ep07 retro S3: a 'told' row proved no delivery)."""
    print(f"[drive] {text}", flush=True)
    if quiet():
        return False
    try:
        done = subprocess.run(["uv", "run", "--no-sync", "python", str(NOTIFY), "text", "--message", text[:3500]],
                              cwd=NOTIFY.parents[1], timeout=120, check=False)
    except (OSError, subprocess.SubprocessError) as why:
        print(f"[drive] notify failed: {why}", flush=True)
        return False
    if done.returncode != 0:
        print(f"[drive] notify failed: exit {done.returncode}", flush=True)
    return done.returncode == 0


def ledger(home: Path, row: dict) -> None:
    with (home / "drive.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), **row}) + "\n")


def run_row(n: int, sha: str, text: str) -> dict:
    """The `run` ledger row: the outcome word and, when the log ended on a
    `<Class>: ...` line, the class -- so the supervisor reads a word, never
    the log's prose (autopilot 2026-10-06; ep19's OverBudget read `failed`)."""
    row = {"event": "run", "n": n, "sha": sha, "outcome": episode_drive.outcome(text)}
    if error := episode_drive.error_class(text):
        row["error"] = error
    if step := episode_drive.last_step(text):
        row["step"] = step                      # P13: where the run stopped, for the brain and the card
    return row


def silence_row(log_name: str, seconds: float) -> dict:
    """The ledger row for a log silent past SILENCE_S: written even under DRIVE_QUIET,
    where the Telegram stays with the supervisor (P13)."""
    return {"event": "silent", "minutes": int(seconds // 60), "log": log_name}


def first_log_number(home: Path) -> int:
    """The number of this launch's first run log: one past the logs already there,
    so a launch never overwrites an earlier one (Jekyll ep01: twelve launches left
    one 8 KB log).  Two digits keep sorted(...)[-1] the newest."""
    return len(list(home.glob("drive_run*.log"))) + 1


def run_once(codex: str, number: int, log: Path, label: str) -> str:
    """episode.py to its exit, the log watched for silence; returns the log text."""
    env = {**os.environ, "PATH": FFMPEG_DIR + os.pathsep + os.environ.get("PATH", ""), "PYTHONUNBUFFERED": "1"}
    with log.open("w", encoding="utf-8") as out:
        proc = subprocess.Popen(["uv", "run", "--no-sync", "python", "episode.py", codex, str(number)],
                                cwd=ROOT, env=env, stdout=out, stderr=subprocess.STDOUT)
        size, grew, told = 0, time.time(), False
        while proc.poll() is None:
            time.sleep(POLL_S)
            now_size = log.stat().st_size
            if now_size != size:
                size, grew = now_size, time.time()
            elif episode_drive.silent(grew, time.time(), told):
                notify(f"{label}: no log output for {episode_drive.SILENCE_S // 60} min\n"
                       f"{episode_drive.tail(log.read_text(encoding='utf-8', errors='replace'))}")
                told = True
                ledger(log.parent, silence_row(log.name, episode_drive.SILENCE_S))
    return log.read_text(encoding="utf-8", errors="replace")


def finish_report(home: Path) -> None:
    """The 'charged | wall | dead' line and the GPU minutes per step; printed, never fatal (P12, P13)."""
    try:
        from scripts.episode import gpu_ledger
        notify(gpu_ledger.finish_report(home, gpu_ledger.read_rows()))
    except Exception as why:                            # noqa: BLE001 -- a report never changes the exit
        print(f"[drive] finish report failed: {why}", flush=True)


def end_row(home: Path, code: int, sha: str) -> dict:
    """The `end` ledger row.  An owner's repair window ends with its drive (owner ruling 2026-10-19):
    it is closed here, the row carries it, and `clock_spent` reads the repair's own cap; any other
    drive reads the episode's clock, as before (the clock_loop backstop)."""
    from studio import repair_clock, run_budget
    closed = repair_clock.close(home)
    spent = (closed["spent_s"] >= closed["cap_s"] if closed
             else run_budget.spent_before(home) >= run_budget.EPISODE_CEILING_SECONDS)
    row = {"event": "end", "code": code, "sha": sha, "clock_spent": spent,
           "paused_at_boundary": code == episode_drive.PAUSED}
    return {**row, "repair": closed} if closed else row


def leftover_window(home: Path, conn=None, say=None) -> dict | None:
    """Before the first run: a repair window a killed drive left open whose repair is no longer owed
    (repair_clock.backed) is closed and said (repair_clock.close_unbacked; incident 2026-10-19 11:18 PDT)."""
    from studio import db, repair_clock
    closed = repair_clock.close_unbacked(conn if conn is not None else db.get_connection(), home)
    if closed:
        (say or notify)(f"closed a leftover repair window (orders {closed['orders']}, "
                        f"{closed['spent_s']:.0f} s spent): {repair_clock.UNBACKED}")
    return closed


def dry_check(codex: str, number: int) -> list[str]:
    """The dry check the launch runs itself (deadline retro item 1, 2026-10-20): [] lets it go; else the
    lines that refuse it -- a delivered take some decider would write without a named owner order."""
    from scripts.episode import repair_dry_check
    from studio import db
    return repair_dry_check.launch_preflight(db.get_connection, codex, number)


REFUSE_NOW = {"chapter_text"}
"""A gap no step runs past: with no chapter text there is no plan (craft ruling A23).  Every other gap parks
at its own step, and a publish-only gap always parks, never refuses."""
RUN_DAYS = 6 / 24
"""The owner's machine budget for one episode (<= 6 h): a token that dies inside it dies before step 13."""
TOKEN_DAYS = 7.0
"""A Testing consent's refresh token dies at 7 days (scripts/publish/youtube_auth.py)."""


def preflight(book: Path, number: int, env: Path | None = None, now: float | None = None) -> list[str]:
    """t=0 (craft ruling A23): every gap the episode will meet, each "refuse now: ..." or "will park at step
    N: ...", before a second is spent (Jekyll ep01 charged 6.69 h before step 13 refused a book.json with no
    `series`).  The proof harness's chapter audit, then the two publish doors it does not hold."""
    env = ROOT / ".env" if env is None else Path(env)
    now = time.time() if now is None else now
    return (audit_lines(Path(book), number) + plan_lines(Path(book), number) + standing_lines(Path(book), number)
            + token_lines(env, now))


def plan_lines(book: Path, number: int) -> list[str]:
    """Jekyll ep07 retro S5: the plan read at t=0.  A contract failure refuses now (a hand edit's
    'slowly' crashed step 01 after launch); bytes no recorded cure carried since the verdict are said."""
    from pydantic import ValidationError
    from studio import episode_home, plan_provenance, plan_verdict
    plan = episode_home.plan_path(book, number)
    if not plan.exists():
        return []
    try:
        episode_home.load_plan(book, number)
    except ValidationError as why:
        first = next((ln.strip() for ln in str(why).splitlines()[1:] if "error" in ln.lower()), str(why)[:160])
        return [f"refuse now: plan.json fails the Episode contract: {first[:200]}"]
    signed = (plan_verdict.read(plan) or {}).get("plan_sha8") or ""
    if signed and plan_provenance.chain(plan.parent, signed, plan_verdict.plan_sha8(plan)) is None:
        return ["will re-plan at step 02: plan.json changed outside a recorded cure since its verdict"]
    return []


def audit_lines(book: Path, number: int) -> list[str]:
    """The chapter audit's parks (scripts/proof/preconditions.py, imported, never moved: the proof harness owns
    it); a book whose records cannot be read, or an audit that breaks, is said, never a crash (the harness is
    still in build: a fault in its file must not stop a production launch)."""
    try:
        from scripts.proof import preconditions as proof
        out = proof.pre.audit(book, number)
    except Exception as why:
        return [f"preflight: book records not read ({type(why).__name__}: {str(why)[:120]})"]
    return [finding(g) for g in out["gaps"] if g["outcome"] == "park"]


def finding(g: dict) -> str:
    head = "refuse now" if g["kind"] in REFUSE_NOW else f"will park at step {g['step']}"
    return f"{head}: {g['kind']} {g['what']} ({g['basis'][:100]})"


def standing_lines(book: Path, number: int) -> list[str]:
    """G-STANDING: step 13 uploads only an episode publish/standing.json lists (no upload unless asked)."""
    from studio import standing_approval
    if standing_approval.ok(book, number):
        return []
    return [f"will park at step 13: G-STANDING {standing_approval.FILE} does not list ep{number:02d}"]


def token_lines(env: Path, now: float) -> list[str]:
    """The YouTube token's age off .env's stamp: one that dies inside the run's budget parks step 13."""
    from scripts.publish import youtube_auth
    age = youtube_auth.token_age_days(env, now)
    if age is not None and age + RUN_DAYS < TOKEN_DAYS:
        return []
    said = "has no recorded age" if age is None else f"is {age} days old (a Testing consent dies at 7)"
    return [f"will park at step 13: the YouTube token {said}; youtube_auth.py re-consents"]


def refusals(lines: list[str]) -> list[str]:
    return [line for line in lines if line.startswith("refuse now")]


def refuse_launch(home: Path, label: str, lines: list[str], why: str = "dry_check") -> int:
    """A refused launch is a run that refused: its lines in this launch's run log (the autopilot reads that
    tail), a run row and an end row that closes no repair window (the owner's order stays owed)."""
    sha, n, text = git("rev-parse", "HEAD").strip(), first_log_number(home), "\n".join(lines) + "\n"
    (home / f"drive_run{n:02d}.log").write_text(text, encoding="utf-8", newline="\n")
    ledger(home, {"event": "start", "sha": sha})
    ledger(home, run_row(n, sha, text))
    ledger(home, {"event": "end", "code": 2, "sha": sha, "clock_spent": False, "paused_at_boundary": False,
                  "refused": why})
    notify(f"{label}: " + "\n".join(lines))
    return 2


def main(codex: str, number: int) -> int:
    label = f"{codex} ep{number:02d}"
    if episode_drive.dirty(git("status", "--porcelain")):
        notify(f"{label}: REFUSED to start: the working tree is dirty; commit the code first (fix #2)")
        return 2
    home = episode_home.home(episode_home.book_dir(codex), number)
    home.mkdir(parents=True, exist_ok=True)
    if refused := dry_check(codex, number):
        return refuse_launch(home, label, refused)
    if refusals(found := preflight(episode_home.book_dir(codex), number)):
        return refuse_launch(home, label, found, why="preflight")
    if found:                                     # A23: said at t=0, the run goes on to its first park
        print("\n".join(found), flush=True)
        notify(f"{label}: t=0 preflight:\n" + "\n".join(found))
    # THE BOOK'S TITLE CARDS EXIST BEFORE ANY EPISODE RUNS (owner design,
    # 2026-09-30): the card depends only on the book, so it is baked book-wide
    # in one i2v session, outside the episode's clock, never mid-run.
    from scripts.episode import titles_batch
    book = episode_home.book_dir(codex)
    if wanted := titles_batch.missing(book):
        notify(f"{label}: baking {len(wanted)} missing title card(s) for the book first")
        baked = subprocess.run(["uv", "run", "--no-sync", "python", "scripts/episode/titles_batch.py",
                                codex], cwd=ROOT, timeout=7200)
        if still := titles_batch.missing(book):
            if number in still:
                notify(f"{label}: REFUSED: ep{number:02d}'s title card could not be baked "
                       f"(exit {baked.returncode}); fix the card, not the episode")
                return 2
            notify(f"{label}: WARNING cards still missing for {still}; this episode's own card is on disk")
    sha, runs = git("rev-parse", "HEAD").strip(), iter(range(first_log_number(home), 1000))
    log = home / "drive.jsonl"
    began = episode_drive.first_sha(log.read_text(encoding="utf-8")) if log.exists() else None
    if began and began != sha:
        # ONE EPISODE, ONE COMMIT (five-hour plan fix 7): ep14 ran across 23.
        notify(f"{label}: WARNING code moved mid-episode: started on {began[:8]}, "
               f"resuming on {sha[:8]}; fix bugs after the ship, not during it")
    ledger(home, {"event": "start", "sha": sha})
    if closed := leftover_window(home, say=lambda text: notify(f"{label}: {text}")):
        ledger(home, {"event": "repair_closed", "repair": closed})

    def run() -> str:
        n = next(runs)
        text = run_once(codex, number, home / f"drive_run{n:02d}.log", label)
        ledger(home, run_row(n, sha, text))
        return text
    code = episode_drive.drive(run, lambda text: notify(f"{label}: {text}"))
    ledger(home, end_row(home, code, sha))                 # closes a repair window; the clock_loop backstop
    finish_report(home)
    return code


if __name__ == "__main__":
    utf8_console()
    raise SystemExit(main(sys.argv[1], int(sys.argv[2])))
