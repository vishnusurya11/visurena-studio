"""Script Department — story → narration script.

Takes a parsed story (JSON with chapters/paragraphs) and produces
a narration script suitable for TTS. The script includes:
- Narrator directions (pacing, tone)
- Paragraph-level text chunks for sequential TTS generation
- Scene break markers for image placement

Phase 0: Reads story JSON and formats into a flat narration script.
Phase 2+: LLM-enhanced with dramatic pacing, character voice directions.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from studio_orchestrator.models import ProductionJob, ProductionStep, StepResult
from studio_orchestrator.production.departments.base import Department


class ScriptDepartment(Department):
    """Converts a parsed story into a narration script for TTS."""

    def process(self, job: ProductionJob, step: ProductionStep, context: dict) -> StepResult:
        start = time.time()
        story_data = context.get("story_data")
        artifacts_dir = Path(context["artifacts_dir"])
        output_dir = artifacts_dir / str(job.id) / "script"
        output_dir.mkdir(parents=True, exist_ok=True)

        if not story_data:
            return StepResult(success=False, error="No story data in context")

        try:
            # Build narration script from story chapters
            script = self._build_script(story_data)

            # Write script to disk
            output_path = output_dir / "narration_script.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(script, f, indent=2, ensure_ascii=False)

            duration = time.time() - start
            return StepResult(
                success=True,
                output_path=str(output_path),
                duration_seconds=duration,
                metadata={
                    "total_chunks": len(script["chunks"]),
                    "total_words": script["total_words"],
                    "scene_count": script["scene_count"],
                },
            )
        except Exception as e:
            return StepResult(
                success=False,
                error=str(e),
                duration_seconds=time.time() - start,
            )

    def estimate_cost(self, job: ProductionJob) -> int:
        return 0  # Local processing, no API cost

    def validate_output(self, result: StepResult) -> bool:
        if not result.success or not result.output_path:
            return False
        path = Path(result.output_path)
        if not path.exists():
            return False
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return len(data.get("chunks", [])) > 0

    def _build_script(self, story_data: dict) -> dict:
        """Build a narration script from story JSON.

        Output format:
        {
            "title": "story title",
            "author": "author name",
            "total_words": 5000,
            "scene_count": 3,
            "chunks": [
                {"type": "title", "text": "Story Title by Author", "scene": 0},
                {"type": "narration", "text": "paragraph text...", "scene": 1},
                {"type": "scene_break", "text": "", "scene": 2},
                ...
            ]
        }
        """
        chunks = []
        total_words = 0
        scene_idx = 0

        # Title announcement
        title = story_data.get("story_title", "Untitled")
        author = story_data.get("author", "Unknown")
        chunks.append({
            "type": "title",
            "text": f"{title}, by {author}.",
            "scene": scene_idx,
        })

        chapters = story_data.get("chapters", [])
        for ch_idx, chapter in enumerate(chapters):
            scene_idx += 1

            # Chapter title (if multi-chapter)
            if len(chapters) > 1 and chapter.get("title"):
                ch_title = chapter["title"]
                # Don't repeat the story title
                if ch_title.lower() != title.lower():
                    chunks.append({
                        "type": "chapter_title",
                        "text": ch_title,
                        "scene": scene_idx,
                    })

            # Paragraphs
            for para in chapter.get("paragraphs", []):
                text = para.strip()
                if not text:
                    continue
                words = len(text.split())
                total_words += words
                chunks.append({
                    "type": "narration",
                    "text": text,
                    "scene": scene_idx,
                })

            # Scene break between chapters
            if ch_idx < len(chapters) - 1:
                chunks.append({
                    "type": "scene_break",
                    "text": "",
                    "scene": scene_idx,
                })

        return {
            "title": title,
            "author": author,
            "total_words": total_words,
            "scene_count": scene_idx + 1,
            "chunks": chunks,
        }
