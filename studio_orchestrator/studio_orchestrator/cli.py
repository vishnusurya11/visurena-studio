"""CLI entry point for the studio orchestrator.

Commands:
  approve <story_id>                     — Human sign-off on a story
  reject <story_id>                      — Reject a story from production
  stories [--book <book_id>]             — List stories with approval status

  schedule add --day --time --genre      — Add a slot to the weekly grid
  schedule list                          — Show the weekly programming grid
  schedule remove <slot_id>              — Remove a slot from the grid

  show create --slot --name --book --genre — Create a show and link to slot
  show list                              — List all shows

  plan                                   — Generate production jobs for next week
  produce [<job_id>]                     — Run production pipeline (specific or next)
  status                                 — Show grid + pipeline status
  retry <job_id>                         — Reset failed steps and retry a job

  doctor                                 — Health check before production
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from studio_orchestrator import db
from studio_orchestrator.config import load_config
from studio_orchestrator.models import ApprovalStatus, JobStatus, StepStatus


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="studio",
        description="Visurena Studio Orchestrator — content scheduling & production pipeline",
    )
    parser.add_argument("--config", help="Path to config.yaml")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- approve ---
    p_approve = subparsers.add_parser("approve", help="Approve a story for production")
    p_approve.add_argument("story_id", type=int, help="Story ID to approve")

    # --- reject ---
    p_reject = subparsers.add_parser("reject", help="Reject a story")
    p_reject.add_argument("story_id", type=int, help="Story ID to reject")

    # --- stories ---
    p_stories = subparsers.add_parser("stories", help="List stories")
    p_stories.add_argument("--book", help="Filter by book_id")
    p_stories.add_argument("--approved", action="store_true", help="Show only approved")

    # --- schedule ---
    p_sched = subparsers.add_parser("schedule", help="Manage the weekly grid")
    sched_sub = p_sched.add_subparsers(dest="schedule_command")

    p_sched_add = sched_sub.add_parser("add", help="Add a slot")
    p_sched_add.add_argument("--day", required=True, help="Day of week (monday, mon, 1)")
    p_sched_add.add_argument("--time", required=True, help="Time in HH:MM format")
    p_sched_add.add_argument("--genre", required=True, help="Genre for this slot")

    sched_sub.add_parser("list", help="Show the weekly grid")

    p_sched_rm = sched_sub.add_parser("remove", help="Remove a slot")
    p_sched_rm.add_argument("slot_id", type=int, help="Slot ID to remove")

    # --- show ---
    p_show = subparsers.add_parser("show", help="Manage shows")
    show_sub = p_show.add_subparsers(dest="show_command")

    p_show_create = show_sub.add_parser("create", help="Create a show and link to slot")
    p_show_create.add_argument("--slot", type=int, required=True, help="Slot ID to link")
    p_show_create.add_argument("--name", required=True, help="Show name")
    p_show_create.add_argument("--book", required=True, help="Book ID (e.g., pg8486)")
    p_show_create.add_argument("--genre", required=True, help="Genre")
    p_show_create.add_argument("--art-style", default="classical_illustration")
    p_show_create.add_argument("--voice", default="default")

    show_sub.add_parser("list", help="List all shows")

    # --- plan ---
    p_plan = subparsers.add_parser("plan", help="Generate production jobs for next week")
    p_plan.add_argument("--lead-days", type=int, help="Days ahead to plan (default: from config)")

    # --- produce ---
    p_produce = subparsers.add_parser("produce", help="Run production pipeline")
    p_produce.add_argument("job_id", type=int, nargs="?", help="Job ID (or --next for next pending)")
    p_produce.add_argument("--next", action="store_true", help="Produce the next pending job")

    # --- status ---
    subparsers.add_parser("status", help="Show grid + pipeline status")

    # --- retry ---
    p_retry = subparsers.add_parser("retry", help="Retry a failed job")
    p_retry.add_argument("job_id", type=int, help="Job ID to retry")

    # --- doctor ---
    subparsers.add_parser("doctor", help="Health check before production")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        sys.exit(1)

    config = load_config(args.config)
    db_path = config.database.path

    # Ensure tables exist
    db.ensure_tables(db_path)

    # Dispatch commands
    if args.command == "approve":
        cmd_approve(db_path, args.story_id)
    elif args.command == "reject":
        cmd_reject(db_path, args.story_id)
    elif args.command == "stories":
        cmd_stories(db_path, args)
    elif args.command == "schedule":
        cmd_schedule(db_path, args)
    elif args.command == "show":
        cmd_show(db_path, config, args)
    elif args.command == "plan":
        cmd_plan(db_path, config, args)
    elif args.command == "produce":
        cmd_produce(db_path, config, args)
    elif args.command == "status":
        cmd_status(db_path)
    elif args.command == "retry":
        cmd_retry(db_path, args.job_id)
    elif args.command == "doctor":
        cmd_doctor(config)


# --- Command implementations ---


def cmd_approve(db_path: str, story_id: int) -> None:
    if db.approve_story(db_path, story_id):
        print(f"Approved story #{story_id}")
    else:
        print(f"Story #{story_id} not found")
        sys.exit(1)


def cmd_reject(db_path: str, story_id: int) -> None:
    if db.reject_story(db_path, story_id):
        print(f"Rejected story #{story_id}")
    else:
        print(f"Story #{story_id} not found")
        sys.exit(1)


def cmd_stories(db_path: str, args) -> None:
    if args.approved:
        stories = db.get_approved_stories(db_path, book_id=args.book)
    else:
        stories = db.get_stories(db_path, book_id=args.book)

    if not stories:
        print("No stories found.")
        return

    # Table header
    print(f"{'ID':>4} {'Status':>10} {'Book':>10} {'Title':<40} {'Words':>6} {'Genre':<15}")
    print("-" * 95)

    for s in stories:
        status = s.human_approved if isinstance(s.human_approved, str) else s.human_approved.value
        title = s.story_title[:38] + ".." if len(s.story_title) > 40 else s.story_title
        genre = (s.genre or "")[:15]
        print(f"{s.id:>4} {status:>10} {s.book_id:>10} {title:<40} {s.word_count:>6} {genre:<15}")

    print(f"\nTotal: {len(stories)} stories")


def cmd_schedule(db_path: str, args) -> None:
    if args.schedule_command == "add":
        from studio_orchestrator.scheduler.grid import add_slot
        slot = add_slot(db_path, args.day, args.time, args.genre)
        print(f"Created slot #{slot.id}: {slot.day_name} {slot.time_slot} [{slot.genre}]")

    elif args.schedule_command == "list":
        from studio_orchestrator.scheduler.grid import format_grid, get_grid
        slots = get_grid(db_path)
        if not slots:
            print("No slots configured. Use 'studio schedule add' to create one.")
            return
        print("\nWeekly Programming Grid:")
        print(format_grid(slots))
        print(f"\n{len(slots)} active slot(s)")

    elif args.schedule_command == "remove":
        from studio_orchestrator.scheduler.grid import remove_slot
        if remove_slot(db_path, args.slot_id):
            print(f"Removed slot #{args.slot_id}")
        else:
            print(f"Slot #{args.slot_id} not found")

    else:
        print("Use: studio schedule {add|list|remove}")


def cmd_show(db_path: str, config, args) -> None:
    if args.show_command == "create":
        from studio_orchestrator.scheduler.slot_manager import create_show_and_link
        show = create_show_and_link(
            db_path=db_path,
            slot_id=args.slot,
            name=args.name,
            book_id=args.book,
            genre=args.genre,
            art_style=args.art_style,
            voice_profile=args.voice,
        )
        print(f"Created show #{show.id}: \"{show.name}\"")
        print(f"  Book: {show.book_id} | Genre: {show.genre}")
        print(f"  Episodes: {show.total_episodes} | Slot: #{args.slot}")

    elif args.show_command == "list":
        shows = db.get_active_shows(db_path)
        if not shows:
            print("No active shows.")
            return
        print(f"{'ID':>4} {'Name':<25} {'Book':>10} {'Episode':>10} {'Status':<10}")
        print("-" * 65)
        for show in shows:
            ep = f"{show.current_episode}/{show.total_episodes or '?'}"
            print(f"{show.id:>4} {show.name:<25} {show.book_id:>10} {ep:>10} {show.status:<10}")

    else:
        print("Use: studio show {create|list}")


def cmd_plan(db_path: str, config, args) -> None:
    from studio_orchestrator.scheduler.planner import plan_next_week
    lead_days = args.lead_days if args.lead_days else config.production.lead_days

    print(f"Planning production jobs ({lead_days} days ahead)...")
    jobs = plan_next_week(db_path, lead_days=lead_days)

    if not jobs:
        print("No new jobs to create. All slots are either filled or have no approved stories.")
    else:
        print(f"\nCreated {len(jobs)} production job(s)")


def cmd_produce(db_path: str, config, args) -> None:
    from studio_orchestrator.production.pipeline import run_job

    if args.job_id:
        job = db.get_job(db_path, args.job_id)
        if not job:
            print(f"Job #{args.job_id} not found")
            sys.exit(1)
    elif args.next:
        job = db.get_next_pending_job(db_path)
        if not job:
            print("No pending jobs. Run 'studio plan' first.")
            sys.exit(1)
    else:
        job = db.get_next_pending_job(db_path)
        if not job:
            print("No pending jobs. Run 'studio plan' first.")
            sys.exit(1)

    success = run_job(job, config)
    if success:
        print(f"\nJob #{job.id} completed successfully!")
    else:
        print(f"\nJob #{job.id} failed. Use 'studio status' for details.")
        sys.exit(1)


def cmd_status(db_path: str) -> None:
    from studio_orchestrator.production.job_queue import get_queue_status
    from studio_orchestrator.production.step_tracker import StepTracker
    from studio_orchestrator.scheduler.grid import format_grid, get_grid

    # Weekly grid
    slots = get_grid(db_path)
    print("\n=== WEEKLY GRID ===")
    if slots:
        print(format_grid(slots))
    else:
        print("  (no slots configured)")

    # Queue status
    queue = get_queue_status(db_path)
    print("\n=== PRODUCTION QUEUE ===")
    print(f"  Total: {queue['total']} | Pending: {queue['pending']} | "
          f"Producing: {queue['producing']} | Ready: {queue['ready']} | "
          f"Published: {queue['published']} | Failed: {queue['failed']}")

    # Recent jobs
    jobs = db.get_jobs(db_path, limit=10)
    if jobs:
        tracker = StepTracker(db_path)
        print("\n=== RECENT JOBS ===")
        print(f"{'ID':>4} {'Status':<12} {'Publish At':<22} {'Progress':<12}")
        print("-" * 55)
        for job in jobs:
            progress = tracker.get_job_progress(job.id)
            pct = f"{progress['done']}/{progress['total']}"
            pub = job.scheduled_publish_at[:19] if job.scheduled_publish_at else "—"
            print(f"{job.id:>4} {job.status:<12} {pub:<22} {pct:<12}")


def cmd_retry(db_path: str, job_id: int) -> None:
    job = db.get_job(db_path, job_id)
    if not job:
        print(f"Job #{job_id} not found")
        sys.exit(1)

    # Reset failed steps
    steps = db.get_steps(db_path, job_id)
    reset_count = 0
    for step in steps:
        if step.status == StepStatus.FAILED:
            db.reset_step(db_path, step.id)
            reset_count += 1

    if reset_count == 0:
        print(f"Job #{job_id} has no failed steps to retry")
        return

    # Reset job status to pending
    db.update_job_status(db_path, job_id, JobStatus.PENDING)
    print(f"Reset {reset_count} failed step(s) for job #{job_id}")
    print(f"Run 'studio produce {job_id}' to retry")


def cmd_doctor(config) -> None:
    """Health check — verify all external dependencies are available."""
    print("=== STUDIO DOCTOR ===\n")
    all_ok = True

    # 1. Database
    db_path = config.database.path
    try:
        conn = db.get_connection(db_path)
        count = conn.execute("SELECT COUNT(*) FROM parsed_stories").fetchone()[0]
        conn.close()
        print(f"  [OK] Database: {db_path} ({count} stories)")
    except Exception as e:
        print(f"  [FAIL] Database: {e}")
        all_ok = False

    # 2. FFmpeg
    try:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        print(f"  [OK] FFmpeg: {ffmpeg}")
    except Exception as e:
        print(f"  [FAIL] FFmpeg: {e}")
        all_ok = False

    # 3. ComfyUI
    try:
        import httpx
        resp = httpx.get(f"{config.comfyui.base_url}/system_stats", timeout=5)
        if resp.status_code == 200:
            print(f"  [OK] ComfyUI: {config.comfyui.base_url}")
        else:
            print(f"  [WARN] ComfyUI: responded with {resp.status_code}")
    except Exception:
        print(f"  [WARN] ComfyUI: not running at {config.comfyui.base_url} (needed for images)")

    # 4. TTS
    try:
        import torch
        gpu = torch.cuda.is_available()
        if gpu:
            name = torch.cuda.get_device_name(0)
            print(f"  [OK] GPU: {name}")
        else:
            print("  [WARN] GPU: CUDA not available (TTS will be slow on CPU)")
    except ImportError:
        print("  [WARN] PyTorch: not installed (install with: uv pip install -e \".[tts]\")")

    # 5. YouTube credentials
    creds_path = Path(config.youtube.credentials_path) / "token.json"
    if creds_path.exists():
        print(f"  [OK] YouTube: credentials at {creds_path}")
    else:
        print(f"  [WARN] YouTube: no token.json at {creds_path}")

    # 6. Workflow files
    workflow_dir = Path(config.comfyui.workflow_dir)
    if workflow_dir.exists():
        workflows = list(workflow_dir.glob("*.json"))
        print(f"  [OK] Workflows: {len(workflows)} found in {workflow_dir}")
    else:
        print(f"  [WARN] Workflows: directory not found at {workflow_dir}")

    print()
    if all_ok:
        print("  All systems ready!")
    else:
        print("  Some checks failed. Fix the issues above before production.")
