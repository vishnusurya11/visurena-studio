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
from openai import BadRequestError
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
            "structured_output": entry.get("structured_output"),
            "timeout_s": entry.get("timeout_s"),
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


DEFAULT_TIMEOUT_S = 600.0
"""One request's wall, when the tier names none (the SDK's own default)."""


class OverBudget(RuntimeError):
    """A paid call refused BEFORE it was sent: the episode would cross its USD
    ceiling (owner 2026-10-04: "3 dollar max for episode generation")."""


EXPECTED_OUTPUT_TOKENS = 13_000
"""The median writer call's output (usage table, 400 calls, 2026-10-04): the
part of the next call's cost a prompt length cannot tell."""


def episode_ceiling_usd() -> float:
    """The per-episode spend ceiling from models.yaml (`money.episode_ceiling_usd`)."""
    return float((load_models_config().get("money") or {}).get("episode_ceiling_usd", 3.00))


def estimated_cost(model: str, prompt: str) -> float:
    """This call's likely USD: prompt chars/4 in, the median output out; 0 if unpriced."""
    from studio import spend
    rate = spend.rate_for(model) or {}
    return (len(prompt) / 4 * rate.get("input_per_m", 0)
            + EXPECTED_OUTPUT_TOKENS * rate.get("output_per_m", 0)) / 1e6


def publish_reserve_usd() -> float:
    """models.yaml `money.publish_reserve_usd`: the slice of the ceiling the
    writers may not eat, so step 13's one metadata call survives them (ep19,
    2026-10-06: the writer spent $3.10 of $3.00 in step 02; a signed plan would
    still have died at the publish)."""
    return float((load_models_config().get("money") or {}).get("publish_reserve_usd", 0.10))


PUBLISH_STEP = "13"
RESERVE_TIERS = ("workhorse",)
"""The callers that may use the reserve: the publish step, and the workhorse
tier (validators, cures, metadata-class calls); every other tier is a writer."""


def effective_cap(tier: str | None, step_id: str | None, cap: float, reserve: float) -> float:
    """The ceiling THIS call is held to: the whole of it at the publish step
    or on the workhorse tier; `cap - reserve` for the writers (local,
    reasoning, canon -- the tiers that ate ep19's wall to the cent)."""
    if step_id == PUBLISH_STEP or tier in RESERVE_TIERS:
        return cap
    return max(0.0, cap - reserve)


def guard_spend(model: str, prompt: str, ceiling: float | None = None, tier: str | None = None) -> None:
    """Refuse the call when the episode's recorded spend plus this call would
    cross the ceiling.  Outside an episode (no unit in the context): no wall."""
    if not _SPEND.get("conn") or not _SPEND.get("unit"):
        return
    from studio import spend
    whole = episode_ceiling_usd() if ceiling is None else ceiling
    cap = effective_cap(tier, _SPEND.get("step_id"), whole, publish_reserve_usd())
    held = f" (${whole - cap:.2f} reserved for the publish)" if cap < whole else ""
    spent = spend.unit_spent(_SPEND["conn"], _SPEND["codex_id"], _SPEND["unit"])
    if spent + estimated_cost(model, prompt) > cap:
        raise OverBudget(f"episode {_SPEND['unit']} has spent ${spent:.2f} of its ${cap:.2f} "
                         f"ceiling{held}; this call would cross it, so it was not sent")


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
        # ep21 (2026-10-07): the SDK's default is 600 s retried twice in silence; the
        # tier names its timeout and `structured()` owns every retry.
        self._client = OpenAI(api_key=_api_key(pc), base_url=base_url,
                              timeout=float(resolved.get("timeout_s") or DEFAULT_TIMEOUT_S), max_retries=0)
        self._model = resolved["model"]
        self._params = resolved.get("params") or {}
        self._tier = tier                   # the wall holds the writers to cap - reserve
        if resolved.get("structured_output") == "loose":
            STRICT_REFUSED.add(self._model)   # models.yaml says so: never probe the strict grammar

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
        guard_spend(self._model, prompt, tier=self._tier)
        messages = [{"role": "user", "content": prompt}]
        if self._model in STRICT_REFUSED:
            completion, parsed = self._parse_loose(messages, structured_output_model)
            return _result(parsed, completion.usage)
        try:
            completion = self._client.chat.completions.parse(
                model=self._model, messages=messages, response_format=structured_output_model, **self._params)
            parsed = completion.choices[0].message.parsed
        except BadRequestError as refused:
            if not grammar_too_large(refused):
                raise
            STRICT_REFUSED.add(self._model)
            completion, parsed = self._parse_loose(messages, structured_output_model)
        return _result(parsed, completion.usage)

    def _parse_loose(self, messages: list[dict], model):
        """ep20/ep21 (2026-10-06): the strict grammar of a big schema is refused
        by the provider, and OpenRouter makes ANY json_schema response_format a
        strict tool -- so the schema goes in the prompt, no response_format at
        all, and the JSON reply is validated here."""
        asked = [*messages[:-1], {"role": "user", "content": schema_prompt(messages[-1]["content"], model)}]
        completion = self._client.chat.completions.create(
            model=self._model, messages=asked, max_tokens=LOOSE_MAX_TOKENS,
            extra_body=LOOSE_EXTRA_BODY, **self._params)
        try:
            return completion, model.model_validate_json(json_body(content_of(completion)))
        except (ProviderNoContent, ValueError) as bad:    # pydantic's ValidationError is a ValueError
            raise refused_with_usage(bad, completion.usage) from bad


