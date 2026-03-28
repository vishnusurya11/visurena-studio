"""Production pipeline — orchestrates departments to produce a video.

The pipeline runs 5 departments in sequence for a production job:
1. Script: story → narration script
2. Audio: script → TTS narration (Qwen3-TTS)
3. Images: story → scene illustrations (ComfyUI)
4. Video: audio + images → composed video (FFmpeg)
5. Upload: video → YouTube (scheduled publish)

Each step tracks its own state via StepTracker. Failed steps retry
with exponential backoff. Terminal failures mark the job as failed
and free the slot for the next story.

──────────────────────────────────────────────────────────
  ProductionJob          StepTracker
       │                      │
       ▼                      ▼
  Script Dept ──────→ script.json
       │
       ▼
  Audio Dept  ──────→ narration.wav
       │
       ▼
  Image Dept  ──────→ scene_*.png
       │
       ▼
  Video Dept  ──────→ final.mp4
       │
       ▼
  Upload Dept ──────→ YouTube URL
──────────────────────────────────────────────────────────
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from studio_orchestrator import db
from studio_orchestrator.config import StudioConfig
from studio_orchestrator.models import (
    JobStatus,
    ProductionJob,
    StepName,
    StepResult,
    Story,
)
from studio_orchestrator.production.departments.audio_dept import AudioDepartment
from studio_orchestrator.production.departments.base import Department
from studio_orchestrator.production.departments.image_dept import ImageDepartment
from studio_orchestrator.production.departments.script_dept import ScriptDepartment
from studio_orchestrator.production.departments.upload_dept import UploadDepartment
from studio_orchestrator.production.departments.video_dept import VideoDepartment
from studio_orchestrator.production.job_queue import claim_job, complete_job, fail_job
from studio_orchestrator.production.step_tracker import StepTracker


# Department registry: step name → department class
DEPARTMENTS: dict[str, type[Department]] = {
    StepName.SCRIPT.value: ScriptDepartment,
    StepName.AUDIO.value: AudioDepartment,
    StepName.IMAGES.value: ImageDepartment,
    StepName.VIDEO.value: VideoDepartment,
    StepName.UPLOAD.value: UploadDepartment,
}


def run_job(job: ProductionJob, config: StudioConfig) -> bool:
    """Run the full production pipeline for a job.

    Args:
        job: The production job to execute
        config: Studio configuration

    Returns:
        True if all steps completed successfully
    """
    db_path = config.database.path
    artifacts_base = Path(config.artifacts.base_dir)
    artifacts_dir = artifacts_base.resolve()

    # Claim the job
    if not claim_job(db_path, job.id):
        print(f"  Job #{job.id} could not be claimed (already in progress?)")
        return False

    print(f"\n{'='*60}")
    print(f"  PRODUCING JOB #{job.id}")
    print(f"  Publish at: {job.scheduled_publish_at}")
    print(f"{'='*60}")

    # Load story data
    story = _load_story(db_path, job.story_id)
    if not story:
        print(f"  ERROR: Story ID {job.story_id} not found")
        fail_job(db_path, job.id)
        return False

    story_data = _load_story_json(story)
    print(f"  Story: \"{story.story_title}\" by {story.author}")
    print(f"  Words: {story.word_count} | Chapters: {story.chapter_count}")

    # Build shared context
    context = {
        "config": config,
        "artifacts_dir": str(artifacts_dir),
        "story": story,
        "story_data": story_data,
    }

    # Initialize step tracker
    tracker = StepTracker(
        db_path=db_path,
        backoff_seconds=config.production.retry.backoff_seconds,
    )

    # Process steps sequentially
    step_order = [StepName.SCRIPT, StepName.AUDIO, StepName.IMAGES, StepName.VIDEO, StepName.UPLOAD]

    for step_name in step_order:
        step = db.get_step(db_path, job.id, step_name)
        if not step:
            print(f"  ERROR: Step {step_name.value} not found for job #{job.id}")
            fail_job(db_path, job.id)
            return False

        # Skip already completed steps (for retry scenarios)
        if step.status == "done":
            _update_context_from_step(context, step_name, step)
            continue

        dept_cls = DEPARTMENTS.get(step_name.value)
        if not dept_cls:
            print(f"  ERROR: No department for step {step_name.value}")
            fail_job(db_path, job.id)
            return False

        dept = dept_cls()
        success = _run_step_with_retry(
            dept=dept,
            step=step,
            job=job,
            context=context,
            tracker=tracker,
            max_attempts=config.production.retry.max_attempts,
        )

        if not success:
            print(f"  FAILED: Step {step_name.value} failed after all retries")
            fail_job(db_path, job.id)
            return False

        # Update context with this step's output for downstream steps
        _update_context_from_step(context, step_name, step)

    # All steps complete
    complete_job(db_path, job.id)
    print(f"\n  JOB #{job.id} COMPLETE — ready for publish at {job.scheduled_publish_at}")
    return True


def _run_step_with_retry(
    dept: Department,
    step,
    job: ProductionJob,
    context: dict,
    tracker: StepTracker,
    max_attempts: int,
) -> bool:
    """Run a single step with retry logic."""
    step_label = step.step_name.upper() if hasattr(step.step_name, 'upper') else step.step_name

    while True:
        print(f"\n  [{step_label}] Attempt {step.attempts + 1}/{max_attempts}")

        tracker.mark_running(step)
        result = dept.process(job, step, context)

        if result.success:
            tracker.mark_done(step, result)
            print(f"  [{step_label}] Done ({result.duration_seconds:.1f}s)")
            # Store output path in step for context propagation
            step.output_path = result.output_path
            return True

        # Step failed
        tracker.mark_failed(step, result.error or "Unknown error")
        print(f"  [{step_label}] Failed: {result.error}")

        if tracker.should_retry(step):
            tracker.wait_for_retry(step)
            tracker.reset_for_retry(step)
        else:
            return False


def _load_story(db_path: str, story_id: int) -> Optional[Story]:
    """Load a story from the database."""
    conn = db.get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM parsed_stories WHERE id = ?", (story_id,)
        ).fetchone()
        return Story(**dict(row)) if row else None
    finally:
        conn.close()


def _load_story_json(story: Story) -> dict:
    """Load the full story JSON from the json_path."""
    json_path = Path(story.json_path)
    if json_path.exists():
        with open(json_path, encoding="utf-8") as f:
            return json.load(f)
    return {
        "story_title": story.story_title,
        "author": story.author,
        "book_id": story.book_id,
        "genre": story.genre,
        "chapters": [],
    }


def _update_context_from_step(context: dict, step_name: StepName, step) -> None:
    """Update shared context with a step's output for downstream use."""
    output = step.output_path
    if step_name == StepName.SCRIPT:
        context["script_output_path"] = output
    elif step_name == StepName.AUDIO:
        context["audio_output_path"] = output
    elif step_name == StepName.IMAGES:
        context["images_output_path"] = output
    elif step_name == StepName.VIDEO:
        context["video_output_path"] = output
    elif step_name == StepName.UPLOAD:
        context["upload_result"] = output
