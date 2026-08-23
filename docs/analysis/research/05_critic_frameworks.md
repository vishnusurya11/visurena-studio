# Research 5 — How professionals analyse a book (critics, academics, BookTube, rereads)

*Wave-2 subagent report, 2026-08-22.*

## 1. Journalistic book criticism

- **Kirkus formula**: 250-350-word capsule — **logline → one paragraph plot summary → one/two-line italicized verdict**. Requires significant summary for context + opinion-based analysis of plot development, character depth, writing style, pacing, structure; named strengths/weaknesses; no hyperbole. (kirkusreviews.com/indie-reviews/traditional-reviews)
- **Publishers Weekly**: ~200-word anonymous capsules by genre experts; reviewers audition with a sample capsule — the capsule IS the form.
- **What critics actually judge** (Phillipa Chong, *Inside the Critics' Circle*, Princeton UP 2020 — interviews with NYT/LAT/WaPo reviewers): five recurring criteria — **(1) characterization, (2) language and prose, (3) plot and structure, (4) themes and ideas, (5) genre expectations** — the book is judged against what its own genre promises, never an absolute standard.
- **Updike's rules** (*Picked-Up Pieces*, 1975; canonical reviewer's code):
  1. Understand what the author *wished to do*; judge intent-relative.
  2. Give enough **direct quotation** — at least one extended passage.
  3. Confirm every description with quotation, never "fuzzy précis."
  4. Go easy on plot summary; **never give away the ending**.
  5. If deficient, cite a successful comparable and understand the failure.
  6. No predisposed bias.
- **Longform (LRB/NYRB/New Yorker)**: the review-essay — thesis-driven, book as evidence in a larger argument; the "find the thread" method (one organizing observation all evidence hangs from).

## 2. Academic literary analysis in practice

- **Close reading protocol**: initial read → annotate → **multiple focused passes, one element per pass** (diction register / imagery families / syntax rhythm / tone) → patterns and anomalies → claim about how form produces meaning.
- **Character-study vocabulary**: agency, motivation (and where it shifts), **interiority** (degree of access + technique: free indirect discourse, direct thought, external inference), foils, dynamic/static, round/flat, unreliable narration, arc.
- **Forster's test** (1927): round = "capable of surprising in a convincing way. If it never surprises, it is flat. If it does not convince, it is a flat pretending to be round." → machine form: per-character surprise ledger + was-it-grounded.
- **Propp**: 31 fixed-order plot functions; 7 roles (villain, donor, helper, princess, dispatcher, hero, false hero).
- **Greimas actantial model**: 6 actants on 3 axes — Subject↔Object (desire), Sender↔Receiver (transmission), Helper↔Opponent (power). **Actants are roles, not characters**: one character can hold several actants, several characters one actant, per narrative program — the right abstraction for machine role-tagging per plotline.
- **Character arcs** (Weiland codification): Positive Change / Flat / Negative (Disillusionment, Fall, Corruption), driven by "the Lie the character believes" vs a Truth.
- **Pacing has a real brick**: Genette's duration — **scene** (discourse ≈ story time), **summary** (acceleration), **pause** (description; story time stops), **ellipsis** (story time skipped). A pacing profile = ratio of story-time to page-time per segment.
- **Thematic analysis**: annotate → code → cluster codes into themes → per-theme evidence (quotes/scenes) → interpret. Motifs/symbols are the trackable surface of themes.

## 3. BookTube / video essays

