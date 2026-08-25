# Stage 02 — screenplay: Design

**Status: PLANNED, not built. Awaiting owner approval.**
Research: 5 agents, ~1M tokens, primary sources throughout. Every number below is
measured — from a real production draft, a published corpus, or my own run on this
machine — not quoted from a blog.

---

## Why this is a STAGE and not a step inside analysis

> **Analysis asserts. A screenplay invents. Never put an inventing step inside an
> asserting stage.**

Every step of `analysis` answers *what does the text say?*, and the whole grounding
apparatus — verbatim quotes, `wrong-scene` detection, `stated | inferred | approx`
labels — exists to enforce that nothing is fabricated. A cinematic screenplay must
invent: shot choices, compression, visual specificity the prose never had. Put that in
the same stage and "grounded" stops meaning anything.

Three practical consequences point the same way:

- **One analysis → many screenplays.** A 60-second short, a 10-minute episode and a
  feature are different screenplays from identical facts. A step inside analysis is 1:1
  with the book.
- **Resume keys differ.** Analysis resumes on the book's sha256. A screenplay resumes on
  `(book, target format, version)`.
- **Gating differs.** Analysis is cheap and safe to re-run. Screenplay is where the
  ESCALATE gate and the owner's spend approval belong, and it feeds `shorts/` S0–S7.

---

## The brick

**Ray Morton's four elements.** A screenplay may contain only:

1. **Images** — people, places, objects
2. **Action** — moving images, behaviour
3. **Sound** — effects and music
4. **Dialogue** — spoken words

> *"Cinema is a visual/audio medium. Viewers can only experience what they see on the
> screen or what they hear coming out of the speakers."*

Every formatting and craft rule in this document derives from it, and — the reason it is
the brick rather than a slogan — **it is a decidable predicate**: every sentence maps to
one of the four, or it is unfilmable. Contrast the usual advice, "write visually," which
a machine cannot test.

---

## The second organising idea: TRANSFER vs ADAPTATION PROPER

McFarlane, *Novel to Film* (1996), distinguishes what moves between media for free from
what must be rebuilt:

| | |
|---|---|
| **TRANSFER** | narrative — cardinal functions, catalysers, informants. Not tied to one sign system. |
| **ADAPTATION PROPER** | enunciation — *"the whole expressive apparatus that governs the presentation of the narrative."* |

> **What the novel already stages transfers nearly free. What the novel narrates,
> summarises, or declines to stage must be re-invented from nothing — and that
> re-invention is where the entire budget and all the risk live.**

Austen writes Edward's proposal as *"in what manner he expressed himself, and how he was
received, need not be particularly told"* — Thompson had to build the scene from nothing.
Meanwhile Austen's Chapter 2, already dialogue, moves across almost untouched.

**And we can compute the prior mechanically**, because analysis already emits it:

| signal (already in our data) | implies |
|---|---|
| `type: "scene"` + dense `dialogue[]` | TRANSFER — cheap |
| `type: "nonscene"` (16 of 92 in Study in Scarlet) | ADAPTATION PROPER — expensive |
| `events[]` with verbatim quotes | TRANSFER |
| narrated summary, no dialogue | ADAPTATION PROPER |

The story editor is handed the prior and adjudicates the middle. Same division of labour
that works everywhere else in this pipeline.

---

## Steps

Step ids are **stage-scoped** — the events table keys on `(codex_id, stage, step_id)`,
so `screenplay/01` never collides with `analysis/01`. "Stage 02" is the stage's position
in the studio, which file order in `stages.yaml` already encodes.

| id | name | executor | writes | resume key |
|---|---|---|---|---|
| `01` | `dossier` | **code**, zero LLM | `screenplay/dossier.json` | file + `input_sha256` |
| `02` | `plan` | agent ×1 | `<target>/plan.json` | file + fingerprint(dossier + target block) |
| `03` | `draft` | agents ×2 per beat | `<target>/scenes/sc_NNNN.json` | **per-scene file** — the paid unit |
| `04` | `render` | **code**, zero LLM | `<target>/screenplay.json` (**the artifact**), `.fountain`, `.pdf`, `elements.json` | none — free, always re-render |
| `05` | `verify` | code + agent | `<target>/qc_report.json` | file |

### Substeps

