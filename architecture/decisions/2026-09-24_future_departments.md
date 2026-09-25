# Future departments — the studio as a big studio

Status: **PROPOSAL, awaiting the owner's decision** (2026-09-24). Nothing here is
applied; `stages.yaml` is unchanged. The draft registry is beside this file as
[2026-09-24_stages_future.yaml](2026-09-24_stages_future.yaml); the visual is the "Future architecture"
tab of [../index.html](../index.html).

How it was made: five reports — two web researches (film/TV/animation org; YouTube,
streaming and transmedia operations), a production executive, an organisation
designer, and a keeper of this codebase's constraints — then a chair ruled every
point they disagreed on. The owner's framing going in: Pre-production = Analysis +
Screenplay; Production = episode video; Post-production = finishing + publishing +
promotion; a Research department later; "think of it like a big studio which has TV
shows, movies, music, games, books"; "we are just starting with episodes; we will
expand"; "a chapter can be a unit; it can expand". Book-neutral throughout.

The brick is unchanged: a **Step** (identity `production_id + step_name + input_hash`,
one artefact on disk, known cost, a gate). A department is an ordered list of Steps
(a stage in `stages.yaml`), a production is a DAG of Steps, an agent is a Step whose
executor is an LLM. Everything ruled below is a statement about which Steps sit in
which list, what file crosses each list boundary, and who may refuse it.

---

## 1. Debate record

Format per point: the positions with their strongest argument, then the verdict.
Where the owner's framing loses, it is said plainly with the replacement name.

### 1.1 "Post-production" = finishing + publishing + promotion, or Distribution + Marketing?

| position | held by | strongest argument |
|---|---|---|
| One post department: finish, publish, promote | owner; E's draft `post` stage (9 steps); C's `post` (FINISH, PACKAGE, DELIVER, PROMOTE, MEASURE) | Everything after the master is "what happens to a finished file"; one intake, one runner keyed on the finished file (E §3) |
| Two departments, Distribution and Marketing; the cut stays in the format line | D §7.1; A §3 and §4 (marketing has its own editorial, runs in parallel with post, reports to the studio not the producer; scheduling is separate from the crew) | Distribution is per `(master, platform)` and irreversible; Marketing is per release and *orders* work. Different unit keys cannot share one stage, because a stage has one unit grain and one runner. And industry "post" means the cut, grade, mix and QC, which must stay with the measured voice (audio-first rule) |
| Post has four units incl. Promotion, plus a catalogue owner | B (Finishing, Packaging, Delivery, Promotion; "stand up the catalogue owner now") | Every platform, own or third-party, asks for the same five bundles (master, audio, timed text, artwork set, metadata record) plus a QC verdict and a date; the role that makes them is one role |

**Verdict: the owner's framing loses on the word and wins on the list.** Everything he
named happens after the master and belongs outside the format line — publishing,
finishing to each platform's spec, promotion. But it is two divisions, not one
department, because the unit keys differ: **Distribution** (stages `publish`,
`analytics`: per `(master, platform)`, irreversible, owner-gated, owns the
catalogue) and **Marketing** (stage `promo`: per release, writes orders, posts
through Distribution). The cut, mix and QC are the last steps of each *Production*
line, never a post step: the picture is cut to the measured voice and the take gates
are format-specific (D, C unit 05-06, E 4.13). Retire the word "post-production" from
the org chart; in this industry it names the cut, and ours stays in the line.

### 1.2 Trailer: a format or a promotion?

| position | held by | strongest argument |
|---|---|---|
| Under promotion | owner; A rec. 4 ("the existing trailer stage moves under this department unchanged") | A trailer exists to sell the title; its purpose is marketing |
| A Production format line, ordered by Marketing | C §3, D §7.2, E option A | It has a 10-step DAG, ADAPT ladders, a runner, a music-first chain and registered events. Filing a GPU render chain inside a posting department creates a second floor (C). Moving it renumbers stable ids and breaks `run_budget.TRAILER_SHARES`, ten tests and the event history (E) |

**Verdict: Production format line; the owner's framing loses on placement of the work
and wins on purpose.** Stage `trailer` is untouched. Marketing's `promo` stage writes
`promo/<release>/order.json`; the scheduler launches `trailer.py` to fill it. Call it
*a promotional format made by Production on a Marketing order*. The same ruling covers
shorts, cutdowns and key art: Marketing orders, Production or Distribution makes.

### 1.3 Promotion: a unit of post, or a client of production?

Both, and the split is exact (C §4.1): the **decision** (which assets, which dates,
which platforms, inside which budget) is Marketing's step; the **manufacture** of any
asset that needs a render is a Production order; the **shipping** of any asset is
Distribution. Marketing never touches a GPU workflow and never calls a platform API.
B's "cut-list selector" survives as Marketing's `cutdowns` step because a cutdown is
ffmpeg on `placed.json` — no render, no new floor; a vertical or short-form cut that
needs new pictures is a `shorts` order.

### 1.4 Owner gates: three or five?

| position | count | list |
|---|---|---|
| A rec. 5 | 3 | plan, reference sheets, master (the animatic, the model sheets, the final cut) |
| C §4.3 | 5 | PILOT LOCK, LOOK LOCK, SPEND, RELEASE, QC OVERRIDE |
| D §2.1 | 3 classes | money, publish, taste; plus `RENDER_HOLD` |
| E 5a | open-ended | every approval kind, the synthetic declaration, going public, the master eye, the panel/strip eye until a VLM rubric is calibrated |
| Owner invariant | — | every spending step ESCALATES |

**Verdict: three classes (money, publish, taste), seven mechanical signatures today,
and a retirement rule that shrinks taste to A's three.** The counts disagree because
they count different things: A counts steady-state taste gates, C counts events, D
counts decision classes, E counts what the code refuses without today. Section 3
lists the seven with their files. The owner's invariant stands and is not retirable
for paid credits; GPU time (`render`) is the one money kind a format may retire.

### 1.5 Organising axis: function, format or IP?

| position | held by | strongest argument |
|---|---|---|
| Function on top, one `production` stage with shared units, format as a file (`formats/<name>.yaml`) | C §2, §4.4 | "Build PREP once, build post once"; six units defined by artefact kind; a new product is five lines of yaml |
| Function on top, one stage per format inside Production, IP as the data key | D §1, E option A | The episode DAG (audio-first) and the trailer DAG (music-first) share modules, not steps and not a gate ladder; a functional Production leader would be a switch statement; events key on `(codex_id, stage, step_id)` and ids are stable |
| Format (craft) × IP (worldview) grid; IP needs a managerial owner | B Q3 | Every transmedia company converges on the grid; what no vendor sells is the catalogue/canon/rights owner |
| Owner | — | "a big studio which has TV shows, movies, music, games, books" — format lines under one roof |

**Verdict: function at the top (five divisions), one registry stage per format line
inside Production, IP as the data key plus one owned record.** C's single-stage model
loses on the registry rule (ids stable, one step list per stage) and on E's cost
table, but C's *vocabulary* wins: every format line names its steps from the same
six words — plan, record, board, shoot, edit, qc — so a new line is recognisably the
same shape, and the shared PREP work (sheets, voices) becomes its own department,
`refs`. B's IP owner is not a department; it is `library/<book>/series.json` (canon,
title record, rights flags, policy) written by Pre-production and read by everyone,
plus the `catalog` step of Distribution. Never a department per book (D §1.2).

### 1.6 Research: one department or two?

| position | held by |
|---|---|
| One Research department, later | owner |
| Research = the industry's Development phase (what gets made and why), before Analysis; plus a Pipeline department for tooling | A rec. 5 |
| Two: R&D (Platform, experiment ledger, no codex id) and audience research (Distribution `analytics`); never let view counts move a threshold | D §5.3 |
| MEASURE feeds RESEARCH; PROGRAMMING owns the slate | C 2.2 unit 05, §2.3 |

**Verdict: three things wear the word; the owner's "one department later" loses and
each gets a slot.** (i) **R&D** — models, prompts, workflows, calibration: lives under
Platform, outside `stages.yaml`, with its own ledger `experiments/<id>/manifest.json`
(hypothesis, variants, measures, verdict, cost); its only outputs are a constant with a
decision id, a workflow or `models.yaml` entry, or a calibration doc. The bench
scripts already in the tree are this. (ii) **Analytics** — a Distribution stage,
read-only, scheduled, consumed by Marketing and by Development; a view count is not
a quality measure and may never reach a gate threshold. (iii) **Development** — the
slate: what to make next. That is the Studio level's Programming function (`studio.py`
+ `series.json`), not a stage.