- **CAWPILE rubric** (Book Roast): **C**haracters, **A**tmosphere, **W**riting, **P**lot, **I**ntrigue, **L**ogic (internal consistency, decision plausibility), **E**njoyment — each 1-10, averaged, banded to stars. Variants: weighted; **Two-Part** (technical score vs pure enjoyment). The technical/affective split is universal.
- **Spoiler convention**: spoiler-free section → announced marker → spoiler section; big releases get two videos. → every analytical output needs a **spoiler-level tag** (premise-safe / mid-book / ending).
- **Video-essay structure**: hook → *arguable* thesis → body sections each answering one sub-question with pointed-at evidence → conclusion.
- **Lore-explainer channels** (Alt Shift X, In Deep Geek, Quinn's Ideas): formats = episode/chapter recap-explainers, character-journey essays, theory/lore videos. Structural requirements on an analysis layer: **chronological event timelines, relationship webs, independently-extractable per-character journey threads, evidence chains for theories (foreshadowing clue lists), "what this scene means" annotations.** Recap-explainer form: what happened → what it means → what it sets up.

## 4. Reread communities — per-chapter schema

- **Tor/Reactor WoT Reread**: per chapter — "What Happens" (neutral summary + significant quotes) + commentary (ongoing mysteries, themes, Crowning Moments of Awesome).
- **Malazan Re-read**: scene-by-scene summary + **two commentaries: naive first-time reader (raw reaction, predictions) and veteran (foreshadowing, connections, significance)**.
- Converged per-chapter field set: scene summaries; POV; key quotes; new characters/places/terms; open mysteries raised/advanced; foreshadowing (veteran) vs first-read feel (naive); emotional highlights; predictions.
- **The killer feature: the dual naive/veteran lens.** A machine reading the whole book natively has the veteran view and must **deliberately reconstruct the naive view** — the delta between them (dramatic irony, hidden setups, twist force) is itself high-value analysis.

## 5. The 20-dimension checklist (judgments-with-evidence, not entity fields)

Corroboration: ACL 2025 paper mining reader reviews derived the same axes (plot coherence, character development, pacing, emotional engagement, worldbuilding, dialogue, thematic depth). (aclanthology.org/2025.acl-long.799.pdf — PDF saved in session scratchpad)

| # | Dimension | Brick | Consumers |
|---|---|---|---|
| 1 | **Pacing profile** — per-chapter scene/summary/pause/ellipsis classification; story-time:page-time curve | Genette duration | 🎬 (scene-mode segments are inherently filmable) 🎧 (tempo) 📖 |
| 2 | **Prose style characterization** — register, syntax rhythm, imagery families, quoted exemplar | close reading; Updike r.2 | 🎧 (narrator casting) 🎵 (vocabulary palette) 📖 (style target) |
| 3 | **Tone/mood shift map** — chapter-level coloring + transitions | close reading; CAWPILE Atmosphere | 🎵🎬🎧 |
| 4 | **Roundness & surprise ledger** — Forster verdict + (surprise, grounded?, evidence) | Forster | 🎬📖 |
| 5 | **Agency & motivation timeline** — wants, shifts, drive-vs-driven, interiority technique | character-study protocol | 🎧🎬🎵 |
| 6 | **Arc classification** — Positive/Flat/Negative(+subtype); Lie vs Truth; beat positions | Weiland | 🎬🎵📖 |
| 7 | **Actantial role map per plotline** — incl. role switches over time | Greimas | 🎬📖 explainers |
| 8 | **Foil pairs** — contrasted traits, theme served | character study | 🎬🎵 |
| 9 | **Foreshadowing/payoff pairs** — setup↔payoff, distance, type, naive-noticeable? | craft + Malazan veteran lens | 🎬 (theory videos, spoiler protection) 📖 |
| 10 | **Naive-reader experience track** — per chapter: knows/feels/wonders/predicts | Malazan dual lens | 🎬 spoiler cutting 🎧 (irony vs surprise) |
| 11 | **Open-mystery ledger** — raised/advanced/answered per chapter | WoT reread | 🎬 recaps |
| 12 | **Stakes escalation curve** — what's at risk, for whom, try-fail cycles | trade "plot & structure" | 🎬🎵 |
| 13 | **Emotional beats / highlight reel** — ranked moments + type (awe/grief/triumph/dread) + quote | reread CMOAs | **🎬 this list IS the shorts backlog** 🎵🎧 |
| 14 | **Internal-logic audit** — rule violations, plausibility, timeline contradictions | CAWPILE Logic | 📖🎬 |
| 15 | **Thematic statement + motif index** — themes backed by coded occurrences | thematic-analysis method | 🎵🎬📖 |
| 16 | **Genre-expectation verdict** — what it tries to be, judged against that | Updike r.1; Chong c.5 | metadata 📖 |
| 17 | **Comparable works** | Updike r.5; PW | metadata, "for fans of X" |
| 18 | **Capsule verdict + logline** — Kirkus form, generated FROM dims 1-17 | Kirkus | video descriptions, pitch |
| 19 | **Structural timeline** — chronological vs narrated order, analepsis/prolepsis flagged | Genette order | 🎬 timeline videos 📖 |
| 20 | **Chapter recap-explainer triplet** — happened / means / sets up (+ POV, new entities, quotes) | reread schema + recap form | 🎬 direct script skeleton |

## Three cross-cutting invariants for the pipeline

1. **Every judgment is quote-backed** (Updike 2-3) — also makes outputs directly usable as video-essay evidence.
2. **Synopsis and evaluation are separate artifacts** (Kirkus; Updike 4) — the entity/summary layer and the judgment layer are distinct records; judgments reference summary units.
3. **Dual-lens analysis** (Malazan) — omniscient/structural view AND reconstructed naive-first-read view; the delta is itself the analysis.
