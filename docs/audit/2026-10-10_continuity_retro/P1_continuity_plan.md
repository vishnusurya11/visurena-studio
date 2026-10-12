# P1 (CONTINUITY): build plan for character looks, place masters and states, and the judges that verify them

Debater P1, 2026-10-10. Read-only pass: no code, workflow or library file changed, nothing rendered.
Inputs: retro reports A-G in this folder, `CLAUDE.md`, `.claude/skills/episode/{SKILL,GATES,LESSONS}.md`,
`docs/DECISIONS.md`, `stages.yaml`, `architecture/index.html`, and the code cited by file:line below
(re-read at HEAD `0b64656`). Evidence images looked at: `A_evidence/strip_ep25.png` (row T0: the panel is
the clean ep01 sheet, a grey suit and a boater; by 2 s H3 has changed him into a striped shirt and a felt
hat; T13 and T18 have the beard while T0, T5 and T9 do not), and `D_evidence/study_refs.jpg` (four
"narrators_study" pictures that are four different rooms: French windows, a door with a fireplace, a
lamp-and-globe desk, and a sash window).

---

## 0. The brick, and what it rules out

**A recurring entity is one base picture. Every story-time state is ONE derivation from that base,
recorded in a table keyed by story time. Each take stages the picture of the state it is in, and the
words describe that picture.**

- Base case: `L0` is the character's identity sheet; `M0` is the place's first master.
- Recursive rule: `look(who, t) = derive(L0, deltas active at t)` and
  `variant(place, side, state, hour) = derive(master(side), state, hour)`. There is always exactly ONE
  hop from the base. A derivation is never made from another derivation.
- Closure: one look table plus one place table is enough to resolve the correct picture for every
  (setup, person) and every setup's place in every episode. Nothing else is chosen by hand.

What this rules out (each is a failure found in the reports):

| Failure | Report |
|---|---|
| The same sheet staged for every state | A §4 |
| A new view drawn from words, giving a new room | B R1, D §0 |
| A second location id for the same room | B R3 |
| Words that contradict the staged pixels, e.g. "dark hair… shaven" beside "grey… beard" (`pack_refs.py:131`), or retention text that says "clothes of <Picture k>" while k shows another look (`episode_ref_official.py:633`) | A §2 |
| Chained edits that drift | C §2c, D §2a |

What this keeps:
- one row per person bound per chapter (`cast_rows`);
- the anchor chain inside a setup (2026-09-28);
- no place slot in H3 (the panel carries the place; D §2c);
- no character composited into a frame (the 09-24 ban stands).

---

## 1. Data model (pydantic first; the contract is the spec)

New module `studio/continuity_spec.py`. It is written before any producer, per `CLAUDE.md` "Spec-driven".
Both files sit under `library/<book>/refs/`, stored with relative paths only.

### 1a. `refs/looks.json`: the look table (costume plot)

```json
{
  "book": "<book_id>",
  "policy": "fresh",                       
  "characters": {
    "unnamed_first_person_narrator": {
      "base": "day_suit",
      "body": "Man of 34, 5 ft 10 in, slender ... grey eyes. Fair English skin ...",
      "looks": [
        {"look_id": "day_suit", "from": {"chapter": 1}, "until": {"chapter": 6},
         "layers": {"top": "mid-grey herringbone three-piece suit, white collar, dark tie",
                    "headwear": "straw boater", "hair": "dark brown hair cut short, combed smooth",
                    "face": "neat close-trimmed dark brown moustache; shaven cheeks and chin"},
         "markers": {"headwear": "boater", "hair_colour": "dark", "facial_hair": "moustache",
                     "top": "suit_jacket"},
         "source": [{"chapter": 1, "quote": "busy upon a series of papers"}],
         "sheet": "refs/characters/unnamed_first_person_narrator/sheet_front.png",
         "made_by": "base", "parent_sha8": null, "seed": 0, "face_change": false},
        {"look_id": "ragged_greyed", "from": {"chapter": 22}, "until": {"chapter": 25},
         "layers": {"top": "cream-and-blue striped flannel shirt torn at the shoulder ...",
                    "headwear": "battered brown felt hat",
                    "hair": "ash-grey, shaggy over the ears",
                    "face": "sixteen days of grey-brown beard; gaunt, cheekbones sharp"},
         "markers": {"headwear": "felt_hat", "hair_colour": "grey", "facial_hair": "beard",
                     "top": "shirt"},
         "source": [{"chapter": 24, "quote": "your hair is grey"}],
         "sheet": "refs/characters/unnamed_first_person_narrator/looks/ragged_greyed.png",
         "made_by": "fresh", "parent_sha8": "<sha8 of the base sheet_front>", "seed": 41022,
         "face_change": true},
        {"look_id": "ragged_greyed", "from": {"chapter": 26, "scene": 1}, "until": {"chapter": 26, "scene": 1}},
        {"look_id": "borrowed_suit", "from": {"chapter": 26, "scene": 2}, "until": {"chapter": 26}}
      ]
    }
  }
}
```

