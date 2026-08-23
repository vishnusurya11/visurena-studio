# Analysis Stage — Proposed Design

**Status: PROPOSAL, v0.2 — 2026-08-22. Nothing built. Owner reviews; we iterate together.**

Evidence base: seven research files in [research/](research/) — NLP tooling (01), LLM extraction
patterns (02), story-bible schemas (03), format precedents + first draft (04), critic frameworks
(05), practitioner timeline tools (06), narratology formalism (07). Every design choice below
cites its research.

---

## 1. What analysis produces — three layers plus free views

The single biggest structural finding (independently reached by 04, 06, 07): **store one event
record; treat every ordering and report as a derived view.** Aeon Timeline, film EDLs, wikis,
stripboards, and TLEX all converged on this.

| Layer | What it is | How it's made |
|---|---|---|
| **L1 EXTRACTED** | The event log: entities, mentions, events, fluents (states), temporal constraints, dialogue attribution, narration metadata — everything **quote-grounded** | per-chapter LLM extraction + structural NLP pass |
| **L2 JUDGED** | The 20 critic dimensions (research 05): pacing profile, arcs, foreshadowing/payoff pairs, stakes curves, emotional highlight reel, themes… every judgment **quote-backed + spoiler-tagged** | LLM analysis passes over L1 + text |
| **L3 SYNTHESIZED** | Production blocks: locked visual prompt blocks (50-100 words, verbatim-copied), voice/casting blocks, pronunciation guide, song seeds, capsule/logline | paid-model synthesis over L1+L2, `stated_vs_inferred` flagged per attribute |
| **VIEWS (free)** | Character sheets, chronological & told-order timelines, location indexes, character×chapter presence/state matrices (the film-industry **DOOD test**), spoiler-gated "bible as of chapter N", relationship webs, shorts backlog | **pure code over L1+L2 — never extracted separately, so they can never contradict** |

