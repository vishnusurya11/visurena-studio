# Visurena Studio — Project Rules

## Python
- **uv only.** `uv add`, `uv run`, `uv sync`. Never pip / poetry / conda.
- Pin every dependency with `==` in `pyproject.toml`. No `>=`, no `~=`.

## Frameworks
- **Strands Agents SDK is the go-to** for all LLM calls and agent loops.
- Anthropic SDK direct is permitted only for prompt-cached long-context parser calls.
- Do not introduce LangChain, LangGraph, or Pydantic AI into this repo.
- Structured output uses the current API — `agent(prompt, structured_output_model=Model)`
  then `result.structured_output`. `Agent.structured_output()` is deprecated.

## Test-first, always
- No implementation before its test. Write the failing test, then the function.
- One function does ONE thing, 10–20 lines. If describing it needs "and", split it.
- Every function has at least one test. No exemption for "trivial" helpers.

## Spec-driven
- The pydantic contract IS the spec. Write `SceneSpec` / `ShotList` / `AudioPlan`
  before writing the department that produces it.
- Fixtures are derived from the contract, never hand-written drift.

## Tests must never cost money
- **No test may call a paid API or spend a credit.** Not Higgsfield, not Anthropic,
  not OpenAI, not OpenRouter. A test that spends is a failing test.
- LLM steps: inject a `FakeModel` returning canned structured output. Test the
  *contract* — schema validates, retry fires on `StructuredOutputException` —
  never the model's judgment.
- Media steps: `FakeArtifactStore` + recorded fixtures.
- Local Ollama / LM Studio calls are free but slow and nondeterministic:
  mark `@pytest.mark.local`, excluded from the default run.

## Architecture invariants
- Strands owns models and agents. `stepwise` owns the DAG, ledger, and gates.
- Departments import neither — typed inputs in, typed artifacts out.
- Never store an absolute path. `production_id` + relative path only.
- Default gate policy for any credit-spending step is ESCALATE.
- One checkout, on `master`. Never a worktree, a per-book branch or a copied library.
  The code tree names no book; everything book-specific lives under `library/<book>/`.

## The architecture page is the org chart — keep it true
The studio is read as a company: code is management (runners, step scripts), agents
are specialists, `stages.yaml` is the org chart the code runs. The page
`architecture/index.html` is where that reading lives, and it goes stale the moment a
change lands without it. So:
- **Every architecture change, proposed or implemented, updates `architecture/index.html`
  in the same commit.** Proposed → the *Future architecture* tab. Implemented → the
  *Current architecture* tab (and the Future tab's state for that slot flips to built).
  Architecture change means: a stage, step or department added, removed or renamed; a
  runner or leader changed; who reports to whom; a unit of work; an owner gate; an agent
  registered or retired; a shared service added.
- A **proposal** also gets a dated file in `architecture/decisions/`; work that follows a
  decision gets a tracker in `architecture/plan/` (status line, checkboxes per commit,
  a dated log); the owner's ruling gets its line in `docs/DECISIONS.md`.
- `architecture/README.md` indexes the departments, decisions and plans; update its tables
  with the same commit.
- The page is one self-contained HTML file: the org trees are markup, the Future tab's
  per-team trees come from the `TEAMS` table in its script, the animated runs from the
  `CURRENT` / `FUTURE` step tables. Edit the data, not the drawing. Republish the
  claude.ai copy linked from the README when the page changes.
