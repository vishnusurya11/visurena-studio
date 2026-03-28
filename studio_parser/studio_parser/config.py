from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class OllamaConfig(BaseModel):
    model: str = "gpt-oss:20b"
    base_url: str = "http://localhost:11434"


class OpenRouterConfig(BaseModel):
    model: str = "gpt-oss/20b"
    api_key: str = ""


class LLMConfig(BaseModel):
    provider: str = "ollama"
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    openrouter: OpenRouterConfig = Field(default_factory=OpenRouterConfig)


class DatabaseConfig(BaseModel):
    path: str = r"D:\Projects\GlobalDatabases\visurena_studio.db"


class PathsConfig(BaseModel):
    output_dir: str = str(Path(__file__).resolve().parent.parent / "output")

    @property
    def download_dir(self) -> Path:
        return Path(self.output_dir) / "downloads"

    @property
    def stories_dir(self) -> Path:
        return Path(self.output_dir) / "stories"


class ParsingConfig(BaseModel):
    min_paragraph_length: int = 10
    llm_timeout_seconds: int = 120
    llm_fallback_to_deterministic: bool = True


class ParserConfig(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    parsing: ParsingConfig = Field(default_factory=ParsingConfig)


def load_config(
    config_path: Path | None = None,
    *,
    provider_override: str | None = None,
    model_override: str | None = None,
) -> ParserConfig:
    """Load config from YAML file with optional CLI overrides.

    Priority: CLI flags > env vars > config.yaml > defaults.
    """
    data: dict = {}
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}

    # Env var overrides
    env_provider = os.environ.get("STUDIO_PARSER_LLM_PROVIDER")
    env_api_key = os.environ.get("STUDIO_PARSER_OPENROUTER_API_KEY")
    env_ollama_model = os.environ.get("STUDIO_PARSER_OLLAMA_MODEL")
    env_db_path = os.environ.get("STUDIO_PARSER_DB_PATH")
    env_output_dir = os.environ.get("STUDIO_PARSER_OUTPUT_DIR")

    if env_provider:
        data.setdefault("llm", {})["provider"] = env_provider
    if env_api_key:
        data.setdefault("llm", {}).setdefault("openrouter", {})["api_key"] = env_api_key
    if env_ollama_model:
        data.setdefault("llm", {}).setdefault("ollama", {})["model"] = env_ollama_model
    if env_db_path:
        data.setdefault("database", {})["path"] = env_db_path
    if env_output_dir:
        data.setdefault("paths", {})["output_dir"] = env_output_dir

    # CLI overrides (highest priority)
    if provider_override:
        data.setdefault("llm", {})["provider"] = provider_override
    if model_override:
        llm_data = data.setdefault("llm", {})
        provider = llm_data.get("provider", "ollama")
        if provider == "ollama":
            llm_data.setdefault("ollama", {})["model"] = model_override
        else:
            llm_data.setdefault("openrouter", {})["model"] = model_override

    return ParserConfig(**data)