### 1.7 Where Trailer and Shorts sit in the registry

E's three options: own stages (A), substeps of `promote` (B), targets of one
`production` stage (C). **Verdict: A.** Trailer stays `trailer`. Shorts registers as
`shorts: steps: []` with a comment until a Python client for its paid service exists
(E 5d); the eight skills stay the interactive driver of an honest empty slot. Episode
registers as stage **`episode`**, not `production`: production is the division, and
naming the first line after the division is how the second line ends up as flags on
the first runner (D §7.3).

### 1.8 The per-unit fan-out key

E's options: (i) `run_id` + `detail: ep=NN`, (ii) sub-level id `NN_MM_<unit>`,
(iii) a `production_id`/`unit` column. **Verdict: (iii), as a `unit` text column on
`events` (NULL for book-level stages), and `codex_ready_for_stage(stage, unit)`.**
The brick's identity already contains the production; a status that is a log filter
(i) violates "status is derived from the table"; (ii) breaks fixed-width ids. The
unit is an opaque string whose grammar each stage declares (`ch04`, `ch04-05`,
`scene_12`, `cue_03`, `seq_07`, `main`, `<sha8>@youtube`). The trailer's
`trailer_id="main"` is this column already. This is the mechanism behind the owner's
"a chapter can be a unit; it can expand": a two-chapter episode is unit `ch04-05`,
a season is the ordered unit list in `series.json`, a feature is one unit whose steps
fan out per sequence inside its folder.

### 1.9 The episode plan: Screenplay's output or Production's?

| position | held by | strongest argument |
|---|---|---|
| Screenplay produces it as a per-chapter target; the line starts from `plan.json` | D §1.4 | "Analysis asserts, Screenplay invents"; the plan invents; one screenplay feeds many productions; `targets.yaml` exists |
| The format line's first step, written by a registered agent | C unit 01 (`showrunner`), E step 02 (`episode_writer`), A rec. 1 (the plan is the last pre-production step, "exactly where Pixar draws the line", i.e. layout inside the line) | The plan's contract is the format's (`Episode` with cells, camera, take budget) and its battery is the format's (`plan_check`, cell gates, take-path lint) and must run before anything is voiced or drawn; its constants come from `refs.json` rows |

**Verdict: Production's first step, as data under the library.** Putting format
gates (G-ANCHOR, H3 constants) inside a book-level department would move a format's
calibration out of the format, and Screenplay would have to read `refs.json`, which
inverts the DAG (refs and screenplay are siblings under analysis). D's half that
stands: the plan is **data** at `library/<book>/episodes/<unit>/plan.json`, produced
by `episode/02` from an agent brief, never a `.py` in the code tree; the 18 plan
scripts move under the library (audit Phase 5.0). The brief takes the chapter's
analysis rows, the screenplay's elements for those scenes where a screenplay target
exists, and the bound refs rows. Owner's "Pre-production = Analysis + Screenplay"
stands, with `refs` added to it.

### 1.10 Skill as leader vs runner as leader

Unanimous among C, D, E and the architecture ("one implementation, two drivers").
**Verdict: a department leader is a root runner; a skill is the owner's desk.** The
skill's command table is generated from the registry and a test asserts equality.
Two lines are led by skills today (episode, shorts); that is the largest defect (D
§0.5) and the first migration target.

### 1.11 Smaller disagreements, ruled in one line each

- **Refs as a department** (D) vs inside PREP (C) vs episode steps 1/3/5 (E draft):
  own stage `refs`, keyed `(book, style)`, the only writer of `refs.json`, run
  just-in-time per unit by the scheduler (memory: build only what the episode needs).
  Per-episode place pictures stay in the line because a recurring location is never
  pinned to one picture.
- **Finishing to spec** (versions per aspect and loudness, sidecar captions): a
  Distribution step (`publish/02 versions`), because the format line delivers one
  master and the platform decides the shape (A §1, B Q2 reading, C FINISH).
- **Thumbnail vs key art**: the upload's thumbnail is packaging (`publish/04 art`);
  the campaign's key-art *pool* is Marketing (`promo/03 keyart`); `art` reads the
  pool when one exists.
- **Analytics placement**: Distribution (D), not a post unit (C) — it repeats on a
  schedule and is keyed on `(master, platform)`.
- **Measured music bed for episodes** (C RECORD 02_05): accepted as a missing substep
  of `episode/10 finish`, using the trailer's metre modules.
- **The EYE as an artefact** (C risk 2, E): every eye is a verdict file the next step
  refuses without; "looked at" in prose is not a gate.
- **Programming / scheduler**: Studio level, `studio.py` (D) reading `requires:`; not
  a registry stage because it is the thing that reads the registry.
- **`formats.yaml`** (C): not adopted; a format's constants live in its
  `studio/<stage>_spec.py` and `docs/calibration/`.

---

## 2. The final structure

```
STUDIO (owner)          studio.py scheduler . series.json slate . RENDER_HOLD . DECISIONS.md
  |
  +-- PLATFORM          llm gateway . comfy/GPU lease . db+ledger . approval . measures .
  |                     notify . publish clients . paths/library . R&D experiments
  |
  +-- PRE-PRODUCTION    analysis (built)  screenplay (built)  refs (scripts exist, stage missing)
  |
  +-- PRODUCTION        episode (scripts exist, stage missing)  trailer (built)
  |   (format lines)    shorts (skills only)  feature . song . audiobook . game . book (empty slots)
  |
  +-- DISTRIBUTION      publish (scripts partial, stage missing)  analytics (missing)
  |                     own-platform adapter (slot inside publish)
  |
  +-- MARKETING         promo (missing)
  |
  +-- R&D               experiments/ ledger under Platform (bench scripts exist)
```

Reporting, mechanically (D §2.4): D reports to E when D's final step writes one typed
artefact at a path E's contract names, D's runner emits `completed` for that step with
the artefact hash, and E declares `requires: [D/<step>]` in the registry. Nothing else
is reporting.

### 2.1 Studio level

| element | artefact | built? |
|---|---|---|
| Scheduler ("head of production") | `studio.py`: one loop — read `stages.yaml`, find `(book, unit)` pairs whose `requires:` are `completed`, launch that stage's runner; park on ESCALATE, batch escalations into one call sheet, notify | MISSING (seed: orchestrator at commit `d060598`, read not extended) |
| Slate / season | `library/<book>/series.json`: display title, ordered unit list, targets, `synthetic` declaration, publish policy per platform | partial (series/display_title/episodes exist) |
| Brake | `RENDER_HOLD` file at repo root, read by the GPU lease and every runner | built |
| Decisions | `docs/DECISIONS.md`: every gate retirement with its count; every constant's decision date | built |

The owner sits above the chart, not in it. He receives plan lines and verdict requests
generated from the ledger, never questions; his answer is a typed signature (section 3).

### 2.2 Platform (shared services; no deliverable of its own)

| service | artefact | exists | rule |
|---|---|---|---|
| Model gateway | `studio/llm.py` + `models.yaml` | yes | tiers not models; a `local` tier is a yaml edit and is required for $0 agents |
| GPU | `studio/comfy.py` + `lease(stage)` moved out of `scripts/episode/run.py` | partial | one GPU one stage; `RENDER_HOLD` checked here; absolute paths (`WORKFLOWS`, `COMFY_ROOT`) become config |
| Ledger / DB | `studio/db.py`, `studio/spend.py` | yes; `STAGES` hard-coded, no `unit` | derive from the registry; add `unit` |
| Approval | `studio/approval.py` | yes | per kind, per run |
| Measures | `studio/measure/` (describe, people_count, motion_scan, frame_match, voice_ear, av_sync) | scattered | a measure returns a number; a gate (department-owned) returns a verdict |
| Notify | `studio/notify.py` (pinned client) | MISSING (trailer shells out to another repo) | every department calls, none copies |
| Publish clients | `studio/youtube.py`; later one per platform; `studio/higgsfield.py` | youtube yes; higgsfield MISSING | no format line calls a platform API |
| Library paths | `studio/paths.py`, `book_root.py`, `episode_home.py`, `*_spec.py` | yes | codex id + relative path only |
| R&D ledger | `experiments/<id>/manifest.json` | MISSING (bench scripts exist) | spends through the same approval kinds |

