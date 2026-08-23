# Decision Log

Newest first. Every architectural change gets an entry.

---

## 2026-08-22 — Library structure: flat, book-id-anchored (owner decision)

**Every book has a unique id (the codex id) and everything starts from there.** Folder
structure is flat and id-keyed: `library/<codex_id>_<slug>/` per book — hierarchy
(universe/world/series) lives in the DB only, never in paths (the taxonomy is a DAG:
crossovers/Hoid break any real tree). Codex grain stays BOOK-level, always. Series/universe
level artifacts and the `atlas`/`entity`/`appearance` tables come later, trigger-based —
see [db/LIBRARY_STRUCTURE.md](db/LIBRARY_STRUCTURE.md). Existing folders are disposable;
the id is the anchor. `library/`, `views/`, `logs/` gitignored.

---

## 2026-08-22 — Storage model: codex + events + file logs (owner decision)

Owner simplified the proposed 6-table stepwise schema to three pieces: the `codex` master
table; **one append-only `events` table** (event_ts, codex_id, stage, hierarchical `step_id`
in **fixed-width 2-digit segments** like `01_01_02` so plain text sort = pipeline order —
growth rule: a level nearing 99 gets restructured into a sub-level; insertions get a sub-level,
never renumbering — event, small detail; current status derived from latest event per key); and
**file-based logs** (Python-logging / Glue-style JSONL, one file per run, joined to events via
`run_id`) — errors and detail live in logs, never in the events table. Pipeline shape lives in
a **step-registry folder** (`stages/<stage>.yaml`, file order = execution order) so future
steps/substeps are added by editing a file, never by migration. Details + the step_id text-sort
pitfall and its fix: [db/EVENT_MODEL.md](db/EVENT_MODEL.md). The stepwise 6-table design stays
as reference for gates/ledger/staleness ideas.

---

## 2026-08-22 — Main table is `codex`

Considered: `books`, `works`, `titles`, `tomes`, `volumes`, `slate`, `texts`,
`properties`, `chronicles`, `sources`, `corpus`.

**Chosen: `codex`** — singular, not `codices` (misspelling magnet; reads as a collective
the way `corpus` does). Gives `codex.name`, `codex_id`, `codex_stages`, `Codex`.
No Python collisions.

Rejected `properties` because `property` is a Python builtin. Rejected `titles` because
`titles.title` is awkward — though the column is `name`, so it was survivable.

Note: `/codex` is also the OpenAI Codex CLI skill in the gstack setup. Ambiguous in
conversation only, not in code. Say "the codex table" when referring to the data.

---

## 2026-08-22 — Row id reduced to second precision (owner decision)

**Supersedes the microsecond entry below.** The id is `TEXT`, fixed **14 chars**,
`YYYYMMDDHHMMSS`, UTC. It is **THE id across the entire system** — stages, production
folders, artifacts all reference it; it is never reformatted downstream.

Collision handling at second precision: entry is manual for now; any bulk insert must
wait ≥1 second between rows or retry with +1 second on `PRIMARY KEY` conflict. The PK
makes a collision a loud failure, not a silent overwrite.

`source_type` + `source_ref` approved the same day (no longer PROPOSED).

---

## 2026-08-22 — [superseded] Row id is microsecond UTC text

**Chosen: `TEXT`, fixed 20 chars, `YYYYMMDDHHMMSSffffff`, generated from UTC.**

- Microseconds as INTEGER is **impossible**: `20260822143015123456` is 20 digits
  (~2.0e19) and SQLite's 64-bit signed INTEGER maxes at ~9.22e18. Milliseconds
  (17 digits) would fit; microseconds do not. So the real choice was
  *ms-as-INTEGER* vs *us-as-TEXT*.
- Fixed-width zero-padded text sorts identically to numeric. `ORDER BY id` just works.
- Range filters use the index:
  `WHERE id >= '20260801000000000000' AND id < '20260901000000000000'`.
  **Do not use `LIKE '202608%'`** — SQLite's LIKE optimization depends on collation
  settings and will silently fall back to a full table scan.
- Drops straight into a path: `20260822143015123456_the_way_of_kings/`, matching the
  existing shorts production folder convention.

**Must be UTC.** With local time, the DST fall-back repeats an hour once a year and ids
go *backwards* — sort order breaks silently and the cause is near-impossible to find.

**Uniqueness:** `PRIMARY KEY` + retry with +1us on conflict. A timestamp is
collision-*unlikely*, not collision-*proof*; a batch import can land two rows in the same
microsecond. Retry costs nothing in the normal case. A sleep-based delay layer is a poor
substitute — Windows `time.sleep()` granularity is roughly 1–15 ms, thousands of times
larger than the window being guarded, and it would slow bulk imports for no benefit.

---

## 2026-08-22 — Database lives in-repo at `db/visurena_studio.db`

Covered by the existing `*.db` gitignore, so `db/` needs a `.gitkeep`.

**Open:** `studio_parser` currently writes `parsed_stories` to
`D:\Projects\GlobalDatabases\visurena_studio.db`. That split must be resolved before P0
lands — two databases with the same name in different places is a guaranteed confusion.

---

## 2026-08-22 — Four-level hierarchy

`universe > world > series > book`. The Cosmere is the *universe*, Roshar is a *world*,
Stormlight Archive is a *series*, The Way of Kings is the book. `world` is included now
rather than deferred, since Cosmere-shaped material is a stated target.

---

## 2026-08-21 — Strands Agents SDK over Pydantic AI, LangChain, LangGraph

**Chosen: Strands**, scoped to `visurena_studio` only. pheonix and visurena_novel keep
LangChain.

An initial Pydantic AI recommendation was **withdrawn** — it rested on two claims that
proved false on checking the docs:

1. *"Wider provider coverage"* — false. Strands' list is longer, OpenRouter is
   first-class, and LM Studio is reached the same way on both (OpenAI-compatible
   `base_url`; neither ships a dedicated LM Studio provider).
2. *"Better local structured output"* — false. Strands' llama.cpp provider constrains at
   decode time via native `json_schema` **and** exposes raw GBNF grammars, which Pydantic
   AI does not. LM Studio is llama.cpp underneath, and `gpt-oss:20b` is the default local
   model, so this favours Strands for exactly this setup.

Remaining reasons to prefer Strands: OpenTelemetry built in; better tool loops for the two
genuinely agent-shaped jobs (story scout, QC/retry ladder); no fresh major version
(Pydantic AI V2 shipped 2026-06-23).

Known gap: Strands raises `StructuredOutputException` on schema violation and does **not**
auto-retry. The `extract()` wrapper in `studio/llm/` owns retry — about six lines.

**LangChain / LangGraph rejected** because v1 is `create_agent` over LangGraph, and
LangGraph checkpoints graph state rather than artifacts-and-credits. See the load-bearing
rule in [ARCHITECTURE.md](ARCHITECTURE.md).

**Strands' own Graph / Swarm / workflow primitives are deliberately unused** for the
production DAG, for the same reason. They persist agent/session state, not artifacts and
spend.

---

## Deferred

| Item | Status |
|---|---|
| Stage tracking: columns on `codex` vs a `codex_stages` table | Owner will decide at build time |
| Resolving the two database locations | Before P0 lands |
