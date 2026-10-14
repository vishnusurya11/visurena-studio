# 2026-10-13 — Picture/motion lane (Jekyll ep01 review)

Status: **BUILT 2026-10-13** — atmosphere and declared looks, the take gate against its
panel, the camera-move row, G-DEAD, the camera-text lint.
Decision: `architecture/decisions/2026-10-13_picture_motion_lane.md`.
Binding: `docs/audit/2026-10-13_jekyll_ep01_review/DIAGNOSIS.md` (#6, #8, #9).

## Commits

- [x] the take gate sees: G-PANEL-BOARD, the compounded scale curve, `camera-move` (b637bc9)
- [x] any declared look, with its atmosphere, reaches the grid and the H3 line (9b56e99)
- [x] two close figures are two figures: the bridged sheet run splits (bf3b2e4)
- [x] `studio/camera_lint` on automatic camera text (d5e8c6c)
- [x] G-DEAD at step 10: `studio/dead_footage`, `assemble.dead_plan`, `work_r2v/dead_cuts.json`
- [x] skill (SKILL/GATES/LESSONS), this page, README, DECISIONS
- [ ] item 6, the photoreal finish (grain, sharpen, grade): not built -- Jekyll is drawn now
- [x] item 7, Hyde's sheet: superseded by the owner's Hellsing ruling (refs lane, 2026-10-13)

## Log

- 2026-10-13: lane 3 left uncommitted by its builder; finished and committed by the
  Hellsing switch session. 25 lane tests and 1602 tests over the touched modules pass;
  `test_episode_tail::test_a_part_the_join_silently_drops_is_refused` fails before and
  after (the lane does not touch `tail`).
- G-DEAD refuses a master it cannot cure; the take ladder's own terminals (a still past
  2.5 s, a kept-best failed take) therefore stop step 10 for a retake round rather than ship.
