# 2026-10-30 -- the narrow ship-block (Jekyll ep01-06 retro)

**Status:** BUILT 2026-10-30, owner ruling ("Yes, narrow block") recorded in `docs/DECISIONS.md`.

## Why

The retro's brick: a gate's finding ships unless it is a people line. The gates saw most of what the owner later
caught -- 5 of 12 owner catches were already in a verdict on the shipped bytes -- but option A (2026-10-18) ships
every settled take flagged, and only G-PEOPLE (2026-10-28) refused. Public faults it let through: ep06 T19's envelope
reading "THE FOCUS OF THE PICTURE", ep05 T07's grey-haired Jekyll (row: black), ep04 T05/T10/T12's plate leaks.

## What

`studio/ship_block.blocks(fault)` -- one predicate read by G-DEAD (`dead_footage.admitted`, `assemble.people_wrong`)
and the master's terminal (`master_ladder.flag`):

| kind | detector | replay evidence |
|---|---|---|
| a wrong person | G-PEOPLE / G-WHO lines (unchanged) | 2026-10-28 |
| the prompt's scaffold words | take content check: when the reader sees text, EasyOCR on the sampled frames; any of focus / picture / panel / storyboard / framing | ep06 T19 |
| hair no staged row allows | `take_content.drifted` ("... where the row says otherwise") | ep05 T07 |
| plate leak >= 9 frames | take DQ `leak` row, `frames` | ep04 T05, T10, T12 |

Everything else settled -- warp, gait, framing, generic lettering, look -- still ships flagged.

## Replay

On the latest take eyes of ep02-06 the list refuses exactly the five eye-confirmed faults above and ships ep06 T23
(warp, probable false), ep05 T18/T22 (the chapter's own letter) and every gait row. The broad alternative (only gait,
camera-move, look and story may ship) parked 4 of 5 episodes, about 30 % on correct pictures (skeptic.md section 2).
Test: `tests/test_a_settled_fault_ships_only_off_the_block_list.py`. Take content gate v12.

## What a refusal does

The take is failed at assembly: G-DEAD cuts it when its neighbours cover the seconds, else refuses the master -- the
same road a wrong person has taken since 2026-10-28.
