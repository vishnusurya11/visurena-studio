# Retro improvement cycles: plan and log

Owner, 2026-10-10/11: "once your research is concluded and changes are done ... repeat the whole exercise on my feedback and your retro, 3 more cycles: research, debate, identify issues at 95% confidence, propose a solution, use agents to implement and improve."

Owner scoping, 2026-10-11:
- This is a retro and testing pass. **Do not start a new book.**
- Test on **replays of WotW and Sherlock (A Study in Scarlet)** shots only. Nothing is published, and shipped files are never overwritten.
- One generalization probe is allowed: **a single scene or shot** of a ready book with fewer than 20 chapters. The pick is *Dr Jekyll and Mr Hyde* (`20260827135504`, 11 chapters, screenplay, refs and analysis ready). The Jekyll to Hyde change is the hardest look-timeline test there is.
- The owner doesn't want to manage cycles. Run them back to back. Stop only for rulings that are the owner's: a style or look change, a composite, a licence, or a budget trade over 6 h.

## Standing constraints
- At most 6 h of machine time per 2-3 min episode, measured on the replay set and projected.
- Never edit an existing ComfyUI workflow. A new one is a new file named `<base>_<source>.json`.
- Write tests first. No test may spend money or touch the GPU.
- The checkout is shared: never run `git stash`, `checkout` or `reset`, and commit explicit paths only.
- Never kill or relaunch ComfyUI. If it is down, stop and tell the owner.
- 95 % confidence means an issue is acted on only when the evidence is measured on the artefact (frames, graphs, logs), seen in at least 2 independent shots, and survives a skeptic. Anything weaker is logged as a hypothesis, not built.

## The replay set (fixed, so cycles are comparable)
- **WotW:** the phase-0 bench shots (S2-S6, D1-D2); the narrator ep25 `fulham_road` and ep27 `study_table` grids; the house (ep26 villa, ep27 study reverse, the ep11 study, the dining room).
- **Scarlet:** chosen in cycle 1. Holmes and Watson faces, 221B interior, one dialogue take (lip lag) and one exterior.
- **Jekyll/Hyde:** one transformation shot, refs plus look plus grid plus take. The book stays unstarted.

## Each cycle
1. **Retro:** the owner's feedback so far, plus the previous cycle's measurements, scored on the replay set.
2. **Research:** 2-3 agents, online and in the code.
3. **Debate:** proposer(s) and a skeptic, ending in a verdict with issues at 95 % confidence.
4. **Build:** an agent, test-first.
5. **Measure:** the same replay set, compared before and after.
6. **Skill update:** LESSONS, SKILL and GATES.
7. **Report:** `CYCLE_N.md`, with full paths first.

## Status
- [x] Round 0: look judge fixed (08ebcb0), narrator replay (ep27 PASS 3/3; ep25 FAIL, the look picture was drawn without a beard), BENCH_r2 (no arm passed every hard check; 4-step NOT wired), seam gate (3ea5461), invented-speech check (17eab28)
- [x] Cycle 1: 10 verdict commits + CK8 adopted for narration; bench 69 min; report CYCLE_1.md
- [x] Cycle 2: CYCLE_2.md, owner sheet ruled
- [x] Cycle 3: CYCLE_3.md + FINAL.md (21201c6); reserve 4931687 + companion 6f343d3; P90 5.54 h, 0/9 over 6 h; tick_error fixed 50a35c8

## Log
- 2026-10-11: plan written; waiting for round 0 to land.
- 2026-10-11: owner raised S4/B4 audio ("indeed ... deed" repeated). Whisper on the r2 takes found the extra speech is H3's own invented audio in the silent tail of the voice guide:
  - S4_B3ck "Indeed."
  - S4_B4beta "Heed."
  - D1_B3ck "HAHAHA"

  The controls are clean. Masters strip take audio (`trailer_assemble.extract -an`), so no shipped sound is affected. A mouth that moves in the tail would still ship, though. The bench builder is adding an INVENTED-SPEECH hard check and review copies that carry the recorded line. **Cycle 1 issue:** prove the root cause at 95 % (silent guide tail vs shift/attention) and check shipped masters for mouths moving in silence.
- 2026-10-11: round 0 done. Cycle 1 issues carried in:
  - (1) ep25 look drawn without a beard; ghost faces in the clothing texture go undetected.
  - (2) Invented speech and mouth motion in the voice-guide tail; the 4-step LoRA raises the tail from -57.6 to -30.2 dB.
  - (3) 4-step loses content (the S3 frogs); last sigma 0.72.
  - (4) The CK attention PSNR floor of 28 dB is miscalibrated (another seed gives 13-17 dB).
  - (5) 16 of 18 seam panels shipped on keep_best: the terminal leak.
  - (6) The Scarlet replay set has not been chosen.
  - (7) The D1 laugh is asked for in its prompt, so the speech check needs an exemption.
  - (8) Red test test_an_unknown_size_is_refused.
