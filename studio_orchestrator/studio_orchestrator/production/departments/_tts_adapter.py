"""TTS adapter — bridges Qwen3-TTS engine to the audio department.

Isolated in its own module so the heavy torch/qwen_tts imports
only happen when audio generation is actually invoked.

Reuses the QwenTTSEngine from house_of_novels/src/tts/qwen_tts_engine.py
via a thin adapter that maps our script format to the engine's API.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import soundfile as sf


def generate_audio(
    script: dict,
    output_path: Path,
    tts_config,
) -> dict:
    """Generate narration audio from a script using Qwen3-TTS.

    Args:
        script: Narration script dict with "chunks" list
        output_path: Path to write the output WAV
        tts_config: TTSConfig from studio config

    Returns:
        Metadata dict with duration, chunk count, etc.
    """
    # Add house_of_novels to path for importing the TTS engine
    hon_path = Path(r"D:\Projects\KingdomOfViSuReNa\alpha\house_of_novels")
    if str(hon_path) not in sys.path:
        sys.path.insert(0, str(hon_path))

    from src.tts.qwen_tts_engine import QwenTTSEngine, CustomVoiceConfig

    # Initialize engine with config
    narrator_voice = CustomVoiceConfig(speaker=tts_config.narrator_voice)
    engine = QwenTTSEngine(
        device=tts_config.device,
        precision=tts_config.precision,
        model_size=tts_config.model_size,
        narrator_voice=narrator_voice,
        narration_mode=tts_config.narration_mode,
        pause_between_speakers_ms=tts_config.pause_between_speakers_ms,
        pause_within_speaker_ms=tts_config.pause_within_speaker_ms,
    )

    try:
        # Build audio script from narration chunks
        audio_script = []
        for chunk in script.get("chunks", []):
            if chunk["type"] in ("narration", "title", "chapter_title"):
                text = chunk["text"].strip()
                if text:
                    audio_script.append({
                        "speaker": "NARRATOR",
                        "text": text,
                        "instruct": "Calm, measured narration with storytelling warmth.",
                    })

        if not audio_script:
            raise ValueError("No narration text found in script")

        # Generate using engine's scene audio method
        voice_map = {"NARRATOR": narrator_voice}
        success, duration = engine.generate_scene_audio(
            audio_script=audio_script,
            voice_map=voice_map,
            output_path=output_path,
        )

        if not success:
            raise RuntimeError("TTS generation failed — no audio produced")

        return {
            "duration_seconds": duration,
            "chunk_count": len(audio_script),
            "sample_rate": engine._sample_rate,
        }
    finally:
        engine.close()
