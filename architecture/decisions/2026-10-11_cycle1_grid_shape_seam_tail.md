# 2026-10-11 — Cycle 1: grid shape, the seam rung, the dialogue tail gate

**Status:** RULED (owner, 2026-10-11). BUILT: #3 G-GRID-SHAPE (a51ecef), #4 the seam rung + refs-only fallback (0f6c92d), #7 G-TAIL.
**Debate:** `docs/audit/2026-10-10_continuity_retro/C1_verdict.md`, from the reports
`C1_G_gates_speed.md` (grid and seam), `C1_A_audio_tail.md` (tail) and `C1_L_looks_replayset.md`.

## What changes in the org chart

| slot | before | after | commit |
|---|---|---|---|
| episode/07 Board, `grid_layout` | grids of 1-4 cells, a 2- or 3-shot run drawn as a 2x1 or 3x1 strip | **G-GRID-SHAPE:** a grid is 1 or 4 cells, never 2 or 3; n shots = [4]*(n//4) + [1]*(n%4) | #3 |
| episode/08 Panels, `panel_ladder` | a `seam` / `stacked` fault climbed seed, then reprose, then keep_best | **the seam rung:** the faulted shot is isolated into its own 1x1 once, outside the 2-grid cap; reprose no longer carries a seam cure | #4 |
| episode/08 terminal → episode/09 | a seamed panel survived keep_best and was staged as the take's first frame | **per-shot refs-only (owner ruling):** a shot still seamed after its isolate renders from the reference sheets and place picture only, ships unattended, and is flagged in the audit sheet | #4 |
| episode/09 Shoot, take gate | dialogue takes had no tail check (masters strip take audio, so a mouth moving in silence shipped) | **G-TAIL:** a dialogue take whose shipped tail sounds above -45 dB and in which Whisper hears words after the line fails; cure one reseed, then keep_best flagged | #7 |

## Owner rulings (2026-10-11)
- Seam fallback: refs-only per shot, ships unattended, flagged in the audit sheet.
- Shipped ep10/T21 and ep26/T25 (mouth moving in the silent tail): left as they are, logged as known faults.
- Jekyll/Hyde probe: skipped.
- Stubble vs short beard: not ruled; the `beard` marker draws "a full short <colour> beard", `stubble` is untouched.

## Why (measured)
- Strip grids seamed 15/201 panels, square-ish grids 0/198 (Fisher p = 4.7e-5): Qwen draws its own grid count on a strip canvas. A seed bump never cured it.
- The 1x1 grids carried 0/92 seams, so isolating a seamed shot is the cure that can work, and it is finite: a shot already alone cannot be isolated again.
- H3 continues the line into a digitally silent guide tail; every invented word echoes the line's last word. 2 of 154 shipped dialogue takes speak into silence.
