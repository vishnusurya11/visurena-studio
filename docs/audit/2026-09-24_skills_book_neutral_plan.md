# Skills and agents must be book-neutral — change plan

Status: PLAN, owner decisions recorded 2026-09-24. No skill file has been edited yet.
Source: five read-only audits, 2026-09-24 (episode core; LESSONS + archive;
trailer core + 01-05; trailer 06-10 + voices + agents + shorts; architecture).

## The problem, in one line

Skills and agents cite where a rule was learned (ep09 T02, Holmes, "the owner's
'ai slop'", Scarlet, WotW) instead of the failure it guards. An agent on another
book reads one book's history as canon, copies its examples as templates, and
inherits its constants as law.

## Scale

| area | story-specific hits |
|---|---|
| episode SKILL.md + GATES.md + agents/episode.md | ~40 |
| episode LESSONS.md | ~31 lines (52 lessons, all generic once IDs are stripped) |
| episode SCARLET_ARCHIVE.md | 1839-line old skill, ~181 hit lines, **on the "read before you work" list** |
| trailer SKILL/BLUEPRINT/BUILD + 01-05 | ~150 hits (58 grouped rows) |
| trailer 06-10, cast-voices, agents, shorts | ~35 rows + ~45 run/row IDs |

Worst three, across all audits (each actively misleads an agent on a new book):

1. **SCARLET_ARCHIVE.md is required reading.** SKILL.md:17-21 and agents/episode.md:8-12
   send every episode agent into 120 KB of another book's route.
2. **Genre and book defaults live in code while the skill calls them generic.**
   Period palette ("practical period light sources", "gaslight amber") in
   `trailer_refs.py`; `form_for` defaults to `detective`; register fallback
   `procedural`; `cast_card` wardrobe pools are Victorian (bowlers, bonnets,
   custodian helmets); accents RP/LONDON/FRONTIER/PULPIT in `voice_design.CAST`;
   `house_style.py:33 HOUSE_WHERE = "1881 London"`; mystery emotion set.
   A modern or sci-fi book would silently get a Victorian look, cast and score.
3. **One-book, one-machine calibrations stated as law.** Panel/take walls
   (held 0.75 on n=2, jump 0.50, ink 0.007), "Scarlet is 100 BPM", H3 cycle
   floor 1.70 min/s from one run, `MAX_LINES` 13 from a 108 s cue (format is now
   60 s ±10). Plus the plan name `wotw_epNN_*.py`, which
   `tests/test_a_plan_script_regenerates_its_plan.py:23` globs literally, so
   another book's plan silently loses its guard.

## Where to edit

**One folder.** 2026-09-24: master was fast-forwarded to `wotw-refs-poc`
(`f6ea1e0`); master had 0 commits of its own, and its uncommitted mirror of the
episode skill was byte-identical to that commit. The owner's rule: the worktree
should never have existed. **Everything lives in
`D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio`, on master; everything
book-specific lives under `library/<book>/`.** No worktrees, no per-book
branches, no second copies. The worktree and its branch are removed
(see `docs/ARCHITECTURE.md`, "One folder").

## Layering (the convention)

| layer | path | holds | auto-loaded |
|---|---|---|---|
| Skill | `.claude/skills/**`, `.claude/agents/*.md` | rules with stable IDs (`G-ANCHOR`, `L-<slug>`), failure stated neutrally, counts allowed, no identifiers | yes |
| Casebook | `library/<codex>/casebook/CASEBOOK.md` (owner's rule 2026-09-24: everything book-related lives under `library/`; it is gitignored, so it is not versioned) | per rule ID: book, episode/take, date, owner's words, numbers | no |
| Calibration | `docs/calibration/*.md` (exists) | datasets behind thresholds; may cite episodes | no |
| Per-book data | `library/<codex>/` (`book.json`, `registry.json`, `refs.json`, new `wardrobe.json`, `accents.json`, `story_defaults.json`) | the book's era, cast, looks, accents, banned props | read by code |

Writing rule (for CLAUDE.md and `docs/CASEBOOK_FORMAT.md`):

> **Skills and agents state the failure, never where it happened.** A rule in
> `.claude/` names the mode and carries an ID. No episode/take numbers, dates,
> book, character or place names, or owner quotes — those go in
> `library/<codex>/casebook/CASEBOOK.md` under the rule's ID. A worked example uses
> `<placeholders>`, never one book's literal values. A threshold names what it
> was calibrated on and says to re-measure on a new book, style, GPU or LoRA.
> `tests/test_skills_are_book_neutral.py` enforces this.

## Phases

### Phase 1 — the guard ($0, test first)
- `tests/test_story_names.py` (red) → `studio/story_names.py`:
  `produced_books`, `title_terms`, `registry_names`, `story_hits` — names derived
  from `library/<codex>/source/book.json` + `analysis/registry.json` of books that
  have `episodes/` or `trailer/`; never a hand-typed denylist.
- `tests/test_skills_are_book_neutral.py`: patterns `ep\d+`, `T\d{2}`,
  `shots? \d+`, ISO dates, `the owner's "`; plus derived names. Skips vendored
  skills. Name half skips if no library; pattern half always runs.
- Ratchet: today's offenders listed in `MIGRATING`, `xfail(strict=True)` — the
  suite is green on day one and a cleaned file must leave the list.
- Add the writing rule to CLAUDE.md.

### Phase 2 — take the archive off the reading list
- `git mv .claude/skills/episode/SCARLET_ARCHIVE.md` out of the repo to `library/<scarlet-codex>/casebook/ARCHIVE.md`
- Remove it from SKILL.md:17-21 and agents/episode.md:8-12.
- Create `docs/CASEBOOK_FORMAT.md` (format only) and `library/<wotw-codex>/casebook/CASEBOOK.md`.

### Phase 3 — scrub, one commit per file, evidence moves to the casebook
Order (always-loaded first): agents/episode.md → episode SKILL.md → GATES.md →
LESSONS.md → trailer 02-refs, BUILD, 05-dialogue, 01-story, BLUEPRINT, 09-voice,
trailer SKILL, 03-music, 10-casting (+VOICEDESIGN), 08-assemble, 06-style,
04-shots, 07-cards → cast-voices → other agents → shorts.
Each commit: rewrite per Appendix, add CASEBOOK entries, drop from `MIGRATING`.
- LESSONS.md: delete the 7 duplicates (P1, P3, P4, C6, D1, D4, D8, D12),
  re-section D13-D19 into Cast/Grids/Takes, strip IDs from the rest.
- BUILD.md narratives and 03-music §§11-21 (one book's cue ledger) move to
  `library/<scarlet-codex>/casebook/trailer-retrospect.md` / `trailer-music-ledger.md`;
  the skill keeps one RULE line per mechanism.
- Worked examples become `<placeholder>` templates (03-music §1 FILL-THE-SLOT,
  `1881 London` setting example, §9 lyric nouns).
- Every calibrated threshold gets a "calibrated on … ; re-measure when …" note,
  its per-episode evidence moves to `docs/calibration/`.

### Phase 4 — rescue the 27 rules only the archive holds
Music bed method, story layer (one question per episode, every shot turns a
value), YouTube title/snippet rules, "no group is described once", "every prop
carries a size", twin panels, safety-filter wording, writing-with-agents, etc.
Promote neutrally into LESSONS/GATES or `docs/calibration/bed.md`. Four voice
rules were measured on IndexTTS2 and must be re-validated on Qwen3-TTS first.

### Phase 5 — code track (separate, test first; docs first, then this)
0. **Book content out of the code tree** (owner, 2026-09-24: anything book-related
   goes under `library/`). Tracked book-named files today:
   `scripts/episode/plans/wotw_ep01..11_*.py` and `ep09..14_*.py`, `_ep05_prop_mast.py`
   → `library/<codex>/episodes/epNN/plan.py`;
   `docs/A_STUDY_IN_SCARLET_HANDOFF.md`, `docs/SERIES_GOAL.md` → `library/<scarlet-codex>/`;
   `.claude/skills/episode/SCARLET_ARCHIVE.md` → Phase 2.
   `tests/fixtures/scarlet_*.json`, `wikiquote_*.json` are recorded parser
   fixtures the tests need; keep, rename neutral. `test_a_plan_script_regenerates_its_plan.py`
   globs `library/*/episodes/*/plan.py` and names no book in its docstring.
1. Plan prefix `wotw_epNN` disappears with 0 (the folder names the book).
2. `house_style.py` HOUSE_WHERE/light → per-book config.
3. `trailer_refs.py` period palette → era from the book.
4. `voice_design.CAST` accents → `library/<book>/cast/accents.json`.
5. `cast_card` POOLS/ROLE_ITEMS/FEMALE_ONLY → `library/<book>/refs/wardrobe.json`.
6. Register fallback `procedural`, `form_for` default `detective`, detective
   palette "gaslight amber", mystery emotion set → per-book defaults, neutral fallback.
7. `MAX_LINES` / `PINNED_DURATION` re-derived from the 60 s ±10 format.
8. Rename book-named tests (`test_scarlet_thread_line_is_in_pool`, `test_sparta_outscores_ferrier_errand`, `test_run_6_…`, `test_the_run_9_…`).

### Phase 6 — close out
- Delete `MIGRATING`. Update `SERIES_GOAL.md` step 5 ("improve the skills,
  book-neutral; evidence to the casebook") — that step is where leaks are written.
- Memory (outside repo): make MEMORY.md index lines neutral; mark
  `project_series_goal` (Scarlet ch. 4-14) stale.
## Owner decisions (2026-09-24)

- **D-A Where:** master only. All current working code lives in master
  (done: fast-forward to `f6ea1e0`).
- **D-B Order:** docs first (Phases 1-4, 6), then the code track (Phase 5)
  straight after, test-first.
- **D-C Camera push rule:** dropped. Camera variety wins; the archive's
  "close/insert takes pan or tilt only" is not carried over.
- **D-D Accent rule:** name the accent. 09-voice:21 is rewritten to defer to
  10-casting + VOICEDESIGN; accents move to per-book `accents.json` in Phase 5.
- **D-E Memory index:** open — not yet asked.

---

## Appendix — line-level work orders

Types: A delete · B generalise the evidence · C per-book/machine constant → config ·
D section moves out · G genre baked into a generic rule. Line numbers are
identical in both trees as of 2026-09-24.

### episode/SKILL.md
| line | now | type | becomes |
|---|---|---|---|
| 8-11 | worktree `visurena_studio_wotw`, branch `wotw-refs-poc` | C/D | DONE 2026-09-24: "runs from the repo root, on master; one checkout, never a worktree or per-book branch". |
| 17-21 | reading list incl. SCARLET_ARCHIVE.md | D | drop the archive line |
| 36, 43-44, 84 | `wotw_epNN_<slug>.py` | C | `<bookslug>_epNN_<slug>.py` (+ Phase 5.1) |
| 47-49 | "ep06 paid for three picture stages… ep09…" | B | "Skipping it has cost whole picture stages: over-length prompts and banned props surfaced only at takes." |
| 51-52 | "each cost ep09 renders" | A | delete clause |
| 55 | "he walked with the fence… ai slop (ep09 T02)" | B | "A person leaning on a fence or wall slides through it — rejected on sight as AI slop." |
| 58-59, 62-63, 66-67 | ep09 shots 14/15/18; ep10 T18 | B | neutral failure (re-seed does not fix; landmark named but not drawn gets invented; "low over him" drew upright → world rotated) |
| 70-71 | "failed every WotW plan for another book's reasons" | B | "It once refused plans for another book's reasons; now a refusal is real." |
| 77 | `20260827135508_the-war-of-the-worlds` | A | `<timestamp>_<book-slug>` |
| 110-111 | "ep01, ep03 and ep04 were patched" | A | "Hand-patched plans have shipped before…" |
| 142-143 | "Horsell Common into ep09's daylight" | B | "moved every earlier episode's picture of the place into the new episode's hour" |
| 155 | "cook yer" | B | "an eye-dialect spelling" |
| 173-174 | lawn with no fire; Snippy clean-shaven | B | "a place's defining state / a character's defining feature was dropped" |
| 186-197 | ep09 grids, riders, hussars | B/D | neutral count rules; open decision D3 status → decisions log |
| 202 | "(ep10 narrator and landlord)" | A | delete |
| 211-213 | "On ep09 both gates passed…" | B | "Both gates have passed a white gutter, one man with two hats, and an insert that was the place reference copied back." |
| 233-234, 242, 245 | T02 92.6; ep08 T16; ep09 shots | B/A | neutral measurement or delete |

### episode/GATES.md
| line | type | action |
|---|---|---|
| 7 | A | drop "from the 2026-09-22 audit"; keep "a gate that measured nothing has passed nothing" |
| 22 | C/D | keep HARD; calibration IDs → `docs/calibration/cell_gates.md` |
| 30 | B/C | SHEET TEXT: "books whose sheets came from the paid route (flag in `book.json`)" |
| 61 | C | banned props → per-book `dq_rules.json` |
| 68-69 | B | "Matching by the last word of a display name staged the wrong person in several published takes." |
| 80-82, 91-92, 98 | C/D | keep thresholds + "calibrated on N panels of one book's style; recalibrate on a new book or style"; IDs → `docs/calibration/panel_gates.md` |
| 132-133 | A/D | delete dry-run status |
| 142-149 | B/A | T14 lawn, sappers/hussars, NEWSPAPER BOY, ep07 S12-S14 → neutral |

### agents/episode.md
| line | type | becomes |
|---|---|---|
| 8-12 | D | drop SCARLET_ARCHIVE; "Older routes are archived under docs/casebook/, history only." |
| 17 | B | "…a copied reference, and a person the scenery slid through — all passed by gates, rejected on sight as AI slop." |

### episode/LESSONS.md
Delete: P1, P3, P4, C6, D1, D4, D8, D12 (duplicates). Move D13→Cast, D14/D15→Grids,
D17/D18/D19→Takes. Neutral rewrites for P5-P8, C1-C3, C5, C7-C9, PL1-PL5, GR6-GR9,
T2, T7, T9, T10(+D7), D6, D9-D11, D16-D19 as in the audit (strip episode/take IDs
and names; keep counts and numbers). Already neutral: P2, C4, PL6, GR1-5, T1,
T3-T6, T8, D2, D3, D5.

### trailer SKILL / BLUEPRINT / BUILD
- SKILL:15-17, BLUEPRINT:21 Scarlet folder → `library/<codex_id>_<slug>/` (C)
- SKILL:44-50, 82, 116-132, 212, 264-345; BLUEPRINT:132-211, 346, 482-505 → "the lead", "a delivered cut", "the reference book" (B)
- BLUEPRINT:28-38 keep the "corpus of one" caveat, book-neutral; push it into every subskill header
- BLUEPRINT:54, 78-79 → delete / "3 of 30 books die in step 01" (A)
- BLUEPRINT:322 fallback `procedural` (G) → per-book `story_defaults.json`, neutral
- BUILD:20-219 run narratives, table cells rows 58-71 → `docs/analysis/research/trailer-retrospect.md` (D); BUILD:299 emotion set (G/C)

### trailer 01-story
16, 18, 31-99, 134, 187-221 → roles not names (B); 22-27 `verified` column (D);
114, 116, 121 detective==procedural "gaslight amber", `1881 London` → placeholders + per-book palette (G)

### trailer 02-refs (densest)
23-75, 101-169, 201-260, 275, 294-343, 358-381 → roles ("the lead", "the narrator",
"the figure", "an inspector") (B). 63-64, 84, 175-212, 288-301 wardrobe pools,
ROLE_ITEMS, bonnets (G/C) → "pools are the book's wardrobe, from `wardrobe.json`";
keep "two people may not share a BUCKET".

### trailer 03-music
§0/§1 head and FILL-THE-SLOT strings → `<family>`, `<lead instrument>`,
`<diegetic object>` placeholders (G/B, highest copy risk). §4 bar map → "Worked
example at 100 BPM (reference book)" (D). §6 palettes → "reference; tone.json is
truth; replace for modern/sci-fi" (G). §7 "Scarlet is 100 BPM" → tempo rule, value in
`tone.json` (C). §8:405 delete; §8:433, §9 → neutral (B/A). §§11-21 (~542-1375)
cue ledger → `docs/analysis/research/trailer-music-ledger.md` (D); owner quotes →
"the listener's verdict".

### trailer 04-shots
15, 58-59, 112, 175-181 → "the reference plan" (B). 24-155 H3 cycle constants →
header "calibrated RTX 4090, H3 turbo LoRA @0.8, 2026-09, 22 takes; re-measure on
hardware/LoRA change" or `docs/calibration/h3_cycle.json` (C).

### trailer 05-dialogue
13-26, 52-68, 86-88, 135-143, 170-262, 281 → roles (B); 103-104 (A); 322, 407 →
"the listener's verdict" (B); 436-443 label worked example (D); 305-306, 379-391
`MAX_LINES`/108 s stale (C).

### trailer 06-style, 07-cards, 08-assemble
06:12 "Scarlet's 19 words" (B), "period light sources" (C, in code); 06:18, 42,
48, 55, 65; 07:44 Jekyll clipped title, 110, 162 (B/A); 07:124 Bookman "genuinely
Victorian" → per-book `title_face` (C); 08:158, 362, 455, 462, 513-527 (B).
Run/row IDs across 06-09 (~45) → "an earlier run"; exact IDs to run NOTES.

### trailer 09-voice, 10-casting, VOICEDESIGN, cast-voices
09:33-59, 170, 214, 262-275 → neutral (B); 09:21 conflicts with 10-casting (D-D).
10:24-38, 96, 106, 153 (B); 10:43-44 accents (C, in code); 10:161-184 "Open, not
solved" → `library/<book>/cast/STATUS.md` (D). VOICEDESIGN:101-135 (B).
cast-voices:8-16, 46-47 (B), :28 `--only <char_id>,<char_id>` (A).

### other agents and shorts
trailer-cinematographer:12-14 "naming Holmes…" (B); trailer-art:19-21 "period
figure… period dress" (B/G); shorts-screenwriter:65 `kaladin_sheet.png` →
`<character_id>_sheet.png` (A); shorts-story:16 channel brand → channel config (C, low risk).
