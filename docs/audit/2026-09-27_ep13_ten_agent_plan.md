# ep13 post-mortem and the fix plan: ten agents, two rounds

2026-09-27. The owner watched ep13 master_iter8 and asked three things:
1. Why are the sound effects too loud?
2. Why does the first shot show the curate?
3. Why did ep13 take 8 masters and two days, when Sherlock and WotW ep1-11 did not?

Ten read-only agents each took one angle. Each then critiqued the other nine.
Their files are in the session scratchpad, `debate10/*.md` (round 1) and `debate10/critique_*.md` (round 2).

## The answers

### 1. The effects were too loud because no episode before ep13 had any
- **ep13 was the first mix with a sound layer.** Sherlock ep01-14 and WotW ep01-12 were mixed with an empty cue list: voice plus a ducked bed (`7eab344` .. `aaeb431`).
- **The new layer went in with half the rules the bed has:**
  - Only the bed ducked under a line (`trailer_assemble.mix_with_lines`). Effects and ambience played at full level: 5 of 8 cues sat under narration.
  - Cue peaks were allowed up to the voice's own ceiling (`CUE_TP = LINE_TP = -3`).
  - Ambience was set 8 LU under a bed that actually measured 5 LU lower.
  - QC's sound row had a floor (6 dB) and no ceiling.
- **The one hand change made it louder:** the shot-3 gun raised +6 dB by hand at 16:17 (master_iter4).
- **Fixed in the mix, with no cue re-rendered:**
  - Effects duck 6 dB and ambience 3 dB under every line (`133513d`).
  - Every cue is trimmed 3 dB (`558efe5`).
  - Ambience loops' own spikes are compressed (`06d275e`).
  - The +6 dB was reverted.
- **Measured on master_iter11:** speech over the gaps went from 10.9 dB (iter8) to 12.0 dB, against WotW ep10-12 at 11.3-13.5 and Sherlock at 9.8-16.5. All 8 cues are still heard, at 12.7-24.0 dB. The master is -14.1 LUFS, -1.7 dBTP.

### 2. The curate opens the episode because a gate pushed a line forward and nothing stopped it
- **G-STORY refuses a plan whose first spoken line lands after 25 % of the runtime** (`plan_gates.py:305`). The threshold was fitted on Sherlock.
- **Chapter 13 has no speech until about halfway**, so every writer draft failed (0.57, 0.28, 0.53, 0.53).
- **The orchestrator hand-patched the curate's "What does it mean?" to the front** (`scratchpad/p13b.py`, 09-26). It was an unmarked flash-forward.
- **No gate reads chapter order**, the plan judge passed it, and the "declare a cold open" rule lives only in the screenwriter skill.
- Every other WotW and Sherlock episode opens in chapter order.

### 3. ep13 took 8 masters and 42.9 h because code was debugged on a live episode
Only about 5 h of the 42.9 h was necessary work (one render of 25 takes, one check pass, the cut). The 8 masters were cut in one afternoon (15:29-20:08) with code commits between them. The lost hours, by cause (round 2, corrected):

| cause | hours |
|---|---|
| pipeline design and bugs: re-reading every picture, stale state keyed to timestamps, silent rungs, two writers of plan.json | ~8.4 |
| gates miscalibrated or armed untested: blur, posture, mountain, join guard, QC edit rows, advisory-lag rungs (157 min) | ~7.9 |
| orchestrator: guard-stops, ~2 h unwatched deferral, a hand plan.py run, hand state edits, code commits mid-run | ~6.6 |
| budget mechanics: per-run ceiling, rungs priced 18x low, overruns charged forward | ~6.3 |
| real quality retries: T07 cut, frozen takes, T21, the speech gap | ~4.2 |
| hardware (GPU lost) | ~3.8 |

- **Sherlock ep04-14:** median 1 master, 2.7-5.9 h. It composed each picture once, ran every free gate before spending, batched one retake round with a written reason, and had no model-opinion judge in the loop. What it lacked: gates that caught only what they were built for. ep09 scored 28/28 with 62 % of its frames off-board.
- **WotW ep09-11:** 1-2 masters, with the owner's eye in the loop. The break came on 09-24, when judges and ladders replaced the eye. The eye did not cost iterations; the ladders and resumes did.

## ep13 as it stands