Resolution of the "bible: projection or sibling?" fork from draft 04: **the story bible
(research 03's field lists) is a VIEW assembled from L1+L2+L3** — one source of truth. Only the
genuinely synthetic blocks (L3) are stored; everything positional/factual is projected.

Three invariants adopted from professional practice (05):
1. **Every judgment is quote-backed** (Updike rules 2-3).
2. **Synopsis and evaluation are separate artifacts** (Kirkus structure).
3. **Dual lens**: the omniscient/structural view AND a reconstructed naive-first-reader view;
   the delta (dramatic irony, twist force) is itself stored analysis (Malazan reread pattern).

## 2. The timeline format (name: OWNER PICKS — candidates in §6)

Draft v0.1 was research 04; v0.2 below folds in the 14 narratology primitives (07) and the
18 practitioner features (06). Full spec to be written after review; the load-bearing choices:

- **Dual clock, never derived from each other** (fabula/syuzhet): every event mention has a
  precise **discourse anchor** (chapter/scene/paragraph span — always known) and every event a
  **story-time anchor** (often fuzzy). Flashback/foreshadow status and pacing are *computed*
  (Genette order/duration), never stored.
- **Mentions ≠ events, many-to-many** (Genette frequency): a retold event = n mentions → 1
  event; "every Sunday…" = 1 mention → recurring event-set. *(Upgrade over draft v0.1.)*
- **Events are typed n-ary frames** — action / state_change / **perception** / reporting /
  dialogue / movement — with roles: agent, patient, experiencer, **witness**, location-of
  (NKRL/SIG/Aeon's Participant-vs-Observer).
- **Realis/modality flag on every event**: actual / planned / wished / dreamed / counterfactual
  (TimeML SLINK; LitBank realis). Dracula is full of feared and dreamed events.
- **Fluents for states** (event calculus): character-at-location, possession, injury, knowledge,
  alive/dead, relationship — `initiated_by` / `terminated_by` event links. This is what answers
  "where is Mina in chapter 18" when chapter 18 never says, and it is exactly a film script
  supervisor's continuity log (06 §4).
- **Story time = Aeon's shipped uncertainty model + Allen relations**: optional calendar value,
  **notBefore/notAfter bounds (4-date model)**, granularity, story-day numbering (film "D1/N3");
  between events, qualitative Allen relations with disjunction sets ("meanwhile") plus optional
  metric offsets ("three days later" = +3d ± slack). **Raw constraints stored; the solved global
  timeline (with indeterminacy flags) is a derived, regenerable view** (TLEX).
- **Narrative containers** (chapter/scene) give default temporal scope — keeps the constraint
  graph sparse (Pustejovsky & Stubbs) and matches how LLMs extract.
- **Narration segment metadata**: narrator, focalizer, focalization type, person, narrative
  level, world index. Dracula (epistolary) even has a third clock — narration time (journal
  entry date ≠ event date) — which the format carries as the container's own story-time anchor.
- **Per-character epistemic ledger** — derived from participant/witness/focalization + reporting
  events: what W knows at story-time T. Powers spoiler-safe and POV-correct generation
  (Living the Novel; TimeChara).
- **Typed causal edges** with strength (Trabasso via Swartjes-Theune; R²) — feeds dimension
  #12 stakes and lore-explainer "evidence chains".
- **Provenance + confidence on every assertion**; `extracted_vs_inferred` everywhere.
- **Engineering**: human-readable JSON (YAML accepted for editing), per-object schema versions
  (`"Event.1"`, OTIO pattern), open `meta` dict per object (FHIR-style extensions), stable IDs,
  **open published spec** — the market leader (Aeon) has none.
- **Acceptance tests for the spec**: (a) the **DOOD test** — character × chapter presence/state
  matrix computable by pure code; (b) round-trip a "meanwhile" chapter pair (Dracula's parallel
  Whitby/Transylvania threads) without contradiction; (c) losslessly export the temporal layer
  to ISO-TimeML.

## 3. Pipeline steps (each one a future `stepwise` Step: artifact out, gate, resume)

| Step | What | Executor | Model tier |
|---|---|---|---|
| **A0 Segment** | Chapters → scenes (>~6k-token chapters sub-split at scene boundaries); build container tree; set `num_ctx` explicitly | code | — |
| **A1 Structural pass** | BookNLP/ModernBookNLP: name clusters + aliases, quote attribution (94.5% acc), mention spans. *Optional but recommended (01); vendored+pinned; fallback = LLM sweep* | library | free/local |
| **A2 Registry** | Canonical entities: merge A1 clusters + LLM sweep; residual dedup = embedding kNN + string distance → **one paid merge-judge call**; roster cross-check (the "Recall Them All" failure) | code+LLM | local; 1 paid |
| **A3 Chapter extraction** | Per chapter, registry injected, **reason-then-JSON**, small per-concern schemas, evidence span per claim: events+mentions, fluent changes, dialogue map, narration metadata (POV/focalizer), scene records (location, time-of-day, characters, emotional function, **visual_potential**), recap triplet (happened/means/sets-up), naive-reader track, new-entity debuts, key quotes | LLM loop | **local** (~5-7 calls × chapters) |
| **A4 Fold** | Pure code: accumulate per-entity records, first/last appearance, build temporal constraint network, compute fluent spans | code | — |
| **A5 Timeline solve** | Allen propagation + metric bounds → global timeline + **contradiction list**; contradictions arbitrated by paid model against cited evidence (ASOIAF method: anchors + offset chains + slack) | code+LLM | code; paid arbitration |
| **A6 Consolidate** | Character sheets (arcs = the measured weak spot → strong model), locations, world rules (statement+cost+cannot-do), synopsis via hierarchical merge **with source re-injection**, themes/motifs, POV structure | LLM | **paid** (~15-25 calls) |
| **A7 Judge** | The 20 dimensions (05 §5). **v1 subset proposal**: pacing profile (1), tone map (3), arc classification (6), foreshadow/payoff (9), naive-reader track (10), stakes (12), **highlight reel (13 — the shorts backlog)**, themes (15), recap triplets (20). Rest phased in later | LLM | local draft + paid final |
| **A8 Synthesize** | L3 blocks: visual prompt blocks, voice/casting (S-VoCAL's 8 attributes), pronunciation guide, song seeds, logline/capsule | LLM | paid |
| **A9 Verify** | Grounding pass (does cited span support each claim? local y/n; flagged → paid arbitration); DOOD + timeline coherence checks; **QC report with per-artifact confidence** | LLM+code | local; paid on flags |

Chunking, context, and structured-output rules from research 02 are binding: chapter-sized
inputs on the local model, reason-then-JSON, per-concern schemas, retry wrapper in `studio/llm`.

## 4. Artifacts on disk (proposal)

```
media/analysis/<codex_id>/            # codex_id = THE id (YYYYMMDDHHMMSS)
  manifest.json                       # step statuses, hashes, QC summary
  text/                               # segmented source (from studio_parser)
  l1/  registry.json  events.jsonl  fluents.jsonl  constraints.json
       narration.json  dialogue.jsonl  chapters/ch_NN.json
  l2/  judgments/<dimension>.json
  l3/  visual_blocks.json  voice_blocks.json  pronunciation.json  seeds/
  views/                              # regenerable cache — deletable anytime
  qc/report.json
```

Relative paths only; `codex_id` is the join key everywhere (per DECISIONS).

## 5. Cost & gates

- A0-A5, A9: overwhelmingly **local** (free) + a handful of paid arbitration calls.
- A6-A8: the paid concentration — rough order **50-80 paid calls/book**, mostly small-context.
  Ballpark **$2-6/book** on a mid-tier API model; ~$0 with local-only degraded mode.
- **Zero Higgsfield credits anywhere in analysis.**
- Gate policy per ARCHITECTURE.md: paid-API steps carry an itemized estimate; first runs
  ESCALATE everything.

## 6. Open questions for the review (numbered — answer any subset)

1. **Format name** (you pick): `fabula` / `loom` / `NEL` / `tapestry` / `canon` / other.
2. **A7 v1 subset** — agree with the 9 proposed dimensions, or different picks from the 20?
3. **Dialogue granularity**: every line as an L1 event, or significance-tiered (proposal:
   attribution for ALL lines via A1 since it's free; full event records only for tier-1/2)?
4. **BookNLP dependency**: accept a vendored, pinned, Windows-fussy library for a real accuracy
   win (01), or LLM-only first and add it when it hurts?
5. **Confirm**: bible-as-view resolution (§1), scene as first-class container, JSON canonical.
6. **Where artifacts live**: `media/analysis/<codex_id>/` as proposed, or elsewhere?
7. Stage tracking (codex table option A/B) — still deferred, needed before A0 is coded.
8. **Paid model choice** for A6-A8 (Claude via API vs OpenRouter routing).

## 7. Publishable artifacts (standing goal — now confirmed from four directions)

1. **The format spec** — open, versioned, with JSON Schema + validator + an annotated
   public-domain novel (Dracula) as reference corpus. No incumbent exists (04, 06, 07).
2. **The extractor** — "public-domain novel → grounded story bible + timeline", local-model-first
   with verification. No strong incumbent (02).
Both are cleanly separable from the private studio; build as standalone packages imported here.