```
01 dossier                                      (code)
  01_01 gather     read the six analysis/source artifact families; hash them
  01_02 join       resolve surface names -> canonical ids via registry aliases;
                   attach int_ext / dialogue / events / pov from extraction;
                   build CHARACTER cues; carry verbatim paragraph spans
  01_03 checks     every scene has int_ext, a location name, DAY|NIGHT; every speaking
                   character resolves to a registry id; WARN (never fail) on a speaking
                   character with no profile.voice
  01_04 emit       screenplay/dossier.json

02 plan                                         (1 agent call, whole book)
  02_01 brief      code: target config + scene index (~40 words/scene, ~5k tokens)
  02_02 select     AGENT story_editor -> ScreenplayPlan
  02_03 checks     code: every beat's (chapter, scene) exists; roster subset of registry;
                   budget within target; EVERY source scene is in a beat or in `omitted`
  02_04 emit       plan.json + source_fingerprint

03 draft                                        (2 agent calls per beat)
  03_01 write      AGENT screenwriter -> elements[]; WRITE THE FILE IMMEDIATELY
  03_02 shoot      AGENT shot_designer -> shots[]
  03_03 assemble   code: sluglines, CONT'D/CONTINUOUS, page_eighths, scene numbering

04 render                                       (code, zero LLM)
  04_01 json       screenplay.json — THE ARTIFACT. Every downstream stage reads this.
  04_02 fountain   screenplay.fountain — rendered FROM the json, never hand-assembled
  04_03 pdf        screenplay.pdf — screenplain, industry geometry, Courier 12
  04_04 elements   elements.json — flat shot list keyed (scene, shot) for the video stage
  04_05 format     round-trip lint + runtime/page budget vs the target

05 verify                                       (code + 1 agent over K scenes)
  05_01 guards     coordinate / roster / place-and-time / verbatim-claim
  05_02 audit      AGENT adaptation_auditor, K=3 sampled (first / middle / last)
  05_03 improve    re-run ONE dimension for flagged scenes; MAX_IMPROVE_ROUNDS = 2
  05_04 report     qc_report.json
```

### Why `01 dossier` exists

Analysis is lossy exactly where the screenplay needs it. **`int_ext` (half of every
slugline), 549 dialogue exchanges, `events` and `pov` live only in
`analysis/extraction/ch_NN.json`** — step 03's remap drops them.

And it must read `timeline.json["scenes"]`, **not `scenes.json`**: the latter has 27 of
92 scenes at `time_of_day: "UNKNOWN"`, the former has none, plus `t` (a total order),
dates, tracks, and the `legs` of the four traversal scenes.

### Output layout

```
library/<codex_id>_<slug>/screenplay/
  dossier.json                     # per BOOK — shared by every target
  short60/
    plan.json
    scenes/sc_0001.json …          # one paid unit per file
    screenplay.json               # THE ARTIFACT — machine-readable, agents read this
    screenplay.fountain           # rendered from the json
    screenplay.pdf                # rendered from the fountain — the human artifact
    elements.json                 # flat (scene, shot) index for the video stage
    qc_report.json
  episode10/ …
  feature/   …
```

Deleting `screenplay/short60/` re-runs exactly one target. Deleting `dossier.json`
re-runs the free join.

---

## The crew — four agents

The rule: **split agents when their outputs are orthogonal and merge mechanically; keep
them together when the outputs interleave.**

| agent | tier | input | output | calls / feature |
|---|---|---|---|---|
| `story_editor` | reasoning | target config + scene index | `ScreenplayPlan` | 1 |
| `screenwriter` | reasoning | one beat's source scenes + roster + voice | `SceneDraft` | 1 / beat |
| `shot_designer` | workhorse | the frozen element stream + location `profile.visual` | `ShotPlan` | 1 / beat |
| `adaptation_auditor` | workhorse | one drafted scene + its source paragraphs | `AuditVerdict` | K = 3 |

**`screenwriter` owns dialogue as well as action.** A separate dialogue writer fails the
orthogonality test: action and dialogue interleave into *one ordered stream*, and each
depends on the other. "He doesn't answer. He pours the brandy." is only writable knowing
the previous line was a question. Two agents producing halves of one sequence would need
a third to interleave them.

**`shot_designer` splits.** Shots attach to element *indices* in an already-frozen
stream, so they merge by index exactly as analysis merges by scene number. Decisive: it
can be re-run alone when the shot language is wrong, without paying to rewrite dialogue.

