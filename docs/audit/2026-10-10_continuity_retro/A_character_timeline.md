# A: Character look timeline. Why the late War of the Worlds episodes look like episode 1

Investigator A, 2026-10-10. Read-only: no code changed, nothing rendered, nothing spent.
Book: `library/20260827135508_the-war-of-the-worlds` (written `<book>` below). Episode n is chapter n.

Evidence strips are in `docs/audit/2026-10-10_continuity_retro/A_evidence/`. Each row shows three
frames: storyboard panel, take at 2 s, take last frame. The scripts that made them are in the same folder.

---

## 0. Short answer

1. **The book already has a look timeline, and the pipeline reads it as words only.**
   `analysis/characters/<id>.json → profile.wardrobe` lists the named looks, and
   `profile.wardrobe_by_chapter` says which look each chapter uses. The narrator has 10 looks.
   `studio/pack_refs.py:character_row` turns the chapter's look into **text**, which reaches every
   grid and take prompt (verified on all 27 episodes, §2). The **picture** never changes: every
   character has ONE sheet (`refs/characters/<id>/sheet.png`, plus its crop `sheet_front.png`). That
   sheet is drawn in the character's **first** look. For the narrator that is the clean mid-grey suit,
   straw boater, dark hair, moustache and shaven chin.
2. **When the words and the sheet disagree, the sheet wins in a large share of panels, and it wins hardest on the face.**
   Clothes-only changes mostly survive: soaked in ep10, scalded in ep13, flannel shirt in ep20, and
   the wife's mourning dress in ep26. Face and hair changes mostly lose: the grey hair and 16-day beard
   in ep22-25, and the ash-grey hair in ep26-27. Full-figure standing shots also tend to copy the sheet
   outright: suit, boater, pose and all.
3. **No gate looks for it.** `panel_content.json` listed "man in suit", "straw hat" and "tie" for ep18
   shot 0, a chapter-18 panel where he should be in the found flannel shirt, and passed it. No gate
   compares a panel's clothes or face with the chapter's look.
4. **The take step adds a second fault.** Every take stages the clean `sheet_front.png` as
   `<Picture 1>`, and the retention line orders H3 to keep "the face, hair, build **and clothes** of
   <Picture 1>". H3 gets three conflicting inputs: a clean sheet, a ragged text row, and a panel that is
   sometimes clean and sometimes ragged. You can see the result: **the costume changes mid-take**
   (ep18 T0, ep24 T0, ep25 T0).
5. **The early episodes were not built differently on this axis. They were spared by the story.**
   In chapters 1-9 the narrator is in `day_suit` (or the hatless version of it in ch 7), which is
   exactly the sheet. So the sheet and the words agreed. The conflict starts at ch 10 and grows. The
   face changes arrive in ch 22, by which point the run was fully unattended (autopilot from ep15,
   `sheet_front` crop from ep16).

---

## 1. Book timeline: the narrator and the recurring cast

Sources:
- the chapter text, `<book>/source/chapters/ch_NN.json`;
- the dossier, `<book>/analysis/characters/unnamed_first_person_narrator.json`:
  `profile.physical_evolution`, `profile.wardrobe`, `profile.wardrobe_by_chapter`, `profile.design.book_evidence`.

### 1a. The narrator

