"""Video Department — audio + images → video via FFmpeg.

Composes scene images with narration audio into a final video file.
Each scene image is displayed for the duration of its corresponding
audio segment, then concatenated into a single video.

Phase 0: Static images with audio overlay (proven E3 approach).
Phase 1+: Ken Burns effect, transitions, title cards.

External dependency: FFmpeg (via imageio-ffmpeg).
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path

from studio_orchestrator.models import ProductionJob, ProductionStep, StepResult
from studio_orchestrator.production.departments.base import Department


def _get_ffmpeg_path() -> str:
    """Get FFmpeg executable path via imageio-ffmpeg."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise RuntimeError("imageio-ffmpeg not installed. Run: uv pip install imageio-ffmpeg")


def _get_audio_duration(ffmpeg_path: str, audio_path: Path) -> float:
    """Get duration of an audio file in seconds."""
    try:
        result = subprocess.run(
            [ffmpeg_path, "-i", str(audio_path), "-f", "null", "-"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        match = re.search(r"Duration: (\d+):(\d+):(\d+)\.(\d+)", result.stderr)
        if match:
            h, m, s, ms = match.groups()
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 100
    except Exception:
        pass
    return 0.0


class VideoDepartment(Department):
    """Composes scene images + narration audio into video using FFmpeg."""

    def process(self, job: ProductionJob, step: ProductionStep, context: dict) -> StepResult:
        start = time.time()
        artifacts_dir = Path(context["artifacts_dir"])
        audio_path = context.get("audio_output_path")
        images_dir = context.get("images_output_path")

        output_dir = artifacts_dir / str(job.id) / "video"
        output_dir.mkdir(parents=True, exist_ok=True)

        if not audio_path or not Path(audio_path).exists():
            return StepResult(success=False, error="No audio file found from audio step")

        try:
            ffmpeg_path = _get_ffmpeg_path()
            audio_path = Path(audio_path)

            # Get available images
            if images_dir and Path(images_dir).exists():
                images = sorted(Path(images_dir).glob("scene_*.png"))
            else:
                images = []

            output_path = output_dir / "final.mp4"

            if images:
                # Create video from images + audio
                self._compose_video(
                    ffmpeg_path=ffmpeg_path,
                    images=images,
                    audio_path=audio_path,
                    output_path=output_path,
                )
            else:
                # Fallback: black video with audio (for testing pipeline)
                self._create_audio_only_video(
                    ffmpeg_path=ffmpeg_path,
                    audio_path=audio_path,
                    output_path=output_path,
                )

            duration = time.time() - start
            return StepResult(
                success=True,
                output_path=str(output_path),
                duration_seconds=duration,
                metadata={
                    "image_count": len(images),
                    "video_duration": _get_audio_duration(ffmpeg_path, audio_path),
                },
            )
        except Exception as e:
            return StepResult(
                success=False,
                error=str(e),
                duration_seconds=time.time() - start,
            )

    def estimate_cost(self, job: ProductionJob) -> int:
        return 0  # Local processing

    def validate_output(self, result: StepResult) -> bool:
        if not result.success or not result.output_path:
            return False
        path = Path(result.output_path)
        # Check file exists and is substantial (>100KB)
        return path.exists() and path.stat().st_size > 100_000

    def _compose_video(
        self,
        ffmpeg_path: str,
        images: list[Path],
        audio_path: Path,
        output_path: Path,
    ) -> None:
        """Compose scene images with audio into a video.

        Strategy: Use the first image as the video background for the full
        duration. Phase 1+ will implement per-scene image switching.
        For Phase 0 with single-scene stories, this works perfectly.
        """
        # Use first image looped over full audio duration
        # This is the E3 proven approach: -loop 1 + -shortest
        cmd = [
            ffmpeg_path,
            "-y",
            "-loop", "1",
            "-i", str(images[0]),
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr[-500:]}")

        print(f"    Video composed: {output_path.name}")

    def _create_audio_only_video(
        self,
        ffmpeg_path: str,
        audio_path: Path,
        output_path: Path,
    ) -> None:
        """Create a black video with audio (fallback when no images)."""
        duration = _get_audio_duration(ffmpeg_path, audio_path)
        if duration <= 0:
            duration = 60  # Fallback

        cmd = [
            ffmpeg_path,
            "-y",
            "-f", "lavfi",
            "-i", f"color=c=black:s=1920x1080:d={duration}",
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr[-500:]}")

        print(f"    Audio-only video created: {output_path.name}")
