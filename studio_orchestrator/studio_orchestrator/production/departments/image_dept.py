"""Image Department — story → scene images via ComfyUI.

Generates scene illustrations for the video using ComfyUI workflows.
Each scene in the narration script gets one image.

Phase 0: One image per scene, single art style, ComfyUI API.
Phase 1+: Multiple image candidates, style consistency enforcement.

External dependency: ComfyUI running locally.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from studio_orchestrator.models import ProductionJob, ProductionStep, StepResult
from studio_orchestrator.production.departments.base import Department


class ImageDepartment(Department):
    """Generates scene images using ComfyUI."""

    def process(self, job: ProductionJob, step: ProductionStep, context: dict) -> StepResult:
        start = time.time()
        config = context["config"]
        artifacts_dir = Path(context["artifacts_dir"])
        script_path = context.get("script_output_path")
        story_data = context.get("story_data", {})

        output_dir = artifacts_dir / str(job.id) / "images"
        output_dir.mkdir(parents=True, exist_ok=True)

        if not script_path or not Path(script_path).exists():
            return StepResult(success=False, error="No narration script found from script step")

        try:
            with open(script_path, encoding="utf-8") as f:
                script = json.load(f)

            # Generate image prompts from script scenes
            scene_prompts = self._build_scene_prompts(script, story_data, context)

            # Generate images via ComfyUI
            image_paths = self._generate_images(
                scene_prompts=scene_prompts,
                output_dir=output_dir,
                comfyui_config=config.comfyui,
            )

            # Write manifest
            manifest_path = output_dir / "manifest.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"images": [str(p) for p in image_paths], "prompts": scene_prompts},
                    f,
                    indent=2,
                )

            duration = time.time() - start
            return StepResult(
                success=True,
                output_path=str(output_dir),
                duration_seconds=duration,
                metadata={
                    "image_count": len(image_paths),
                    "manifest_path": str(manifest_path),
                },
            )
        except Exception as e:
            return StepResult(
                success=False,
                error=str(e),
                duration_seconds=time.time() - start,
            )

    def estimate_cost(self, job: ProductionJob) -> int:
        return 0  # Local GPU

    def validate_output(self, result: StepResult) -> bool:
        if not result.success or not result.output_path:
            return False
        output_dir = Path(result.output_path)
        # Check at least one image was generated
        images = list(output_dir.glob("scene_*.png"))
        return len(images) > 0

    def _build_scene_prompts(
        self, script: dict, story_data: dict, context: dict
    ) -> list[dict]:
        """Build image generation prompts for each scene.

        Phase 0: Simple descriptive prompts from story metadata.
        Phase 2+: LLM-generated prompts with Style Sandwich pattern.
        """
        title = script.get("title", "story")
        genre = story_data.get("genre", "")
        art_style = context.get("art_style", "classical illustration, moody lighting")

        # Determine unique scenes
        scenes = set()
        for chunk in script.get("chunks", []):
            scenes.add(chunk.get("scene", 0))

        prompts = []
        for scene_idx in sorted(scenes):
            # Collect text from this scene for context
            scene_text = " ".join(
                chunk["text"]
                for chunk in script["chunks"]
                if chunk.get("scene") == scene_idx and chunk["text"]
            )

            # Build a basic image prompt
            # Phase 0: simple format. Phase 2: LLM-enhanced Style Sandwich.
            summary = scene_text[:200] if scene_text else title
            prompt = (
                f"{art_style}, illustration for \"{title}\". "
                f"Scene: {summary}. "
                f"Genre: {genre}. High quality, detailed, atmospheric."
            )

            prompts.append({
                "scene": scene_idx,
                "prompt": prompt,
                "filename": f"scene_{scene_idx:03d}.png",
            })

        return prompts

    def _generate_images(
        self,
        scene_prompts: list[dict],
        output_dir: Path,
        comfyui_config,
    ) -> list[Path]:
        """Generate images via ComfyUI API.

        Uses the comfyui_trigger module from house_of_novels.
        """
        import sys

        hon_path = Path(r"D:\Projects\KingdomOfViSuReNa\alpha\house_of_novels")
        if str(hon_path) not in sys.path:
            sys.path.insert(0, str(hon_path))

        from src.comfyui_trigger import trigger_comfy

        # Find a suitable workflow
        workflow_dir = Path(comfyui_config.workflow_dir)
        workflow_candidates = [
            workflow_dir / "z_image_turbo_example.json",
            workflow_dir / "image_generation.json",
        ]
        workflow_path = next((p for p in workflow_candidates if p.exists()), None)

        if not workflow_path:
            raise FileNotFoundError(
                f"No ComfyUI workflow found in {workflow_dir}. "
                f"Expected one of: {[p.name for p in workflow_candidates]}"
            )

        image_paths = []
        for sp in scene_prompts:
            output_path = output_dir / sp["filename"]

            print(f"    Generating: {sp['filename']}...")
            result = trigger_comfy(
                workflow_json_path=str(workflow_path),
                replacements={
                    "11_text": sp["prompt"],
                    "10_filename_prefix": f"api/studio_{output_path.stem}",
                },
                comfyui_url=comfyui_config.base_url,
                timeout=comfyui_config.timeout,
            )

            if result["status"] == "completed" and result["outputs"]:
                # Save the first output image
                with open(output_path, "wb") as f:
                    f.write(result["outputs"][0])
                image_paths.append(output_path)
                print(f"    Saved: {sp['filename']} ({result['execution_time']:.1f}s)")
            else:
                print(f"    FAILED: {sp['filename']} — {result.get('error', 'unknown')}")

        return image_paths
