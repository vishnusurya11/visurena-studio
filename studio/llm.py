"""LLM gateway — tiers from models.yaml -> Strands model objects + structured calls.

Agents never import a provider or name a model: they ask for a TIER ("workhorse",
"reasoning"); models.yaml decides what that means today. Switching provider = yaml
edit, zero code changes. Design approved 2026-08-23 (tier model).

API keys: environment variables (name per provider in models.yaml); a gitignored
.env file at the repo root is loaded if present.
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import yaml
from strands.types.exceptions import StructuredOutputException


class ContentFiltered(Exception):
    """Provider refused the request (content filter). Not retryable — the caller
    decides whether to skip. Real-run 2026-08-23: Doyle's murder scenes trip it."""

MODELS_PATH = Path("models.yaml")
ENV_PATH = Path(".env")


def _load_dotenv(path: Path = ENV_PATH) -> None:
    """Tiny .env loader: KEY=VALUE lines, never overrides real env vars."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def load_models_config(path: Path = MODELS_PATH) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def resolve_tier(tier: str) -> dict:
    """Tier name -> {model, provider, provider_config}. Loud on unknowns."""
    config = load_models_config()
    if tier not in config["tiers"]:
        raise ValueError(f"unknown tier {tier!r}; defined: {sorted(config['tiers'])}")
    entry = config["tiers"][tier]
    provider = entry["provider"]
    if provider not in config["providers"]:
        raise ValueError(f"tier {tier!r} names unknown provider {provider!r}")
    return {"model": entry["model"], "provider": provider,
            "params": entry.get("params") or {},
            "provider_config": config["providers"][provider]}


def _api_key(provider_config: dict) -> str:
    env_name = provider_config.get("api_key_env")
    if not env_name:
        return "not-needed"  # local servers (LM Studio / Ollama)
    _load_dotenv()
    key = os.environ.get(env_name)
    if not key:
        raise RuntimeError(f"API key env var {env_name} is not set (set it or add to .env)")
    return key


def _model_kwargs(resolved: dict) -> dict:
    """Constructor kwargs for an OpenAI-compatible Strands model. Per-tier `params`
    (reasoning_effort etc. — provider quirks) pass through from models.yaml verbatim."""
    kwargs = {
        "client_args": {"api_key": _api_key(resolved["provider_config"]),
                        "base_url": resolved["provider_config"]["base_url"]},
        "model_id": resolved["model"],
    }
    if resolved.get("params"):
        kwargs["params"] = resolved["params"]
    return kwargs


def make_agent(tier: str, *, max_turns: int = 8, **agent_kwargs):
    """Build a Strands Agent for GENUINELY agentic loops (tools, multi-turn).

    ALWAYS capped: real-run incident 2026-08-23 — an uncapped Agent in forced
    structured-output mode retried a failing validation 800+ times, re-sending the
    growing conversation each cycle. Strands' Limits default to None (unbounded);
    this helper makes a turn cap mandatory. For plain structured extraction, use
    structured() — it never enters an agent loop at all."""
    from strands import Agent
    return Agent(model=get_model(tier), limits={"turns": max_turns}, **agent_kwargs)


def get_model(tier: str):
    """Build the Strands model object for a tier."""
    resolved = resolve_tier(tier)
    if resolved["provider"] == "ollama":
        from strands.models.ollama import OllamaModel
        return OllamaModel(host=resolved["provider_config"]["host"],
                           model_id=resolved["model"])
    from strands.models.openai import OpenAIModel
    return OpenAIModel(**_model_kwargs(resolved))


def _extract_usage(result) -> dict:
    """Token usage off a Strands result, defensively — {} if the shape is unknown."""
    raw = getattr(getattr(result, "metrics", None), "accumulated_usage", None) or {}
    return {"input_tokens": raw.get("inputTokens", 0),
            "output_tokens": raw.get("outputTokens", 0),
            "total_tokens": raw.get("totalTokens", 0)}


_TRANSIENT_BACKOFF = (3, 10)  # seconds between transient-error retries


class _NativeStructuredCaller:
    """ONE provider request with native structured outputs (response_format +
    constrained decoding). Replaces the Strands agent loop for extraction calls —
    real-run lesson 2026-08-23: the agent loop re-called the output tool 800+ times,
    re-paying the prompt each cycle. A single parse request CANNOT loop.
    Implements the same call protocol as an Agent, so tests/fakes are unchanged."""

    def __init__(self, tier: str):
        from openai import OpenAI
        resolved = resolve_tier(tier)
        pc = resolved["provider_config"]
        base_url = pc.get("base_url") or (pc["host"].rstrip("/") + "/v1")  # ollama compat
        self._client = OpenAI(api_key=_api_key(pc), base_url=base_url)
        self._model = resolved["model"]
        self._params = resolved.get("params") or {}

    def __call__(self, prompt: str, structured_output_model=None):
        from openai import ContentFilterFinishReasonError
        from pydantic import ValidationError
        try:
            return self._parse(prompt, structured_output_model)
        except ContentFilterFinishReasonError as exc:
            raise ContentFiltered(str(exc)) from exc
        except ValidationError as exc:
            # `parse` validates the JSON itself: a rule refusing inside the schema
            # is a schema violation to re-ask on, never a transient to sleep on
            raise StructuredOutputException(f"output did not match schema: {exc}") from exc

    def _parse(self, prompt: str, structured_output_model=None):
        completion = self._client.chat.completions.parse(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            response_format=structured_output_model,
            **self._params,
        )
        u = completion.usage
        return SimpleNamespace(
            structured_output=completion.choices[0].message.parsed,
            metrics=SimpleNamespace(accumulated_usage={
                "inputTokens": getattr(u, "prompt_tokens", 0),
                "outputTokens": getattr(u, "completion_tokens", 0),
                "totalTokens": getattr(u, "total_tokens", 0)}),
        )


# --- spend recording -------------------------------------------------------------
#
# Recording lives HERE, at the single place every paid call passes through, because the
# alternative was asking each step to remember `usage={}` — and the steps that forgot
# are why this project has 64 log files and no cost history at all.
#
# It is best-effort by design: a failure to record must never break a call that already
# succeeded and already cost money. Losing the receipt is bad; losing the work is worse.

_SPEND: dict = {}


@contextmanager
def spend_context(conn, codex_id: str, stage: str, step_id: str):
    """Attribute every call made inside this block to one (book, stage, step)."""
    previous = dict(_SPEND)
    _SPEND.update(conn=conn, codex_id=codex_id, stage=stage, step_id=step_id)
    try:
        yield
    finally:
        _SPEND.clear()
        _SPEND.update(previous)


def model_for(tier: str) -> str | None:
    """The concrete model a tier resolves to right now, for the spend record."""
    try:
        return resolve_tier(tier).get("model")
    except Exception:
        return None


def _record_spend(tier: str, usage: dict) -> None:
    if not _SPEND.get("conn") or not usage:
        return
    try:
        from studio import spend
        spend.record(_SPEND["conn"], _SPEND["codex_id"], _SPEND["stage"],
                     _SPEND["step_id"], tier, model_for(tier),
                     usage.get("input_tokens", 0), usage.get("output_tokens", 0))
    except Exception:                      # never break a call that already succeeded
        pass


def structured(tier: str, prompt: str, schema, *, retries: int = 3,
               transient_retries: int = 2, usage: dict | None = None, _agent=None):
    """One structured-output call: validated `schema` instance back, or raises.

    Engine: native provider structured outputs (single request, schema-constrained
    decoding — no agent loop, no tool cycles). Two retry ladders:
    - schema violations (StructuredOutputException): up to `retries` immediate re-asks
    - transient failures (connection errors): up to `transient_retries` with backoff.
    Pass `usage={}` to receive token counts (input/output/total + tier) back.
    `_agent` is the test seam (a fake caller; no test may call a paid API)."""
    agent = _agent or _NativeStructuredCaller(tier)
    for attempt in range(transient_retries + 1):
        try:
            local: dict = {} if usage is None else usage
            result = _structured_once(agent, prompt, schema, retries, local, tier)
            _record_spend(tier, local)
            return result
        except (StructuredOutputException, ContentFiltered):
            raise
        except Exception:
            if attempt == transient_retries:
                raise
            time.sleep(_TRANSIENT_BACKOFF[min(attempt, len(_TRANSIENT_BACKOFF) - 1)])


REFUSED = "--- REFUSED, fix these ---"
"""The heading under which a re-ask quotes the refusal back."""


def re_ask(prompt: str, exc: Exception) -> str:
    """The original prompt with the LATEST refusal under it -- never a stack of
    them.  Episode 13 (2026-09-25): ten from-scratch drafts refused on rules
    the skill states, because a re-ask repeated the same prompt and the model
    never heard what was wrong."""
    return (f"{prompt}\n\n{REFUSED}\nThe previous answer was refused: {exc}\n"
            "Return the whole answer again with every refusal fixed.")


def _structured_once(agent, prompt, schema, retries, usage, tier):
    last_error, asked = None, prompt
    for _ in range(retries):
        try:
            result = agent(asked, structured_output_model=schema)
            if usage is not None:
                usage.update(_extract_usage(result), tier=tier)
            return _validated(result.structured_output, schema)
        except StructuredOutputException as exc:
            last_error, asked = exc, re_ask(prompt, exc)
    raise last_error


def _validated(obj, schema):
    """GUARANTEE: the caller gets a valid `schema` instance or an exception — never
    None, never a raw dict, never a wrong shape (all retried upstream)."""
    if obj is None:
        raise StructuredOutputException("model returned no structured output")
    if isinstance(obj, schema):
        return obj
    try:
        return schema.model_validate(obj)
    except Exception as exc:
        raise StructuredOutputException(f"output did not match schema: {exc}") from exc
