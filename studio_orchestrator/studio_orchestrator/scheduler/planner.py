"""Production planner — generates production jobs from the weekly grid.

The planner looks at the grid, finds slots that need content for next week,
and creates production jobs with scheduled publish times.

─────────────────────────────────────────────
  Grid Slot (Mon 09:00 Horror)
       │
       ▼
  Show Runner → picks next approved story
       │
       ▼
  Production Job (story_id, publish_at)
       │
       ▼
  5 Production Steps (script, audio, images, video, upload)
─────────────────────────────────────────────
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from studio_orchestrator import db
from studio_orchestrator.models import (
    JobStatus,
    ProductionJob,
    ScheduleSlot,
)
from studio_orchestrator.scheduler.show_runner import ShowRunner


def plan_next_week(db_path: str, lead_days: int = 3) -> list[ProductionJob]:
    """Generate production jobs for the upcoming week.

    For each active slot with a linked show:
    1. Calculate the next publish datetime (next occurrence of that day/time)
    2. Check no job already exists for that slot + publish time
    3. Ask the show runner for the next episode
    4. Create a production job

    Args:
        db_path: Database path
        lead_days: How many days ahead to plan (default: 3)

    Returns:
        List of newly created ProductionJob instances
    """
    slots = db.get_slots(db_path, active_only=True)
    created_jobs: list[ProductionJob] = []

    for slot in slots:
        if not slot.show_config_id:
            continue

        show = db.get_show_config(db_path, slot.show_config_id)
        if not show or show.status != "active":
            continue

        # Calculate next publish datetime
        publish_at = _next_slot_datetime(slot, lead_days)
        if not publish_at:
            continue

        # Check if a job already exists for this slot + time
        if _job_exists(db_path, slot.id, publish_at):
            continue

        # Get next episode from show runner
        runner = ShowRunner(show, db_path)
        story = runner.get_next_episode()
        if not story:
            print(f"  Slot {slot.day_name} {slot.time_slot}: no approved stories for {show.name}")
            continue

        # Create the production job
        job = ProductionJob(
            story_id=story.id,
            show_config_id=show.id,
            slot_id=slot.id,
            scheduled_publish_at=publish_at,
        )
        job_id = db.create_job(db_path, job)
        job.id = job_id

        print(
            f"  Created job #{job_id}: \"{story.story_title}\" "
            f"→ {slot.day_name} {slot.time_slot} ({publish_at})"
        )
        created_jobs.append(job)

    return created_jobs


def _next_slot_datetime(slot: ScheduleSlot, lead_days: int) -> Optional[str]:
    """Calculate the next publish datetime for a slot.

    Returns the ISO 8601 UTC string for the next occurrence of this
    day/time that is at least lead_days from now.
    """
    now = datetime.utcnow()
    earliest = now + timedelta(days=lead_days)

    # Parse time
    hour, minute = map(int, slot.time_slot.split(":"))

    # Find the next occurrence of this day_of_week
    # Python: Monday=0, Sunday=6. Our schema: Sunday=0, Saturday=6.
    # Convert: our Sunday(0) -> Python Sunday(6), our Monday(1) -> Python Monday(0), etc.
    py_weekday = (slot.day_of_week - 1) % 7  # Convert Sun=0 -> 6, Mon=1 -> 0, etc.

    # Start from earliest date and find next matching weekday
    candidate = earliest.replace(hour=hour, minute=minute, second=0, microsecond=0)
    days_ahead = (py_weekday - candidate.weekday()) % 7
    if days_ahead == 0 and candidate <= earliest:
        days_ahead = 7
    candidate = candidate + timedelta(days=days_ahead)

    return candidate.isoformat() + "Z"


def _job_exists(db_path: str, slot_id: int, publish_at: str) -> bool:
    """Check if a job already exists for this slot + publish time."""
    conn = db.get_connection(db_path)
    try:
        row = conn.execute(
            """SELECT COUNT(*) as cnt FROM production_jobs
               WHERE slot_id = ? AND scheduled_publish_at = ?
               AND status NOT IN (?, ?)""",
            (slot_id, publish_at, JobStatus.FAILED.value, "cancelled"),
        ).fetchone()
        return row["cnt"] > 0
    finally:
        conn.close()
