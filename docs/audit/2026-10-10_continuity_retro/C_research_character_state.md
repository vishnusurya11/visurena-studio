# C. Character state over a serial: research and a recommended approach

Researcher C, 2026-10-10. Question: a 27-episode adaptation holds a character's
identity with one reference sheet, but the character's state changes over the
story (clean, dusty, torn coat, wound, beard, starvation). The models copy the
sheet's clothes, so late episodes show the episode-1 outfit. The owner now wants
per-state sheets on a timeline. Any new generation has to fit inside the 6 h
per-episode machine budget (current median about 6.0 h).

Evidence grades used below:
- **[P]** primary: a paper, a model card, or a measurement in this repo.
- **[V]** vendor or practitioner write-up. Treat as a heuristic, not a measurement.
- **[I]** my own inference. Untested here.

---

## 0. The brick

**A character's look is the base identity plus the cumulative set of deltas
active at that story moment. Every take must get the look in pixels, because
the video model copies pixels and ignores words that contradict them.**

- Base case: look `L0` is the identity sheet.
- Recursive rule: `L(n) = L0 + every delta whose story interval contains n`.
- Closure claim: one look table, plus one picture per distinct look, gives the
  correct reference for every setup in every episode.

The next level down is why words alone failed here. Section 3 covers it in full.
In short: a reference-conditioned model treats the reference image as
authoritative and the prose as secondary. This repo has measured the same
behaviour in H3: it ignores clauses that ask for something the cell does not
show.

---

## 1. How film and TV continuity tracks state (the data model to copy)

**What the industry does**
- **Story days, not scenes, are the clock.** The AD numbers script days in story
  order. Days with no scenes are skipped, and flashbacks and dreams are X-days
  (X1, X2, ...). Script days "are also the basis for all make-up and costume
  changes", for example "the development of wounds" between two script days.
  [V] https://yamdu.com/en/learn/preproduction/script-days-and-scene-days/
  Same concept, with "Day 1 / Night 1" marking:
  [V] https://studiobinder.com/blog/how-to-mark-story-days
- **Who records it.** The script supervisor's pre-production breakdown records
  "key scripted information about each scene that may impact continuity such as
  costume, make-up or props" and shares it with the heads of department.
  [P] ScreenSkills job description:
  https://www.screenskills.com/media/7610/final-jd-script-supervisor-110523.pdf
  The textbook layout (Continuity Synopsis / One-Liner, Wardrobe Outline, scene
  breakdown):
  [P] Rowlands, *The Continuity Supervisor*, 4th ed., ch. 12 "Scene Breakdown":
  https://oreilly.com/library/view/continuity-supervisor-4th/9780240516134/19_chapter12.html
