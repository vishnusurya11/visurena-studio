D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\docs\audit\2026-10-10_continuity_retro\bench_evidence\c3\FINAL_before_after.jpg

# The continuity retro, 2026-10-10/11, in one page

**Scope.** A retro and testing pass on WotW and A Study in Scarlet replays only. No new book was started, nothing was published, no shipped file was overwritten, and $0 was spent. It ran as round 0 plus three cycles, each one research, a skeptic verdict, a test-first build and a GPU bench. The reports are `CYCLE_1.md`, `CYCLE_2.md`, `CYCLE_3.md` and `C3_p90_residual.md` in this folder.

**The sheet above** shows shipped | replay under today's code:
1. the narrator's chapter look, re-drawn on the new tile (ep25, ep27);
2. the house as one place;
3. strip grids against 1x1/2x2 grids.

The 3B redraw of every house and seam grid is bit-identical to these replays.

---

## Your complaints

### 1. The narrator's look did not follow the story
- **Root cause.**
  - Every character had ONE sheet, drawn in his first look, and every grid and take staged it.
  - The chapter's look reached the prompts only as words, and the picture won, hardest on the face: the grey hair and beard of ep22-25.
  - No gate compared a panel with the chapter's look.
- **Built.**
  - A look is ONE hop from the base, on a story-time table; a look-timeline writer for every book (`3892664`, `4d6fac0`, `efe4094`, `985aefc`, `42593eb`).
  - The LOOK-STATE judge (`08ebcb0`), with the beard words from the closed marker (`fda4b9f`, `f58cfa1`).
  - The hat family and hat words (`34f16c1`, `6f1dc54`), and the head from the bound row (`4bcd813`).
  - Cycle 3:
    - dossier negations ("gives no … hair") no longer author a head (`aa4085b`);
    - the hair colour is the one next to "hair" (`27ca328`);
    - new looks draw on the neutral tile (`a74e6a5`).
- **Before → after (replays).**
  - ep25 `fulham_road`: shipped 0/1 face-visible panels show the ragged look; the 3B replay shows **1/1** (grey beard, felt hat; LOOK-STATE passed).
  - ep27 `study_table`: **0/3 → 3/3** (ash-grey).
  - Look tables: Scarlet's Watson, Hope, Lestrade and Gregson now get their hair. WotW's Gregg reads red (was bald), and the artilleryman reads dark (was red, from "a red cut across the chin").
- **Open.**
  - Back views cannot show a beard.
  - Stubble wording.
  - Jekyll, Hyde and Utterson are refused ("head unauthored"): their dossiers and rows name no head.

### 2. The house was not one house
- **Root cause.**
  - The house picture WAS passed to every grid (90/90 recovered).
  - But from 2026-09-22 each episode drew its "view" fresh from words: one dining room became 3 rooms, the study 6 or more.
  - From ep07 the takes no longer saw `refs/locations/`.
- **Built.** A place is its master, and a state is one edit of it (`6dce1b8`, `9fe2731`, `e39d3c2`).
- **Before → after.**
  - The ep26 villa, ep27 study reverse, ep11 study and ep11 dining replay as one house.
  - **3B: 8/8 house and seam grids bit-identical to the cycle-1 replay, 0 seams on 15 panels.**
- **Open.** A recurring place must be pinned from its first episode in the next book.

### 3. "Low quality"
- **Root cause.**
  - The pixel chain did not get worse. The picture source changed: Krea2 references in ep01-03, then a Qwen-Image storyboard panel the take copies, all under a 768 canvas.
  - Measured faults on top of that:
    - strip grids seamed two pictures into one cell (18/572, 16 shipped);
    - the 2x tile pass painted ghost faces;
    - a tight size is drawn a size wide.
- **Built.**
  - No strip grids (`a51ecef`); the seam rung, refs-only fallback and seam check (`0f6c92d`, `3ea5461`).
  - CRF 10 takes (`c55daac`).
  - CK8 narration, 39-45 % faster (`06d8ade`).
  - G-FRAME, advisory, calibrated on your episodes (`e97bc9a`, `5385ee4`).
  - The **neutral tile** for new refs draws (`a74e6a5`, comfy_studio `8d7c4f3`).
- **Before → after.**
  - Seams: 0 replayed (was 18/572 in production).
  - Ghost faces: 0 in every tile arm (the today narrator sheet had one), and 0/12 in takes at full 768 px.
  - The neutral tile at 0.15: 0 ghosts, the best head facenet, and colour streaking 0.6-1.5× today's (at 0.2 it was up to 4.7×).
  - G-FRAME 0.15: flags 1/13 of your good MCU panels against 3/6 bad.
- **Open, and a new finding.**
  - **The content gate does not track your judgement.** On your fixtures it refuses **23/28 panels of the good ep05 and 5/27 of the good ep07, and 0 of the bad ep08/ep09**.
  - The refusals are rule and format faults ("hills" on a flat place, figures against a plan that declared none, day light on a night shot). Calibrating those rules on your four episodes is the top open item.
  - Framing has no cure at 95 %.
  - 992: you ruled no.

### 4. Speed: 6 h an episode
- **Root cause.**
  - Renders are not the tail. It is the plan climbs and the relaunches: 22/23 kills were sessions landing a fix mid-episode.
  - The clock was dishonest: 398 machine-min sat in killed steps it never saw, and 67 retries each reset it to a fresh 5 h.
