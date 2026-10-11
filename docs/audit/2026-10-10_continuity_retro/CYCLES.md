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
- [ ] Cycle 2
- [ ] Cycle 3

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