### 2.3 Pre-production division

**Analysis** — built. Leader `analysis.py`; unit `book`, subdivides chapter → scene →
paragraph; boundary artefacts `analysis/book.json`, `timeline.json`,
`characters/<id>.json`, `locations/<id>.json`, `qc_report.json`; gate `analysis/06`;
text model only. Agents: the 12 in the registry, unchanged.

**Screenplay** — built. Leader `screenplay.py`; unit `(book, target)`, subdivides
sequence → scene → element/shot; boundary artefact `screenplay/<target>/screenplay.json`
(+ `elements.json` view); gate `screenplay/05`; text model only. Agents: story_editor,
screenwriter, shot_designer, adaptation_auditor, unchanged. The `book` format line
(an own novel) reuses this department's writer/auditor with a prose contract.

**Refs & Cast** — stage MISSING; scripts exist. Leader `refs.py` (clone of
`trailer.py`); unit `(book, style)`, subdivides per entity (character, prop, voice),
run just-in-time when a plan binds a new entity; the only writer of `refs/refs.json`,
`refs/sheets/*.png`, `refs/pack.jsonl`, `cast/<id>/voice/*`; boundary gate
`refs/04 verdict` = the LOOK gate (owner, once per book); local GPU, $0 for the local
route; the paid sheet route exists behind approval kind `sheets`.

| step | script (exists → wrap) | gate |
|---|---|---|
| 01 canon | `agents/casting_director.py` rows + `scripts/refs/cast_rows.py` | id outside the registry refused |
| 02 sheets | `scripts/refs/build_pack.py`, `prop_refs.py`, `cast_bust.py`; trait card from `scripts/trailer/step_02_refs.py` | ≥3 traits differ from every bound face; look-back (VLM reads the sheet against its prompt) |
| 03 voices | `scripts/cast/cast_voices.py` | pairwise similarity under `SAME_SPEAKER`; ≤4 new voices per run |
| 04 verdict | new: writes `refs/verdict.json` bound to `pack.jsonl` sha | ESCALATE (LOOK) |

| agent | the one question | handed | returns | QC |
|---|---|---|---|---|
| `trait_reader` (local VLM) | "What traits does this sheet show, and does it clash with any bound sheet?" | the new sheet, every bound trait card | `TraitCard` + clash list | code counts differing traits |
| `look_back` (local VLM) | "Does this picture show what its prompt asked: the must-appear nouns, the facial hair both ways, the landmark?" | one picture, its prompt | `LookReading` | code diffs against the prompt's noun list |
| `voice_director` (text, local tier) | "What voice instruction fits this character's region, body and speech and holds a register nobody else holds?" | profile, existing registers | `VoiceDesign` | similarity wall (measured) |

### 2.4 Production division — format lines

Every line: leader = a root runner; unit declared in the registry; the six-word step
vocabulary (plan, record, board, shoot, edit, qc) so lines are comparable; ends at
`deliver` writing `cut/master_iterN.mp4` + `qc.json` + `manifest.json` and never
publishing. A line may skip a word (a song has no board) but never reorders record
before plan or edit before record.

**Episode (TV)** — scripts exist, stage MISSING. Leader `episode.py` + `studio/episode_run.py`.
Unit `(book, chapter)`; a unit may span chapters (`ch04-05`); inside the unit: setup →
shot → take; a season is `series.json`'s ordered unit list. Requires `analysis/06`,
`refs/04`; reads `screenplay/<target>` when present. $0, local GPU. Boundary
artefacts, in order: `plan.json` → `audio/lines.json` (measured seconds) →
`placed.json` (fingerprinted to plan and voice) → `storyboard/shot_NN.png` +
`panel_dq.json` + `panel_content.json` + `eye_<sha8>.json` → `takes/r2v/T*.mp4` +
`.dq.json` + `.content.json` + `eye_<sha8>.json` → `cut/master_iterN.mp4` →
`reports/qc.json` + `review/eye_<sha8>.json` → `manifest.json`. Full step list in the
yaml (section 5). Owner gates: PLAN, EYE (board, takes), MASTER; money kind `render`.

| agent | the one question | handed | returns | QC |
|---|---|---|---|---|
| `episode_writer` (reasoning, local tier) | "Which setups, shots, cells, camera moves and lines tell this unit of story inside the band, naming people only through their bound rows?" | chapter analysis rows, screenplay elements (if any), bound refs rows, place rows, camera catalog, the book's dq_rules | `Episode` | `plan_check` + take-path lint; improve loop ≤2, then ESCALATE |
| `cast_lister` (or `casting_director` reused) | "Who is in this chapter, with display name and gender?" | chapter scenes | `CastList` | ids must exist in the registry |
| `listener` (Whisper) | "What words are on this file?" | wav + the written line | `Hearing` | code compares |
| `panel_reader` (local VLM, no plan shown) | "List what is in this picture." | one panel or three take frames | `PanelReading` | code judges vs plan, landform, dq_rules |
| `eye` (local VLM rubric, calibrated against the casebook) | "Would a viewer see a fault here no measurement names?" | contact sheet + shot list | `EyeRubric` | none; it is the last board/take QC; owner until retired |

**Trailer** — built, untouched. Leader `trailer.py`; unit `book` (`main`); requires
`screenplay/05`, `refs/04` (its own `step_02_refs` becomes a reader of `refs.json`
in a later commit; its trait-card gate moves up into `refs/02`). Ordered by
`promo/02 orders`. Agents: story (register/thesis), cue_author, function labeller —
existing.

**Shorts** — skills only; `shorts: steps: []`. Unit `(book, scene)`; shot → clip.
Paid (credits); every image and video call ESCALATE, cap per short in the spec.
Becomes a stage when `studio/higgsfield.py` (cost preflight, recorded fixtures) and a
reserve→commit credit ledger exist; then eight `scripts/shorts/step_NN` modules over
the JSON contracts (`scene.json`, `style.json`, `shots.json`, `audio.json`) as pydantic
specs. Until then the skills are the driver of an honest empty slot; the showrunner
skill loses the wallet and the gates to the runner on that day.

**Feature (film)** — empty slot `feature: steps: []`. Unit `(book, target=feature)`;
sequence → scene → shot; one plan and one refs pack, then record → board → shoot →
edit per sequence, a final conform edit, qc, deliver. Same modules as episode at a
longer band; a separate stage, never a flag on `episode.py`.

**Song (music)** — empty slot `song: steps: []`. Unit `(book, cue)`; section → bar.
Steps plan (lyric/cue brief) → record (the trailer's measured-metre music step is the
whole production; voice optional) → board/shoot only if the format asks for a video →
edit → qc → deliver (audio master + optional video). The metre modules exist.

**Audiobook** — empty slot. Unit `(book, chapter)`; paragraph → line. plan (reading
script from analysis chapters) → record (cast voice, listen gate) → edit (mix,
chapter markers) → qc → deliver. The cheapest line to register; every module exists.

**Game** — empty slot. Unit `(book, arc)`; level → screen → asset. plan (design doc,
asset bible = the same one-sheet-per-entity pack) → board (screens) → **build**
(replaces shoot: the moving artefact from the still ones; a playable) → qc (playtest
ladder) → deliver (a build, not a master). The one line that adds a step word; it is
a new step script, not a new department. Distribution gains a store adapter.

**Book (own novel)** — empty slot. Unit `(book, target=prose)`; chapter → scene.
Screenplay's agents with a prose contract; deliver = a text master; Distribution gains
an ebook/print adapter.

### 2.5 Distribution division

**Publish** — scripts partial, stage MISSING. Leader `publish.py` + `studio/publish_run.py`,
keyed on finished files, not on `codex_pending_stage`. Unit `(master, platform)`;
subdivides per deliverable bundle (video, audio tracks, timed text, artwork set,
metadata record). Requires any production stage's `deliver`. Contracts first:
`FinishedFile`, `PublishManifest` (mirrors the platform's upload fields: privacy,
`publish_at`, made-for-kids, synthetic media, licence, localisations, caption tracks,
playlists, `manual_after_publish`), `CatalogEntry`/`TitleRecord`. Boundary artefacts:
`publish/<master>/<platform>.json` (id, url, published_at) → `uploads.jsonl` →
`library/<book>/publish/catalog.json`. Owner gates: PUBLISH (private insert = machine
gates, public = ESCALATE until retired per (series, platform)), OVERRIDE. Spends
nothing on the video site; a paid posting service (per-post pricing) is a money kind.
The **own platform** ("a Netflix of our own content") is one more platform adapter
under `publish/05 upload` whose client writes the catalogue and an HLS package
(FFmpeg → packager, fixed 3-4 rung ladder, signed URLs, no DRM until a paid tier)
instead of a third party's API. Nothing in Production knows it exists.