Contract rules. Each is a pydantic validator with its own test:
1. `body` is the invariant body: build, face shape, eyes and skin. It holds **no** hair, facial-hair or
   hat sentence. Those belong to the look's layers. This fixes the "dark brown … shaven" plus "grey …
   beard" contradiction at its source.
2. Every non-base look has `parent_sha8` equal to the **base** sheet's sha8 (star topology). A look whose
   parent is another look is refused.
3. Intervals are `(chapter, scene?)`, so a chapter can change look between scenes. This covers ch26, ch7,
   ch12 and ch18 (A §1a). The intervals of one character never overlap, and an open `until` means "until
   the next look". A look id may repeat with a second interval (ragged_greyed in ch26 scene 1).
4. `markers` uses a **closed vocabulary**, in the same style as `content_gate` / `picture_read`:
   - `headwear` ∈ {none, boater, felt_hat, cap, bonnet, helmet, bandage, …}
   - `hair_colour` ∈ {dark, brown, fair, red, grey, white, bald}
   - `facial_hair` ∈ {none, moustache, beard, stubble}
   - `top` ∈ {suit_jacket, shirt, shirtless, coat, dress, uniform, nightshirt, …}
   - `dirt` ∈ {clean, dusty, sooted, muddy, bloodied}

   The judges compare markers, never prose.
5. `face_change` is true exactly when the look's `hair` or `face` layer differs from the base. It decides
   both the derivation route and whether the identity judge runs.
6. `made_by` ∈ {base, fresh, edit, edit_headkept}. `policy` ∈ {fresh, edit} is the owner's open question
   (§7). It defaults to `fresh`.

### 1b. `refs/places.json`: the set bible

```json
{
  "places": {
    "narrators_villa": {
      "name": "The narrator's villa at Maybury Hill",
      "members": ["narrators_home", "narrators_study", "narrators_dining_room", "narrators_garden"],
      "masters": [
        {"master_id": "front_ext", "location": "narrators_home", "view": "wide_establishing",
         "side": "front", "derived_from": null, "made_by": "fresh", "sha8": "7972962f",
         "fixed": [{"thing": "canted brick bay", "x": "LEFT", "y": "MIDDLE", "depth": "near", "size": "large"}]},
        {"master_id": "study_wide", "location": "narrators_study", "view": "wide_establishing",
         "side": "study_window_wall", "derived_from": null, "made_by": "fresh", "sha8": "13c8eea6",
         "fixed": []},
        {"master_id": "study_reverse", "location": "narrators_study", "view": "reverse_from_wide",
         "side": "study_door_wall", "derived_from": "study_wide", "made_by": "edit", "sha8": "",
         "fixed": []}
      ],
      "states": [
        {"state_id": "intact", "from": {"chapter": 1}, "until": {"chapter": 25}, "deltas": []},
        {"state_id": "abandoned", "from": {"chapter": 26}, "until": {"chapter": 26},
         "deltas": ["the front door stands forced open on its hinge", "dust on every flat surface",
                    "the privet hedge smashed and trailing red weed"],
         "source": [{"chapter": 26, "quote": "..."}]},
        {"state_id": "restored", "from": {"chapter": 27}, "deltas": []}
      ],
      "variants": [
        {"master_id": "front_ext", "state_id": "abandoned", "hour": "day",
         "view": "front_ext__abandoned__day", "made_by": "edit", "parent_sha8": "7972962f",
         "geomcons": 0, "sha8": ""}
      ]
    }
  }
}
```

Contract rules:
1. A location id belongs to exactly one Place. That stops the `narrators_dining_room` / `narrators_home`
   split (B R3).
2. A variant's `parent_sha8` equals its master's `sha8`, so there is one hop and never a chain.
3. A derived master (a reverse) names `derived_from` a fresh master of the same Place. It is frozen once
   it is judged, and it is never redrawn.
4. `fixed` is the master's own `studio/picture_read.read` list (`picture_read.py:59`). It is cached once,
   and it is the reference that the fixed-feature judge counts against.
5. A Place with no `states` is `intact` for every chapter. An empty-delta state resolves to the master
   itself, with no derivation.

Pictures on disk:
- `refs/characters/<id>/looks/<look_id>.png` is a one-figure, full-body front. It has the same shape as
  `sheet_front.png`, because that is what grids and takes stage today
  (`takes_r2v.py:211 FRONT_SHEETS`, `grids.py:152`).
- `refs/locations/<loc>/<view>.png` is unchanged. Variants are written as
  `<master_view>__<state>__<hour>.png` beside their master.