def refused_with_usage(bad: Exception, u) -> StructuredOutputException:
    """A failed PAID call is a refusal the ladder re-asks, and it carries the
    tokens it cost so the ledger (and the $3 wall) count it: ep21 (2026-10-07)
    paid ~$1.8 for six replies nobody recorded."""
    exc = StructuredOutputException(f"{type(bad).__name__}: {str(bad)[:300]}")
    exc.usage = {"input_tokens": getattr(u, "prompt_tokens", 0) or 0,
                 "output_tokens": getattr(u, "completion_tokens", 0) or 0}
    return exc


LOOSE_EXTRA_BODY = {"reasoning": {"max_tokens": 2048}}
"""A small thinking budget on the loose call: ep21 (2026-10-07) came back
finish_reason=length, reasoning=yes, content None -- the model spent the whole
output budget reasoning -- and OpenRouter refuses `enabled: false` for this
model ("Reasoning is mandatory for this endpoint").  2k of thought, the rest of
LOOSE_MAX_TOKENS for the plan."""


STRICT_REFUSED: set[str] = set()
"""Models whose strict grammar the provider refused this process: the probe
cost ep21 ~25 min while OpenRouter cycled three providers before the 400
(2026-10-07); the next call on that model goes loose at once."""


class ProviderNoContent(RuntimeError):
    """A 200 whose choice carries no text: the provider failed mid-generation
    (ep21: content None, a TypeError in json_body).  The message names what the
    choice did carry, so the run log says why."""


def content_of(completion) -> str:
    choice = completion.choices[0]
    content = getattr(choice.message, "content", None)
    if content:
        return content
    raise ProviderNoContent(
        f"no content in the reply: finish_reason={getattr(choice, 'finish_reason', None)} "
        f"error={getattr(choice, 'error', None)!r} refusal={getattr(choice.message, 'refusal', None)!r} "
        f"reasoning={'yes' if getattr(choice.message, 'reasoning', None) else 'no'}")


LOOSE_MAX_TOKENS = 32_000
"""Output room for the loose call: ep21 (2026-10-07) came back cut off at ~4k
tokens -- a provider default once no response_format carries the plan -- and a
plan is 12-16k (EXPECTED_OUTPUT_TOKENS)."""


def grammar_too_large(error: Exception) -> bool:
    return "compiled grammar is too large" in str(error)


def schema_prompt(prompt: str, model) -> str:
    """The prompt plus the model's JSON schema and the one rule: answer JSON only."""
    import json
    return (f"{prompt}\n\nAnswer with ONE JSON object only, no prose, no code fence, valid against this "
            f"JSON schema ({model.__name__}):\n{json.dumps(model.model_json_schema())}")


def json_body(text: str) -> str:
    """The JSON object inside a reply that may carry a fence or a preamble."""
    import re
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fenced:
        return fenced.group(1)
    start = text.find("{")
    return text[start:text.rfind("}") + 1] if start >= 0 else text


