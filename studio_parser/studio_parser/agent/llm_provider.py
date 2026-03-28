from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from studio_parser.config import ParserConfig


def get_llm(config: ParserConfig) -> BaseChatModel:
    """Factory: returns ChatOllama or ChatOpenAI based on config.

    This is the single swap point for LLM switching.
    """
    provider = config.llm.provider

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=config.llm.ollama.model,
            base_url=config.llm.ollama.base_url,
            temperature=0.1,
        )
    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=config.llm.openrouter.model,
            api_key=config.llm.openrouter.api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.1,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