### Not building, and why

| | reason |
|---|---|
| dialogue writer | fails the orthogonality test (above) |
| format validator agent | Fountain is a grammar. `re.match` validates it free and deterministically. An LLM here makes the one byte-stable artifact nondeterministic. |
| continuity supervisor | every question is already answered by data or arithmetic. `step_06_verify.who_is_where()` exists. |
| PDF renderer | `screenplain[PDF]==0.11.0` is MIT, pure Python, uv-native, **now a pinned dependency and verified end-to-end on this machine** — correct element typing, Courier embedded, real industry geometry. Called through the Python API (`parsers.fountain.parse` → `export.pdf.to_pdf`); `python -m screenplain` does not work, there is no `__main__`. |
| a coverage/quality score | any scalar will be gamed by the next prompt tweak and read as truth by nobody |

---

## Contracts

`studio/screenplay_spec.py` (shared by three agents, the renderer and the checks) and
`studio/fountain.py` (renderer). Agents already import `studio.llm`, so
`studio → agents → scripts` stays a clean one-way layering.

### Nine element types, not thirty

The format's entire expressive range is **nine typed paragraphs plus capitalisation
conventions**: `SceneHeading · Action · Character · Parenthetical · Dialogue ·
Transition · Shot · General · CastList` (+ `Singing`).

Montage, intercut, superimpose, mini-slug and flashback are **conventions expressed in
the text of an Action or Scene Heading**, never distinct types. Confirmed in John
August's own *Big Fish* FDX: `QUICK MONTAGE as he demonstrates:` is
`<Paragraph Type="Action">`.

### The wire model is flat, not a discriminated union

```python
Kind      = Literal["action", "dialogue", "transition"]
Prov      = Literal["verbatim", "adapted", "invented"]
IntExt    = Literal["INT", "EXT", "INT/EXT"]
TimeOfDay = Literal["DAY", "NIGHT", "DAWN", "DUSK", "CONTINUOUS", "LATER",
                    "MOMENTS LATER"]

class ScriptElement(BaseModel):
    kind: Kind
    text: str
    character: str | None = None      # dialogue only — canonical character id
    parenthetical: str | None = None
    provenance: Prov = "invented"
    source: SceneRef | None = None    # required when provenance == "verbatim"
    dual: bool = False
```

A discriminated union is correct in principle, but `studio/llm.py` calls
`chat.completions.parse` with OpenAI **strict** structured outputs, and pydantic emits
tagged unions as `oneOf` + `discriminator`. We have been burned once already by an
untested provider interaction (the 800-retry incident). The decision procedure is a free
offline test:

```python
def test_element_schema_is_provider_safe():
    schema = json.dumps(SceneDraft.model_json_schema())
    assert "oneOf" not in schema and "discriminator" not in schema
```

Flip to the union, run that test, keep it if it passes.

### `screenplay.json` is the artifact; `.fountain` and `.pdf` are renders

**The direction of travel is one-way and never reversed:**

```
scenes/sc_0001.json …  ->  screenplay.json  ->  screenplay.fountain  ->  screenplay.pdf
   (paid, per beat)         (the artifact)        (a projection)         (for humans)
```

Nothing downstream ever parses Fountain to recover a fact. **Fountain is lossy by
construction** — it throws away `provenance`, `source`, `location_id`, every camera field,
and the distinction between a character id and the cue text printed on the page. Anything a
later stage needs must be in the JSON, because it cannot be got back out of the render.

The PDF is the *human* artifact and nothing reads it at all.

