# Research 1 — Established NLP tooling & academic work (Aug 2026)

*Wave-1 subagent report, 2026-08-22. Verbatim findings; synthesis happens in the design doc.*

## 1. BookNLP (and forks)

**What it is:** Python pipeline for book-length English documents by David Bamman (UC Berkeley). One pass produces: POS tagging + dependency parsing (via spaCy), NER tuned for fiction (PER/FAC/GPE/LOC/VEH), **character name clustering + coreference resolution**, **quotation speaker attribution**, **supersense tagging** (coarse semantic classes — useful for pulling out "body/clothing/artifact" nouns around a character), **event tagging** (realis events only), and **referential gender inference**. Output is token/entity/quote/supersense TSVs plus a `.book` JSON per character listing their agent/patient verbs, possessions, modifiers, and attributed quotes — i.e., exactly the raw material for a character sheet. Two model sizes: "big" (GPU; entity F1 90.0, coref 79.0, events 74.1) and "small" (laptop; ~2-4 min per novel). Repo: https://github.com/booknlp/booknlp

**Maintenance reality in 2026:** effectively frozen (2021 + one 2024 commit). Unanswered issues incl. Apple Silicon, Windows problems, missing coref output. Runs on newer Pythons only with pinned old `transformers`/`torch`/spaCy. Treat as archival research code you vendor and pin.

**The important 2026 development — ModernBookNLP:** "Fast and Accurate Quotation Attribution in Literary Texts" (Aug 2026, https://arxiv.org/abs/2608.02359) releases **ModernBookNLP_QA** (https://github.com/gasmichel/ModernBookNLP_QA/), replacing BookNLP's quote attribution with a ModernBERT-large joint-scoring model: **94.5% attribution accuracy on PDNC** (explicit 99.3% / anaphoric 95.5% / implicit 89.3%), +9.4 CoNLL-F1 over original BookNLP on LitBank QA, ~5.5s per book on a consumer GPU, 20× faster than comparable methods and >1000× faster than LLM approaches — while also **beating** Llama-3-8B joint prompting (89.8%).

**Multilingual:** NEH Multilingual BookNLP (Spanish/Japanese/Russian/German); BookNLP-fr (CCLS 2024). Only relevant for non-English classics later.

## 2. LitBank & Bamman-group corpora

**LitBank** (https://github.com/dbamman/litbank): 100 English fiction works (1719-1922, public domain, from Gutenberg — exactly the target era), ~210k tokens, four annotation layers on ~2k-word samples per book: entities, realis events, coreference, quotation attribution. It's a *training/eval corpus*, not a tool. Value for the pipeline: **ground truth to benchmark our own extraction**. Key limitation: 2,000-word excerpts — never tests book-scale behavior (why BookCoref exists).

## 3. Quotation attribution & character networks

- **PDNC** (Project Dialogism Novel Corpus, https://arxiv.org/pdf/2204.05836) — 35k+ annotated quotations, the standard benchmark.
- SOTA progression: BookNLP baseline → character-embedding hybrids (EMNLP 2024) → Llama-3 joint prompting (NAACL 2025) → **encoder joint scoring back on top in 2026** (94.5%, ModernBookNLP).
- **Character networks:** classical co-occurrence/conversation-network literature (Labatut & Bost survey, ACM CSUR 2019) superseded by LLM extraction: CREFT (2025, multi-agent relation extraction, https://arxiv.org/html/2505.24553), R2 novel-to-screenplay causal plot graphs (https://arxiv.org/html/2503.15655v1). **No maintained off-the-shelf character-network library worth adopting** — the graph is a few lines of aggregation once attribution + coref exist.
- "Recall Them All: Long List Generation from Long Novels" (https://aclanthology.org/2025.lm4dh-1.13.pdf) — merely *listing all characters* is a nontrivial LLM failure mode; cross-check the LLM roster against BookNLP's clustered entity list.

## 4. Coreference at book scale (the "the Count = Dracula = he" problem)

Weakest link everywhere. LitBank-trained coref (~76-79 F1) only ever saw 2k-word excerpts. **BookCoref** (ACL 2025, https://arxiv.org/abs/2507.12075) is the first book-scale benchmark: retraining on it gains up to +20 CoNLL-F1; **Maverick-XL at 82.2 CoNLL-F1** is current best. Maverick (`maverick-coref` on PyPI, Sapienza NLP) is maintained and pip-installable.

Practical note: we don't need mention-level perfection — we need **character-level alias resolution**, which BookNLP's name clustering plus an LLM verification pass solves cheaply. Full-document coref matters mainly for per-mention evidence spans.

## 5. LLM-based literary analysis, 2024-2026

- **Character profiling benchmark:** CroSS / "Evaluating Character Understanding of LLMs via Character Profiling" (EMNLP 2024, https://arxiv.org/abs/2404.12726) — 126 novels, profiles = **Attributes / Relationships / Events / Personality**. GPT-4-class strong on Personality (~4/5), **weakest on Events** (~3.4-3.7/5).
- **BookWorm** (EMNLP 2024 Findings, https://arxiv.org/abs/2410.10372): **retrieval-based (especially coreference-guided retrieval) beats hierarchical chunk-summarization** for factual character descriptions — direct evidence the classical layer *improves* an LLM pipeline.
- **Long-context limits:** **NoCha** (https://arxiv.org/abs/2406.16264): best model only **55.8%** on claim-pairs over full novels vs near-ceiling humans; global-reasoning claims hardest; heavy world-building worse. **FABLES** (https://arxiv.org/pdf/2404.01261): book-length summaries systematically wrong about **events and character states** — chapter-wise extraction with verification beats one-shot whole-book prompting.
- **CoSER** (ICML 2025, https://arxiv.org/abs/2502.09082) — 17,966 characters from 771 books with experiences/internal thoughts; reference for derived-novel/dialogue products.
- **Audiobook-specific:** **S-VoCAL** (LREC 2026, https://arxiv.org/abs/2603.00958) — infers 8 sociophonetic *voice* attributes (age, gender, origin, health…) for 952 Gutenberg character-book pairs to drive TTS voice casting.
- **Image-gen adjacent:** no established tool extracts *physical* descriptions per se — supersense tags (body/clothing) + coref-guided retrieval + LLM synthesis is the assembled solution.

## Verdict for a 2026 pipeline

**Keep (as libraries alongside LLMs):**
1. **ModernBookNLP / BookNLP** — one cheap local pass per book: entity clusters with aliases, per-character verb/possession/modifier lists, 94.5%-accurate quote attribution in seconds. Vendor + pin (Windows dependency-pinning work expected).
2. **Maverick coref** — only if mention-level, evidence-linked retrieval is wanted; otherwise BookNLP clustering + LLM alias verification suffices.
3. **LitBank / PDNC / CroSS / BookCoref as eval sets** — score the extractor before trusting it.

**Replace with LLM calls:** chapter summaries, world/setting extraction, relationship semantics, physical-description synthesis, personality profiles, character networks (derived), voice casting. But per NoCha/FABLES: **chapter-wise with structured schemas and a verification pass**, never one whole-book prompt.

**Recommended architecture:** structural pass (characters+aliases, quotes+speakers, mention spans) → coref-guided retrieval of per-character evidence → LLM synthesis per chapter into schema → LLM verification against retrieved spans. BookWorm/NoCha/FABLES consistently show this hybrid beats LLM-only on factuality.
