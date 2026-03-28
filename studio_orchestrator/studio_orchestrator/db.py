"""Database operations for the studio orchestrator.

Extends the shared visurena_studio.db with scheduling and production tables.
Follows the same patterns as studio_parser/db.py: WAL mode, UPSERT, context managers.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from studio_orchestrator.models import (
    ApprovalStatus,
    JobStatus,
    ProductionJob,
    ProductionStep,
    ScheduleSlot,
    ShowConfig,
    ShowStatus,
    StepName,
    StepStatus,
    Story,
)


def get_connection(db_path: str) -> sqlite3.Connection:
    """Open a SQLite connection with WAL mode and row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def ensure_tables(db_path: str) -> None:
    """Create orchestrator tables if they don't exist.

    Also runs migrations on parsed_stories to add human_approved columns.
    """
    conn = get_connection(db_path)
    try:
        # Add human_approved columns to existing parsed_stories table
        existing_cols = {
            row["name"] for row in conn.execute("PRAGMA table_info(parsed_stories)").fetchall()
        }

        migrations = [
            ("human_approved", "TEXT DEFAULT 'pending'"),
            ("approved_at", "TEXT"),
            ("show_config_id", "INTEGER"),
        ]
        for col_name, col_def in migrations:
            if col_name not in existing_cols:
                conn.execute(f"ALTER TABLE parsed_stories ADD COLUMN {col_name} {col_def}")

        # Create schedule_slots table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schedule_slots (
                id INTEGER PRIMARY KEY,
                day_of_week INTEGER NOT NULL,
                time_slot TEXT NOT NULL,
                genre TEXT NOT NULL,
                show_config_id INTEGER REFERENCES show_configs(id),
                active BOOLEAN DEFAULT TRUE,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(day_of_week, time_slot)
            )
        """)

        # Create show_configs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS show_configs (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                book_id TEXT NOT NULL,
                genre TEXT NOT NULL,
                art_style TEXT DEFAULT 'classical_illustration',
                voice_profile TEXT DEFAULT 'default',
                narrator_config JSON,
                current_episode INTEGER DEFAULT 0,
                total_episodes INTEGER,
                status TEXT DEFAULT 'active',
                slot_id INTEGER REFERENCES schedule_slots(id),
                budget_cents INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Create production_jobs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS production_jobs (
                id INTEGER PRIMARY KEY,
                story_id INTEGER NOT NULL,
                show_config_id INTEGER REFERENCES show_configs(id),
                slot_id INTEGER REFERENCES schedule_slots(id),
                scheduled_publish_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Create production_steps table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS production_steps (
                id INTEGER PRIMARY KEY,
                job_id INTEGER REFERENCES production_jobs(id),
                step_name TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                worker_id TEXT,
                input_path TEXT,
                output_path TEXT,
                error_message TEXT,
                attempts INTEGER DEFAULT 0,
                max_attempts INTEGER DEFAULT 3,
                started_at TEXT,
                completed_at TEXT,
                cost_cents INTEGER DEFAULT 0,
                UNIQUE(job_id, step_name)
            )
        """)

        conn.commit()
    finally:
        conn.close()


# --- Story operations ---