```python
class Slug(BaseModel):
    int_ext: IntExt                   # INT | EXT | INT/EXT
    location_id: str                  # canonical id from the registry
    location_name: str                # as printed on the page
    time: TimeOfDay                   # DAY | NIGHT | DAWN | DUSK | CONTINUOUS | …
    text: str                         # the rendered line: "INT. 221B BAKER STREET - NIGHT"

class Shot(BaseModel):
    index: int
    covers: tuple[int, int]           # inclusive element-index range in this scene
    setup: str                        # "medium close-up, Holmes" — spelled out, no MCU
    term: str | None                  # "dolly in" — null when no vocabulary term fits
    visual_consequence: str           # "parallax shifts, foreground slides past frame edges"
    axis_side: Literal["A", "B"]      # which side of the action line
    looks_screen: dict[str, str]      # character id -> "left" | "right"
    travel_direction: str | None      # "left" | "right" for anything moving
    crosses_axis: bool = False
    licensed_by: int | None           # the neutral shot that permits a crossing

class Scene(BaseModel):
    number: int                       # 1-based, as numbered on the page
    beat_id: str                      # which plan beat produced it
    slug: Slug
    cast: list[str]                   # canonical character ids present
    speaking: list[str]               # subset of cast with dialogue
    elements: list[ScriptElement]     # the ordered stream — action, dialogue, transition
    shots: list[Shot]
    source: list[SceneRef]            # (chapter, scene) coordinates this covers
    transfer: Literal["transfer", "adaptation_proper"]
    page_eighths: int                 # measured by code after rendering
    duration_s: float                 # page_eighths / 8 * 60

class Screenplay(BaseModel):
    title: str
    source_work: str
    target: str                       # "feature" | "episode10" | "short60"
    source_fingerprint: str           # hash of the analysis artifacts it was built from
    scenes: list[Scene]
    omitted: list[Omission]           # every source scene not used, with a reason
    totals: Totals                    # pages, runtime, scene count, cast size
```

**Why each field is there rather than derivable:**

| field | who needs it downstream |
|---|---|
| `location_id`, `cast` | the video stage, to reuse a location look and a character reference across scenes |
| `shots[]` with `visual_consequence` | prompt assembly — the term alone does not survive the text channel |
| `axis_side`, `looks_screen` | screen-direction continuity, which no model can enforce |
| `provenance`, `source` | the auditor, and the grounding guard |
| `page_eighths`, `duration_s` | budget arithmetic, measured not asked |
| `transfer` | knowing which scenes were built from nothing when a QC pass flags one |
| `source_fingerprint` | invalidating the whole target when analysis upstream changes |

**`elements.json` is a flattened view of the same data**, keyed `(scene, shot)` so the
video stage can iterate shots without walking the scene tree. It is generated, never
edited — if the two ever disagree, `screenplay.json` wins.

### `page_eighths` is derived by code, never asked of an agent

Models cannot count rendered lines. Neither can they be trusted with `sum(duration_s)` —
the agent is *told* the budget and code *measures* the result.

---

## Grounding vs invention — the provenance contract

Analysis's contract is **containment**: every quote's words appear in its scene. A
screenplay cannot use that, because its output is meant to be words the book never wrote.
The replacement is **non-contradiction**, and one field makes it enforceable:

> Analysis labels every claim `stated | inferred`.
> Screenplay labels every dialogue element **`verbatim | adapted | invented`**.
> The same `is_grounded()` machine checks the `verbatim` bucket; the other two are
> checked structurally.

A mislabeled `verbatim` line is **downgraded to `adapted` and counted**, not failed — the
label was wrong, not the line. A rising downgrade rate is the signal that the
screenwriter's skill needs its verbatim rule sharpened.

### Four deterministic guards (free, gating)

| | guard | kills |
|---|---|---|
| **G1** | every `source` names a `(chapter, scene)` present in the dossier | invented coordinates |
| **G2** | every speaking character exists in the registry **and** the timeline places them there that day (`who_is_where()`) | invented people, bilocation |
| **G3** | `location_id` is the source's or a declared alias; `slug.time` is the source's or a legal *narrowing* (DAY→DAWN ok, DAY→NIGHT not); ordering monotonic in `t` unless the plan marked the beat `flashback` | contradiction of place and time |
| **G4** | every `provenance == "verbatim"` runs `is_grounded()` — failure **downgrades**, does not fail | mislabeled quotes |

**Scenes named in `timeline.contradictions` are downgraded to advisory.** The two known
`clock-reversed` entries are an upstream defect; screenplay must not gate on it.

### The auditor cannot manufacture evidence

The highest risk in this stage: on a pipeline whose product is *difference*, an auditor
tuned to report difference produces the 316-violations-nobody-reads failure again. The
defence is structural, in the schema rather than the prose:

```python
class Issue(BaseModel):
    scene: int
    kind: Literal["contradiction", "anachronism", "roster", "tone"]
    severity: Literal["blocking", "minor"]
    book_quote: str      # verbatim; checked with is_grounded() BEFORE it counts
    note: str
```