### 1c. Plan contract (`studio/episode_spec.py:383 Setup`)

Add two fields:
- `looks: dict[str, str]`: person → look_id. When it is empty the resolver uses the chapter default.
- `place_state: str`: empty means the state the Place table resolves for the chapter.

`Setup.state` (the indoor/outdoor property at `:440`) is left alone because Scarlet's per-state cards
still read it. The new fields get new names, so the two meanings cannot be confused.

Book gate: a book with no `refs/looks.json` runs the legacy path, which is one sheet plus words. It
writes an audit row `continuity: legacy` and is never silent. A **new book** gets both files at refs/01,
so it cannot take the legacy path.

---

## 2. Where it plugs in (file:line from the reports, verified at HEAD)

| # | Where | Change |
|---|---|---|
| a | `studio/pack_refs.py:125 wardrobe_state` | Becomes `look_for(book, who, chapter, scene=None, named="") -> Look`. It reads `looks.json` and falls back to `wardrobe_by_chapter` only on a legacy book. |
| b | `studio/pack_refs.py:131 character_row` | `physical = look.body + layers in order (headwear, hair, face, top, dirt, …)`, with the defining layer FIRST (SKILL: "a detail buried mid-sentence is dropped"). The row gains `look` and `markers`, and `rel_path` = the look's picture. |
| c | `studio/pack_refs.py:97 character_sheet` | New sibling `look_sheet(book, who, look_id)`. It returns the look picture. For a non-base look with no picture it **refuses** (step 03 draws it), and it never falls back to the base. |
| d | `scripts/refs/cast_rows.py:39` → `pack_refs.py:309 rows_for` | Stamps each row with the chapter's default `look` and `looks_allowed` (every look whose interval meets the chapter). |
| e | `scripts/episode/grids.py:152 sheet_of` | Signature `(book, who, look_id)`. It stages the look picture, and `front_of` still applies to the base sheet. `cast_of` (`:175`) passes the setup's look and quotes that look's row as `wear`. `inputs_sha` (`:139`) makes old grids stale automatically, and no new staleness code is needed. |
| f | `studio/episode_seq_board.py:45 cast_sheet` | New first rung: `look_sheet(book, who, setup_look)`. The Scarlet state-card rungs stay below it. |
| g | `scripts/episode/takes_r2v.py:226 reference_list`, `:305 refs_from_cards` | Pass the setup's look into `cast_sheet`. `one_figure` (`:219`) is a no-op on a look picture, which is already one figure. |
| h | `studio/episode_ref_official.py:619/633 retention` | Keep "face, hair, build and clothes of <Picture k>". It becomes TRUE once k is the look picture. A new lint in step 06 refuses a take whose subject text's look id ≠ the staged picture's look id. |
| i | `scripts/refs/places.py:88 draw_missing` | If the setup's location belongs to a Place with a master, derive a variant or a side from that master (§4). A fresh draw happens only when the Place has no master for that side yet, and that draw then becomes the master. `ensure_rows` (`:56`) refuses a new id whose name or aliases fuzzy-match (0.85) a Place member. |
| j | `studio/plan_brief.py:170 cast_rows`, `:198 places` | The brief carries the look ids and the drawn masters, variants and history (§5). |
| k | `studio/panel_content.py:202 contradictions`, `studio/take_content.py:62 drifted` | Both compare against the **look's markers** instead of the concatenated row. Today the row contains "dark brown hair" AND "ash-grey", so the grey/dark check can never fire (A §5). |
| l | `studio/judges/look.py` | New sibling judge `studio/judges/look_state.py`. It reuses the facenet embedder (`:77`) and DINOv3 (`:89`). |
| m | `studio/picture_read.py:59 read` | Reused as-is by the fixed-feature judge. |

---

## 3. Drawing a look (step 03, substep 03_04 `looks`, just-in-time)

The order inside step 03 is **looks first, then places**, so Krea2 is loaded once for both. The draw
batch is every `(who, look_id)` named by this plan's setups that has no picture yet. Nothing is
pre-rendered book-wide, per memory `build-only-what-the-episode-needs`.

| policy | delta kind | route | workflow (none is edited) |
|---|---|---|---|
| `fresh` (default until ruled) | any | Krea2 T2I from the **base row's own prompt and seed** (`refs/pack.jsonl`). Look layers are written FIRST and the invariant body after. Then the one-figure crop (`studio/sheet_front.front_of`). | `image_krea2_cinematic_2x.json` (existing) |
| `edit` | garment, dirt, headwear or held only (`face_change: false`) | Edit `sheet_front.png` with the instruction "Same man, same face and hair. Change ONLY: <layers>". Then **head-keep**: code pastes the base's head box back, using a facenet box grown 1.3x and a 12 px feather. The face pixels are then identical by construction. | `image_krea2_identity_edit.json` (existing, unused today; Krea2 + identity LoRA + the house Cinematic LoRA) |
| `edit` | face or hair (beard, grey, gaunt, wound) | The same identity edit with no head-keep (`ref_boost 4`). The relative identity judge must pass. | `image_krea2_identity_edit.json` |

