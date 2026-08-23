# Research 2 — LLM-era whole-book structured extraction (Aug 2026)

*Wave-1 subagent report, 2026-08-22. Context: default model gpt-oss:20b local (practical context 8k-32k), paid APIs for hard steps, Strands + pydantic structured output, Dracula ~160k words ≈ 220k tokens.*

## 1. Hierarchical vs incremental summarization

- **BooookScore (ICLR 2024, https://arxiv.org/pdf/2310.00785):** hierarchical merging (map-reduce) is **more coherent** (GPT-4: 90.8 vs 82.4) than incremental updating; incremental gives more detail but overwrites early-book facts — fatal for arcs and "first appearance."
- **Context-Aware Hierarchical Merging (ACL Findings 2025, https://aclanthology.org/2025.findings-acl.289/):** hallucination concentrates in the *merge* steps; **re-injecting source text alongside intermediate summaries during merges** measurably reduces it.
- **CROSS character profiling (EMNLP 2024, https://arxiv.org/abs/2404.12726):** one-go (whole book in context) best *when it fits*; all models worst on **events/arc** — the hardest field, needs the strong model.

**Takeaway:** map-reduce for coherent rollups (synopsis, themes, world); for character sheets use a **structured running state (JSON accumulator, not prose rewrite)** — merging JSON is append/update, so the incremental overwrite failure disappears.

## 2. Knowledge graphs & the "Count Dracula" vs "the Count" merge problem

- **Microsoft GraphRAG (35.6k★):** merges entities **by exact normalized name only** — ships **no real entity resolution**. "Count Dracula"/"the Count"/"the vampire" become three nodes.
- **Neo4j ER recipe** (https://neo4j.com/blog/developer/global-graphrag-neo4j-langchain/): embed name+description → kNN similarity graph filtered by edit/word distance → weakly-connected candidate groups → **LLM as final merge judge**. The pattern to copy.
- **LightRAG (39k★, EMNLP 2025):** name-normalized dedup + per-entity profile description; when merged descriptions exceed budget it **map-reduce-summarizes the descriptions themselves**; supports incremental updates. **nano-graphrag (4k★)** is the hackable minimal reference.
- **BookNLP/BookCoref:** traditional pipelines **still beat prompted LLMs at book-scale coref**; LLM full-book coref erroneously conflates distinct entities.

**Takeaway: alias-table-first.** Pass A builds a canonical character/location registry (names + aliases + epithets); every per-chapter extraction prompt *includes the registry* and uses canonical IDs. Residual dedup: embedding-kNN + string distance → candidates → one paid merge-judge call.

## 3. Character-sheet / story-bible prior art

- **chargraph (46★, Show HN Feb 2025, https://news.ycombinator.com/item?id=42946317):** one-shot whole-book into long-context model. Documented failures: **missing minor characters**, **hallucinated relationships** ("Friends" edges with no textual basis), mistyped entities. Direct evidence single-pass needs verification — worse on a 20B.
- **lorecard (94★):** character cards + lorebooks (SillyTavern World Info format) — proven "story bible" JSON shape from the roleplay community.
- **novel-engine (58★, active July 2026):** imports a manuscript and **backfills outline, story bible, voice profile from the text**; runs on Claude/Codex/Ollama. Closest living project.
- **google/langextract (38.5k★):** structured extraction with **precise source grounding** (every value maps to a character-offset span), few-shot schema-by-example, works with Ollama, chunks long docs, multiple passes. Grounding makes verification cheap: a claim with no supporting span is auto-suspect.
- **NousResearch/autonovel:** has character-registry and world-bible JSON templates worth stealing.

**Notably: no high-star project does "classic novel → full structured story bible JSON" well.** Pieces exist; the integrated pipeline doesn't. (EB-1 relevance: standalone `novel-bible` extractor would fill a real gap — both wave-1 agents reached this independently.)

## 4. Chunking strategy for novels

- **Structure first, token budget second** — chapter boundaries are the natural unit; fixed windows fracture scenes. Hybrid: chapter split, sub-split >~6k-token chapters at scene/paragraph boundaries with modest overlap.
- **LitSeg (May 2026, https://arxiv.org/pdf/2605.27156):** first literary-specific segmentation paper — narrative-aware segmentation significantly improves retrieval and QA.
- **Context Rot (Chroma, https://www.trychroma.com/research/context-rot):** every model degrades as input grows, well before the limit; worse with distractors (a novel is *all* distractors); small open models degrade earliest. On gpt-oss:20b keep inputs to one chapter (~3-6k tokens).
- **Ollama gotcha:** defaults to tiny context unless `num_ctx` is set explicitly — classic silent-truncation bug for gpt-oss:20b.
- **Structured-output tax:** "Let Me Speak Freely" (https://arxiv.org/pdf/2408.02442) + follow-ups: format restriction degrades small-model reasoning ~10-15%, worst under strict constrained decoding; damage comes from **premature serialization** and recovers if free reasoning precedes the JSON. gpt-oss:20b has documented structured-output flakiness under Ollama (ollama#11691). **Reason first, emit JSON last; small per-concern schemas** (characters-in-chapter, locations-in-chapter, chapter summary), never one giant book schema per call.

## 5. Two-pass / verification designs

- **Extract-then-consolidate is the standard shape** (LlamaIndex "Deep Extraction"): extract → verify against source → find gaps → re-extract to threshold.
- **PARSE/SCOPE (https://arxiv.org/html/2510.08623v1):** 3-stage validation — missing-attribute check, **grounding verification** (is each value findable in source?), rule-compliance check.
- **Grounding is the cheap primitive:** span-verification is a yes/no a small model does reliably; the paid model only arbitrates flagged fields.
- **Cost split:** per-chunk extraction = high volume → local 20B. Consolidation/merge = few calls but where hallucination concentrates and small models fail (events/arcs) → paid. Dedup merge-judge = one small paid call.

## 6. Per-sub-task pattern recommendation

| Sub-task | Pattern | Model |
|---|---|---|
| Chunking | Chapter primary; scene-split >~6k tokens; set `num_ctx` explicitly | — |
| Pass 0: registry | Alias sweep / BookNLP name clustering → canonical alias table | local/free |
| Pass 1: per-chapter extraction | Alias table injected; reason-then-JSON; small per-concern schemas; source spans on every claim | local |
| Chapter summaries | Direct per-chapter; book synopsis via hierarchical merge **with source snippets re-injected** | local; paid rollup |
| Character sheets | **JSON accumulator fold** (code), first/last appearance computed mechanically; final profile+arc call | fold = code; profile = paid |
| Entity dedup | Alias table + embedding kNN + string distance → LLM merge judge | judge = paid, 1 call |
| Relationships | Per-chapter **with evidence spans required**; consolidate per pair | local; paid consolidate |
| Themes / world | Map-reduce over chapter notes | local map; paid reduce |
| Verification | Grounding pass per field; escalate flags | local; paid arbitration |

Key sources: BooookScore · Context-Aware Hierarchical Merging · CROSS · Neo4j GraphRAG ER · LightRAG · nano-graphrag · BookNLP · BookCoref · langextract · chargraph HN thread · LitSeg · Context Rot · Let Me Speak Freely · LlamaIndex Deep Extraction · PARSE · novel-engine · lorecard · ollama#11691