| agent | the one question | handed | returns | QC |
|---|---|---|---|---|
| `publicist` / `metadata_writer` (workhorse) | "What title, description, tags and chapter markers describe this unit for this platform, in the series format, claiming nothing the master does not show?" | plan, dossier, `series.json`, platform walls | `PlatformMetadata` | lint: lengths, forbidden words, attribution present, title from the series record only; `synthetic` is never generated |
| `subject_keeper` (local VLM) | "Where is the subject in this frame, so a tighter aspect keeps it?" | frame samples per shot | `CropPath` | face stays inside the crop |
| `thumbnail_director` (text; drawing local) | "Which one frame and at most three words sell this unit without lying?" | shot list + key frames + key-art pool if any | `ThumbnailBrief` | claims lint (words must be in the plan); OCR read-back |

**Analytics** — MISSING. Leader `analytics.py`; unit `(master, platform)` on a
schedule; requires `publish/06`; read-only; writes
`publish/<master>/<platform>_stats.jsonl` and, joined to the dossier,
`publish/<master>/reading.json` (which shot the drop-off lands on, which thumbnail
won). No gate. Consumed by Marketing and by the Studio's slate; may never write a
threshold.

| agent | the one question | handed | returns | QC |
|---|---|---|---|---|
| `retrospect` (reasoning) | "What did the numbers say against the intention, and which rule would have changed it?" | reading + dossier + prior learnings | `Retrospect` (rule candidates) | code appends to the book's casebook; a candidate becomes a rule only through R&D |

### 2.6 Marketing division

**Promo** — MISSING. Leader `promo.py`; unit `release` (one master or one season
launch); subdivides order → asset → post. Requires `publish/01 intake` (a release
exists) and reads analytics. Boundary artefacts: `promo/<release>/campaign.json` →
`order.json` rows the scheduler turns into Production units (trailer, shorts) →
`promo/<release>/keyart/*.png` (the pool, one-picture-per-entity rule) →
`promo/<release>/cutdowns/*.mp4` (ffmpeg on `placed.json`, no render) →
`posts.jsonl` shipped through `publish`. Gates: brief lint; every order carries a
format and a cost ceiling and the campaign total is inside budget; posting ESCALATES
per platform account; paid posting is a money kind.

| agent | the one question | handed | returns | QC |
|---|---|---|---|---|
| `campaign_planner` (reasoning) | "What assets, on what dates and platforms, carry this release inside this budget?" | release date, `series.json`, analytics reading, budget | `CampaignPlan` | every order has a format and ceiling; total ≤ budget |
| `copywriter` (workhorse) | "What does this post say, in the channel's voice, about this asset?" | asset dossier, platform walls | `Post` | claims lint; length walls per platform in code |

### 2.7 What is built today vs a defined empty slot

| slot | state |
|---|---|
| analysis, screenplay, trailer | built, registered |
| refs, episode, publish | scripts exist; stage + runner missing |
| analytics, promo, notify, scheduler, R&D ledger | missing |
| shorts | skills only; registry slot with `steps: []` |
| feature, song, audiobook, game, book | empty slots, defined unit and step words |
| own platform | an adapter slot inside `publish`, after the catalogue |

---

## 3. Owner gates

Three classes — **money, publish, taste** — seven signatures. A gate is a function
returning `APPROVE | REJECT | ESCALATE`; a runner obeys; ESCALATE parks the unit in
`awaiting_approval`, notifies, and the runner moves on. The owner's answer is always a
file or a flag the ledger records; a sentence in chat is not a decision.

| # | gate | class | when | mechanical signature (what records it) | retirable? |
|---|---|---|---|---|---|
| 1 | MONEY | money | any step with a cost kind (`render`, `sheets`, `panel`, `title`, `cast`, `plates`, `publish`, later `credits`, `post`) | `--approved=<kind>` on the runner for one run, after an itemised plan line; `approval.require(kind, detail, usd, approved)`; `usage`/spend row + `approved` event with kind and usd | paid credits: never (owner invariant). GPU time `render`: per format, by the count rule |
| 2 | LOOK | taste | once per `(book, style)`; re-opened only for a newly bound entity | `library/<book>/refs/verdict.json` {pack sha, APPROVE, one line, date}; event `refs/04 completed` | no — it is already once |
| 3 | PLAN | taste | per unit, before anything is voiced or drawn | `episodes/<unit>/plan.verdict.json` bound to `plan.json` sha; event `episode/02 completed` | per format, by the count rule (a reversal = a plan edit after a downstream render) |
| 4 | EYE — board and takes | taste | per unit, after both machine gates | `storyboard/eye_<sha8>.json`, `takes/r2v/eye_<sha8>.json` (rubric: pass / fault named / cannot tell); the next step refuses without a current one | per format, when a VLM rubric reproduces the eye's catches on the casebook set (calibration doc), then the count rule |
| 5 | MASTER | taste | per master | `review/eye_<sha8>.json` (exists, `eye_review.py`); `publish/01 intake` refuses without it | per series only, by a written standing instruction in `series.json` `policy.master_eye: waived` with date; never studio-wide — the judged masters are the calibration set |
| 6 | PUBLISH | publish | every public write on every platform, and every post | `--approved=publish` on upload and on release; `uploads.jsonl` row with `approved_by`, `policy`; the release re-checks QC and takes as they stand then | per `(series, platform)` by `series.json` `policy.auto_public[platform]: true` with date; every new platform starts ESCALATE |
| 7 | OVERRIDE | publish | any waiver of a machine gate | `--override="<reason>"`; ledger row | never |

Plus one declaration and one brake, listed because code refuses without them:
the **synthetic-media declaration** (`series.json` `synthetic: true|false`, typed once
by the owner, never generated); **`RENDER_HOLD`** (a file; every runner and the GPU
lease read it on the way in).

**Retirement rule** (D §2.2.4, adopted verbatim in spirit): a gate flips from
ESCALATE to auto for one `(format, gate)` only after K consecutive owner APPROVEs with
zero later reversals on that gate, recorded in `docs/DECISIONS.md` with the count and
the date, and expressed as a policy value the runner reads — never by switching a
mode, never by a sentence in a skill. Suggested K = 5; the owner sets it. Steady state
after retirement is the industry's three (LOOK once per book, MASTER, and PUBLISH as
a policy) plus MONEY for credits and OVERRIDE, which never retire.

---

## 4. Mapping: every existing script, skill and agent → its slot

Legend: → wrap (a `step_NN` module calls the existing `main`); ✗ missing; ~ partial.

### 4.1 Pre-production

| existing | division / stage / step | note |
|---|---|---|
| `analysis.py`, `scripts/analysis/step_01..06`, 12 `agents/*.py` | Pre-production / analysis | unchanged |
| `screenplay.py`, `scripts/screenplay/step_01..05`, story_editor, screenwriter, shot_designer, adaptation_auditor | Pre-production / screenplay | unchanged; `TARGET` comes from the work queue later |
| `scripts/*/audit_locations.py`, location_auditor | Pre-production / audit bench | unchanged |
| `scripts/refs/cast_rows.py` | refs/01 canon (chapter stamp) → also called by episode/01 bind | → wrap |
| `agents/casting_director.py` | refs/01 canon (cast list) | reuse |
| `scripts/refs/build_pack.py`, `scripts/episode/prop_refs.py`, `cast_bust.py` | refs/02 sheets | → wrap |
| `scripts/trailer/step_02_refs.py` (trait-card gate, `studio/describe.py`) | refs/02 sheets gate | the gate moves up; the trailer step becomes a reader of `refs.json` |
| `scripts/episode/cast_cards.py`, `frames.py`, `sheet_dq.py` (paid route) | refs/02 sheets, paid route behind kind `sheets` | keep, off the $0 chain |
| `scripts/cast/cast_voices.py`, skill `cast-voices` | refs/03 voices | → wrap; the skill becomes the desk |
| `studio/canon.py` | refs (contracts) | |
| `refs.py` (runner), `refs/04 verdict` writer, `look_back` agent | refs | ✗ |

### 4.2 Production — episode line