An issue whose `book_quote` fails `is_grounded()` against the source paragraphs is
**dropped before it reaches the improve loop**. No quote, no issue.

---

## Skills, calibrated to measured practice

Numbers below are measured from John August's *Big Fish* final production draft
(120pp / 125min), cross-validated across both the `.fountain` and the writer's own
`.fdx`, plus two published corpora.

| rule | measured |
|---|---|
| action blocks | mean **2.0 lines**; **92% ≤ 3**; nothing over 6 |
| parentheticals | **0.81 per page** (12.6% of speeches); commonest is `(beat)` — a *timing* note |
| scene headings | **97%** are `PREFIX LOCATION - TIME`; DAY+NIGHT = **85%** |
| camera direction | **~1 per 2–3 pages** |
| dual dialogue | **0** in 120 pages |
| `CUT TO:` | Scott Myers found **zero** across ~24 recent scripts |
| page → time | **1.10 mean** (≈55 sec/page) across n=2,520; only **18.2%** land within ±5% |
| feature page count | median **106**; 68.5% between 90 and 120; ~110 scenes |

### Two hard grammar invariants

Zero exceptions across 2,772 paragraphs. These go in the **type system**, not the linter:

```
Character     → Dialogue (91%) | Parenthetical (9%)   — nothing else, ever
Parenthetical → Dialogue (100%)                        — nothing else, ever
```

### Every craft rule is a DENSITY metric, never a binary

For each absolute rule, a credible named professional rejects it. Mazin on directing on
the page: *"I just want to slap the world, because what else can we do?"* August on
"we see": *"perfectly valid, and a growing trend."* **Check densities against the table
above and flag outliers, not occurrences.**

### `agents/skills/screenwriter.md` — the core ladder

Try each rung; stop at the first that works:

1. **Consequential action** — he doesn't say the address, he opens the door with the old key
2. **Contestable evidence** — a torn-out page, a scar, who is holding the object
3. **Spatial behaviour** — who blocks the exit, who avoids the chair
4. **Dialogue tactic** — probing, misleading, bargaining; never neutral explanation
5. **Sound / V.O.** — *only* when the work has explicitly chosen that mode

With its anti-pattern, which is the rule LLM output violates most:

> *"Visualizing does not mean giving every line an action. Pouring water back and forth,
> walking to the window, leafing through irrelevant files — if it doesn't change the
> agenda or the evidence conditions, it's fake motion."*

**The V.O. rule, with counts.** Shawshank 141 · Gone Girl 89 · No Country **12** (10 in
the first two pages, 2 in the last, *zero* across the middle 110) · Little Women 8 ·
Sense and Sensibility 30 · Godfather 0. And the finding: **not one of Little Women's or
S&S's 38 cues is narration** — all are letters or off-screen dialogue.

> **The letter is the only film-legal voice-of-interiority in a period adaptation,
> because reading or writing a letter is an ACTION — something a character is caught
> doing. Narration is not.**

Directly relevant here: A Study in Scarlet is Watson's reminiscence, and Part II is a
third-person Utah flashback he cannot have witnessed. The documented solution is **give
interiority an interlocutor** — the Coens invented four listeners so Sheriff Bell could
argue rather than assert.

### `agents/skills/story_editor.md` — selection

**Adaptation is fixed-budget allocation, not compression.** Measured across seven
scripts, every screenplay lands in **22,000–33,000 words regardless of source size**
(S&S 4.3:1, P&P 5.1:1, Little Women 8.1:1). *A longer novel doesn't get a longer film,
it gets a higher cut rate.* Dialogue budget: 10,000–15,000 words.

**Dialogue survives adaptation at a measurably higher rate than narration** — retention
ratio 1.04 vs 0.97, p < 3×10⁻⁶, Cohen's d = 1.09, over 40 aligned book/film pairs. When
in doubt, keep the line and cut the description.

**Order is preserved.** Alignments are highly monotonic; restructuring (Gerwig's *Little
Women*) is a strong thematically-motivated exception, not a default.

**Cut whole subplots BEFORE merging characters.** Merging reassigns a function to a
person; if that person is later cut, every assignment is void.

**The unit is the sequence, not the scene.** Coppola's notebook: 5 acts → **50 sections
→ 225 slug lines** (~4.5:1). The wedding is 17 slug lines and *one* section. Our 92
scenes should group into ~20–25 sequences. His five per-section headings are a
ready-made beat record: **Synopsis · The Times · Imagery and Tone · The Core · Pitfalls**.