- 2026-10-11: cycle 1 research done (C1_L, C1_A, C1_G) and skeptic verdict C1_verdict.md: 10 commits, one ~90 min bench.
  - C1_G showed the 4-step LoRA runs off its authors' schedule (simple@12); R2_verdict had cut that arm wrongly.
  - Owner rulings: a seamed panel falls back to refs-only, ships and is flagged; shipped ep10/T21 and ep26/T25 are left as they are; the Jekyll probe is SKIPPED.
  - The cycle 1 builder is launched.
- 2026-10-11: cycle 1 built and benched (CYCLE_1.md). Met: seams 0/25 under no-strips, beard 3/3, G-TAIL replay exact, CK8 adopted for narration (-39-45 % sampling). Out: G1. Inconclusive: room tone. Not met: ep25 regrid 2/4 (back views). Projection ~5.7 h.
- 2026-10-11: cycle 1 done (CYCLE_1.md). Carried to cycle 2:
  - the LOOK-STATE hat vocabulary;
  - the regrid bar should exempt back views;
  - CK for dialogue needs a second seed;
  - a neutral prompt for the 2x upscale (the cause of the ghost faces);
  - 1x1 panels framed wider than planned;
  - 9 of 15 Scarlet heads are empty;
  - 2 red tests (book_title placed.json lint, ep11 plan regen);
  - the C1 hypotheses (subject noun first, G2 six calls, 992, the Hope sheet, flashback story time).

  The architecture page needs republishing at the end of cycle 3.
- 2026-10-11: cycle 2 research done (C2_J, C2_F, C2_B) and skeptic verdict C2_verdict.md: 10 commits and one ~86 min bench, with an owner sheet.
  - Refuted: the "same faults, skip the climb" memory, because 5 of 10 re-climbs made real progress.
  - Honest projection: P50 about 4.8 h, P90 about 6.3 h.
  - Owner rulings pending: P-WORDS, 992, the neutral-tile upscale and the narrator sheet redraw, and whether the 6 h ceiling is P50 or P90.
  - The cycle 2 builder is launched.
- 2026-10-11: cycle 2 done (CYCLE_2.md, 9 commits; the QC memo was dropped because its own check showed it would never hit).
  - Measured:
    - the ghost faces come from the 2x tile pass;
    - CK is NO for dialogue;
    - the framing arms missed the bar;
    - 992 broke S6's identity.
  - Projection: P50 5.0 h, P90 6.9 h.
  - Owner rulings from the sheet:
    - P-WORDS: no, keep v2;
    - 992: no, stay at 768;
    - neutral tile: adopt for NEW draws only;
    - the 6 h limit applies to EVERY episode (P90).
  - Cycle 3 targets the P90 tail (plan-ladder loops and relaunches), adopts the neutral tile, and works the carried hypotheses.
- 2026-10-11: OWNER: "don't ask me for any more details, design it the best way and implement it". From here every ruling is made by us on the evidence and recorded in the cycle report for veto. Spend approval still applies.
- 2026-10-11: cycle 3 research done (C3_T, C3_R) and verdict C3_verdict.md: 11 commits, a ~55 min bench, and the final 3A/3B measurement. Decisions D1-D12 are made on the owner's behalf and logged for veto:
  - an honest clock;
  - a retry never resets the clock;
  - at the ceiling, render whatever is missing, take the best and flag it, never park;
  - only a closed SAFETY list stops an episode.

  Projected P90 is about 5.9-6.2 h. The final builder is launched; it writes CYCLE_3.md and FINAL.md.
- 2026-10-11: helper fixed the autopilot tick crash (50a35c8). Residual report C3_p90_residual.md: ep20 is under 6 h as built, but ep21 lost about 170 min to pre-ceiling faults (most now fixed). DECISION, on the owner's behalf: build the downstream reserve (a retry runs only if spent + its price + the shares of the steps still owed fit under 6 h; a refusal is flagged, never parked) and the signed-verdict-stands companion rule. The run-14 counterfactual is not built.
- 2026-10-11: cycles complete. The last open item, the content gate inverted on the owner's own fixtures (it refuses good ep05 23/28), is being recalibrated on CPU (C3_content_gate.md). After that the pipeline is clear for the owner's next chapter. Architecture page republish in flight.
- 2026-10-11: J5 is done (78df605, ab50971): the content gate is calibrated on the owner's episodes, and the architecture page is republished. **THE RETRO IS COMPLETE.** Still open:
  - `master_eye.content_faults` keeps the old hour and crowd logic;
  - 4 one-panel J5 residuals;
  - Jekyll heads are unauthored;
  - room tone;
  - framing has no cure.