| existing | stage / step | note |
|---|---|---|
| `scripts/episode/run.py` (clock, queue guard, `STAGES` dict) | `episode.py` runner + `studio/episode_run.py` | the lease moves to Platform; the dict is replaced by the registry |
| `scripts/episode/episode.py` (stale blind path) | delete after `episode.py` exists | names the paid route |
| `.claude/agents/episode.md`, skill `episode` | the desk over `episode.py` | command table generated from the registry |
| `scripts/episode/plans/*.py` (18) | data: `library/<book>/episodes/<unit>/plan.py` → `plan.json` | audit Phase 5.0; new units come from `episode_writer` |
| `studio/episode_spec.py`, `episode_home.write_plan` | episode/02 plan (contract) | |
| `scripts/episode/plan_check.py`, `studio/cell_gates.py` | episode/02_03 checks | → wrap |
| `agents/episode_writer.py` + `agents/skills/episode_writer.md`, `studio/plan_brief.py` | episode/02_01-02 | ✗ (requires a `local` tier) |
| `scripts/refs/places.py` | episode/03 places | → wrap (per-episode hour) |
| `scripts/episode/say_lines.py`, `speaker_check.py` | episode/04 lines | → wrap; settle the TTS engine constant |
| `scripts/episode/respot.py`, `timeline.py` | episode/05 timeline | → wrap |
| `scripts/episode/takes_r2v.py --prompts`, `no_last_frame.py` | episode/06 prompts | → wrap |
| `scripts/episode/grids.py`, `studio/storyboard_grid.py` | episode/07 grids | → wrap; `studio/grid_layout.py` ✗ |
| `scripts/episode/panels.py`, `panel_check.py`, `panel_content_check.py`, `studio/panel_content.py` | episode/08 panels | → wrap; `studio/panel_contact.py` ✗ |
| `scripts/episode/redraw_panel.py`, `storyboard.py`, `seq_boards.py` (paid route) | episode/08, paid route behind kind `panel` | keep, off the $0 chain |
| `scripts/episode/takes_r2v.py --approved=render`, `take_dq.py`, `take_content_check.py`, `take_strip.py`, `motion_quality.py`, `people_check.py` | episode/09 takes | → wrap; `studio/take_ladder.py` ✗ (the prose cure-to-cause table) |
| `scripts/episode/eye_review.py` | episode/08_05, 09_04, 11_03 (eye verdicts) | promote to refused-without; VLM rubric ✗ |
| `scripts/episode/series_title.py` (`title.py` paid) | episode/10_01 title | → wrap |
| `scripts/episode/assemble.py`, `studio/episode_bed.py`, `edit_gate.py`, `bed_gate.py`, `trailer_assemble.mix_with_lines` | episode/10 finish | → wrap; measured bed (trailer metre) ✗ |
| `scripts/episode/qc.py`, `studio/judged.py` | episode/11 qc | → wrap |
| `scripts/episode/dossier.py`, `runcards.py`, `handbook.py`, `refcard.py`, `sheetcards.py`, `takecards.py`, `story.py` | episode/11_04 dossier (the input of Distribution) | reads only |
| `scripts/episode/migrate_layout.py` | one-off | |
| episode-numbered shell driver under `scripts/episode/` | none | delete (book/episode name in the code tree) |
| `episode/12 deliver`, `studio/notify.py` | episode/12 | ✗ (port of trailer step 10 without the external subprocess) |

### 4.3 Production — trailer, shorts

| existing | stage / step | note |
|---|---|---|
| `trailer.py`, `scripts/trailer/step_01..10`, `studio/trailer_run.py`, `run_budget.py`, `ladder.py`, `learnings.py`, skill `trailer`, `.claude/agents/trailer-*.md` | trailer, unchanged | `step_10 deliver` = manifest + notify; the registry's `desc` prose is refreshed in a doc-only commit |
| `scripts/trailer/step_03_music.py`, `studio/beatmap.py`, `metre_report.py` | trailer/03; reused by episode/10 bed and the `song` line | |
| `scripts/trailer/build_*.py`, `lora_ab.py`, `two_subject_ab.py`, `render_script.py` | R&D bench → `experiments/` | |
| the trailer ref-import script whose filename carries a character name | under the book, or delete | book-neutral rule |
| skills `shorts-story`, `shorts-screenwriter` | shorts/plan | slot |
| skill `shorts-art` | shorts/board (frames) — spends | slot; ESCALATE |
| skill `shorts-cinematographer` | shorts/shoot — spends | slot; ESCALATE |
| skills `shorts-sound`, `shorts-editor` | shorts/edit | slot |
| skill `shorts-publisher` | publish (upscale as a paid finishing kind; metadata; archive) | its upload is owner-manual today |
| skill `shorts-showrunner` | the desk over a future `shorts.py` | the wallet and the gates move to the runner |
| `studio/higgsfield.py`, reserve→commit credit ledger, `scripts/shorts/step_00..07` | shorts | ✗ (the blocker) |

### 4.4 Distribution, Marketing, Studio

| existing | stage / step | note |
|---|---|---|
| `studio/finished_file.py`, `youtube_publish.deliverable` | publish/01 intake | ~ ; `FinishedFile` contract ✗ |
| `publish/02 versions`, `subject_keeper` | publish/02 | ✗ |
| `youtube_publish.series_title`, hand-written `youtube.json`, `scripts/publish/youtube_retitle.py` | publish/03 metadata | ~ ; `metadata_writer` ✗; retitle becomes the normal path |
| `publish/04 art` (thumbnail from master frames + series lettering + OCR; `thumbnails.set`) | publish/04 | ✗ (shorts has an optional workflow in prose) |
| `scripts/publish/youtube_upload.py`, `studio/youtube_publish.py`, `studio/youtube.py`, `youtube_auth.py` | publish/05 upload | → wrap |
| `scripts/episode/eye_review.py` (master rubric) | publish/06 review reads it | |
| `scripts/publish/youtube_privacy.py` | publish/07 release | → wrap; playlists, captions ✗ |
| `publish/08 catalog`, `CatalogEntry`/`TitleRecord` | publish/08 | ✗ |
| Telegram send inside `scripts/trailer/step_10_deliver.py` | Platform `studio/notify.py`; publish/09 notify | ✗ in-repo |
| own-platform adapter (catalogue + HLS package + signed URLs) | publish/05, one more platform | ✗, after the catalogue |
| `analytics.py`, `retrospect` agent | analytics | ✗ |
| trailer `RETROSPECT.md`, `learnings.jsonl`, the casebook convention | analytics/04 learnings | seeds |
| `promo.py`, `campaign_planner`, `copywriter`, keyart, cutdowns, posts | promo | ✗ |
| `docs/orchestrator/README.md` (deleted design, commit `d060598`) | Studio `studio.py` | ✗; read, not extended |
| series-goal watchdog doc named for one book | `library/<book>/series.json` + `studio.py` | book-neutral rule |
| `docs/command_center/DESIGN.md` | Studio (reads `stages.yaml` + events) | proposal |
| `studio/db.py` `STAGES`, no `unit` | Platform | ✗ derive; add column |
| `studio/comfy.py` absolute paths; `queue_is_clear()` + `run.py` lease | Platform `lease()` | consolidate |

---

## 5. Draft `stages.yaml`

Conventions as the file states them: file order = execution order; ids fixed-width,
stable, insertions by sub-level; `script` = `step_NN_<name>` in `scripts/<stage>/`;
`desc` says code vs AGENT vs what it writes. Two keys are **new** on every stage
introduced here — `unit:` (the grain of the stage's production id; the events
`unit` column) and `requires:` (what must be `completed` before a unit is ready;
read by `studio.py`). The existing `analysis`, `screenplay` and `trailer` blocks are
untouched; they gain `unit`/`requires` in the migration commit that teaches the
runner to read them. `# MISSING` = no script yet; `# WRAP` = a thin `step_NN` over
an existing script. No `desc` carries a threshold; those live in `docs/calibration/`.

