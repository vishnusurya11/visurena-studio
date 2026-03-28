"""Upload Department — video → YouTube (scheduled publish).

Handles YouTube upload with metadata, thumbnails, and scheduled publishing.
Reuses the youtube upload module from house_of_novels.

Phase 0: Upload single video with basic metadata.
Phase 1+: Playlist management, SEO optimization, thumbnail A/B testing.

External dependency: Google API client + OAuth credentials.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from studio_orchestrator.models import ProductionJob, ProductionStep, StepResult
from studio_orchestrator.production.departments.base import Department


class UploadDepartment(Department):
    """Uploads videos to YouTube with scheduled publishing."""

    def process(self, job: ProductionJob, step: ProductionStep, context: dict) -> StepResult:
        start = time.time()
        config = context["config"]
        video_path = context.get("video_output_path")
        story_data = context.get("story_data", {})

        if not video_path or not Path(video_path).exists():
            return StepResult(success=False, error="No video file found from video step")

        try:
            # Build metadata
            title = self._build_title(story_data)
            description = self._build_description(story_data)
            tags = self._build_tags(story_data)

            # Get authenticated YouTube service
            youtube = self._get_youtube_service(config.youtube)

            # Import upload function from house_of_novels
            hon_path = Path(r"D:\Projects\KingdomOfViSuReNa\alpha\house_of_novels")
            if str(hon_path) not in sys.path:
                sys.path.insert(0, str(hon_path))

            from src.youtube.upload import upload_video, set_thumbnail

            # Upload with scheduled publish time
            result = upload_video(
                youtube=youtube,
                file_path=Path(video_path),
                title=title,
                description=description,
                tags=tags,
                category_id=config.youtube.category_id,
                privacy_status=config.youtube.privacy_status,
                publish_at=job.scheduled_publish_at,
            )

            if not result.success:
                return StepResult(
                    success=False,
                    error=result.error or "Upload failed",
                    duration_seconds=time.time() - start,
                )

            duration = time.time() - start
            return StepResult(
                success=True,
                output_path=result.video_url,
                duration_seconds=duration,
                metadata={
                    "video_id": result.video_id,
                    "video_url": result.video_url,
                    "title": title,
                    "scheduled_publish_at": job.scheduled_publish_at,
                },
            )
        except Exception as e:
            return StepResult(
                success=False,
                error=str(e),
                duration_seconds=time.time() - start,
            )

    def estimate_cost(self, job: ProductionJob) -> int:
        return 0  # YouTube API is free (within quota)

    def validate_output(self, result: StepResult) -> bool:
        if not result.success:
            return False
        return bool(result.metadata.get("video_id"))

    def _build_title(self, story_data: dict) -> str:
        """Build YouTube video title."""
        title = story_data.get("story_title", "Story")
        author = story_data.get("author", "")
        if author:
            return f"{title} | {author} | Audiobook"
        return f"{title} | Audiobook"

    def _build_description(self, story_data: dict) -> str:
        """Build YouTube video description."""
        parts = []
        title = story_data.get("story_title", "Story")
        author = story_data.get("author", "")
        description = story_data.get("description", "")

        parts.append(f'"{title}" by {author}')
        if description:
            parts.append(f"\n{description}")
        parts.append("\n---")
        parts.append("Narrated by AI (Qwen3-TTS)")
        parts.append("Part of The Keeper's Lantern — classic stories, beautifully told.")
        parts.append("\n#audiobook #shortstory #publicdomain")

        book_id = story_data.get("book_id", "")
        if book_id:
            parts.append(f"\nSource: Project Gutenberg ({book_id})")

        return "\n".join(parts)

    def _build_tags(self, story_data: dict) -> list[str]:
        """Build YouTube video tags."""
        tags = ["audiobook", "short story", "public domain", "classic literature"]
        genre = story_data.get("genre", "")
        if genre:
            tags.extend([g.strip().lower() for g in genre.split(",")])
        author = story_data.get("author", "")
        if author:
            tags.append(author.lower())
        return tags[:30]  # YouTube limit

    def _get_youtube_service(self, yt_config):
        """Get authenticated YouTube API service."""
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds_dir = Path(yt_config.credentials_path)
        token_path = creds_dir / "token.json"

        if not token_path.exists():
            raise FileNotFoundError(
                f"YouTube token not found at {token_path}. "
                f"Run YouTube OAuth flow first (see E3 setup)."
            )

        creds = Credentials.from_authorized_user_file(str(token_path))
        return build("youtube", "v3", credentials=creds)