Deliverables for the owner to validate:
- `library/20260827135508_the-war-of-the-worlds/episodes/ep13/cut/master_iter11.mp4`: the full cut, sound fixed.
- `library/.../ep13/cut/master_iter11_no_open_PREVIEW.mp4`: the same cut, starting on the pit (the chapter's first beat), without the flash-forward. The curate's close still appears at its own place.

Still in the picture, each needing a re-render, and listed for the owner rather than retaken unasked:
- The narrator's face shape drifts across shots. Identity is "not measured" on every cast take.
- T18, "Be a man!", holds nearly still for about 3.5 s.
- T04 shows oars under the line "No oars."
- Shot 3's "insert" is a dark wide with the gun low-left.
- The curate's red irises in the angry close at 1:54.
- The chapter's last two paragraphs (the moon, "follow this path northward") are not in the plan.

## The process fix plan, ranked by the round-2 consensus

Each item has the ep14 measure that proves it.

| # | fix | where | ep14 proof |
|---|---|---|---|
| 1 | **A driver, not an operator.** `drive.py` launches `episode.py`, resumes a DEFERRED run at its stopped rung, keeps spend per episode, and alerts (Telegram) on a stop, a REFUSED line or 10 min of silence. No guard-stops, no scratch drivers. | runner | at most 3 launches; no idle over 10 min; 0 `Stop-Process` |
| 2 | **Freeze the code for the episode.** The runner records its git SHA and refuses a dirty tree. A QC or gate change is replayed on an earlier master before it meets a live one. | runner | one SHA in the ledger; no master cut to debug code |
| 3 | **Rungs only for HARD faults they are measured to cure.** Advisories ride to the terminal note, and a climb stops on an unchanged fault set. | take_ladder, panel_ladder, judged_gate | 0 advisory retakes; at most 15 ladder rows |
| 4 | **Measure early.** The measured speech gap at step 05. At step 02: G-STILL, G-ORDER (chapter order unless a declared, repaid flash-forward), G-STORY made conditional on the chapter's own first quote, and an insert-size lint. A rendered plan is still judged, in report mode, never rewritten. | plan_check, step 05 | nothing first found at QC; at most 5 first-pass take failures of 25 |
| 5 | **Re-read only what changed.** Panel and take verdicts are keyed per file sha (the raw VLM cache is built). Stills, heads and graphs carry the take's content sha, never a timestamp. | panel/take checks, assemble | panel_content at most 30 min; no stale still or head |
| 6 | **A sound band, both sides.** Effects duck under lines (built). QC gets a ceiling: effects at least 10 LU under the voice during speech and 4 LU in the clear, speech at least 11 LU over the gaps. Cue levels move out of the render cache key, so a level fix is a free remix. | episode_sound, qc | the sound row passes both sides |
| 7 | **"Not measured" is not a pass.** A cast take with no identity reading, or a master with no EYE_MASTER row, cannot sign. The lip "laid by the edit" pass needs correlation of at least 0.5, otherwise it reads "cannot tell". | take_verdict, qc | an identity row on every cast take |
| 8 | **One writer of plan.json after the first render: the ladders.** `plan.py` refuses to overwrite a plan.json newer than itself, and step 02 never runs the writer on a rendered plan (built, 971485e). | episode_home.write_plan | 0 hand plan writes |
| 9 | **SKILL.md on one page.** The run order, 10 non-negotiables, and "ask once, before the run". Stale rules out: the plan.py invariant, parks, the manual retake, the tools table. Draft: `debate10/critique_skills_audit_SKILL_draft.md`. | .claude/skills/episode | the agent follows it with 0 hand edits |

Refused by the debate:
- Dropping any gate that caught a real fault (frozen-whole, cut/jump, content, G-COVER/G-SHOUT, emotion vectors, the publish lock).
- Loosening QC's 6.0 s gap wall.
- Removing the director's watch-and-listen sign-off.
- Lowering `CUE_LUFS` before ducking.

## Owner decisions needed

1. **The opening.** Validate `master_iter11_no_open_PREVIEW.mp4` (the recommendation), or keep the curate first. If the preview is chosen, a tested `drop_shot` edit makes it the real master.
2. **One batched retake round** for T18 (freeze), T04 (oars), shot 3, and the red irises, with a written reason per take. About 40 GPU minutes. Or ship without it.
3. **Go on the process plan** (items 1-9). The architecture page and a decision file follow the go.
