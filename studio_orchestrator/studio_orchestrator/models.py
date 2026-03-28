"""Pydantic models for all studio orchestrator entities."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --- Enums ---


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class JobStatus(str, Enum):
    PENDING = "pending"
    PRODUCING = "producing"
    READY = "ready"
    PUBLISHED = "published"
    FAILED = "failed"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class StepName(str, Enum):
    SCRIPT = "script"
    AUDIO = "audio"
    IMAGES = "images"
    VIDEO = "video"
    UPLOAD = "upload"


class ShowStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


# --- Core Models ---


class Chapter(BaseModel):
    """A chapter within a story."""

    title: str
    paragraphs: list[str]
    word_count: int


class Story(BaseModel):
    """A parsed story from the content library."""

    id: int
    book_id: str
    story_title: str
    book_title: str
    author: str
    word_count: int
    paragraph_count: int
    chapter_count: int
    format_source: str
    json_path: str
    genre: Optional[str] = None
    publish_year: Optional[str] = None
    language: Optional[str] = None
    description: Optional[str] = None
    pg_metadata: Optional[str] = None
    parse_quality_score: Optional[int] = None
    human_approved: ApprovalStatus = ApprovalStatus.PENDING
    approved_at: Optional[str] = None
    show_config_id: Optional[int] = None
    parsed_at: Optional[str] = None
    updated_at: Optional[str] = None


class ShowConfig(BaseModel):
    """Configuration for a show (evolves to show runner agent in Phase 2)."""

    id: Optional[int] = None
    name: str
    book_id: str
    genre: str
    art_style: str = "classical_illustration"
    voice_profile: str = "default"
    narrator_config: Optional[dict] = None
    current_episode: int = 0
    total_episodes: Optional[int] = None
    status: ShowStatus = ShowStatus.ACTIVE
    slot_id: Optional[int] = None
    budget_cents: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ScheduleSlot(BaseModel):
    """A slot in the weekly programming grid."""

    id: Optional[int] = None
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Sun, 6=Sat
    time_slot: str  # "09:00", "20:00"
    genre: str
    show_config_id: Optional[int] = None
    active: bool = True
    created_at: Optional[str] = None

    @property
    def day_name(self) -> str:
        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        return days[self.day_of_week]


class ProductionJob(BaseModel):
    """A production job for a single video."""

    id: Optional[int] = None
    story_id: int
    show_config_id: Optional[int] = None
    slot_id: Optional[int] = None
    scheduled_publish_at: str  # ISO 8601 UTC
    status: JobStatus = JobStatus.PENDING
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ProductionStep(BaseModel):
    """Per-step status for fault-tolerant production."""

    id: Optional[int] = None
    job_id: int
    step_name: StepName
    status: StepStatus = StepStatus.PENDING
    worker_id: Optional[str] = None
    input_path: Optional[str] = None
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    cost_cents: int = 0


class StepResult(BaseModel):
    """Result returned by a department after processing a step."""

    success: bool
    output_path: Optional[str] = None
    error: Optional[str] = None
    cost_cents: int = 0
    duration_seconds: float = 0.0
    metadata: dict = Field(default_factory=dict)


class CreativeConfig(BaseModel):
    """Creative configuration for a show's visual and audio identity."""

    art_style: str = "classical_illustration"
    voice_profile: str = "default"
    narrator_config: Optional[dict] = None
    color_palette: Optional[str] = None
    intro_template: Optional[str] = None
    outro_template: Optional[str] = None
