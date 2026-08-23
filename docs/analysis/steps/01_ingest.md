# Step 01 — ingest: Design

**Status: APPROVED & BUILT (substeps 01_01–01_04); 01_05/01_06 pending. Output location: source/ (owner, 2026-08-23).**

One job: turn the source EPUB into clean, numbered, anchor-able text. Zero LLM calls,
fully deterministic — same input, same output, forever.

**Why it matters for timelines:** ingest establishes the **coordinate system**
`(chapter, paragraph)` that every later claim anchors to. When extraction says
*"ch 5 ¶12: 'the next morning'"*, those coordinates are minted here and never shift.

## Substeps

Substeps pass data **in memory** — ingest is fast and free, so re-running the whole
step is the re-run unit; no intermediate files. **Only two things are ever written,
and both are read downstream:**

| id | name | does | writes |
|---|---|---|---|
| `01_01` | `read_source` | Open the EPUB (zip + spine walk, stdlib); parse container → OPF → spine + TOC(nav); pull every spine document's raw XHTML | — (in memory) |
| `01_02` | `clean` | Drop non-content items (cover, TOC page, colophon); **strip Project Gutenberg license boilerplate** (header before the `*** START ***` marker, footer after `*** END ***`); strip HTML → plain paragraphs | — (in memory) |
| `01_03` | `chapterize` | Map cleaned documents onto the TOC's chapter list; capture **part structure** (Part I reminiscences / Part II Utah flashback — the part boundary IS timeline evidence); number chapters `1..N` and paragraphs `1..M` within each | `source/chapters/ch_01.json … ch_NN.json` |
| `01_04` | `finalize` | Validate loudly (no empty chapters, chapter count == TOC count, word counts sane, paragraph numbering contiguous); compute `source_sha256` (future staleness key); write the manifest | `source/book.json` |

| `01_05` | `agent_check` | **Strands agent review** (local model): reads manifest + samples (first/last paragraphs per chapter, titles); flags what rules can't catch — boilerplate leakage mid-text, broken chapter boundaries, wrong title, garbled/mojibake text. Verdict + issue list → event; detail → log | — |
| `01_06` | `improve` | Applies the agent's findings by **steering the deterministic code** (adjust boilerplate markers, chapter-boundary corrections) and re-running `01_02`→`01_05`. **Max 2 rounds**; still failing → step `failed` loudly for the owner. The agent never edits output files directly — determinism survives | (rewrites `chapters/` + `book.json` via re-run) |

**Validation is two layers by design (owner, 2026-08-23):**
1. **Python checks** (`01_04`) — hard rules, free, deterministic: counts, contiguity,
   non-empty, TOC agreement. Catch structural breakage.
2. **Agent review** (`01_05`) — judgment: "does this read like a clean, complete book?"
   Catches what no rule can express. Local model, ~zero cost.
Plus the **improve loop** (`01_06`): agent findings drive parameter fixes + re-run,
bounded at 2 rounds — the QC/retry-ladder pattern from the architecture, in miniature.

Substeps still emit their own `started`/`completed`/`failed` events — granular
tracking without file clutter. Debugging a failed substep = read the log + re-run
the step (seconds, free).

**File-creation principle (owner rule, 2026-08-23): a file exists only if something
downstream reads it or the owner would look at it.** Applies to every future step.

**Output location (owner decision 2026-08-23):** extracted chapters + manifest live in
`source/` (they are normalized source text, consumed by every stage), not `analysis/`.

## File formats

```jsonc
// source/book.json (manifest — written LAST, only after validation passes)
{
  "codex_id": "20260822113400",
  "title": "A Study in Scarlet",
  "source": "source/pg244.epub",            // relative path, always
  "source_sha256": "…",
  "parts": [
    {"n": 1, "title": "Being a Reprint from the Reminiscences of John H. Watson, M.D."},
    {"n": 2, "title": "The Country of the Saints"}
  ],
  "chapters": [
    {"n": 1, "part": 1, "title": "Mr. Sherlock Holmes",
     "file": "chapters/ch_01.json", "paragraphs": 32, "words": 2841}
    // … 14 total expected for this book
  ]
}

// source/chapters/ch_01.json
{
  "n": 1, "part": 1, "title": "Mr. Sherlock Holmes",
  "paragraphs": [
    {"n": 1, "text": "In the year 1878 I took my degree of Doctor of Medicine…"}
    // verbatim text, exactly as the book has it — never paraphrased
  ]
}
```

(¶1 of ch1 literally opens "In the year 1878" — the timeline's first anchor exists
from the first paragraph.)

## Events & logs (first real exercise of the event model)

- `run_id` = `<codex_id>_analysis_<yyyymmddhhmmss>` (UTC).
- Events per substep: `started` → `completed` (or `failed` with a one-line summary in
  `detail`; full trace goes to the log). Step `01` itself gets `started`/`completed`
  wrapping the substeps.
- Log: `logs/<codex_id>/analysis/<run_id>.log` — JSONL lines
  `{ts, level, codex_id, stage, step_id, msg}`.

## Rules honored

- No CLI args — codex id from the config block / DB.
- All paths stored relative to the book folder.
- No LLM, no network, no cost. Tests use a tiny fixture EPUB built in-test — never the
  real 380KB file, never a download.
- Deterministic: byte-identical outputs on re-run (dict key order fixed, no timestamps
  inside artifacts — timestamps live in events/logs only).

## Edge cases handled

| Case | Behavior |
|---|---|
| Gutenberg license text | stripped by marker scan; if markers missing → warn in log, keep all text |
| TOC chapter count ≠ detected content documents | `failed` event, loud — never guess silently |
| Nested TOC (parts containing chapters) | parts recorded; chapter numbering continuous across parts (1–14, not restarting) |
| Images/illustrations in text | dropped; noted in log |
| Empty paragraphs / whitespace-only | dropped before numbering |
| Re-run | overwrites `source/chapters/` + `book.json` (safe: deterministic); new run_id + fresh events |

## Open items for approval

1. Substep granularity: 4 substeps as above — or fold `01_04` into `01_03`?
2. ~~`_work/` intermediates~~ — CUT (owner, 2026-08-23): in-memory only, no scratch files.
3. Chapter numbering continuous across parts (1–14) — or per-part (I.1–I.7, II.1–II.7)?
   Continuous proposed: simpler ids, part recorded as a field anyway.
4. `run_id` format above OK?