Prompt (fresh), in order:
1. Defining layers first: `"Ash-grey shaggy hair over the ears; sixteen days of grey-brown beard; gaunt
   face, sharp cheekbones; battered brown felt hat; cream-and-blue striped flannel shirt torn at the
   shoulder…"`.
2. Then the body: `"Man of 34, slender, long oval face, grey eyes…"`.
3. Then the existing sheet style tail.

Removals are drawn, not negated: "bare-headed, hair visible" rather than "no hat" (C §3.4). The plan
gates already refuse negation words (`Setup._the_drawer_reads_only_what_is`).

Ladder (inside the 6 h clock, priced):
1. Draw, then judge.
2. On a fault, redraw on seed+1 with the faulted layer moved to the front.
3. On a second fault, the terminal keeps the best by (markers met, identity margin), signs `flagged`,
   and writes an audit row.

The cap is 2 redraws per look. A look picture is never redrawn once it is bound, and the next episode
that uses the look reuses it.

---

## 4. Places: masters, states, sides (step 03, substep 03_05 `variants`)

| need | route | workflow |
|---|---|---|
| A Place side with no master | Fresh Krea2 T2I, as today. It becomes the master and is frozen. `picture_read` caches `fixed`. | `image_krea2_cinematic_2x.json` (existing) |
| A state or hour of an existing master | One-hop edit of the master: "Same room as Image 1: same walls, windows, doors and furniture in the same places. ONLY change: <first delta>." **One delta per pass.** When there are several deltas, each pass edits the master again, never the output of the previous pass, and the passes are capped at 2. Hour uses a separate relight pass. | Default: `image_qwen_image_edit_2511_single_image.json` (existing; Qwen-Image-Edit-2511 + the on-disk Lightning-4step LoRA; earlier-line license, which the owner should confirm). Hour: **new** `image_qwen_image_edit_2511_single_image_relight_dx8152.json` (on-disk `Qwen-Edit-Relight.safetensors`). If the owner clears the Qwen Research License: **new** `image_qwen_image_2_1_edit_consistency_ausboss.json` (A/B against 2511 first; D §2a). |
| A new side of a room (a reverse) | Derived ONCE from the master, judged, then frozen as a master. It is never drawn from words. This replaces ep27's `reverse` fresh draw. | **New** `image_qwen_image_edit_2511_single_image_multiangle_fal.json` (on-disk `qwen-image-edit-2511-multiple-angles-lora.safetensors`) |
| A different room of the same Place (the dining room) | Fresh, once, as the master of that side. Every later dining scene reuses it. | existing T2I |

Rules for new workflows: each new workflow is a **new file** with its manifest, named `<base>_<source>.json`
(owner fact 4). The three base files are copied, not edited. A test checks that every `inject` node in
each new manifest exists in its graph.

Place grouping for a new book happens in refs/01 `canon`, as a new substep 01_03 `places`. A new agent,
`agents/production_designer.py` (Strands, local tier), takes the `analysis/locations/*.json` rows and
returns a typed `PlaceList` (place_id, name, member location ids, sides, and states with
chapter/scene/quote). Code writes `refs/places.json`. Every state needs a quote, which code finds in the
chapter text at 0.85, the same matcher as G-SOURCE. A state without a quote is dropped. In its test the
agent is a `FakeModel`.

Things deliberately not done:
- No place slot in H3 (D §2c; memory `h3-freeze-and-hardcut`).
- No 360/ERP plate in this plan. That is phase 2 and needs its own bench.

---

## 5. How the plan writer learns the ids (brief + skill + gates)

**Brief** (`studio/plan_brief.py`):
- `cast_rows` (`:170`) adds, per person:
  - `looks_allowed`: `[{look_id, from, until, markers, drawn: bool}]`;
  - `default_look`;
  - a one-line `change_note`, for example "ch26 opens ragged_greyed (scene 1) then borrowed_suit".
- `places` (`:198`) returns **Place rows**, not the raw analysis rows. Each row has:
  - `members`;
  - `masters` with `{location, view, side, hour, drawn: true}`;
  - `variants` already drawn;
  - `state_for_chapter`;
  - `history`: the `location/view` pairs earlier episodes staged for this Place, scanned from
    `episodes/*/plan.json`. This is code with no LLM.
- Planned-but-undrawn `design.views` ids are **removed** from the brief. They are what tempted the writer
  into new rooms (B R3).