```yaml
  # =================================================================================
  # DIVISION — PRE-PRODUCTION (continued).  refs: the reference bible.
  # One sheet per character, one per key prop, one voice per speaker, per (book,
  # style). The ONLY writer of refs/refs.json; every format line reads it, none
  # writes it. Run just-in-time: the scheduler launches it when a plan binds an
  # entity with no row. LOOK is the owner's once-per-book taste gate.
  # =================================================================================

  refs:
    unit: [book, style]
    requires: [analysis/05]
    steps:
      - id: "01"
        name: canon
        script: step_01_canon                     # WRAP scripts/refs/cast_rows.py + agents/casting_director.py
        desc: Which entities this book binds. AGENT casting_director rows name who
          appears; code writes one refs.json row per character (display name,
          gender, chapter stamp) and refuses an id outside the analysis registry.
        substeps:
          - id: "01_01"
            name: list
            desc: AGENT (workhorse, local tier) -> CastList from analysis scenes.
          - id: "01_02"
            name: rows
            desc: Code writes and stamps the rows (cast_rows). Every later reader
              refuses a row stamped for another unit.

      - id: "02"
        name: sheets
        script: step_02_sheets                    # WRAP build_pack, prop_refs, cast_bust; trait card from trailer step_02_refs
        desc: One sheet per character and per key prop from profile.design on the
          local image model; pack.jsonl records prompt and seed. A picture on disk
          is never redrawn. Paid sheet route only behind approval kind sheets.
        substeps:
          - id: "02_01"
            name: draw
            desc: Local render; content-addressed staging.
          - id: "02_02"
            name: traits
            desc: AGENT trait_reader (local VLM) -> TraitCard; code refuses a new
              face that does not differ from every bound face in the calibrated
              number of seen traits. Reroll seed x1, distinguish x3, then UNBOUND.
          - id: "02_03"
            name: look_back
            desc: AGENT look_back (local VLM) reads each new sheet against its own
              prompt (must-appear nouns, facial hair both ways); a miss is redrawn
              with the defining state first; then ESCALATE.               # MISSING

      - id: "03"
        name: voices
        script: step_03_voices                    # WRAP scripts/cast/cast_voices.py
        desc: New speakers only. AGENT voice_director -> VoiceDesign (region, body,
          speech, a register nobody else holds); local TTS renders the design clip;
          code measures pairwise similarity against every bound voice and refuses
          a match. Filed at book level under cast/<id>/voice/.

      - id: "04"
        name: verdict
        script: step_04_verdict                   # MISSING
        desc: ESCALATE - LOOK. The owner's one taste verdict per (book, style),
          written as refs/verdict.json bound to the pack.jsonl sha. Re-opened only
          for a newly bound entity. Every format line refuses a pack without a
          current verdict.

  # =================================================================================
  # DIVISION — PRODUCTION.  One stage per FORMAT LINE.  Step vocabulary shared by
  # every line: plan, record, board, shoot, edit, qc, deliver. A line may skip a
  # word, never reorder one. A line ENDS at deliver (master + qc + manifest) and
  # never publishes; Distribution does.
  # ---------------------------------------------------------------------------------
  # episode: one unit of story (a chapter, or a chapter range) -> one finished
  # master, $0, local GPU. Contract: studio/episode_spec.Episode. Gates:
  # .claude/skills/episode/GATES.md. Every step: typed input -> typed output -> a
  # gate that can fail -> an adapt ladder -> ESCALATE (never a silent terminal rung
  # on a picture the owner has not seen). GPU time is approved per kind.
  # =================================================================================

  episode:
    unit: [book, chapter]                         # "ch04" or a range "ch04-05"
    requires: [analysis/06, refs/04]              # reads screenplay/<target> when present
    steps:
      - id: "01"
        name: bind
        script: step_01_bind                      # WRAP scripts/refs/cast_rows.py (chapter stamp)
        desc: This unit's cast. Code stamps the bound rows with the unit; a
          character with no refs row parks the unit and orders refs for it.
        substeps:
          - id: "01_01"
            name: cast
            desc: AGENT cast_lister (workhorse, local tier) -> CastList for the
              unit's scenes; code refuses an id outside the registry.   # MISSING
          - id: "01_02"
            name: rows
            desc: Code rewrites refs.json rows for this unit (cast_rows).

      - id: "02"
        name: plan
        script: step_02_plan                      # WRAP plan_check; the writer is new
        desc: The contract, gated before anything is voiced or drawn. plan.json is
          data under the unit folder; no plan lives in the code tree.
        substeps:
          - id: "02_01"
            name: brief
            desc: Code assembles the chapter's analysis rows, the screenplay
              elements for those scenes where a target exists, the bound rows, the
              place rows, the camera catalog and the book's dq_rules.
          - id: "02_02"
            name: write
            desc: AGENT episode_writer (reasoning, local tier) -> Episode. Names
              people only through cast_refs.tag from the bound row; declares every
              unnamed person; one picture per place per unit.            # MISSING
          - id: "02_03"
            name: checks
            desc: Code - every free gate in one pass (plan_check + cell gates +
              take-path lint). Exit 1 is a stop.
          - id: "02_04"
            name: improve
            desc: Refusals quoted back to the writer; max 2 rounds; then
              ESCALATE.                                                   # MISSING
          - id: "02_05"
            name: lock
            desc: Code writes plan.json only through episode_home.write_plan, then
              ESCALATE - PLAN: the owner's verdict as plan.verdict.json bound to
              the plan sha. Retirable per format by the count rule.

      - id: "03"
        name: places
        script: step_03_places                    # WRAP scripts/refs/places.py
        desc: Each setup's location+view at THIS unit's hour, drawn from its own
          described words on the local image model. A recurring place is never
          pinned to one picture.
        substeps:
          - id: "03_01"
            name: draw
            desc: Every setup resolves to a picture on disk (guard test).
          - id: "03_02"
            name: look_back
            desc: AGENT look_back reads each new picture against its prompt (the
              landmark, the hour); a miss is redrawn; then ESCALATE.     # MISSING

      - id: "04"
        name: record
        script: step_04_record                    # WRAP say_lines + speaker_check
        desc: Every line in its character's voice, MEASURED and LISTENED to.
        substeps:
          - id: "04_01"
            name: say
            desc: Local TTS clone per line; seconds measured from the file.
          - id: "04_02"
            name: listen
            desc: AGENT listener (Whisper) reads each clip back; not word-perfect
              -> re-roll once -> refuse. Similarity to the design clip.
          - id: "04_03"
            name: spread
            desc: One speaker, one voice across the unit (advisory).

      - id: "05"
        name: timeline
        script: step_05_timeline                  # WRAP respot + timeline
        desc: AUDIO FIRST - the animatic. Every shot's seconds derive from the
          measured voice; placed.json is fingerprinted to the plan AND the voice;
          every reader goes through load_placed.
        substeps:
          - id: "05_01"
            name: respot
            desc: Cuts rescaled measured/projected on the grid.
          - id: "05_02"
            name: place
            desc: placed.json inside the format's band; misaligned() refuses a
              line off its shot's start plus the handle.

      - id: "06"
        name: prompts
        script: step_06_prompts                   # WRAP takes_r2v --prompts + no_last_frame
        desc: Every take prompt built and linted for $0 with no GPU, BEFORE any
          grid: length per block, style line, banned props, no last frame, no
          fragments. HARD.

      - id: "07"
        name: board
        script: step_07_board                     # WRAP grids
        desc: Storyboard grids on the local image model from the plan's prose, up
          to three references - cast sheets first, the setup's place last.
        substeps:
          - id: "07_01"
            name: layout
            desc: Code lays a setup out by shot size (cols x rows = shots); the
              minimum grid is a constant with its decision date.         # MISSING
          - id: "07_02"
            name: draw
            desc: One render per grid; the manifest written AFTER the render with
              the prompt and every staged picture's bytes.

      - id: "08"
        name: panels
        script: step_08_panels                    # WRAP panels + panel_check + panel_content_check
        desc: One panel per shot, two machine gates, then an eye. The takes refuse
          without all three verdicts.
        substeps:
          - id: "08_01"
            name: cut
            desc: Panels cut between measured gutters, cropped square; a stale
              grid or a shot in two grids is refused.
          - id: "08_02"
            name: dq
            desc: People vs faces+extras, missing face, sharpness, ink, stacked.
              HARD. Nothing judged = nothing passed.
          - id: "08_03"
            name: content
            desc: AGENT panel_reader (local VLM, shown no plan) LISTS; code JUDGES
              against the plan, the landform and the book's banned list. Unread
              = fail.
          - id: "08_04"
            name: contact
            desc: Code writes one contact sheet of every panel.          # MISSING
          - id: "08_05"
            name: eye
            desc: ESCALATE - EYE. A rubric file storyboard/eye_<sha8>.json (pass /
              fault named / cannot tell) the takes refuse without. Owner today;
              AGENT eye (local VLM rubric) once calibrated on the casebook.
          - id: "08_06"
            name: improve
            desc: A failed grid is superseded and redrawn (shots, tag or seed
              bump); old files move to storyboard/superseded/. Max 2 rounds per
              grid.                                                       # partial

      - id: "09"
        name: shoot
        script: step_09_shoot                     # WRAP takes_r2v render, take_dq, take_content_check, take_strip
        desc: The slow step. ref2va takes on the local video model, staged from
          the panel, the sheets the shot's faces need and the line's wav. A take
          is current only to its words AND its pictures. Approval kind render;
          the GPU lease: one GPU, one stage; the queue is read before every POST.
        substeps:
          - id: "09_01"
            name: round
            desc: Every live shot's next take rendered back to back with the model
              resident.
          - id: "09_02"
            name: dq
            desc: Frozen start, cut landing, churn, zoom, face at end, look,
              pulse, lip-sync lag and WER, held, jump. HARD rows as marked.
          - id: "09_03"
            name: content
            desc: AGENT panel_reader on three frames past the head leak, each
              read alone; code judges.
          - id: "09_04"
            name: strip
            desc: Code writes a strip of every take, then ESCALATE - EYE:
              takes/r2v/eye_<sha8>.json the cut refuses without.
          - id: "09_05"
            name: retake
            desc: LADDER matching cure to cause: moving take froze -> seed; still
              take froze -> change the move TYPE; lag -> shorter take; the same
              fault on a fresh seed -> back to the PLAN (re-aim at what the cell
              holds) -> ESCALATE. One batched round, --why recorded; the losing
              attempt kept under attempts/.                              # partial

      - id: "10"
        name: edit
        script: step_10_edit                      # WRAP series_title + assemble (+ trailer metre for the bed)
        desc: Title card, measured bed, cut, mix. Picture cut to the measured
          voice. cut/master_iterN.mp4, never overwriting.
        substeps:
          - id: "10_01"
            name: title
            desc: Series base once per book; the unit's lettering read back by
              OCR; short animated card.
          - id: "10_02"
            name: bed
            desc: Tone spans -> local music bed, metre MEASURED and ranked on
              fitness (the trailer's music step); bed gate.               # partial
          - id: "10_03"
            name: cut
            desc: Takes trimmed to placed.json, lines at their at, mix to the
              house loudness, captions, end chip.
          - id: "10_04"
            name: sound
            desc: Ambience and spot effects when the format asks; otherwise
              skipped.                                                    # MISSING

      - id: "11"
        name: qc
        script: step_11_qc                        # WRAP qc + eye_review + dossier
        desc: Measure the DELIVERED master, never the intention. Stamps the sha8
          it measured. No import from the edit step.
        substeps:
          - id: "11_01"
            name: measure
            desc: Loudness, every planned cut, every line heard on the mix, the
              silent-gap wall naming its shot, edit is the takes, every take
              judged twice, title card present.
          - id: "11_02"
            name: recut
            desc: Fail -> the silent shot gets a line or the silence moves;
              re-cut x2 (free); then ESCALATE.                            # partial
          - id: "11_03"
            name: eye
            desc: ESCALATE - MASTER. review/eye_<sha8>.json; an n needs a waiver
              the owner signs. Waivable per series only by series.json policy.
          - id: "11_04"
            name: dossier
            desc: Code - one page of every input, prompt, picture, take, verdict.

      - id: "12"
        name: deliver
        script: step_12_deliver                   # MISSING (trailer step 10 is the model, without the external subprocess)
        desc: manifest.json beside the master (every gate verdict, every rung,
          timing totals), the deliverable's full path printed first, notify()
          through the platform. Never publishes; Distribution does.

  # ---------------------------------------------------------------------------------
  # trailer: unchanged above. Ordered by promo/02; requires screenplay/05, refs/04
  # once step_02_refs reads refs.json (migration, not now).
  # ---------------------------------------------------------------------------------

  # shorts: paid format line (credits). Registered when studio/higgsfield.py (cost
  # preflight, recorded fixtures) and a reserve->commit credit ledger exist; then
  # scripts/shorts/step_00..07 over the JSON contracts as pydantic specs. Every
  # image and video call ESCALATE; hard cap per short in the spec. Until then the
  # eight shorts-* skills are the interactive driver of this empty slot.
  shorts:
    unit: [book, scene]
    requires: [screenplay/05, refs/04]
    steps: []                                     # MISSING (see E §5d)

  # Defined empty slots. Same shape; scripts in scripts/<stage>/ when built.
  # feature:   unit: [book, target]   sequence -> scene -> shot; plan, refs pack once,
  #            then record/board/shoot/edit per sequence, final conform, qc, deliver.
  # song:      unit: [book, cue]      section -> bar; plan, record (measured metre is
  #            the whole production), board/shoot only with a video, edit, qc, deliver.
  # audiobook: unit: [book, chapter]  paragraph -> line; plan, record, edit, qc, deliver.
  # game:      unit: [book, arc]      level -> screen -> asset; plan, board, BUILD
  #            (replaces shoot: a playable), qc (playtest ladder), deliver (a build).
  # book:      unit: [book, target]   chapter -> scene; Screenplay's agents with a
  #            prose contract; deliver = a text master.
  # feature:
  #   steps: []
  # song:
  #   steps: []
  # audiobook:
  #   steps: []
  # game:
  #   steps: []
  # book:
  #   steps: []

  # =================================================================================
  # DIVISION — DISTRIBUTION.  publish: keyed on a FINISHED FILE and a PLATFORM, not
  # on a book. Publishing is the one irreversible step: private is machine-gated,
  # public is ESCALATE until retired per (series, platform) in series.json policy.
  # Contracts first: FinishedFile, PublishManifest, CatalogEntry.
  # =================================================================================

  publish:
    unit: [master, platform]                      # "<sha8>@youtube", "<sha8>@own"
    requires: [<any production stage>/deliver]
    steps:
      - id: "01"
        name: intake
        script: step_01_intake                    # MISSING (studio/finished_file.py + youtube_publish.deliverable are the seeds)
        desc: Code - the finished-file registry: which master, its sha8, its qc,
          its master eye, its kind (episode | trailer | short | ...), its series
          position. Refuses a master whose qc or eye is about other bytes.

      - id: "02"
        name: versions
        script: step_02_versions                  # MISSING
        desc: From the master, each platform's deliverable bundle: aspect
          versions (AGENT subject_keeper says where to crop), platform loudness,
          sidecar captions from the timeline, an upscale only as a registered
          paid kind. Each version measured against its spec.

      - id: "03"
        name: metadata
        script: step_03_metadata                  # partial: series_title() exists; the rest is hand-written
        desc: Title from the book's own series record (code); AGENT
          metadata_writer (workhorse) drafts description, tags and chapter
          markers inside the platform's walls; attribution and licence lines by
          code; the synthetic-media declaration is read from series.json and
          never generated. Lint. Writes the PublishManifest.

      - id: "04"
        name: art
        script: step_04_art                       # MISSING
        desc: Thumbnail from the master's own frames plus the series lettering
          (AGENT thumbnail_director picks; local render; OCR read-back), reading
          the promo key-art pool when one exists; poster still for the catalogue.

      - id: "05"
        name: upload
        script: step_05_upload                    # WRAP scripts/publish/youtube_upload.py; one adapter per platform
        desc: PRIVATE insert, machine-gated (qc on this sha8, no failed or
          unjudged take, not already uploaded), the ledger row written BEFORE
          the call, approval kind publish; thumbnail, captions, playlist set.
          Adapters: youtube (exists), own platform (catalogue + HLS package +
          signed URLs), others as pinned clients. A platform's quota is a ledger.

      - id: "06"
        name: review
        script: step_06_review                    # WRAP the master eye verdict
        desc: The human gate for anything a stranger will see: the master eye for
          this sha8 with its waivers. Waived only by series.json policy with a
          date, never by code.

      - id: "07"
        name: release
        script: step_07_release                   # WRAP youtube_privacy public (+ retitle as maintenance)
        desc: ESCALATE - PUBLISH. The flip to public at the scheduled time
          re-checks every machine gate as it stands then, reads the live status
          back and records what the platform returned. Retirable per (series,
          platform) by policy.

      - id: "08"
        name: catalog
        script: step_08_catalog                   # MISSING
        desc: The title record: library/<book>/publish/catalog.json - every public
          artefact by kind, relative paths only, platform ids, dates, artwork
          set, languages, windows. The own platform reads this; every platform
          manifest derives from it.

      - id: "09"
        name: notify
        script: step_09_notify                    # MISSING in-repo (studio/notify.py)
        desc: The public link, the path, the spend and the time to the owner's
          channel. Retry x3 -> undelivered, recorded.

  analytics:
    unit: [master, platform]                      # scheduled; re-runs are new events
    requires: [publish/07]
    steps:
      - id: "01"
        name: ingest
        script: step_01_ingest                    # MISSING
        desc: Code - views, watch time, retention curve, impressions and
          click-through per deliverable per platform, appended to
          publish/<master>/<platform>_stats.jsonl. Read-only; no gate.
      - id: "02"
        name: join
        script: step_02_join                      # MISSING
        desc: Code joins the numbers to the dossier - which shot the drop-off
          lands on, which thumbnail won - into publish/<master>/reading.json.
      - id: "03"
        name: retrospect
        script: step_03_retrospect                # MISSING
        desc: AGENT retrospect (reasoning) -> rule candidates against the
          intention; code appends to the book's casebook. A candidate becomes a
          rule only through an R&D experiment; a view count never moves a gate.

  # =================================================================================
  # DIVISION — MARKETING.  promo: per RELEASE. Decides; never renders; never calls a
  # platform. Orders go to Production through the scheduler; posts go through
  # publish. Paid posting is a money kind.
  # =================================================================================

  promo:
    unit: [release]                               # one master, or a season launch
    requires: [publish/01]
    steps:
      - id: "01"
        name: campaign
        script: step_01_campaign                  # MISSING
        desc: AGENT campaign_planner (reasoning) -> CampaignPlan: which assets
          (trailer, N shorts, K stills, posts), on which dates, on which
          platforms, inside the budget, reading the last analytics. Code: every
          order has a format and a cost ceiling; the total is inside budget.
      - id: "02"
        name: orders
        script: step_02_orders                    # MISSING
        desc: Code writes promo/<release>/order.json rows; the scheduler turns
          each into a Production unit (trailer, shorts) with its ceiling.
      - id: "03"
        name: keyart
        script: step_03_keyart                    # MISSING
        desc: The key-art pool - N candidates per title from the refs pack and the
          master's frames on the local image model (one picture per entity);
          the upload's thumbnail step reads it; analytics reports the winner.
      - id: "04"
        name: cutdowns
        script: step_04_cutdowns                  # MISSING
        desc: Code - vertical and short cuts from the master's best takes on
          placed.json (ffmpeg, no render); a cut that needs new pictures is a
          shorts order, not a step here.
      - id: "05"
        name: posts
        script: step_05_posts                     # MISSING
        desc: AGENT copywriter (workhorse) -> Post per platform, claims lint,
          walls in code; posts.jsonl; shipped through publish/05 with ESCALATE
          per platform account.
```

