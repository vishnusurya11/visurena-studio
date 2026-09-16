# Why episodes 8 and 9 look worse than 4–7

Ten read-only reviewers, one dimension each, 2026-09-16. Every number below was
measured on the artefacts on disk (`library/20260822113400_a-study-in-scarlet/episodes/`);
the measurement scripts are in the session scratchpad and the per-dimension reports are
in the session transcript. Baseline = ep04–07 (London). Suspects = ep08 (alkali plain),
ep09 (Utah farm).

## The one-line answer

**The gates measured the wrong things, and the pipeline was tuned to the gates.**
Episode 9 scored 28/28 takes at 100.0 — the best DQ in the series — while its takes
abandon their storyboard in 62 % of frames, its pictures have no black in them, and its
plan is an illustrated synopsis read to a metronome. Nothing in DQ measures palette,
shadow, panel size, face size, mid-take coherence, repetition, or whether the story
lands. It measures freeze, landing, lip-sync and end-frame drift, and all four were fine.

## Ruled out (measured, not guessed)

| suspect | verdict | evidence |
|---|---|---|
| aspect / canvas | not it | ep02–09 are all 1:1, 768×768 takes, 2048×2048 sheets |
| the drawer | not it | same model, size and quality; its 2×2 London work is the best in the series |
| H3 sharpness / noise | not it | ep08/09 first frames are the **sharpest** in the series (Laplacian 244/188 vs 88–171); noise floor equal |
| the 2× delivery upscale | not it, better | file-level loss is the resample alone (0.925 vs 0.916 retained), zero encode penalty; at YouTube ep09 gets 1440p at 2.7 Mb/s where every 768 upload is capped at 720p / 0.3–0.55 Mb/s |
| audio, mix, sync, gaps | not it | all five masters −14.1…−14.3 LUFS, every line −20 LUFS, gaps mid-pack |
| gutter residue | not it | zero cells in ep04–09 carry a band under the current guard |
| the camera-move rule itself | not it | ep06 and ep07 obeyed it 26/26 and were fine; its **amplitude** is the fault |

## Ranked causes, episode 9

1. **Every take travels, into boards it cannot dolly through, so H3 morphs.** Mean
   frame-to-frame diff median 1.47 / 2.83 / 4.58 / 5.51 / **6.67** (ep05→09); takes over
   6: 1 / 6 / 4 / 13 / **17** of 28. Pan removal explains none of it (it is non-rigid).
   Last frame vs its own cell: 0.59 / 0.20 / 0.33 / 0.30 / **0.075**. Frames off-board:
   62 %. T02's wagon train multiplies into an endless duplicated line; T10's town swaps to
   bare hills; T20's laughing close whips into four riders at a gate. ep05 looked "better"
   because 14 of 25 takes were told to hold and 9 were effectively still — the pendulum
   went from frozen to churning. ep09's moves were also the largest on the shortest shots
   ("a head's height" ×9 on 90 mm faces, "three/four long strides" ×5, 4.9 s mean shot).
   DQ is blind: drift scores the END frame only, "foreign" only knows other takes' cells.

2. **The black floor is gone.** 5th-percentile luma 4–7 (ep05–07) → **16.5**;
   near-black share .29–.45 → .14; mid-tones .25–.34 → .56. Global and local contrast are
   unchanged — the histogram simply lifted off the floor. Cause: the palette sentence
   replaced the London clause that made the series look like film — *"deep shadow;
   practical period light sources"* — with "sunlight only" and a colour inventory. The
   drawer obeys light-direction words; "hard blue shadow" never arrives. And it is one
   hue: 68 % of pixels "colourful" (vs 29–45 %), **94 % of those orange, 0 % green**. The
   lamplit parlour cells sit at luma 40 with true black — the pipeline can still do it;
   the sunlit setups lost the shadow.