def get_stories(db_path: str, book_id: Optional[str] = None) -> list[Story]:
    """Get stories, optionally filtered by book_id."""
    conn = get_connection(db_path)
    try:
        if book_id:
            rows = conn.execute(
                "SELECT * FROM parsed_stories WHERE book_id = ? ORDER BY id", (book_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM parsed_stories ORDER BY book_id, id").fetchall()
        return [Story(**dict(row)) for row in rows]
    finally:
        conn.close()


def get_approved_stories(
    db_path: str, book_id: Optional[str] = None, genre: Optional[str] = None
) -> list[Story]:
    """Get approved stories, optionally filtered."""
    conn = get_connection(db_path)
    try:
        query = "SELECT * FROM parsed_stories WHERE human_approved = 'approved'"
        params: list = []
        if book_id:
            query += " AND book_id = ?"
            params.append(book_id)
        if genre:
            query += " AND genre LIKE ?"
            params.append(f"%{genre}%")
        query += " ORDER BY id"
        rows = conn.execute(query, params).fetchall()
        return [Story(**dict(row)) for row in rows]
    finally:
        conn.close()


def approve_story(db_path: str, story_id: int) -> bool:
    """Mark a story as approved for production."""
    conn = get_connection(db_path)
    try:
        now = datetime.utcnow().isoformat()
        result = conn.execute(
            "UPDATE parsed_stories SET human_approved = ?, approved_at = ?, updated_at = ? WHERE id = ?",
            (ApprovalStatus.APPROVED.value, now, now, story_id),
        )
        conn.commit()
        return result.rowcount > 0
    finally:
        conn.close()


def reject_story(db_path: str, story_id: int) -> bool:
    """Mark a story as rejected."""
    conn = get_connection(db_path)
    try:
        now = datetime.utcnow().isoformat()
        result = conn.execute(
            "UPDATE parsed_stories SET human_approved = ?, updated_at = ? WHERE id = ?",
            (ApprovalStatus.REJECTED.value, now, story_id),
        )
        conn.commit()
        return result.rowcount > 0
    finally:
        conn.close()


# --- Show config operations ---


def create_show_config(db_path: str, show: ShowConfig) -> int:
    """Create a show config and return its ID."""
    conn = get_connection(db_path)
    try:
        narrator_json = json.dumps(show.narrator_config) if show.narrator_config else None
        cursor = conn.execute(
            """INSERT INTO show_configs
               (name, book_id, genre, art_style, voice_profile, narrator_config,
                total_episodes, slot_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                show.name,
                show.book_id,
                show.genre,
                show.art_style,
                show.voice_profile,
                narrator_json,
                show.total_episodes,
                show.slot_id,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_show_config(db_path: str, show_id: int) -> Optional[ShowConfig]:
    """Get a show config by ID."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM show_configs WHERE id = ?", (show_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        if data.get("narrator_config"):
            data["narrator_config"] = json.loads(data["narrator_config"])
        return ShowConfig(**data)
    finally:
        conn.close()


def get_active_shows(db_path: str) -> list[ShowConfig]:
    """Get all active show configs."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM show_configs WHERE status = ? ORDER BY id",
            (ShowStatus.ACTIVE.value,),
        ).fetchall()
        shows = []
        for row in rows:
            data = dict(row)
            if data.get("narrator_config"):
                data["narrator_config"] = json.loads(data["narrator_config"])
            shows.append(ShowConfig(**data))
        return shows
    finally:
        conn.close()


def update_show_episode(db_path: str, show_id: int, episode_num: int) -> None:
    """Update the current episode number for a show."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            "UPDATE show_configs SET current_episode = ?, updated_at = datetime('now') WHERE id = ?",
            (episode_num, show_id),
        )
        conn.commit()
    finally:
        conn.close()


def complete_show(db_path: str, show_id: int) -> None:
    """Mark a show as completed."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            "UPDATE show_configs SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (ShowStatus.COMPLETED.value, show_id),
        )
        conn.commit()
    finally:
        conn.close()


# --- Schedule slot operations ---


def create_slot(db_path: str, slot: ScheduleSlot) -> int:
    """Create a schedule slot and return its ID."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            """INSERT INTO schedule_slots (day_of_week, time_slot, genre, show_config_id, active)
               VALUES (?, ?, ?, ?, ?)""",
            (slot.day_of_week, slot.time_slot, slot.genre, slot.show_config_id, slot.active),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_slots(db_path: str, active_only: bool = True) -> list[ScheduleSlot]:
    """Get schedule slots."""
    conn = get_connection(db_path)
    try:
        query = "SELECT * FROM schedule_slots"
        if active_only:
            query += " WHERE active = TRUE"
        query += " ORDER BY day_of_week, time_slot"
        rows = conn.execute(query).fetchall()
        return [ScheduleSlot(**dict(row)) for row in rows]
    finally:
        conn.close()


def get_slot(db_path: str, slot_id: int) -> Optional[ScheduleSlot]:
    """Get a schedule slot by ID."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM schedule_slots WHERE id = ?", (slot_id,)).fetchone()
        return ScheduleSlot(**dict(row)) if row else None
    finally:
        conn.close()


def remove_slot(db_path: str, slot_id: int) -> bool:
    """Deactivate a schedule slot."""
    conn = get_connection(db_path)
    try:
        result = conn.execute(
            "UPDATE schedule_slots SET active = FALSE WHERE id = ?", (slot_id,)
        )
        conn.commit()
        return result.rowcount > 0
    finally:
        conn.close()


# --- Production job operations ---


def create_job(db_path: str, job: ProductionJob) -> int:
    """Create a production job and return its ID."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            """INSERT INTO production_jobs
               (story_id, show_config_id, slot_id, scheduled_publish_at, status)
               VALUES (?, ?, ?, ?, ?)""",
            (
                job.story_id,
                job.show_config_id,
                job.slot_id,
                job.scheduled_publish_at,
                job.status.value,
            ),
        )
        conn.commit()
        job_id = cursor.lastrowid

        # Create production steps for each department
        for step_name in StepName:
            conn.execute(
                """INSERT INTO production_steps (job_id, step_name, status)
                   VALUES (?, ?, ?)""",
                (job_id, step_name.value, StepStatus.PENDING.value),
            )
        conn.commit()

        return job_id
    finally:
        conn.close()


def get_job(db_path: str, job_id: int) -> Optional[ProductionJob]:
    """Get a production job by ID."""
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM production_jobs WHERE id = ?", (job_id,)).fetchone()
        return ProductionJob(**dict(row)) if row else None
    finally:
        conn.close()


def get_jobs(
    db_path: str, status: Optional[JobStatus] = None, limit: int = 50
) -> list[ProductionJob]:
    """Get production jobs, optionally filtered by status."""
    conn = get_connection(db_path)
    try:
        query = "SELECT * FROM production_jobs"
        params: list = []
        if status:
            query += " WHERE status = ?"
            params.append(status.value)
        query += " ORDER BY scheduled_publish_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        return [ProductionJob(**dict(row)) for row in rows]
    finally:
        conn.close()


def update_job_status(db_path: str, job_id: int, status: JobStatus) -> None:
    """Update a production job's status."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            "UPDATE production_jobs SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (status.value, job_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_next_pending_job(db_path: str) -> Optional[ProductionJob]:
    """Get the next pending job ordered by publish date."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM production_jobs WHERE status = ? ORDER BY scheduled_publish_at ASC LIMIT 1",
            (JobStatus.PENDING.value,),
        ).fetchone()
        return ProductionJob(**dict(row)) if row else None
    finally:
        conn.close()


# --- Production step operations ---


def get_steps(db_path: str, job_id: int) -> list[ProductionStep]:
    """Get all production steps for a job."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM production_steps WHERE job_id = ? ORDER BY id", (job_id,)
        ).fetchall()
        return [ProductionStep(**dict(row)) for row in rows]
    finally:
        conn.close()


def get_step(db_path: str, job_id: int, step_name: StepName) -> Optional[ProductionStep]:
    """Get a specific production step."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM production_steps WHERE job_id = ? AND step_name = ?",
            (job_id, step_name.value),
        ).fetchone()
        return ProductionStep(**dict(row)) if row else None
    finally:
        conn.close()


def update_step_start(db_path: str, step_id: int) -> None:
    """Mark a step as running."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            """UPDATE production_steps
               SET status = ?, started_at = datetime('now'), attempts = attempts + 1
               WHERE id = ?""",
            (StepStatus.RUNNING.value, step_id),
        )
        conn.commit()
    finally:
        conn.close()


def update_step_done(
    db_path: str, step_id: int, output_path: str, cost_cents: int = 0
) -> None:
    """Mark a step as completed."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            """UPDATE production_steps
               SET status = ?, output_path = ?, completed_at = datetime('now'), cost_cents = ?
               WHERE id = ?""",
            (StepStatus.DONE.value, output_path, cost_cents, step_id),
        )
        conn.commit()
    finally:
        conn.close()


def update_step_failed(db_path: str, step_id: int, error_message: str) -> None:
    """Mark a step as failed."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            """UPDATE production_steps
               SET status = ?, error_message = ?, completed_at = datetime('now')
               WHERE id = ?""",
            (StepStatus.FAILED.value, error_message, step_id),
        )
        conn.commit()
    finally:
        conn.close()


def reset_step(db_path: str, step_id: int) -> None:
    """Reset a failed step back to pending for retry."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            """UPDATE production_steps
               SET status = ?, error_message = NULL, started_at = NULL, completed_at = NULL
               WHERE id = ?""",
            (StepStatus.PENDING.value, step_id),
        )
        conn.commit()
    finally:
        conn.close()
