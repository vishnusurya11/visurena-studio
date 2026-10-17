# Plan — the anime-TV grammar in the planner (decision 2026-10-17)

Status: **BUILT 2026-10-17** in one commit (contract, gates, battery, cures, writer, inner
voice, capacity, docs). Decision: `architecture/decisions/2026-10-17_anime_tv_grammar.md`.

- [x] Contract: `grammar`, `motif`, `tease`, sections `act_out` / `tease`, line kind `inner`,
      dialogue outer wall 35 % (`studio/episode_spec.py`)
- [x] Writer: `grammar` code-set from the band, `motif` / `tease` drafted (`agents/episode_writer.py`)
- [x] Framing gates (`studio/framing_grammar.py`), screenplay gates (`studio/screenplay_grammar.py`),
      the shot cap (`studio/episode_capacity.py`), one battery call (`studio/grammar_battery.py`)
- [x] `plan_check`: the GRAMMAR row, `--plan=<file>` for a scratch re-plan, one take per shot
      on a grammar plan, the next chapter for a tease's spans
- [x] Dialogue ceiling follows the chapter (`plan_gates.dial_ceiling`); G-MOVES held shots;
      G-VARIETY 12 closes a person on a grammar plan
- [x] Free cures: `strip_amounts`, `hold_extra_pushes`, `ots_medium_close` (+ plan_repair)
- [x] Inner voice: hushed in the speaker's own engine, close-mic in assemble (`studio/inner_voice.py`)
- [x] Brief: `grammar_rules`, the chapter's dialogue band, the book's motif (`studio/plan_brief.py`)
- [x] Writer skill section; camera catalog rows; SKILL / GATES / LESSONS
- [x] Replay over 41 plans (`scripts/episode/grammar_replay.py`); Jekyll ep01 `plan_v3.json` clean
- [ ] First grammar episode rendered: measure its clock, re-price the shares for 30 shots
- [ ] The owner hears the inner voice; G-INNER's advisory note comes off or the kind goes
- [ ] A panel route for silhouette / Dutch / eye close-up

## Log

- 2026-10-17 — built; the replay and the v3 proof in `docs/audit/2026-10-17_anime_tv_grammar/`.