Registry changes this implies outside the yaml (all small, all org-chart integrity):
`events.unit` column; `db.STAGES` derived from the registry; `studio/registry.py`
reading `unit`/`requires`; `codex_ready_for_stage(stage, unit)`.

---

## 6. Migration order

Cheapest and highest leverage first; sizes from E §5b-5d. Nothing here adds
capability the studio does not already have in scripts — it adds the org.

| # | commit | what | size (E) | why first |
|---|---|---|---|---|
| 1 | **registry keys and the unit column** | `studio/registry.py` (load `unit`, `requires`); `events.unit` column with idempotent migration; `db.STAGES` derived from `stages.yaml`; `codex_ready_for_stage(stage, unit)`; tests first | ~150 lines, 5 tests | unblocks every new stage; the fan-out decision made once |
| 2 | **`refs` stage** | yaml block; `refs.py` from the `trailer.py` template; four `step_NN` wrappers over `cast_rows`, `build_pack`/`prop_refs`, `cast_voices`; `refs/verdict.json` writer; `cast-voices` skill becomes the desk | ~300 lines, 8 tests | the department two lines already duplicate; the LOOK gate becomes an event; smallest new department |
| 3 | **`episode` stage, wrappers only** | yaml block; `episode.py` + `studio/episode_run.py` (lease from `run.py`); `step_NN` wrappers for 01, 03-12 with every eye = ESCALATE (parks + notifies) and no new judgement; `plan` step wraps `plan_check` and reads the existing `plan.json`; the skill's command table generated from the registry with an equality test | ~1,400 of E's ~2,000 lines, ~30 tests | one command, events per step, the DAG readable by the command centre; the skill stops being the leader |
| 4 | contracts for Distribution | `FinishedFile`, `PublishManifest`, `CatalogEntry` in `studio/`; a `local` tier in `models.yaml` | ~200 lines, 6 tests | spec before department |
| 5 | `publish` stage | `publish.py` + `studio/publish_run.py`; wrappers for upload/review/release; intake, catalog, notify (`studio/notify.py`, pinned client, replaces the trailer's subprocess); `episode/12 deliver` | ~700 lines, 15 tests | publishing leaves the format line; the catalogue exists before the app |
| 6 | the new agents | `episode_writer` + `plan_brief` + improve loop; `cast_lister`; `metadata_writer`; `look_back`; each behind its deterministic gate with FakeModel tests; plan scripts move under the library | ~600 lines, 12 tests | the last Claude-skill judgements become registered agents |
| 7 | `studio.py` scheduler | the loop over `requires:`; batched call sheet; `series.json` slate | ~250 lines, 6 tests | the head of production; makes `requires:` real |
| 8 | `analytics`, `promo` | contracts, runners, the two agents each | ~600 lines, 12 tests | the loop closes: numbers feed the next brief |
| 9 | `studio/higgsfield.py` + credit ledger → `shorts` stage | the paid line's client, then eight steps | ~1,700 lines, 31 tests | the showrunner skill retires as manager |
| 10 | gate retirements | one `(format, gate)` at a time, cheapest first, each a `DECISIONS.md` line with its count | — | automation is gates you retire |

**The first three commits**, concretely:

1. `registry: unit and requires keys; events.unit; db.STAGES from stages.yaml` —
   tests: a stage's `unit` parses; `requires` parses; `mark_stage` accepts a
   registered stage and refuses an unregistered one; two units of one stage do not
   collide in `events`; `codex_ready_for_stage` takes a unit.
2. `refs: the reference bible as a department` — tests: registry ids match module
   `STEP_ID`s; the runner brackets each step in events; `refs.json` is written only by
   this stage (a test greps the writers); the verdict file binds to the pack sha and a
   stale pack is refused.
3. `episode: the format line as a department (wrappers, eyes ESCALATE)` — tests:
   ids match; every eye step parks the unit and writes no verdict; a take step refuses
   without all three panel verdicts; the skill's command table equals the registry;
   `RENDER_HOLD` stops the runner before the first GPU step.

---

## 7. Publishable artefacts (standalone packages)

- **`stepwise`** — a step runner whose resume keys are artefact-on-disk and credits
  spent, with `APPROVE | REJECT | ESCALATE` gates and a `requires:` registry; already
  flagged in `docs/ARCHITECTURE.md`; this decision adds `unit` and the scheduler loop.
- **`publish-manifest`** — a typed multi-platform `PublishManifest` + a YouTube adapter
  with a quota ledger, `publishAt` scheduling and a `manual_after_publish` list (B).
- **`higgsfield-client`** — an HTTP client with cost preflight, recorded fixtures and a
  reserve→commit credit ledger (E §5d); the blocker for the shorts line, useful to
  anyone spending credits from code.
- **`list-then-judge`** — the content gate pattern: a VLM lists in a closed vocabulary
  with no plan shown; code judges against the plan (panel and take content gates).
- **`trait-card`** — identity binding for reference sheets: a VLM trait card and a
  differ-in-N-traits gate with reroll/distinguish ladder (trailer `step_02_refs`).
- **`measured-timeline`** — audio-first cut: measured line seconds → fingerprinted
  timeline → `misaligned()` refusal; the animatic as code.
- **`metre`** — music metre/onset measurement and fitness ranking for cutting to a
  cue (`studio/beatmap.py`, trailer step 03).
- **`title-record`** — a small catalogue model (OMC-aligned entities, feed-compatible
  fields, stable ids) that every platform manifest derives from (B Q5).
- **`registry-org-chart`** — `stages.yaml` + runner template + events as an org chart
  for agent studios, with the command-centre DAG view; may fold into `stepwise`.