- **Built (cycle 3, test-first):**
  - the run clock (`644a5aa`);
  - no reset (`08f3e58`);
  - at 5 h, firsts render, rungs ship flagged, nothing parks, and only the closed SAFETY list stops an episode (`97be974`);
  - the plan checkpoint (`a303cf2`);
  - QC fail-fast (`bf09d3a`);
  - priced rungs and measured shares (`315ccde`);
  - `pause --at-boundary` (`39ec248`);
  - the downstream reserve and its companion rule (helper: `4931687`, `6f343d3`).
- **Before → after (CPU replay of ep19-27, k-scaled ±10 min):**

| | P50 | P90 | over 6 h |
|---|---|---|---|
| honest baseline | 5.88 h | 7.55 h | 4/9 |
| cycle-3 code + the 5 h rule (rung-only) | 5.10 h | 6.45 h | 2/9 |
| + D3's QC rule, the reserve and the companion rule | 5.10 h | 5.64 h | 1/9 (ep21 6.2 h) |
| + ep21's upload-door cure (434213e, already on master) | **5.10 h** | **5.54 h** | **0/9** |

- **Open.**
  - "Every episode under 6 h" holds only with the door fix counted.
  - What remains is production code faults landing before the crossing. The lever is fixing on the replay set before a series runs, and landing fixes only at a boundary.

### 5. The "indeed … deed" audio
- **Root cause (95 %).** H3 invents audio in the silent tail of the voice guide: S4 "Indeed.", "Heed.", D1 "HAHAHA". Masters strip take audio, so no shipped sound carried it. 2/154 shipped dialogue takes move a mouth in that tail (ep10/T21 "Moving!", ep26/T25).
- **Built.** The INVENTED-SPEECH bench check (`17eab28`). G-TAIL in production: words in a sounding silent tail fail, one reseed, then flagged (`2aeb777`, `7778b97`).
- **Before → after.** The replay over 204 takes fails exactly those 2, exempts the asked-for laugh, and has 0 false fails. CK8 is a measured no for dialogue.
- **Open.**
  - Room tone (inconclusive).
  - Scarlet's dq lag blindness.
  - The two shipped takes stay (your ruling).

---

## Decisions made on your behalf (veto any line)

| # | Decision |
|---|---|
| D1-D2 | The clock is the process; `retry` never resets it. |
| D3 | At 5 h: firsts render, every ladder signs its best flagged, nothing parks. **Only SAFETY stops:** Short length or title card, a line unheard, unjudged or stale takes, loudness after the leveller, a plan BUILDER line, money, publish auth, GPU lost. |
| D4 | A resume on moved code is allowed, from a boundary only. |
| D5 | The ceiling stays 5 h. **Added by the main session: a downstream reserve at your 6 h.** Its price is a panel rescue on light episodes (ep17 would lose 2). |
| D6 | **No confirm-before-refuse.** The reader's seed flip is 0.9 %; the instability is the pixels. |
| D7-D8 | The neutral tile for new refs draws, never the title plate. **Arm (b), denoise 0.15, ships, not the verdict's fallback (a):** no arm met the 1.2× streak clause on the narrator, and (b) beats (a) on every column. |
| D9 | G-FRAME advisory at MCU 0.15 / close 0.25. |
| D10 | Plan rungs priced; shares re-priced. |
| D11 | Retired: H1, H5/H6, H8 for WotW, the merged LoRA, the moved-SHA refusal, H7 (1 bowler look on disk). |
| D12 | The content rules are unchanged. **3B's inversion argues to revisit them with you.** |
| builder | ONE PER TAKE is JUDGED; G-LIGHT, PLAN GATES, MOTION hard and ACTOR are BUILDER (read from the code). The artilleryman look moves red → dark. A paused step closes `deferred`. |

## Found on the way
- **The autopilot was blind** from 2026-10-10 23:24Z: 1,927 `tick_error` events. The book video's `"episode": "compilation"` rows broke `next_unit`. No episode was lost. Fixed in `50a35c8`.
- **Takes are not bit-exact across an engine restart:** 42-45 dB, the same draw by eye. Grids are still bit-exact.
- The full suite hangs in `test_comfy_text.py` while the engine is down.

## Publishable (flag)
- **"The clock you budget against is not the clock you spend"**, with its missing half, **"a ceiling guarantees completion only if it reserves the never-refusable work still owed"**. The measured cases: ep21 crossing 20 min into round 0, and the 3A tables.
- **"Deterministic but not stable":** a seeded, cached VLM judge. 0 % of the instability is from identical inputs and 0.9 % from the seed; the rest is the pixels.
- **"Dossiers that say what they don't say":** 117 of 281 LLM-written character dossiers across 29 public-domain books negate the very feature a parser reads.
- **"The answer already existed":** one kept draft in 40 from the history-free rung.
- **One prompt per tile:** USDU ghost faces, a bit-exact replay, and a cure at denoise 0.15.
- **A gate inverted on its owner's own fixtures:** the content gate against good and bad episodes.

## Still owed
- The claude.ai copy of the architecture page is not republished.
- WotW's series stays paused (complete).
