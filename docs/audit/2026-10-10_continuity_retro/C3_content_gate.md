# J5: the content gate against the owner's judgement

2026-10-11. This is the last open retro item (FINAL.md §3, CYCLE_3.md 3B "Gate regression").
- **Cost:** CPU only, $0, no GPU. Every panel was re-judged from the cached 3B reads (seed 11) in `bench_evidence/c3/3b_fixtures.json`.
- **Eye check:** every refused panel was read as a picture. The contact sheets are in the session scratchpad (`j5/sheet_0..6.jpg`).
- **Fixture:** `tests/fixtures/content_gate/wotw_owner_fixtures.json` holds the read, the judge's inputs and the eye label for each rule, for all 98 panels. The test is `tests/test_the_content_gate_tracks_the_owner_fixtures.py`.

## 1. Every refusal, by rule, checked by eye

**ep05, owner GOOD: 23/28 refused, with 30 rule hits.**

| Rule | Panels | Eye | Verdict |
|---|---|---|---|
| landform 'hills' on a flat place | s00 s01 s04 s05 s08 s10 s13 s15 s19 s20 s21 (11) | Flat heath with a low far horizon in every one. | **FALSE ×11** |
| landform 'cliffs' on a flat place | s03 | The crater's own sand wall, which the setup stages. | **FALSE** |
| the hour reads 'day' on a night setup | s09 s11 s14 s18 | Each setup asks for "the last daylight" or "afterglow". s14 is borderline: the pit wall is warm-lit where "the last daylight falls". | **FALSE ×4** |
| figures over the declared count, over-the-shoulder | s07 | The second figure is the neighbour's near shoulder, which the shot asks for. | **FALSE** |
| figures over the declared count, crowd in prose | s09 s12 s17 s22 s23 | The shot's own words ask for a "band of people", "people … in ones and twos", a "wedge of dark figures" or "among the others". The plan predates the `crowd`/`extras` fields. | **FALSE ×5** (s12's casting is off: no washerwoman. No count rule measures that.) |
| figures over the declared count, named walk-ons | s10 s18 s19 | The prose names the carter/farmwife/shopkeeper, the flag's bearer, and the governess/carter/boy. This is a legacy plan with no `extras`. | **FALSE ×3, open** |
| figures with copies (crowd: 4 lookalikes) | s16 | Four dark silhouettes, which the prose asks for as "other dark figures". | **FALSE by eye, open** (1 panel; the crowd-clone rule is kept) |
| banned 'mountain' | s10 | A low far ridge. | **FALSE, open** (1 panel) |
| banned 'doll' (+ the doll counted as a figure) | s21 | A child's doll in a pink dress over the crater. | **TRUE** |
| a figure on a wide that names none | s25 | A man in a boater on an empty wide. | **TRUE** |

**ep07, owner GOOD: 5/27 refused.**

| Rule | Panel | Eye | Verdict |
|---|---|---|---|
| figures, over-the-shoulder | s24 | The wife's shoulder, which the shot asks for. | **FALSE** |
| figures | s03 | A second head in the narrator's hands. He is asked for alone, on hands and knees. | **TRUE** |
| figures | s09 | The shot asks for a workman and one boy. A second boy came. | **TRUE** |
| posture | s04, s05 | The shot lays him on his side and then sits him up. The panel stands him both times. | **TRUE ×2** |

**ep08 and ep09, owner BAD:** 0/20 and 0/23 refused, and no content rule fires on them. Their plans declare crowds and extras, and they read flat, at the right hour and with the cast they ask for. Whatever the owner judged bad there is not a content fault. **A green gate on them is not evidence the gate works.**

## 2. What changed

Only rules with at least 2 measured false refusals and 0 true ones were changed. The work was test-first.

1. **'hills' on a flat place: HARD → ADVISORY.** The new `landform_advisory` writes it into the row's `look_advisory`.
   - 'mountains' stays HARD.
   - 'cliffs' stays HARD unless the staged text is a pit (`PIT`, the same test the cliff ban already used).
   - This is a gate-level change, so `GATES.md`, `architecture/index.html` and `architecture/README.md` are updated.
2. **The hour.** `judged_at_night(described)` is `at_night` unless the setup asks for "daylight / sunset / sun going down / afterglow". A night setup without those words still faults on a 'day' read.
3. **Over-the-shoulder.** `shoulder_figure(frame)`: "over the/his/her/X's … shoulder" or "past the near shoulder" in the shot's own words allows one more figure.
   - The copies test is unchanged: a shoulder never excuses a lookalike.
   - ep07 s09 ("past the near shoulder", 4 figures) is still refused.
4. **Legacy crowd.** `crowd_declared(shot, setup)` returns the setup's crowd. If a shot's plan predates `extras` (the field is unset in `model_fields_set`, not 0), "people/crowd/figures/others" in the shot's own words also counts as a crowd.
   - A plan that declares `extras` is held to them.
   - Every plan from ep10 on declares `extras` on every shot (checked: ep10/12/16/20/24/27). **Production judging is unchanged by this rule.**

`panel_content_check.judge` and `take_content_check.verdict_for` now go through these. The judging itself is `pc.judge_staged`, the same function the fixture test calls. `master_eye.content_faults` still uses `at_night` and the raw crowd. It is out of this scope and noted for later.

## 3. Before → after (cached reads, today's code)

| Set | Owner | Before | After | Eye-true faults kept |
|---|---|---|---|---|
| ep05 | good | 23/28 | **6/28** (s10 s16 s18 s19 s21 s25) | 2/2 (s21 doll, s25 stranger) |
| ep07 | good | 5/27 | **4/27** (s03 s04 s05 s09) | 4/4 |
| ep08 | bad | 0/20 | 0/20 | none to keep |
| ep09 | bad | 0/23 | 0/23 | none to keep |
| known-bad: ep16 duplicates (lookalikes / G-TWIN) | bad | caught | caught | Rules untouched: a shoulder never excuses a copy, and modern plans are never "legacy". |
| known-bad: ep18 suit-in-flannel (look contradictions) | bad | caught | caught | `contradictions` untouched |
| known-bad: BENCH/C1 seams | bad | caught | caught | A different gate (`panel_check` seam/stacked), untouched |

The suite covering content, panels and takes passes, including the earlier hills test, which was rewritten to the advisory. One part of the claim is not separately tested: no new test re-runs the ep16, ep18 or seam cases. They are counted as still caught because each one's rule or gate was left unchanged.

## 4. Open (not loosened, logged)

- **Named walk-ons in a legacy plan** (ep05 s10/s18/s19). Counting them needs a person-noun reader. These are legacy plans only, so production is unaffected.
- **A dusk crowd's silhouettes read as copies** (ep05 s16, 1 panel). The crowd-clone rule (≥3) was a five-expert ruling, and one panel does not overturn it.
- **'mountain' ban on a low far ridge** (ep05 s10, 1 panel).
- **The bad episodes are invisible to content.** Whatever made ep08/ep09 bad needs its own measure. The content gate cannot be asked to find it.
