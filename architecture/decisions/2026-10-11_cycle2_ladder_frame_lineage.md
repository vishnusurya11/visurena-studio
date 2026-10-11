# 2026-10-11 — Cycle 2: the plan ladder, G-FRAME, G-LINEAGE

**Status:** BUILT under the cycle-2 skeptic verdict (`docs/audit/2026-10-10_continuity_retro/C2_verdict.md`,
CYCLES.md's 95 % bar). No owner ruling is needed for these three: the ladder change cannot ship a worse
plan (a battery-refused draft is deferred, never shipped), and the two new gates are advisories with no
cure, no wall and no ladder effect. The owner-eye items of the same cycle (P-WORDS v3, the 992 canvas, the
neutral tile prompt, 6 h as P50 or P90) are NOT decided here; they wait on `bench_evidence/c2/C2_owner_sheet.jpg`.
**Reports:** `C2_J_looks_judges.md`, `C2_F_framing_quality.md`, `C2_B_speed_budget.md`.

## What changes in the org chart

| slot | before | after | commit |
|---|---|---|---|
| episode/02 Plan, `plan_ladder` | improve ×2 → fresh_brief → model_tier → terminal | **improve ×2 → model_tier → terminal.** fresh_brief threw the refusal history away and wrote from a new brief; it produced the kept draft once in 40 terminal climbs (ep17-27), an anomaly | #3 |
| episode/08 Panels, `panel_check` | panel_dq.json carried no framing measure | **G-FRAME, advisory:** `face_h` (tallest present face) and `planned_size` on every faced non-back panel; `frame_advisory` when an MCU < 0.22 or a close < 0.32. Uncalibrated (the MCU floor sits above today's 0.208 median); no cure, no wall, no ladder effect | #8 |

## Why (measured)
- Kept-draft source over the 40 terminal climbs: draft 15, improve1 7, improve2 12, fresh_brief 1, model_tier 5.
  The CPU replay with the fresh_brief draft removed from the candidates changes exactly one climb's kept
  count: ep18 2026-10-05 14:21, [3, 3, 1, 58 → 58].
- 547 of 849 rung minutes ran after the kept draft already existed.
- The refuted twin (fault-set memory: skip to the terminal when a climb starts on the last climb's count)
  is NOT built: 5 of 10 such re-climbs made progress.

- G-FRAME replay over the 396 shipped WotW ep12-27 panels reproduces F's per-(size, grid shape) medians
  exactly (every cell within 0.005); MCU 84 panels, median 0.208, 48 flagged; close 23, 8 flagged.

## Watch
- model_tier now edits improve2's draft with the whole merged refusal history. Log its input fault count
  on the next 3 episodes (LESSONS).
