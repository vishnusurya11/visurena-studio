"""Audio Department — narration script → TTS audio.

Uses Qwen3-TTS engine (reused from E3/house_of_novels) to generate
narration audio from the script department's output.

Phase 0: Single narrator, sequential paragraph generation, concatenated WAV.
Phase 1+: Multi-cast voices, parallel chunk generation.

External dependency: qwen_tts library + GPU (torch).
These are optional deps — install with `uv pip install -e ".[tts]"`.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from studio_orchestrator.models import ProductionJob, ProductionStep, StepResult
from studio_orchestrator.production.departments.base import Department


class AudioDepartment(Department):
    """Generates narration audio using Qwen3-TTS."""

    def process(self, job: ProductionJob, step: ProductionStep, context: dict) -> StepResult:
        start = time.time()
        config = context["config"]
        artifacts_dir = Path(context["artifacts_dir"])
        script_path = context.get("script_output_path")

        output_dir = artifacts_dir / str(job.id) / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)

        if not script_path or not Path(script_path).exists():
            return StepResult(success=False, error="No narration script found from script step")

        try:
            # Load narration script
            with open(script_path, encoding="utf-8") as f:
                script = json.load(f)

            # Lazy import TTS engine (heavy deps)
            from studio_orchestrator.production.departments._tts_adapter import generate_audio

            output_path = output_dir / "narration.wav"
            result_meta = generate_audio(
                script=script,
                output_path=output_path,
                tts_config=config.tts,
            )

            duration = time.time() - start
            return StepResult(
                success=True,
                output_path=str(output_path),
                duration_seconds=duration,
                metadata=result_meta,
            )
        except ImportError as e:
            return StepResult(
                success=False,
                error=f"TTS dependencies not installed. Run: uv pip install -e \".[tts]\" — {e}",
                duration_seconds=time.time() - start,
            )
        except Exception as e:
            return StepResult(
                success=False,
                error=str(e),
                duration_seconds=time.time() - start,
            )

    def estimate_cost(self, job: ProductionJob) -> int:
        return 0  # Local GPU, no API cost

    def validate_output(self, result: StepResult) -> bool:
        if not result.success or not result.output_path:
            return False
        path = Path(result.output_path)
        # Check file exists and is non-trivial (>10KB)
        return path.exists() and path.stat().st_size > 10_000