### `agents/skills/shot_designer.md`

Renders into the camera system this repo **already owns** —
`docs/higgs/higgsfield-seedance-prompt-builder.md` (1,133 lines) and
`CINEDANCE HIGGSFIELD SKILL.md` (1,330 lines). It does not reinvent it.

- **Spell every term out.** No vendor documents a single abbreviation; "MCU" is
  polysemous. Abbreviations are internal aliases that expand before any API boundary.
- **Store a `visual_consequence` with every term and always emit both.** Dolly-vs-zoom
  is genuinely hard — CameraBench, built with professional cinematographers, found human
  novices confuse them. *dolly in* → "parallax shifts, foreground slides past the frame
  edges"; *zoom in* → "the background compresses and flattens."
- **One primary move per clip.** Stated independently by Higgsfield, Kling, Seedance and
  Runway.
- **Positive phrasing only** — "the locked-off camera remains perfectly still", never
  "no camera movement".
- **Don't let scene content contradict the camera instruction** — GimbalDiffusion
  documents prompt–camera entanglement, where content wins.
- **Paragraph segmentation IS shot segmentation** — same paragraph, one shot; a break is
  a new angle. Free input.
- **The 180-degree rule is not promptable.** No model has cross-shot memory. It is a
  check on *our* shot list (`axis_side`, `looks_screen`, `travel_direction`), never
  prompt text.

Expectations: text-instructed camera motion succeeds **27–62%** of the time
(VBench-2.0: Kling 1.6 61.7%, Sora 27.2%). Oxford VGG's diagnosis: *"the limitation lies
not in the models themselves, but in how camera motion is induced."* **The capability is
latent; text is a lossy actuator.**

### `agents/skills/adaptation_auditor.md`

1. You are **not** checking whether the screenplay matches the book. By design it does not.
2. You are checking one thing: does it **contradict** the book?
3. **Every issue cites a verbatim book quote. No quote, no issue.**
4. Compression is not contradiction. Merging two conversations is not contradiction.
   Inventing a line to carry what the book delivered in narration is not contradiction.
5. `ok: true` with an empty list is the expected result for a good scene.

---

## Never gate on an LLM's self-score

Two independent results: **TTCW** found none of GPT-4, Claude v1.3 or GPT-3.5 correlated
positively with expert judgment on creative writing; **Spoiler Alert** found LLM judges
rank zero-shot AI stories *above* New Yorker short stories.

A rubric is safe as *a checklist that forces a named, located revision*. It is dangerous
as *a scalar you gate on*.

### And when you do score: aggregate by MINIMUM, not mean

From the Black List's **128,020 evaluations**:

| dimension | share of variance |
|---|---|
| Plot | 32% |
| Characters | 23% |
| Dialogue | 22% |
| Premise | 13% |
| Setting | 11% |

Execution carries **77%**. And the floor effect: the overall score sits at or below the
*lowest* sub-score **35.8%** of the time, versus at or above the highest only 15.0%.
Franklin Leonard: *"Your strengths won't be your salvation, but your weaknesses may well
kill you."*

**A scorer that averages will systematically overrate work that is excellent on one axis
and weak on another — which is exactly the failure profile of machine-generated
screenplays: strong premise, weak plot.**

---

## The Fountain round-trip linter — the highest-value 50 lines here

**Fountain falls back to Action on anything unrecognised, so a parser will never reject
our output.** Verified on this machine:

```
INT. HALL - DAY          →  Slug     ✓
THE DOOR BURSTS OPEN     →  swallowed as the CHARACTER CUE
Anna stands there,       →  Dialog   ✗
Marlow / You're late.    →  Action   ✗
```

Two elements silently misparsed, no error, no warning, wrong PDF. **No Fountain linter
exists in any language.**

Therefore the design is forced and simple: **the emitter knows the intended type of every
line it writes; it parses its own output; it asserts the parser's typing matches the
intent, line by line.**

---

## Target parameterisation

New repo-root `targets.yaml`, sibling to `models.yaml` and `stages.yaml`.

```yaml
default_target: short60

targets:
  short60:
    runtime_seconds: [50, 60]
    scenes: [1, 2]
    shots: [4, 6]
    dialogue: sparse
    aspect: "9:16"
    slice: {mode: best_scene}
    style_note: >
      One continuous dramatic beat. No subplot, no exposition. Ends on the image.
```

