"""Configuration management for the studio orchestrator."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel


class LLMOllamaConfig(BaseModel):
    model: str = "gpt-oss:20b"
    base_url: str = "http://localhost:11434"


class LLMOpenRouterConfig(BaseModel):
    model: str = "gpt-oss/20b"
    api_key: str = ""


class LLMConfig(BaseModel):
    provider: str = "ollama"
    ollama: LLMOllamaConfig = LLMOllamaConfig()
    openrouter: LLMOpenRouterConfig = LLMOpenRouterConfig()


class DatabaseConfig(BaseModel):
    path: str = r"D:\Projects\GlobalDatabases\visurena_studio.db"


class TTSConfig(BaseModel):
    device: str = "cuda"
    precision: str = "bfloat16"
    model_size: str = "1.7B"
    narrator_voice: str = "Ryan"
    narration_mode: str = "single_narrator"
    pause_between_speakers_ms: int = 500
    pause_within_speaker_ms: int = 250


class ComfyUIConfig(BaseModel):
    base_url: str = "http://127.0.0.1:8188"
    timeout: int = 300
    workflow_dir: str = r"D:\Projects\KingdomOfViSuReNa\alpha\house_of_novels\workflows"


class YouTubeConfig(BaseModel):
    category_id: str = "24"
    privacy_status: str = "private"
    credentials_path: str = r"D:\Projects\KingdomOfViSuReNa\alpha\house_of_novels\credentials"


class ArtifactsConfig(BaseModel):
    base_dir: str = "artifacts"
    cleanup_after_days: int = 30


class RetryConfig(BaseModel):
    max_attempts: int = 3
    backoff_seconds: list[int] = [5, 30, 120]


class TimeoutsConfig(BaseModel):
    script: int = 60
    audio: int = 600
    images: int = 900
    video: int = 600
    upload: int = 300


class ProductionConfig(BaseModel):
    lead_days: int = 3
    retry: RetryConfig = RetryConfig()
    timeouts: TimeoutsConfig = TimeoutsConfig()


class StudioConfig(BaseModel):
    database: DatabaseConfig = DatabaseConfig()
    llm: LLMConfig = LLMConfig()
    tts: TTSConfig = TTSConfig()
    comfyui: ComfyUIConfig = ComfyUIConfig()
    youtube: YouTubeConfig = YouTubeConfig()
    artifacts: ArtifactsConfig = ArtifactsConfig()
    production: ProductionConfig = ProductionConfig()


def load_config(config_path: Optional[str] = None) -> StudioConfig:
    """Load configuration from YAML file with environment variable overrides.

    Priority: env vars > config.yaml > defaults.
    """
    # Find config file
    if config_path:
        path = Path(config_path)
    else:
        # Look in studio_orchestrator directory first, then cwd
        candidates = [
            Path(__file__).parent.parent / "config.yaml",
            Path.cwd() / "config.yaml",
        ]
        path = next((p for p in candidates if p.exists()), None)

    # Load YAML
    data = {}
    if path and path.exists():
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    # Build config from YAML
    config = StudioConfig(**data)

    # Apply environment variable overrides
    env_overrides = {
        "STUDIO_DB_PATH": ("database", "path"),
        "STUDIO_LLM_PROVIDER": ("llm", "provider"),
        "STUDIO_OLLAMA_MODEL": ("llm", "ollama", "model"),
        "STUDIO_OPENROUTER_API_KEY": ("llm", "openrouter", "api_key"),
        "STUDIO_TTS_DEVICE": ("tts", "device"),
        "STUDIO_COMFYUI_URL": ("comfyui", "base_url"),
        "STUDIO_YOUTUBE_CREDENTIALS": ("youtube", "credentials_path"),
    }

    for env_var, path_parts in env_overrides.items():
        value = os.environ.get(env_var)
        if value is not None:
            obj = config
            for part in path_parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, path_parts[-1], value)

    return config