| ch / ep | Book state (dress / dirt / wounds / hair / hunger) | Text evidence | Dossier look (`wardrobe_by_chapter`) |
|---|---|---|---|
| 1-6 | Settled civilian, clean day clothes | ch1 "busy upon a series of papers" | `day_suit` (= the sheet) |
| 7 | Fled the heat-ray: hat lost, collar burst, haggard | ch7 "My hat had gone, and my collar had burst away from its fastener." / "so haggard was I" | `flight_hatless` |
| 8-9 | Home again, re-dressed; flees with his wife by dog-cart | — | `day_suit` |
| 10 | Thrown from the dog-cart into a pool in the storm; soaked, muddy, grazed | physical_evolution ch10 | `storm_soaked` |
| 11 | Changes clothes; face blackened and haggard | ch11 "then I was moved to change my clothes" / "his face, blackened and haggard, as no doubt mine was also" | `second_suit_night` |
| 12 | Scalded by the boiling wave at Shepperton | ch12 "scalded, half blinded, agonised" | `second_suit` (the scald comes at the END of ch12) |
| 13-15 | Half-naked: only soaked trousers and socks; scalded; smoke-blackened | ch13 "naked, save for my water-soaked trousers and socks, scalded, and my face and shoulders blackened by the smoke"; ch15 "my scalded hands" | `scalded_halfnaked` |
| 16-17 | Not on screen (the brother's chapters) | — | — |
| 18 | Takes a found hat and flannel shirt; burns oiled and bound in rags; bruised temple from the collapse; very hungry | ch18 "oil and rags for my burns ... a hat and a flannel shirt"; "A bruise on my temple asserted itself."; "very hungry" | `flannel_buried` |
| 19-21 | Buried in the ruined house with the curate; plaster dust; starving (2 weeks) | ch20 "between starvation and a still more terrible death"; ch21 "I weary but resolute" | `flannel_buried` |
| 22 | Comes out after ~15 days: gaunt, bearded, hair gone grey (the hair is noticed in ch24) | physical_evolution ch22; ch22 "the hunger of my long and dismal fast" (ch23) | `ragged_greyed` |
| 23 | Wanders and forages; still starving | ch23 "my dominant motive became the hunger of my long and dismal fast" | `ragged_greyed` |
| 24 | Meets the artilleryman, who sees him as filthy, slender and grey | ch24 "clothes as dusty and filthy as my own"; "your hair is grey"; "You're slender." | `ragged_greyed` |
| 25 | Dead London: weary, footsore, hungry, thirsty | ch25 "intensely weary, footsore, and now again hungry and thirsty" | `ragged_greyed` |
| 26 | **Two states in one chapter.** First found wandering, weeping and raving (still ragged); then 4 days nursed by strangers; then home in borrowed clothes | physical_evolution ch26 | `borrowed_suit` **for the whole chapter**, so the chapter granularity is wrong for its opening |
| 27 | Epilogue: home, writing; grey hair and scars stay | — | `epilogue_home` (the day suit again + ash-grey hair + temple scar) |

### 1b. The other recurring characters

All from `profile.wardrobe_by_chapter` in each dossier. The sheet is drawn in the FIRST look in every case.

| Character | Chapters | Looks over time | Sheet shows |
|---|---|---|---|
| curate | 13, 15, 18-21 | `shirtsleeves_sooted` (13-15) → `scalded_hand` (18) → `buried_bandaged` (19-21): blood-darkened strip round the forehead, collar sprung, plaster dust | `shirtsleeves_sooted` |
| artilleryman | 11, 12, 18, 24 | `rha_hatless` (RHA jacket) → `putney_feral` (24): civilian waistcoat, ditch slime, cut on the chin | `rha_hatless` (`sheet.png` 2026-09-24) |
| wife | 1, 7, 9, 10, 26, 27 | `summer_evening` → `house_dress` → `summerhouse_travel` → `mourning_reunion` (26) → `summer_evening` (27) | `summer_evening` |
| brother | 14, 16, 17 | `student_london` → `flight_injured` (16: split lip, bound wrist) → `coast_steamer` | `student_london` |
| Miss / Mrs Elphinstone | 16, 17 | clean → dust-grimed | clean |
| Ogilvy | 1-6 | observatory → dawn → pit suit → shirtsleeves | 3-piece suit |
| Martians | 1-27 | on_mars → emerging_wet → hood_pilot → pit_worker → dying_rotting (25) → museum_specimen (27) | emerging_wet |

---

## 2. What was staged in each episode, and what the prompts said

Method: I scanned every `episodes/epNN/takes/r2v/T*.graph.json` (the LoadImage inputs and the H3
prompt) and every `episodes/epNN/storyboard/grids/*.txt` (the grid prompt) for markers that
identify each narrator look. Script: `A_evidence/scan_wardrobe_text.py`.

Some markers are ambiguous:
- "herringbone" also matches the brother's Norfolk jacket (ep14, ep16, ep17);
- "beard" also matches Ogilvy and Stent (ep01-04);
- "flannel" in ep02-04 is other cast.

| ep | Authoring | Picture staged for a character | Narrator look in the prompts | Look in the frames (sampled) |
|---|---|---|---|---|
| 01-04 | hand-written `plan.py`, no storyboard, takes from refs | whole `sheet.png` + place wide | day_suit | ep05 strip: day suit, consistent. **Sheet = story.** |
| 05-08 | hand-written `plan.py`, H3-drawn panels | `sheet.png` + panel | day_suit; ep07 `flight_hatless` (11 takes) | consistent (ep05 strip) |
| 09-13 | hand-written `plan.py`, Qwen grids (whole sheet staged) | `sheet.png` | ep10 `storm_soaked` 6 grids / 8 takes; ep11-12 `second_suit`; ep13 `scalded_halfnaked` 6 / 6 | **ep10: soaked dark suit in all 6 sampled; ep13: shirtless and sooted in all 6 sampled.** The text won, because these are clothes-only changes |
| 14 | `plan.py` + first `drive.jsonl` | `sheet.png` | brother's chapter | — |
| 15 | episode_writer agent + drive (autopilot) | `sheet.png` | `scalded_halfnaked` 3 grids / 6 takes | not sampled |
| 16-17 | agent + drive; **`sheet_front.png` crop** in grids and takes from 2026-10-02 (`7ad14e6`) | `sheet_front.png` | brother / Elphinstones | — |
| 18 | agent + drive | `sheet_front.png` (+ sheet) | `flannel_buried` 8 / 9 grids, 15 takes | **4 of 6 sampled panels (T0, T4, T13, T16) are the sheet itself: grey suit, boater, standing front-on.** H3 then changes him into a white shirt within 2 s (T0, T4, T13, T16), so the costume changes on screen |
| 19-21 | agent + drive | `sheet_front.png` | `flannel_buried` | ep20 contact: flannel shirt + felt hat held, but clean, groomed, well-fed. No plaster, bruise, burn rags or hunger |
| 22 | agent + drive | `sheet_front.png` | `ragged_greyed` 8 / 9 grids, 13 takes | T2: no beard. T5 panel: **the clean sheet suit + boater**; the take turns it into a bearded ragged man. T17: suit jacket + boater over the torn shirt. T20: correct |
| 23 | agent + drive | `sheet_front.png` | `ragged_greyed` 11 / 12 grids | not sampled |
| 24 | agent + drive | `sheet_front.png` | `ragged_greyed` 9 / 11 grids, 13 takes | T0 panel: **clean sheet suit + boater**; the take changes it to a striped shirt + felt hat by 2 s. T13 (cellar): clean-shaven, dark-haired. Bower grid 2x1_b: correct |
| 25 | agent + drive | `sheet_front.png` (+ `sheet.png`) | `ragged_greyed` 13 / 14 grids, 20 takes | contact sheet, 20 narrator panels: **4 are the clean sheet (0, 8, 11, 14)**; boater in 7 (0, 1, 2, 5, 8, 11, 13); beard only in about 8. T0 take: suit becomes shirt and braces mid-take |
| 26 | agent + drive | `sheet_front.png` | `borrowed_suit` (8 grids) | contact sheet: **almost every panel is the ep01 sheet** (mid-grey herringbone, boater, dark hair), including the boater in bed (#3). Grey hair in 1 panel (#0). The opening ragged state was never in the plan |
| 27 | agent + drive | `sheet_front.png` | `epilogue_home` (ash-grey hair, temple scar) | contact sheet: dark hair in every narrator panel; ash-grey hair 0 of about 10; boater worn indoors at the desk (#3, #12, #24). **Indistinguishable from ep01** |

Other characters, from the samples:
- The **wife's** `mourning_reunion` reached the ep26 frames (black dress, clothes only).
- The **artilleryman's** `putney_feral` reached ep24 (waistcoat, slime).
- The **curate's** `buried_bandaged` forehead strip comes and goes within ep20 (panels 18-19 have it; 0, 1, 4, 5 and 26 do not).

Frames I looked at:
- `A_evidence/strip_ep05.png`, `strip_ep10.png`, `strip_ep13.png`, `strip_ep18.png`,
  `strip_ep22.png`, `strip_ep24.png`, `strip_ep25.png`;
- `<book>/episodes/ep20/storyboard/contact.png`, `ep25/storyboard/contact.png`,
  `ep26/storyboard/contact.png`, `ep27/storyboard/contact.png`;
- `<book>/episodes/ep24/storyboard/grids/ep24_grid_bower_morning_2x1_b.png` (a correct one);
- `<book>/refs/characters/unnamed_first_person_narrator/sheet_front.png`.

Example prompt, ep25 T05 (`<book>/episodes/ep25/takes/r2v/T05.graph.json`). It contradicts itself inside one subject line:

```
<Subject 1> is the Narrator in <Picture 1>: ... Dark brown hair cut short ... combed smooth.
Neat close-trimmed dark brown moustache; shaven cheeks and chin. Wearing: Cream-and-blue striped
flannel shirt torn ... Hair turned ash-grey throughout ...; sixteen days of grey-brown beard; face gaunt
...
<Subject 1> ...: partially_preserved - the face, hair, build and clothes of <Picture 1> carry into every shot
```

Here `<Picture 1>` is `sheet_front.png`: the clean suit, boater and dark hair.

---

## 3. Early vs late: what changed

| Axis | ep01-13 | ep14/15-27 | Evidence |
|---|---|---|---|
| **Story state vs sheet** | sheet = story (ch 1-9 day_suit); ch10 and ch13 are clothes-only changes | face, hair and hat changes from ch18 (found hat), ch22 (grey hair, beard), ch26-27 (grey hair) | §1, `wardrobe_by_chapter` |
| Plan authoring | hand-written `plan.py` in the session, every strip looked at by the author | `agents/episode_writer.py` (no wardrobe or continuity instruction: grep finds no "wardrobe") driven by `scripts/episode/drive.py`, later `autopilot.py`; judges sign | `plan.py` exists for ep01-14 only; `drive.jsonl` from ep14 |
| Picture staged | whole turnaround `sheet.png` | `sheet_front.png`, a one-figure full-body front crop, in grids AND takes | `7ad14e6` (2026-10-02, grids), `FRONT_SHEETS` in `scripts/episode/takes_r2v.py:211` (A/B on ep16 T11 / T25) |
| Panel gate | (none before ep09) | `panel_content` lists subjects and checks people count, lookalikes, hour, landform and text. **It never checks clothes or face against the chapter's look** | `ep18/storyboard/panel_content.json` shot 0: "man in suit", "straw hat", passed |
| Skill rule | "One sheet per character … states come from the take's camera and words, never from edited pictures" (owner 2026-09-18, refs-only mode) | unchanged | `.claude/skills/episode/SKILL.md:283-285`; `SCARLET_ARCHIVE.md:28-34` |
| Skill rule hazard | — | "When the words and the picture disagree and the book is silent, make the words match the picture." The book is NOT silent about grey hair, but an agent reading this reaches for the sheet | `SKILL.md:290-291` |

**Guess, marked as one.** The `sheet_front` crop makes full-figure panels copy the sheet's costume
and pose more often than the whole turnaround did. The correlation is there: ep10 and ep13 obeyed
the text with the whole sheet; ep18, ep22 and ep25 copied the clean figure verbatim in standing
full-figure panels with the crop. But the state gap is also larger in those chapters, so the two
causes are confounded. An A/B would settle it: the same ep25 grid, same seed, whole sheet vs crop
vs no sheet.

A lesson the project already learned and lost: commit `8c28bf6` (2026-09-14, Scarlet), **"R5: a
wardrobe promise needs a picture"**. A wardrobe line with no state card falls through to a picture
that contradicts it. The Scarlet code still has the per-state card hook (§4). The WotW "one picture
per entity" ruling of 2026-09-18 bypassed it.

---

## 4. Where the character picture is chosen, and where a timeline plugs in

| Location | What it does today |
|---|---|
| `studio/pack_refs.py:125` `wardrobe_state(by_chapter, chapter)` | Picks the chapter's look id. A chapter with no entry keeps the last earlier one. **This is the timeline lookup, and it already exists.** |
| `studio/pack_refs.py:131` `character_row` | `physical` = invariant body + "Wearing: <look text>". The body still says "dark brown hair … shaven cheeks and chin", so a hair or beard look contradicts it in the same sentence. Writes `rel_path: refs/characters/<id>/sheet.png`, always the same picture. |
| `studio/pack_refs.py:309` `rows_for` → `scripts/refs/cast_rows.py:39` | Rewrites `<book>/refs/refs.json` for ONE chapter. `refs.json` is a single mutable snapshot: it is now stamped `chapter: 27`, and its `note` still says "episode 1 cast only … chapter 1 wardrobe". Re-rendering an older episode needs `cast_rows` re-run first (`cast_refs.chapter_refusal` guards this). |
| `studio/pack_refs.py:97` `character_sheet` | `refs/characters/<id>/sheet.png`; no state. |
| `scripts/episode/grids.py:152` `sheet_of` | Grid slot = `front_of(refs/characters/<id>/sheet.png)`. **Hard-coded; no chapter and no look.** |
| `scripts/episode/grids.py:175` `cast_of` | The grid text = `row["physical"]` (the chapter's look, in words). |
| `studio/episode_seq_board.py:45` `cast_sheet(book, who, setup, state)` | The take slot. It already tries `refs/characters/char-<who>_<state>.png` FIRST (Scarlet's per-state card), then the per-setup card, then `sheet.png`. In WotW `state` is `Setup.state` = "indoor" / "outdoor", not a story look. |
| `scripts/episode/takes_r2v.py:219` `one_figure` / `:232` `reference_list` | Swaps in `sheet_front.png`. |
| `studio/episode_ref_official.py:633` `retention` | "the face, hair, build **and clothes** of <Picture k> carry into every shot". This tells H3 to copy the clean sheet's clothes. |
| `studio/cast_refs.py:101` `cast_sheets(book, who, state)` | Scarlet's bust + per-state card pair. Unused by WotW. |

**How a time-varying look could plug in.** This is a design sketch, not done.

1. **Key a picture by look id, not by character.** Add
   `refs/characters/<id>/looks/<look_id>.png`, one per `profile.wardrobe` key actually used, drawn
   just-in-time when the first episode needs that look. Draw each one from the master sheet's face
   with the look's text, so identity carries over.
2. **Resolve the picture through the one function that already knows the time.** A new
   `pack_refs.look_sheet(book, who, chapter)` returns `looks/<wardrobe_state(...)>.png`, falling
   back to `sheet.png`. Call it from:
   - `grids.sheet_of`, by passing the chapter it already has via `chapter_refusal`;
   - `takes_r2v.reference_list`, via `cast_sheet`'s existing state rung.
3. **Split `physical` into an invariant body plus a per-look head.** Hair colour, facial hair and
   gauntness belong to the look, not the body (`character_row`). That removes the
   "dark brown … shaven" vs "grey … beard" contradiction.
4. **Allow scene granularity.** Let `wardrobe_by_chapter` take `"26": [{"until_shot"|"scene": …, "look": "ragged_greyed"}, …]`
   or a per-setup `look` field in the plan, because ch26 (and ch7, ch12, ch18) change look within the chapter.
5. **Retention line:** for a person with a look picture, say "face and build of <Picture k>; the
   clothes this shot's words and its first frame give". Do not say "clothes of <Picture k>" when
   <Picture k> is a different look.
6. **Gate (G-LOOK):** in the panel content check, ask the VLM for the person's hat, top garment,
   hair colour and facial hair, then compare in code with the look's markers, the same list-then-judge
   pattern as `panel_content`. That would have refused ep18 shot 0, ep25 shots 0, 8, 11 and 14, and
   most of ep26-27.

This needs an owner ruling. It reverses the 2026-09-18 "one picture per entity / states in words"
rule (memory `feedback_one_sheet_per_character`) for **story-time looks**. Places and props are unaffected.

---

## 5. Root causes, ranked

1. **One picture per character; the story-time look is words only.** The sheet is the first look,
   and image models weight a staged picture over words, especially for face and hair. Evidence:
   ep26-27 are 0-1 of about 24 panels with grey hair; ep25 has 4 of 20 panels as the verbatim sheet.
   (`pack_refs.character_sheet`, `grids.sheet_of`, `SKILL.md:283`.)
2. **No gate measures the look against the chapter.** Wrong-look panels pass `panel_content` and go
   to H3 (`ep18/storyboard/panel_content.json`).
3. **The take prompt orders H3 to copy the sheet's clothes** (`episode_ref_official.py:633`) while
   the subject text gives a different look. This produces costume changes mid-take: ep18 T0, ep24 T0,
   ep25 T0.
4. **The row text contradicts itself.** The invariant body (dark hair, shaven) plus a look with grey
   hair and a beard (`pack_refs.character_row`) means the model gets both.
5. **The timeline is per chapter only.** It cannot express ch26 (ragged → nursed → borrowed suit),
   and the dossier gave the epilogue the original suit, so ep27 is ep01 by design except for the
   hair, which is lost.
6. **Unattended authoring from ep15.** No in-session eye on strips, and the writer agent has no
   continuity instruction. This is an amplifier, not the cause: hand-authored ep10 and ep13 worked
   because their changes were clothes-only.
7. *(Guess)* **The `sheet_front` full-figure crop (2026-10-02) increases verbatim copying of the
   sheet costume in full-figure panels.** It is confounded with cause 1; it needs the A/B in §3.

Side findings, outside the brief:
- White gutter slivers left in cut panels: ep20 #7, #9, #15; ep25 #9; ep27 #10, #16; ep22 T5, T9.
- A neon "NORTH" sign invented in ep22 T2's last frame.
- ep18 T0's narrator vanishes by the last frame.