The discipline: the target block is **injected as data** into the story editor's prompt,
never compiled into a different prompt or agent; it is **enforced by code afterwards**;
`slice.mode` is resolved **deterministically before the agent sees anything** (only
`best_scene` is a judgement); and `source_fingerprint = sha256(dossier + target block)`,
so editing one target invalidates that target and only that target.

---

## Test strategy — zero API spend

Fixtures are built **from the pydantic models** (CLAUDE.md: *"fixtures are derived from
the contract, never hand-written drift"*), never by reading the real 4.2 MB
`timeline.json`.

| file | covers |
|---|---|
| `test_screenplay_spec.py` | validator rejects dialogue without a character, action with a parenthetical, `verbatim` without a source; **`test_element_schema_is_provider_safe()`** |
| `test_fountain.py` | golden render; `page_eighths`; slugline casing; `CONT'D`; **round-trip type assertion** |
| `test_screenplay_json.py` | `screenplay.json` round-trips through the model; `elements.json` is derivable from it; a field present in the json survives into `.fountain` **or is explicitly listed as render-lossy** |
| `test_pdf.py` | `screenplain` parses our emitted Fountain into the intended element types and writes a `%PDF` header — offline, no network, no spend |
| `test_step_01_dossier.py` | the join; `int_ext` pulled from extraction; UNKNOWN time never reaches the dossier |
| `test_screenplay_guards.py` | G1–G4, including DAY→DAWN **accepted** and DAY→NIGHT **rejected**, and a `timeline.contradictions` scene downgraded to advisory |
| `test_screenwriter.py` | per-scene file written immediately (crash at beat 3 keeps 1–2); `ContentFiltered` skips one beat and continues |
| `test_adaptation_auditor.py` | an issue whose `book_quote` fails `is_grounded()` is dropped before the improve loop |

`tests/test_agent_conventions.py` globs `agents/*.py`, so the four new agents are
automatically required to declare `TIER`, route through `llm.structured()`, and own a
skill file. **No change needed — it starts guarding the new crew the moment the files
land.**

---

## Risks

| | risk | mitigation |
|---|---|---|
| **R1** | **The auditor becomes a censor.** Highest risk — on a stage whose product is difference, an auditor reporting difference is noise. | structural: no `book_quote`, no issue |
| **R2** | Feature-target cost — ~110 scenes × 2 calls on the reasoning tier | ship `short60` first; per-scene files written immediately; **the first `feature` run gates ESCALATE with an itemized estimate** |
| **R3** | Provider strict-mode rejects the element schema | flat wire model + the free offline schema-guard test |
| **R4** | Analysis is lossy where screenplay needs it most | `01 dossier` fixes it now; **also raise carrying `int_ext` through `step_03.remap` as an analysis-side issue** (done — commit `02beeca`) |
| **R5** | **15 of 23 speaking characters have no `profile.voice`**, including Enoch Drebber, the murder victim; 16 of 24 locations have no `profile.visual` | `01_03` warns; fallback is the character's `quotes[]` (up to 12 verbatim lines). Raising `PROFILE_TOP_CHARACTERS` is a **paid analysis re-run and the owner's call.** |
| **R6** | The 16 `nonscene` segments — a screenwriter handed one will invent a scene the book never staged | skill rule + the story editor may route them to `omitted` |
| **R7** | 17 scenes still have `int_ext: UNKNOWN` after normalization | needs re-extraction with the corrected skill, or a gap-filler pass. **Spends.** |

---

## Publishable artifacts

Three gaps surfaced that do not exist anywhere, per the standing goal:

1. **`fountain-lint`** — no Fountain linter exists in any language, and two independent
   parsers make the identical silent misparse on a two-line input.
2. **`studio/fountain.py` as a standalone** — a typed pydantic ↔ Fountain round-trip
   emitter with correct page-eighths. The existing Python libraries are parsers, not
   typed emitters, and none does eighths.
3. **The `verbatim | adapted | invented` provenance contract** with its `is_grounded`
   checker — a general mechanism for auditing any LLM adaptation of a source text
   *without forbidding invention*. This is the interesting one, and a plausible short
   paper: *provenance labelling as a tractable substitute for grounding in generative
   adaptation.*