def _result(parsed, u) -> SimpleNamespace:
    return SimpleNamespace(
        structured_output=parsed,
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
def spend_context(conn, codex_id: str, stage: str, step_id: str | None, unit: str | None = None):
    """Attribute every call made inside this block to one (book, stage, step, unit).

    `unit` is the production below the book (an episode, a pack); None for a
    book-level stage.  A context opened with `step_id=None` FOLLOWS THE JOURNAL:
    a runner wraps its whole run in one, and each `started` the tracker journals
    (`spend_step`) moves the step the next call is attributed to -- so a step
    is never asked to cooperate.  An explicit step id is pinned."""
    previous = dict(_SPEND)
    _SPEND.update(conn=conn, codex_id=codex_id, stage=stage, step_id=step_id,
                  unit=unit, follows=step_id is None)
    try:
        yield
    finally:
        _SPEND.clear()
        _SPEND.update(previous)


def spend_step(step_id: str) -> None:
    """A step was journaled `started`: a following context now attributes to
    it.  A pinned context, or none at all, is left alone."""
    if _SPEND.get("conn") and _SPEND.get("follows"):
        _SPEND["step_id"] = step_id


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
        model = model_for(tier)
        if on_subscription(tier):
            model = f"{model}@subscription"     # unpriced: the tokens are kept, the cost is NULL, the wall ignores it
        spend.record(_SPEND["conn"], _SPEND["codex_id"], _SPEND["stage"],
                     _SPEND["step_id"] or "", tier, model,
                     usage.get("input_tokens", 0), usage.get("output_tokens", 0),
                     unit=_SPEND.get("unit"))
    except Exception:                      # never break a call that already succeeded
        pass


def on_subscription(tier: str) -> bool:
    """A tier on the Claude Agent SDK under the owner's login bills nothing
    (owner, 2026-10-07: "don't use API for money")."""
    try:
        return resolve_tier(tier)["provider"] == "claude-sdk"
    except Exception:
        return False


class _SdkStructuredCaller:
    """ONE Claude Agent SDK session per structured call, on the subscription: the
    schema enforced by the SDK, no tools, no key, no wall.  Same call protocol as
    the native caller, so every fake and every test is unchanged."""

    def __init__(self, tier: str):
        resolved = resolve_tier(tier)
        self._model = resolved["model"]
        self._effort = (resolved.get("params") or {}).get("effort", "medium")
        self._tier = tier

    def __call__(self, prompt: str, structured_output_model=None):
        import asyncio
        from studio import brain
        parsed, receipt = asyncio.run(brain.ask_structured(prompt, structured_output_model,
                                                           model=self._model, effort=self._effort))
        tokens_in = sum(int(u.get("input_tokens", 0)) for u in (receipt.get("model_usage") or {}).values())
        tokens_out = sum(int(u.get("output_tokens", 0)) for u in (receipt.get("model_usage") or {}).values())
        return SimpleNamespace(structured_output=parsed, metrics=SimpleNamespace(accumulated_usage={
            "inputTokens": tokens_in, "outputTokens": tokens_out, "totalTokens": tokens_in + tokens_out}))


def _caller_for(tier: str):
    """The subscription's SDK caller for a claude-sdk tier, the native caller otherwise."""
    return _SdkStructuredCaller(tier) if on_subscription(tier) else _NativeStructuredCaller(tier)


def structured(tier: str, prompt: str, schema, *, retries: int = 3,
               transient_retries: int = 2, usage: dict | None = None, _agent=None):
    """One structured-output call: validated `schema` instance back, or raises.

    Engine: native provider structured outputs (single request, schema-constrained
    decoding — no agent loop, no tool cycles). Two retry ladders:
    - schema violations (StructuredOutputException): up to `retries` immediate re-asks
    - transient failures (connection errors): up to `transient_retries` with backoff.
    Pass `usage={}` to receive token counts (input/output/total + tier) back.
    `_agent` is the test seam (a fake caller; no test may call a paid API)."""
    agent = _agent or _caller_for(tier)
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
            _record_spend(tier, getattr(exc, "usage", None))   # a refused reply was still paid for
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
        if hasattr(obj, "model_dump"):             # another model's instance: its fields (a part of a whole)
            return schema.model_validate(obj.model_dump())
        return schema.model_validate(obj)
    except Exception as exc:
        raise StructuredOutputException(f"output did not match schema: {exc}") from exc