3. **The plan's first-frame prose collapsed to a quarter.** `at_rest` 57–77 words per
   shot (ep04–08) → **14.7**; frame-edge placements 3–4 → 0.8; setup `described` 97–144 →
   59; `geometry` 70 → 41. This is the sentence both the drawer and H3 get for the first
   frame. Inserts 6–7 → **0**. Nine of thirty shots are the same close of Lucy with the
   same hat-hair-skirt list; ep07's closes each had a different object in hand. Three
   `medium_close` shots are written "Medium two-shot" and drawn so (face 0.15–0.23 of
   frame vs 0.33). Not a tool regression: nothing in the spec asked for this.

4. **14 of 44 panels are template ALTERNATES that contradict the sheet's own laws.**
   Each says "the same moment as panel k" on a sheet whose ORDER block says every panel
   is later than the last, is listed as a route panel that must advance, inherits the
   base panel's size word, ladder and at-rest line (a "FULL SHOT … a tight insert of
   hands"), carries a grammar bug in all 14 ("camera The camera stands…"), and names no
   object. Result: the same wide drawn three times per 3×3 sheet; nearest-neighbour
   similarity 0.22 → 0.32. Only ep09 was ever drawn under alternates (commit aae21f9,
   40 minutes before its sheets).

5. **The take block was refilled with boilerplate written for the drawer.** A 36-word
   setup crowd caption injected verbatim into **30/30** blocks (ep07: 2/26), byte-identical
   up to 8×, with `.,` punctuation and "Behind him" in twelve shots with no him. Counted as
   core before the budget, it displaced the shot's own camera position ("The camera is…"
   22→15 words), light (21/26 → 14/30 blocks) and at-rest geometry (32 → **4** words per
   block). The style line went to H3 as a **48-word** malformed paragraph (13 in ep05–08).
   And the `end` written for the drawer became the block's closing motion sentence — "By
   00:05, the log house stands twice its size…" — a still composition as the destination,
   where ep06/07 blocks end "the camera is still pushing in through the last frame".

6. **The story is a synopsis.** First dramatised section at **47 %** of runtime (ep05–08:
   14–17 %); first dialogue at 87.6 s (ep07: 6.6 s); 17 narration lines in a row. The
   rescue — *"a sinewy brown hand caught the frightened horse by the curb"* — is not in
   the episode; it cuts from the danger to "You're not hurt, I hope, miss." Lucy speaks
   **12 words** in her own episode; her one line of nerve is cut. First-person narration
   0 % (ep05 55 %, ep06 36 %). 30 shots × exactly one line, zero silent shots, stdev
   0.85 s, the fastest read in the series (3.2 w/s).

7. **`strip_white_edges` is a third paper test nobody recalibrated.** Mean-only at 170,
   no flatness, no drop. First frames that lost ≥ 30 px of picture on an edge: ep04–07
   **0/0/0/1** → ep08 11/30, ep09 **10/30**, every one to the 6 % cap, then re-squared by
   centre crop (−7 % on both axes, upscale 1.21–1.28× instead of 1.13×). Q00_0 lost its
   snow peaks.

8. **Sheet-side text faults.** WARDROBE block **empty** for every Part Two character
   (garments were moved out of `physical` into `wardrobe`, and the sheet reads `physical`),
   so the "these stay the same in every panel" law holds nothing. BACKGROUND LIFE tells
   the private parlour it is "a public place in a working city that people fill in every
   panel" (its crowd is moths). **Watson's brown bowler card from the 221B hat stand** is
   attached to the parlour and the drove by the alias "his hat". The palette's *objects*
   stamped a gold wheat foreground into five of six plates, including the bare rock
   shoulder.

9. **The Utah cast was never bound the way the London cast is.** No `sheet` block on the
   three lead rows, so the six cards were drawn from the wardrobe sentence alone with no
   "the same black beard" clause; **Lucy's card was drawn by a male-only template** ("The
   same man … hanging back off her shoulders … the face of a man waiting to be
   photographed"); no card prompt on disk; the cast gate never ran between the cards and
   the sheets. The pixels are fine — arguably better than London's.

