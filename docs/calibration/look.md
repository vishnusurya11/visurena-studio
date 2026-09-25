# look — the LOOK judge over the reference bible, measured on real sheets

## First contact 2026-09-25 — the first produced book's bible (49 character sheets on disk, 19 bound, 12 published episodes)

Run with the live tools (Qwen3-VL for must nouns and trait cards, EasyOCR, facenet
faces, DWPose limbs) over every character sheet the pack log named: 1 h 43 min,
971 faults on a cast the owner had accepted across twelve published episodes.

| row | read | ruling |
|---|---|---|
| identity (facenet sheet-vs-sheet) | 635 pairs at or above the STRANGER wall 0.45: cosines 0.45–0.82, median 0.60, between DIFFERENT characters | the wall was fitted on another style's crops (`identity.md`); on these full-figure sheets different people read 0.6 alike. **Advisory** until re-fitted on this style |
| lookalike (trait cards) | 269 pairs under DISTINCT_AT 3: distances 2.0–2.5 | the card reads few distinct traits on stylised sheets; the trailer's gate was calibrated on its own sheets. **Advisory** |
| must_noun (look_back) | 39 sheets: the "missing" nouns were names and places from the prompt (a surname, a country, a rank) | the must-noun list is the prompt's nouns, not its subjects; the extractor needs a subject list. **Advisory** |
| voice (nearest rival ≥ 0.55) | 13 | the wall is the cast step's; here informational. **Advisory** |
| unread | 14: a truncated JSON answer, a card with too few traits | confidence, not a fault |
| lettering (OCR) | 1 | **Hard** (synthetic negatives) |
| extra limb (keypoints) | 0 | **Hard** (synthetic) |
| scope | the pack log names 178 paths; 150 are per-episode places and 30 sheets are for entities nobody bound | the judge reads the BOUND character and prop sheets on disk; places are the line's at their own hour |
| first verdict | a bible that shipped twelve episodes before verdict files existed | **grandfathered**: signed on its calibrated rows only, no VLM ask, no pairwise; a NEW row is read in full and compared against the bound ones |

Cost: ~2 min per sheet with the VLM asks (trait card + must nouns); the light
read is seconds. A new bound row costs its own full read plus one card per
bound sheet it is compared against.

## Second contact 2026-09-25 — the same bible, judged on the re-fitted rows

`refs.py` over the 19 bound sheets, grandfathered (OCR + limbs only, no VLM ask):
10 min per pass. One hard fault: OCR read `BA` on the newspaper boy's sheet (a
printed masthead on the papers under his arm). The ladder redrew once on a bumped
seed (171 s), the re-read found no string, the pack signed `judge:look@1` APPROVE,
0 faults, sha8 4b0a9ecd. The kept sheet holds the boy's identity (cap, corduroy
jacket, satchel, freckles) with unlettered papers; try 1 is under `superseded/`.
First live proof of the sheet ladder on a real fault at $0.
