"""Step tracker — per-step state management with retry logic.

Tracks each production step's state, handles retry with exponential backoff,
and enforces the failure policy from the design doc:
- Exponential backoff: 5s, 30s, 2min across 3 max attempts
- Terminal failure: mark job as failed, don't block the slot
- Rejected stories: skip and pick next approved story

Step lifecycle:
  PENDING → RUNNING → DONE
                    → FAILED (retry if attempts < max)
                    → FAILED (terminal if attempts >= max)
"""

from __future__ import annotations

import time
from typing import Optional

from studio_orchestrator import db
from studio_orchestrator.models import (
    JobStatus,
    ProductionStep,
    StepName,
    StepResult,
    StepStatus,
)


class StepTracker:
    """Tracks and manages production step execution with retry logic."""

    def __init__(self, db_path: str, backoff_seconds: list[int] | None = None):
        self.db_path = db_path
        self.backoff_seconds = backoff_seconds or [5, 30, 120]

    def get_pending_steps(self, job_id: int) -> list[ProductionStep]:
        """Get all pending steps for a job, in execution order."""
        steps = db.get_steps(self.db_path, job_id)
        step_order = [s.value for s in StepName]
        pending = [s for s in steps if s.status == StepStatus.PENDING]
        pending.sort(key=lambda s: step_order.index(s.step_name) if s.step_name in step_order else 99)
        return pending

    def get_next_step(self, job_id: int) -> Optional[ProductionStep]:
        """Get the next step to execute for a job.

        Returns the first pending step in execution order, or None if
        all steps are done or a step has terminally failed.
        """
        steps = db.get_steps(self.db_path, job_id)
        step_order = [s.value for s in StepName]

        for step_name in step_order:
            step = next((s for s in steps if s.step_name == step_name), None)
            if not step:
                continue
            if step.status == StepStatus.PENDING:
                return step
            if step.status == StepStatus.FAILED:
                # Check if retryable
                if step.attempts < step.max_attempts:
                    return step
                return None  # Terminal failure
            if step.status == StepStatus.RUNNING:
                return None  # Step in progress
            # DONE: continue to next step

        return None  # All steps done

    def mark_running(self, step: ProductionStep) -> None:
        """Mark a step as running."""
        db.update_step_start(self.db_path, step.id)
        step.status = StepStatus.RUNNING
        step.attempts += 1

    def mark_done(self, step: ProductionStep, result: StepResult) -> None:
        """Mark a step as completed."""
        db.update_step_done(
            self.db_path,
            step.id,
            output_path=result.output_path or "",
            cost_cents=result.cost_cents,
        )
        step.status = StepStatus.DONE

    def mark_failed(self, step: ProductionStep, error: str) -> None:
        """Mark a step as failed."""
        db.update_step_failed(self.db_path, step.id, error)
        step.status = StepStatus.FAILED

    def should_retry(self, step: ProductionStep) -> bool:
        """Check if a failed step should be retried."""
        return step.attempts < step.max_attempts

    def wait_for_retry(self, step: ProductionStep) -> None:
        """Wait the appropriate backoff duration before retrying."""
        attempt_idx = min(step.attempts - 1, len(self.backoff_seconds) - 1)
        wait_seconds = self.backoff_seconds[attempt_idx]
        print(f"    Waiting {wait_seconds}s before retry {step.attempts}/{step.max_attempts}...")
        time.sleep(wait_seconds)

    def reset_for_retry(self, step: ProductionStep) -> None:
        """Reset a failed step for retry."""
        db.reset_step(self.db_path, step.id)
        step.status = StepStatus.PENDING

    def is_job_complete(self, job_id: int) -> bool:
        """Check if all steps for a job are done."""
        steps = db.get_steps(self.db_path, job_id)
        return all(s.status == StepStatus.DONE for s in steps)

    def is_job_failed(self, job_id: int) -> bool:
        """Check if any step has terminally failed."""
        steps = db.get_steps(self.db_path, job_id)
        return any(
            s.status == StepStatus.FAILED and s.attempts >= s.max_attempts
            for s in steps
        )

    def get_job_progress(self, job_id: int) -> dict:
        """Get a summary of job progress."""
        steps = db.get_steps(self.db_path, job_id)
        total = len(steps)
        done = sum(1 for s in steps if s.status == StepStatus.DONE)
        failed = sum(1 for s in steps if s.status == StepStatus.FAILED)
        running = sum(1 for s in steps if s.status == StepStatus.RUNNING)
        pending = sum(1 for s in steps if s.status == StepStatus.PENDING)

        return {
            "total": total,
            "done": done,
            "failed": failed,
            "running": running,
            "pending": pending,
            "progress_pct": int(done / total * 100) if total > 0 else 0,
        }
