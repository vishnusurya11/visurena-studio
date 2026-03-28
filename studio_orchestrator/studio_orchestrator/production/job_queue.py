"""Job queue — SQLite-backed production job queue.

Phase 0: Sequential processing (one job at a time).
Phase 1+: Concurrent workers with job locking.

The queue pulls the next pending job, runs it through the pipeline,
and updates its status.
"""

from __future__ import annotations

from typing import Optional

from studio_orchestrator import db
from studio_orchestrator.models import JobStatus, ProductionJob


def get_next_job(db_path: str) -> Optional[ProductionJob]:
    """Get the next pending job, ordered by scheduled publish date."""
    return db.get_next_pending_job(db_path)


def claim_job(db_path: str, job_id: int) -> bool:
    """Claim a job for processing (set status to producing).

    Phase 0: Simple status update.
    Phase 1+: Row-level locking for concurrent workers.
    """
    job = db.get_job(db_path, job_id)
    if not job or job.status != JobStatus.PENDING:
        return False
    db.update_job_status(db_path, job_id, JobStatus.PRODUCING)
    return True


def complete_job(db_path: str, job_id: int) -> None:
    """Mark a job as ready (all steps complete, awaiting publish)."""
    db.update_job_status(db_path, job_id, JobStatus.READY)


def publish_job(db_path: str, job_id: int) -> None:
    """Mark a job as published (video is live on YouTube)."""
    db.update_job_status(db_path, job_id, JobStatus.PUBLISHED)


def fail_job(db_path: str, job_id: int) -> None:
    """Mark a job as failed."""
    db.update_job_status(db_path, job_id, JobStatus.FAILED)


def get_queue_status(db_path: str) -> dict:
    """Get a summary of the job queue."""
    conn = db.get_connection(db_path)
    try:
        rows = conn.execute(
            """SELECT status, COUNT(*) as count
               FROM production_jobs
               GROUP BY status"""
        ).fetchall()
        status_counts = {row["status"]: row["count"] for row in rows}

        total = sum(status_counts.values())
        return {
            "total": total,
            "pending": status_counts.get("pending", 0),
            "producing": status_counts.get("producing", 0),
            "ready": status_counts.get("ready", 0),
            "published": status_counts.get("published", 0),
            "failed": status_counts.get("failed", 0),
        }
    finally:
        conn.close()