## Ranked causes, episode 8

1. **"1881 London, gaslight-amber" on 13/13 sheets and 28/28 takes over a noon desert.**
   The drawer resolved the contradiction into the flattest, greyest, least-coloured
   sheets in the series: saturation 0.21, 8 % dark pixels, 34 % coloured. H3 then pulled
   the bone-white plates (luma 162) to neutral mid-grey takes (104). Neither bleached nor
   shadowed.
2. **15 END pins that are a different picture from the start** (first-vs-END 0.33) forced a
   6-second cross-dissolve: trough coherence 0.50 median, T28 −0.21. Fixed since.
3. **19 of 30 shots on one rock**, 16 with no face, the identical light sentence in 30/30
   `camera` fields, three sheets for one setup — the first setup ever split across drawn
   sheets.
4. **Ferrier drawn from the superseded fur-hat bust** (landscape, face 2.8 % of frame), the
   hat and red scarf copied into the sheets against "bareheaded in every panel"; 16/16
   ep08 face refs were bare busts (ep05–07: 63/64 gpt-image cards). Ferrier is a different
   man in ep09.
5. **YouTube's 720p cap hurt ep08 most**: 2× brighter with 1.6–1.8× the high-frequency
   energy, 62 % detail retained vs 66–75 %, and its crf17 sky already banded. **A 1536
   re-cut exists on disk (`cut/master_iter4.mp4`) and was never uploaded.**
6. `strip_white_edges` trimmed 11/30 first frames; the grey shawl from the 221B hat stand
   attached to three crag sheets; `audio/lines/lines.json` carries stale shot numbers.

## What this says about the loop

Every one of ep09's faults passed every gate, and most of them were introduced on
2026-09-16 in the name of fixing ep08. The no-last-frame rule was right and the
measurement that proved it (0/28 frozen) was real — but "not frozen" was read as "good",
and the opposite failure (churning, off-board) has no gate. The palette fix was right and
reached the artefact — and pasted a colour inventory where a light direction belonged.
The alternates fix satisfied the GRID gate and broke the DIFFERENT-PICTURES one. Three
paper tests were recalibrated as two.

The general fault, named in `feedback-constants-outlive-their-world`, has a second half:
**a gate that passes is not evidence of quality, only of the absence of the one fault it
was built for.** The owner's eye found in minutes what 4,600 tests did not.

## What to do (proposed, not done)

Code, free, testable — in this order:
1. `strip_white_edges` asks `episode_gutter.band` (one paper test, not three).
2. Take DQ gains a **mid-take coherence** gate (off-board share, unprompted hard cut) so
   churning fails the way freezing does.
3. Plan gate: a wide/full outdoor shot with a many-figure crowd gets a **hold or a small
   move**; travel amplitude capped by shot length.
4. `house_style`: `where` is 3–6 words (place, date); a separate `light` clause that names
   a **direction that throws shadow into frame and a black**; the style line stays ~13
   words. No colour inventories, no objects.
5. Alternates: distinct prose, no inherited size/path/at_rest, excluded from ORDER/route,
   grammar fixed — or spare cells become END-of-scene beats. Never "the same moment".
6. Sheet WARDROBE reads `wardrobe[state]`; BACKGROUND LIFE only where the crowd names
   people; crowd caption not counted as take core and not repeated per block;
   `props_in` requires `Setup.props` or a distinctive alias; `arrival_clause` says the
   camera arriving, not a layout; `mouth_of` only for faces in the shot; `paced()` runs
   `without_measures`.
7. Cast: `sheet` blocks for the Utah rows, a gender-aware card template, and
   `seq_boards` refuses to draw until `cast_cards --check` has passed the setup's cast.

Then rebuild ep09 (plan rewritten: at_rest as pictures, inserts, the rescue, Lucy's line,
dialogue by 20 %, varied shot lengths, silent shots) and re-upload ep08's 1536 master at
minimum — or rebuild ep08 under the same rules.