- **The costume department's two views.** The *costume plot* is a grid with
  characters across and scene/page down. It logs each look by layer: core
  garment, layering pieces, footwear, accessories. It also flags quick changes.
  [V] https://stageagent.com/resources/templates/costume-plot
  [V] https://human.libretexts.org/Bookshelves/Theater_and_Film/Technical_Theatre_Practicum_(Boltz)/01%3A_Chapters/1.08%3A_Costumes
  Film fittings list "all the costumes required for each character ... with the
  scene numbers". Planning splits a scene division (who is in each scene) from a
  character division (each character's changes through the film).
- **Matching is by photograph.** The continuity standard requires "ensuring
  costumes appear as they were at the end of the previous take", and records
  are kept digitally. [P] UK NOS SKSQ13:
  https://www.ukstandards.org.uk/en/nos-finder/SKSQ13/oversee-and-maintain-costume-continuity
- **A caveat I could not close.** In practice each look is numbered per
  character ("Change 3"), but I found no primary text that defines this
  convention. The structure above (story day, then look, then layers) is the
  sourced part.

**Data model to copy, one row per look**

```
looks:                                  # refs.json, per character
  - look_id: narrator.C03               # "change 3", per-character sequence
    from: {episode: 9, setup: S2}       # the story moment it starts (story-day analogue)
    until: {episode: 14, setup: S1}     # open-ended = null
    base: narrator.C00                  # ALWAYS the identity look, never the previous change
    deltas:                             # cumulative, by layer, each a VISIBLE noun phrase
      coat:  "a long rip down the left sleeve of the grey tweed jacket"
      dirt:  "grey ash dust on shoulders, sleeves and trouser knees"
      face:  null                       # face deltas are separate (section 5): beard, wound, gaunt
      props: "no hat"                   # a removal is a delta too
    source_text: "ch.9 p.3: 'my coat was torn...'"   # the book line that justifies it
    sheet: refs/characters/narrator/looks/C03.png
    made_by: fresh | masked_edit        # how the picture was produced, for audit
```

Three rules come from practice:
1. Deltas are **cumulative and layered**. A wound persists until the story heals it.
2. **Every look derives from the base**, never from the previous look. This
   matters for drift (section 2).
3. Each look cites its **book line**, the way a breakdown cites the page.

The episode plan's setups then name a look id. This replaces today's
`Setup.state` in `{indoor, outdoor}`.

**Prior art in this repo.** `studio/cast_refs.py` already built half of this
for the trailer era. It splits the identity **bust** (bare-headed, `physical`
only) from per-state **wardrobe cards** (`cards: {indoor, outdoor}`), and
`cast_sheets(book, who, state)` returns `[bust, card]`, cited inside one
`<Subject>`. It was retired when the owner ruled "one sheet per character"
(`casts_from_sheets`). Widening `STATES` from two fixed states to a per-character
look timeline is an evolution of code that already exists and has tests. It is
not new architecture.

---

## 2. Keeping identity while the costume or state changes

### 2a. Video side: does wardrobe follow the reference or the prompt?

It follows the reference.
- Phantom (ByteDance) observes that a competing model's "first frame of
  character videos almost matches the input reference image, leading to low
  success rates in virtual try-on scenarios". Reference-copying blocks a
  prompt-driven outfit change.
  [P] https://arxiv.org/pdf/2502.11079
- MAGREF balances "the input concept and prompt". It shows following "wearing
  glasses" while keeping identity: an accessory, not a garment swap.
  [P] https://arxiv.org/pdf/2505.23742
- MV-S2V: single-view baselines "only adhere to a single reference view and make
  guesses about other views". Unseen garment sides are invented.
  [P] https://arxiv.org/pdf/2601.17756
- H3 guidance: "Referencing clothing is not the same as verified garment
  transfer". Its advice is to "state which reference controls identity,
  clothing, composition...".
  [V] https://minimaxh3.run/minimax-h3-reference-to-video
- A MiniMax subject-reference write-up: "Writing 'wearing a red jacket' in the
  prompt may not override the reference image". The reliable route is a
  reference already wearing the target outfit.
  [V] https://www.eachlabs.ai/minimax/sv2/minimax-s2v-01
- This repo's own measurement agrees. H3 obeys what is in the cell and the
  camera verb's direction, and ignores absences and contradicting clauses
  (memory `h3-obeys-direction-not-amount`, ep05-ep10). The 2026-09-18 rule said
  "states come from `profile.wardrobe[state]` in the take prompt". That rule is
  the exact mechanism that failed. [P, in-house]

**Conclusion:** the state must reach H3 **and the Qwen-Image grid** as pixels.
The grid matters as much as the take. If the grid is drawn from the base sheet,
the panel shows the clean outfit and H3 copies the panel.

### 2b. Practitioner consensus: one sheet per look

Practitioners converge on one sheet per visible look.
- "Build one sheet per visual beat". Treat "costume swaps, prop pickups,
  injuries, and age jumps" as separate sheet events. "If a continuity error
  shows up later, fix the sheet, not the shot."
  [V] https://invideo.io/faq/what-is-the-per-beat-character-sheet-method-for-ai/
  [V] https://invideo.io/faq/why-do-you-need-a-new-character-reference-sheet-every/
- Kling's Character ID "assumes the character doesn't change". Seedance guides
  recommend a separate full-body wardrobe image plus a detail crop alongside the
  identity portrait. [V] https://kinovi.ai/en/blogs/seedance-2-5-character-consistency-ai-video ,
  https://www.kapwing.com/resources/how-to-create-consistent-ai-characters-with-seedance-2-0/
- These sources describe fresh generations per look. None of them prescribes
  edits.

### 2c. Deriving a look: edit the base sheet, or render fresh?

**Evidence on edit drift**
- **Drift compounds when edits are chained.**
  - FLUX.1 Kontext §4.3: under existing methods "characters lose identity and
    objects lose defining features with each edit". This is measured as AuraFace
    cosine against the input over successive edits. Kontext drifts slowest, and
    artifacts appear after about 6 iterative edits (Limitations, Fig. 15).
    [P] https://arxiv.org/abs/2506.15742
  - Persistent Identity benchmark (2026): identity similarity after four chained
    edits fell from 0.71 to 0.53 (gpt-image-2) and from 0.65 to 0.50 (NB2). An
    identity-layer method held 0.79 to 0.70.
    [P] https://arxiv.org/html/2609.04151
  - **So: derive every look from the base, never from the previous look.** A
    torn-and-dusty look is one edit of `C00`, not an edit of the dusty look.
    Each look is then always exactly one edit from ground truth.
- **A single unmasked edit still nudges the face.** Qwen-Image-Edit regenerates
  the whole image. "Plain Qwen edit regenerates the whole image, which means
  small drift, usually in the face". The fix is a mask, so unchanged pixels are
  pasted back. Lightning or distilled builds are reported as "much less
  faithful".
  [V] https://hackernoon.com/the-image-editor-that-finally-stops-face-drift-inside-qwen-image-edit-2511 ,
  https://www.runcomfy.com/trainer/ai-toolkit/qwen-image-edit-2511-likeness-custom-lora
  Separately, ComfyUI's stock resize shifted edits by about 8 px. Native-size
  ReferenceLatent brought that to about 1 px.
  [V] https://lilting.ch/en/articles/qwen-image-2-1-edit-pixel-perfect-output-resolution
- **Vendor claims for 2511.** Qwen-Image-Edit-2511 claims improved character
  consistency, "mitigate image drift", and clothing edits that keep identity.
  These are claims, not benchmarks.
  [P/V] https://huggingface.co/Qwen/Qwen-Image-Edit-2511 ,
  https://replicate.com/qwen/qwen-image-edit-2511

**Evidence on fresh-render drift (this repo)**
- Fresh Krea2 sheets of the *same row* have already varied. The 'one picture
  per entity' rule exists because separately drawn views became different
  rooms. Ep07/ep16 lessons show sheets drawn from words drop details (moustache,
  counts).
- A fresh render re-rolls the face. Holding the seed and the identity block
  constant reduces the variation but does not remove it. [I] No measurement in
  the repo isolates "same seed, different wardrobe words" on Krea2.

**Weighing this against the owner's rulings**

The owner's ban was on **compositing characters into plates or frames**.
1. Bowler swapped onto Holmes. That was a multi-person placement.
2. A composed frame zero. That was characters in a room.
3. Derived **location** views. Those became different rooms.

A **single-subject, masked, garment-only edit of that same character's own sheet**
is a different operation:
- There is no second person to bleed wardrobe from. The wardrobe swap was a
  cross-subject attention leak.
- The face pixels are not regenerated at all, because they are pasted back
  under the mask. Identity drift on the face is then zero by construction, the
  strongest guarantee any method here offers.
- Style holds when the same model does the inpaint (Krea2 + LoRA).

The edit is still a reversal of the letter of "never edited pictures" (SKILL.md
§Pictures). **It needs an explicit owner ruling.** Recommend asking it as one
question, with section 6's A/B as the evidence.

**Face-changing states are different.** Beard growth, starvation and a facial
wound must change the face, so the mask must include it, and every source above
says the face is what drifts. For these, the choice is:
- a masked edit over the face region with an identity check after it, or
- a fresh render of the full row with the delta written first.

**Identity-locking adapters (IP-Adapter / PuLID / InstantID).** PuLID-FLUX
trades identity against editability through the ID-insertion timestep: 0-1
gives more identity and less editability, 4 gives more editability. It also
offers an attention mask to confine the ID.
[V] https://replicate.com/bytedance/flux-pulid/readme
They are built for Flux/SDXL photo faces, not the Krea2 + Cinematic LoRA
painted style, and none is installed here. [I] Not recommended. It adds a model
and a style risk to solve a problem the masked edit solves for free on garments.

---

## 3. Prompt-level technique: wording state so a ref2v model obeys it

1. **Never let words contradict the reference.** Words that contradict pixels
   are dropped. This is measured in-house and matches the Phantom and S2V
   evidence. The take prompt must describe *the state the staged sheet shows*,
   in the same words as the look row.
   - This is the house rule "when the words and the picture disagree ... make
     the words match the picture" (SKILL.md), extended to looks.
2. **Assign roles to the slots.** Image 1 is identity (bust or sheet). Image 2
   is the look card: "<Subject 1> wears exactly the clothes in Picture 2". This
   is the H3 guidance ("state which reference controls identity, clothing"),
   and `cast_refs.cast_sheets` already orders the slots this way.
   [V] https://minimaxh3.run/minimax-h3-reference-to-video
3. **State as visible nouns, put first.** Write "a long rip down the left sleeve;
   grey ash dust on both shoulders". Avoid adjectives or amounts ("somewhat
   dishevelled", "dustier than before").
   - This repo measured that H3 ignores amounts, and that a detail buried
     mid-sentence is dropped from a sheet (SKILL.md: Snippy's moustache, the
     lawn fire).
   - Seedance guides say the same: keep outfit descriptors identical across
     shots and avoid fine patterns that destabilise in motion.
     [V] https://kinovi.ai/en/blogs/seedance-2-5-character-consistency-ai-video
4. **Removals are pictures, not negations.** "No hat" is an absence, and H3
   ignores absences. The look card must simply show him bare-headed.
5. **Slot budget.** H3 ref8 has 8 slots, and today's `MAX_FACES = 2` assumes 2
   pictures per face. A look card costs nothing extra if it *replaces* the base
   sheet, which is the recommended shape: one sheet per look, not bust + card.
   It costs a slot if it is added beside it. [P, `studio/cast_refs.py`]

---

## 4. Verification: did the state reach the frame?

- **Decompose into atomic yes/no questions.** Davidsonian Scene Graph (DSG, ICLR
  2024) generates "atomic and unique questions organized in dependency graphs"
  and avoids the duplicated or ambiguous questions that make QG/A scores
  unreliable. It also notes some categories exceed current VQA models.
  [P] https://arxiv.org/abs/2310.18235
  - One question per delta, with a dependency: "Is a man visible?" → "Is his left
    sleeve torn?" → "Is there dust on his shoulders?".
- **Video has a named failure class.** T2V-CompBench (CVPR 2025) separates
  *consistent* attribute binding (an attribute held for the whole clip) from
  *dynamic* binding. It scores them with MLLM, detection and tracking metrics
  validated against human judgment.
  [P] https://arxiv.org/html/2407.14505v2
  - Ours is the consistent case: the look must hold on every sampled frame, not
    only frame 0.
- **House pattern to reuse.** `panel_content` already asks the VLM to *list*,
  then judges in code (memory `content-dq-reads-the-picture`). Keep that order
  to avoid yes-bias. First "describe this man's clothing and its condition",
  then match the listed nouns against the look's deltas in code.
  - Run it at three points: on the **look sheet** (before staging), on the
    **panel**, and on the **take's** first, middle and last frames.
- **The identity check must be relative, not absolute.** `studio/judges/look.py`
  measured identity cosines between DIFFERENT characters at 0.45-0.82 (median
  0.60) on this style. An absolute wall such as EditedID's 0.7
  (https://arxiv.org/abs/2602.18752) would therefore pass strangers. [P, in-house]
  - For a face-changing look, require
    `cos(look, base) > max over other cast members of cos(look, other)` by a
    margin. The look should be nearer its own base than anyone else's sheet.
    That is a test the existing face embedder can run at no new cost.
  - For a garment-only masked edit the face pixels are identical, so the check
    is trivially satisfied and can be skipped.

---

## 5. Cost per look on the 4090, and keeping it to minutes

**Measured or sourced unit costs**

| Item | Cost | Source |
|---|---|---|
| Krea2 + Cinematic LoRA + 2x upscale sheet (3072x2048) | **median 60.2 s**, p90 111 s, n=54 | [P] `library/..._the-war-of-the-worlds/refs/pack.jsonl` |
| Sheet render + VLM read (trailer era, VL cold) | 286 s measured | [P] `docs/analysis/research/trailer-retrospect.md` |
| VL resident, per extra sheet read | 20 s reserved (4 s suspected) | [P] `docs/analysis/research/trailer-render-cycle.md` |
| Qwen-Image-Edit-2511, 4-step, 832x1280, fp8 | 6.1 s on RTX 5090; [I] about 10-15 s on a 4090 | [V] https://huggingface.co/ANXS1/Qwen-Image-Edit-2511-NVFP4 |
| FLUX.1 Kontext edit at 1024² | 3-5 s (datacenter GPU) | [P] arXiv 2506.15742 |

**Per look**

| Path | Render | Look gate (VL resident) | Expected cost incl. one reroll at p≈0.3 |
|---|---|---|---|
| Masked garment edit (same model, face frozen) | about 1 min | about 0.5 min | **about 2 min** |
| Fresh render (face-state looks) | about 1 min | about 0.5 min | **about 2-3 min** |

**Per episode**
- Most episodes introduce 0-2 new looks across the cast. A look persists across
  episodes and is reused, like a costume: it is built once, the first time a
  setup names it.
- Worst realistic case is 3 new looks × 3 min ≈ **10 min, about 3% of the 6 h
  ceiling**.
- The one real risk is a **model swap**. If the edit model is not the one
  already resident, the swap costs minutes. NVMe load times are in
  `five-hour-episode`; VL alone took 214 s per load off the HDD before the NVMe
  move.
- Therefore: build all of an episode's new looks **in one batch at the refs
  step**, before the grid stage loads Qwen-Image. Use the same Krea2 that draws
  sheets, so there is no extra model.

**Just-in-time rule**
- Generate a look only when a setup in the *current* episode names it. This
  follows memory `build-only-what-the-episode-needs`.
- Never pre-render the book's whole timeline. It can be *planned* book-wide (a
  text-only look table from the book), but it is *drawn* per episode.

---

## 6. Recommended approach (concrete)

1. **Write the look table first (spec-driven).** Add a pydantic `Look` model:
   `look_id, from, until, base, deltas{layer: noun phrase}, source_text, sheet,
   made_by`. Give `refs.json` `looks: [...]` per character, and give each plan
   setup `look: <look_id>` (this replaces `Setup.state`).
   - A book-level pass (one LLM call over chapter summaries) proposes the
     timeline: story-day order, cumulative deltas, a book line per delta. The
     plan gate refuses a setup whose look interval does not cover its episode.
2. **Draw each look from the base, never from the previous look, by kind:**
   - **Garment, dirt, prop or removal deltas:** a masked inpaint of the base
     sheet on Krea2 + the same LoRA and seed, face and hair region frozen.
     Identity drift is zero by construction, and the style matches.
     *Needs the owner's ruling* (section 2c). Fallback if he refuses: a fresh
     Krea2 render with the identity block unchanged, the deltas written FIRST,
     and the same seed.
   - **Face deltas** (beard, wound, gaunt, ageing): a fresh render, or a masked
     edit that includes the face. It must pass the relative identity test (§4).
3. **Stage the look, not the base,** in the Qwen-Image grid identity slot AND
   the H3 cast slot. The take and grid prompts quote the look's deltas
   verbatim. Never a word that contradicts the staged picture.
4. **Gate the look three times** with the list-then-judge VLM:
   - the look sheet, before it binds;
   - the panel (does the grid show the state?);
   - the take, at three frames (is it held to the end?).

   A miss on the sheet is a reroll. A miss on the panel or take is a sheet fault
   first ("fix the sheet, not the shot"), never a take retake.
5. **A/B before adopting.** Pick one character in one book with 3 looks, and
   draw each look both ways (masked edit vs fresh). Measure:
   - delta presence (VLM list), on sheet, panel and take;
   - the relative identity margin;
   - style cosine (DINOv3, as `look.py` does);
   - wall seconds.

   About 20 min of GPU. This produces the evidence for the owner's edit ruling.
   [I] Expectation: masked edit wins on identity and time, fresh wins on
   whole-body changes (starvation, posture).

**Time cost:** about 2-3 min per new look, built once and reused. That is 0-10
min per episode, at most about 3% of the 6 h ceiling, with no new model loaded.

**Publishable artifact.** The look table (a script-supervisor breakdown as a
typed contract) plus the three-point list-then-judge verification is a
model-agnostic "continuity bible for serialized AI video". It could ship as a
small standalone package or ComfyUI node with a benchmark: per-delta presence
on sheet, panel and take across a 27-episode book. Flagging it as
generalizable beyond this repo.