**Skill** (`agents/skills/episode_writer.md`), new section "Continuity":
1. Each setup names `looks` for every face whose look differs from the chapter default, and uses
   only ids from `looks_allowed`.
2. `location` is a Place member and `view` is a drawn master or variant, or a new view written as
   `derive:<master_id>` with a `place_state`.
3. Never describe a room again. Describe what changes, as nouns.
4. Never write hair, beard or hat words that differ from the look's layers. The rows already carry them.

**Plan gates** (`studio/plan_gates.py`, free, seconds):

| gate | rule | level |
|---|---|---|
| G-LOOK | every face in every setup resolves to a look whose interval meets this chapter (and the setup's scene when given). A non-default look carries a `source` span found in the chapter text (0.85). | HARD on a new-form plan |
| G-LOOK-WORDS | no shot or setup prose names a hair colour, facial-hair or headwear marker that contradicts the resolved look's markers (closed vocabulary, regex) | HARD |
| G-PLACE | `location` belongs to a Place. `view` is drawn, or is `derive:<master>` of the same Place. A location id not in `places.json` whose name or aliases fuzzy-match a member at 0.85 is refused, which would have refused ep26's `narrators_dining_room`. | HARD |
| G-PLACE-STATE | `place_state`, when set, is in the Place's states and its interval meets the chapter | HARD |

Refusals go back to the writer verbatim through the existing REFUSED loop (`agents/episode_writer.py`).

---

## 6. The judges, thresholds and where they sit

Every judge follows the house list-then-judge pattern: the VLM lists in a closed vocabulary and code
judges. The VLM never decides pass or fail (memory `content-dq-reads-the-picture`).

| judge / gate | where | measure | threshold to start | level | calibration owed (free, local, `@pytest.mark.local`) |
|---|---|---|---|---|---|
| **LOOK-STATE** `judge:look_state@1` (new `studio/judges/look_state.py`) | step 03_04, on every new look picture; signs `refs/looks.verdict.json` bound to `looks.json` sha | VLM lists headwear, hair_colour, facial_hair, top and dirt in the closed vocabulary. Code requires every marker of the look. | all 5 markers met; `unread` → flag | HARD (missing marker) | the narrator's 10 dossier looks as text-only fixtures, plus the bench A/B (§8) |
| **Relative identity** (inside LOOK-STATE) | only when `face_change` | facenet `m = cos(look, base) − max_other cos(look, other cast sheet)` | `m > 0` HARD from day one (a look nearer a stranger than to itself is never right). `m ≥ 0.05` advisory until the bench fits it. No absolute wall: strangers measured 0.45-0.82 on this style (`look.py:46`; C §4). | HARD at 0 | WotW cast: 26 sheets give the stranger distribution; the A/B looks give the self distribution |
| Style (inside LOOK-STATE) | every look | DINOv3 cosine to the base sheet | `≥ STYLE_OUTLIER 0.5` (`look.py:52`) | flag | existing |
| **G-PLACE-FIXED** `judge:place_fixed@1` (new `studio/judges/place_fixed.py`) | step 03_05, on every variant and derived side | `picture_read` lists both pictures. Code counts appear, disappear and moved-third violations among the master's `fixed` list, discounting a thing named in the state's deltas. `GeomCons = 100·(1 − v / max(Na, Nb))` (CANVAS, D §4). | variant ≥ **75**. Derived side (reverse) is exempt from position and needs DINOv3 ≥ a same-place band fitted on this book, plus an audit row for the owner. | HARD for a variant, flag for a side | the 17 WotW house pictures (known different rooms) as negatives, master vs its own hour variants as positives |
| **G-LOOK-PANEL** (extend `panel_content.ASK` and `contradictions`, `panel_content.py:202`) | step 08, every panel with a face | the reader adds `headwear / hair_colour / facial_hair / top` per listed person. Code compares with the staged look's markers. | any of headwear, hair_colour or facial_hair contradicting the look → fault; `top` → advisory | HARD after the bench, advisory for the first episode | positives: ep18 shot 0, ep25 shots 0, 8, 11, 14, ep26-27 grey-hair misses (A §2). Negatives: ep10 and ep13 (correct clothes-only looks). Target recall ≥ 0.8 at false-refusal ≤ 0.1. |
| **G-LOOK-TAKE** (extend `take_content.drifted`, `take_content.py:62`) | step 09 take gate | the same markers on the first, middle and last frames already decoded by take_content (no extra decode) | a marker that changes between frames, or contradicts the look on 2 of 3 frames → fault. Cure: one batched retake (cap from the 09-30 ladder). If the panel also fails, the fault routes to "sheet first", never a retake. | HARD after the bench | ep18 T0, ep24 T0, ep25 T0 (mid-take costume change) are the positives |
| **G-PLACE-PANEL** (extend `panel_place`) | step 08 | GeomCons of the anchor panel against the Place master (not only the setup's plate) | < 55 → flag; a planned reverse is exempt | advisory (as `panel_place` today) | ep26 dining, ep27 study_reverse, ep11 study as positives |

Gate entries go in `gates.yaml` under `refs` (look_state) and `episode` (place_fixed, panel and take
rows), with `auto` terminals per the 2026-10-01 ruling.

---

## 7. Owner questions, defaults and the fallback

- **Q1, character looks by edit:** may a look be an identity edit of the base sheet (garment-only with
  the head pixels kept; face-state with the identity judge)?
  - If unanswered, code ships `policy: fresh`.
- **Q2, place states and sides by edit:** may a state, hour or reverse be a one-hop edit of a frozen
  master? With which model: 2511 (default), or 2.1 + Consistency LoRA (Qwen Research License; not legal
  advice, flagged for his attorney if the channel monetises)?
- **Fallback if he refuses edits (fresh renders only):**
  - Looks: the fresh route of §3 (base prompt and seed, layers first), judged by LOOK-STATE and the
    relative identity rule. It costs about 60 s more per look than an edit and adds no new model.
  - Places: **frozen masters, no variants.** Every view of a Place is one of its masters. A new side is
    a fresh draw only the first time and then frozen. A state is carried by the grid drawer, which is
    already an edit model with the master staged: the grid prompt says "Image 2 is this exact room.
    ONLY change: <delta, first>". It is judged by G-PLACE-PANEL.
  - G-PLACE still stops new rooms under new ids, which B and D say is most of the drift.

---

## 8. Build order: commits, each one test-first

Every function is 10-20 lines. Readers and drawers are injected (FakeModel, fake draw, fake reader and
embed). No test touches ComfyUI or a paid API (the `tests/conftest.py` trap stays armed).

| # | Commit | Test written first (file) |
|---|---|---|
| 0 | **Proposal docs**: `architecture/decisions/2026-10-10_continuity_looks_and_places.md`, tracker `architecture/plan/2026-10-10_continuity_build.md`, the owner's 10-10 ruling line in `docs/DECISIONS.md`, `architecture/README.md` rows, `architecture/index.html` *Future* tab (§10) | none (doc commit) |
| 1 | `studio/continuity_spec.py`: Look, Layers, Markers, CharacterLooks, LookBook, Place, Master, State, Variant + validators (star, intervals, closed vocab) | `tests/test_a_look_is_one_hop_from_its_base.py`, `test_a_place_variant_is_one_hop_from_its_master.py`, `test_look_intervals_never_overlap.py` |
| 2 | `studio/look_table.py`: `layers_of(text)` (sentence → layer by closed keyword list), `markers_of(layers)`, `body_of(physical)` (drops hair, facial-hair and hat sentences), `looks_from_dossier(card)` | `test_the_body_carries_no_hair_or_beard.py` (fixture: the narrator's real `physical` gives no "dark brown hair"/"shaven"), `test_wardrobe_by_chapter_becomes_intervals.py` (list entries for ch26 scenes) |
| 3 | `pack_refs.look_for`, `look_sheet`; `character_row` rebuilt on looks; legacy path on a book with no `looks.json` | `test_a_ragged_row_never_says_dark_hair.py`, `test_an_undrawn_look_refuses_never_falls_back.py`, `test_a_legacy_book_keeps_one_sheet_and_audits_it.py` |
| 4 | `cast_rows`/`rows_for` stamp `look` + `looks_allowed` | `test_bound_rows_carry_the_chapter_look.py` |
| 5 | `Setup.looks`, `Setup.place_state`; plan gates G-LOOK, G-LOOK-WORDS, G-PLACE, G-PLACE-STATE | `test_plan_gates_look.py`, `test_plan_gates_place.py` (ep26's `narrators_dining_room` refused; ep27 `reverse` without `derive:` refused) |
| 6 | `plan_brief.cast_rows`/`places` carry looks, Places and history; drop undrawn view ids; `agents/skills/episode_writer.md` Continuity section | `test_the_brief_names_drawn_views_only.py`, `test_the_brief_lists_place_history.py` |
| 7 | `studio/continuity_place.py` + `agents/production_designer.py` (FakeModel) → `refs/places.json`; quotes verified | `test_places_json_groups_members.py`, `test_a_state_without_a_quote_is_dropped.py` |
| 8 | `scripts/refs/looks.py`: `missing_looks(plan, table)`, `fresh_prompt(look, base_row)`, `edit_prompt(look)`, `keep_head(base, edited, box)`, `draw_looks(..., draw)` | `test_the_fresh_look_writes_layers_first.py`, `test_keep_head_restores_face_pixels.py` (synthetic arrays), `test_only_this_episodes_looks_are_drawn.py` |
| 9 | `studio/judges/look_state.py` + ladder + `refs/looks.verdict.json` | `test_look_state_requires_every_marker.py`, `test_relative_identity_refuses_a_look_nearer_a_stranger.py`, `test_face_kept_looks_skip_identity.py` |
| 10 | Staging: `grids.sheet_of`/`cast_of`, `episode_seq_board.cast_sheet` look rung, `takes_r2v.reference_list`/`refs_from_cards` | `test_the_staged_picture_is_the_setups_look.py`, `test_a_new_look_makes_its_grid_stale.py` (via `inputs_sha`) |
| 11 | Step 06 lint: the subject text's look id = the staged look id | `test_take_words_and_picture_name_one_look.py` |
| 12 | New workflow files (relight, multiangle; consistency only if Q2 clears) + manifests | `test_new_workflow_manifests_inject_real_nodes.py` |
| 13 | `places.py` derive path: `variant_target`, `derive_prompt(state, delta)`, `draw_missing` routes master/variant/side; `ensure_rows` fuzzy refusal | `test_a_known_place_is_derived_not_drawn.py`, `test_variants_edit_the_master_never_a_variant.py`, `test_a_lookalike_new_location_is_refused.py` |
| 14 | `studio/judges/place_fixed.py`: `violations(master, other, discounted)`, `geomcons(...)` | `test_geomcons_counts_moved_and_missing_fixed_things.py` (synthetic `picture_read` lists) |
| 15 | `panel_content` marker read + `contradictions` by look; `take_content.drifted` by look and by frame | `test_panel_with_the_base_suit_fails_a_ragged_look.py` (Seen fixture of ep18 shot 0's real read), `test_a_costume_change_mid_take_fails.py` |
| 16 | Step 03 wiring: substeps 03_04 looks, 03_05 variants; `stages.yaml`; `scripts/episode/commands.py --write` regenerates the SKILL registry table; refs/01_03 places substep | `test_episode_steps_run_alone.py` (extend), `test_every_declared_output_is_a_path_its_step_reads_as_done.py` (extend) |
| 17 | Bench + calibration docs `docs/calibration/look_state.md`, `place_fixed.md`; thresholds written from measured numbers | `@pytest.mark.local` only |
| 18 | Skill text (§9) + architecture page *Current* tab flip + republish | — |

The last commit lands only after the A/B bench (about 30 min GPU, $0, local, no shipped episode
re-rendered). The bench draws the narrator's `flannel_buried`, `ragged_greyed` and `epilogue_home` both
ways (edit vs fresh), plus one ep25 grid re-drawn with {whole sheet, `sheet_front`, look picture} to
split A's confound. It also draws the villa `abandoned` variant with 2511 vs fresh. That bench is the
evidence the owner rules Q1 and Q2 on.

---

## 9. Skill text changes

**SKILL.md**
- `:169` (step 03 row, generated from `stages.yaml`): replace "drawn from its own described words" with
  "this unit's looks and place pictures: a character look and a place state/hour are ONE derivation of
  their base (refs/looks.json, refs/places.json); a recurring place's view is a drawn master or derived
  from one, never a fresh room".
- `:200-201` tools rows 3-4: add `scripts/refs/looks.py <book> <n>`, and the gates LOOK-STATE and
  G-PLACE-FIXED.
- `:283-285` §Pictures "One sheet per character … never from edited pictures": rewrite as "One sheet per
  character LOOK on the book's look table (owner 2026-10-10, reverses 09-18 for story-time looks); one
  master per Place side; a state, an hour or a reverse is derived from its master in one hop
  (policy: fresh until Q1/Q2 rule)".
- `:290-291` "When the words and the picture disagree and the book is silent…": add "A look in
  `looks.json` means the book is NOT silent. Change the picture (stage the look), never the words".

**GATES.md**
- Plan table: G-LOOK, G-LOOK-WORDS, G-PLACE, G-PLACE-STATE.
- New section "Pictures (step 03)": LOOK-STATE, relative identity, G-PLACE-FIXED.
- Panels: G-LOOK-PANEL, G-PLACE-PANEL.
- Takes: G-LOOK-TAKE.
- Known gaps: the face-state identity margin and the place GeomCons wall are uncalibrated until the
  bench runs.

**LESSONS.md**
- *Cast:* "A wardrobe promise needs a picture (`8c28bf6`, learned on Scarlet, lost on 09-18, relearned
  2026-10-10). A look in words loses to the staged sheet, and loses hardest on the face: ep22-27 grey
  hair 0-1 of about 24 panels."
- *Cast:* "Never let a row carry two heads. The body is invariant, and hair, beard and hat belong to the
  look. Otherwise every gate that reads the row allows both."
- *Places:* "A view drawn from words is a new room (dining room ×3, study ×6). Derive it from the
  master, one hop, or reuse the master."
- *Places:* "One room under two ids is two rooms. The Place owns its members."
- *Process:* "A gate that compares against a self-contradicting row cannot fire. Check what the gate
  compares against before trusting its silence."

Memory note for the parent: `feedback_one_sheet_per_character.md` needs its story-time-look clause
superseded once the ruling is filed.

---

## 10. Architecture page rows that change (`architecture/index.html`, same commit as each change)

| where | row | change |
|---|---|---|
| Lede (`:267`) | "Nineteen agents" | twenty (production designer) |
| `TEAMS` Refs & Cast (`:938`) | U('01','Canon') | add A('Production designer','PlaceList: members, sides, states with quotes') |
| `TEAMS` Refs & Cast | U('04','Verdict') | note `looks.verdict.json` signed by `judge:look_state` |
| `TEAMS` Episode (`:946`) | U('03','Places') | rename the description to "Looks and places"; add substeps 03_04 looks and 03_05 variants; agents A('Look-state judge','markers + relative identity','qc'), A('Fixed-feature judge','GeomCons vs the master','qc') |
| `TEAMS` Episode | U('02') brief | "bound rows + their looks + the place bible (drawn views, history)" |
| `CURRENT` / `FUTURE` step tables (`:1166`, `:1246`) | 03_01 "draw every setup's place picture" | add 03_04 "draw this unit's new looks (one hop from the base)", 03_05 "derive place variants (one hop from the master)", each with a log line; refs 01_03 places |
| Org tree markup (`:304`, `:547`) | Refs & Cast node | "4 units · LOOK + LOOK-STATE gates" |
| `architecture/README.md` | Departments rows refs/episode; Decisions row 2026-10-10; Plans row | added in the same commit; republish the claude.ai copy |

A proposal goes to the *Future* tab (commit 0). On build, the *Current* tab is updated and the slot flips
to built (commit 18).

---

## 11. Time against the 6 h ceiling

The median of ep19-27 is about 6.0 h, so it already sits at the ceiling. The numbers:

| item | per episode, typical | worst realistic | basis |
|---|---|---|---|
| New looks (0-2 typical, 3 worst) × (draw about 60 s + judge 30 s + p 0.3 reroll) | +2-4 min | +8 min | `pack.jsonl` median 60.2 s (C §5); Krea2 already resident in step 03 |
| Place variants/sides (0-2) × (2511 4-step about 20 s + `picture_read` about 15 s) + one model swap | +2-3 min | +5 min | D §5 estimates; this **replaces** fresh place draws measured at 60-370 s per episode, so the net is about 0 |
| Plan gates | seconds | seconds | code only |
| G-LOOK-PANEL (4 more fields in the existing read, VL resident) | +1 min | +2 min | 25 panels × 2-4 s |
| G-LOOK-TAKE (frames already decoded) | +1 min | +2 min | 25 takes × 2-3 s |
| Extra retakes caught (each also prevents a wrong take shipping) | +0-5 min | +10 min | 1-4 takes × 2.5 min (E §4), within `ROUNDS_CAP` 2 |
| **Total** | **+5-12 min (1.5-3 %)** | **+25 min** | |

One-time costs per new book:
- the production designer call, about 1 min;
- masters, drawn just-in-time as today.

Looks and variants are reused across episodes: the narrator's 10 looks are built once over 27 episodes,
not per episode. P1 does not claim to pay for itself. The minutes come from the speed lane (F #1 Sage,
about −10-15 min; F #4 LoRA recipe, about −17 min; G #2 grid turbo, about −12 min), and the existing
terminal-at-ceiling clock (five-hour build) still bounds the worst case.

---

## 12. Migration

- **WotW: none.** No shipped episode is re-rendered, and with no `refs/looks.json` the book runs the
  legacy path with an audit row. Its dossiers and the 17 house pictures are reused only as **bench
  fixtures**, for calibration.
- **The next book** gets `looks.json` (from `looks_from_dossier`, commit 2) and `places.json`
  (production designer, commit 7) at refs/01. Its first episode is the proof run. The plan is judged on
  the LOOK-STATE and G-PLACE-FIXED verdicts plus the owner's audit sheet, and is not counted done on
  green gates alone (memory `gates-are-not-quality`).

---

## 13. Publishable (standing goal)

"A continuity bible for serialized generative video" generalizes beyond this repo. It has three parts:
- the typed look and place tables (a script supervisor's breakdown as a contract);
- the star-topology derivation rule;
- the two list-then-judge verifiers (markers + relative identity; fixed-feature GeomCons).

It could ship as a standalone package or ComfyUI node, with a benchmark of cross-episode look and place
agreement on a real 27-episode series that has owner verdicts. Neither C nor D found a public benchmark
of this kind.
