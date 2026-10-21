# 2026-10-21 -- The ep02 proof harness (tracker)

Status: **IN BUILD** -- P1, P2 and P7 landed; P3-P6 in build. No
package spends GPU time or a paid call; the staged real runs SR-0..SR-5 wait for the owner. Decision:
`architecture/decisions/2026-10-21_proof_harness.md`. Design: `docs/audit/2026-10-21_ep02_proof/DESIGN.md`
(outside git). Each builder ticks its own box with its commits.

## Packages (one checkbox per package, its commits beside it)

- [x] P1 the sandbox and its fence: settings override fail-closed both ways, audit-hook write/launch fence,
      socket/openai/SDK-transport tripwires, sandbox builder, checkpoints, stat guard -- 7624d45, 1e6cb4f
- [x] P2 read-only real proofs: recordings index, incident tally + map, ch2 precondition audit -- 9b28b75,
      a0a6291, e49cd2b, bc14771
- [ ] P3 the fake ComfyUI, workflow fingerprint, faults incl. corrupt/exec_fatal, the contract test, the
      transcript proxy
- [ ] P4 fakes.install: SDK ReplayTransport (+ recorder), canned refusals, fake workers + memo filler,
      YouTube/notify, VL consumer log, time scale
- [ ] P5 supervisor, faults, asserts, graph diff, sweeps + distinct traces, scenarios S0a/S0b/F1-F18, rehearse.py
- [ ] P6 face first-pass replay, the instrument gate, panel->take regression, gate false-refusal replay
- [x] P7 time back-test with UNMEASURED steps, confidence.py + questions.yaml, docs and architecture page --
      e24782e, 138238c, 8153be1, and the docs commit

## Owed

- [ ] The final report run, after P5 and P6 write their results: `uv run --no-sync python scripts/proof/confidence.py`.
- [ ] SR-0..SR-5, each on the owner's explicit go (machine minutes in `scripts/proof/questions.yaml`).
- [ ] Q5: a time model that passes its pre-registered back-test (it failed 2 of 4 on 2026-10-21) and a
      measured row for the first-pass refine, the GPU whisper worker and the drive's uncovered clock.

## Log

- 2026-10-21 -- owner order: "proof-backed confidence". Design iteration 1, the skeptic's 19 changes,
  iteration 2 (DESIGN section 8 rules on each).
- 2026-10-21 -- P1 landed (7624d45, 1e6cb4f). P2 landed: incident tally (9b28b75), ch2 precondition audit
  (a0a6291), recordings index (e49cd2b, bc14771).
- 2026-10-21 -- P7 landed: the time back-test FAILED its pre-registered pass (2 of 4 within 0.15; ep01 +0.093,
  ep24 -0.223, ep25 +0.098, ep26 -0.365); measured under the predicted p90 on 4 of 4; Q5 not provable (three
  unmeasured steps over 0.05 of the p90 or unbounded); base rate 0 of 1 under 6 h. The report enforces DESIGN
  5.1 on fixture rows (19 tests). OPERATOR.md gained its one rehearse line (read set 131,070 B before and after;
  OPERATOR 13,386 -> 13,206 B, the history moved to LESSONS_ARCHIVE).  The first report over the real
  results folder (CONFIDENCE_iter2.md): Q1/Q2 REAL-RUN (the face_eye gate failed), Q3 FAILING (the panel->take
  regression failed its kill), Q5 FAILING (the back-test), Q6 PARTIAL (no scenario rows yet), Q4/Q7/Q8 REAL-RUN.
- 2026-10-21 -- P7 review fixes: R15 fails closed (a time measure counts only with clock `measured` and absolute
  evidence outside any sandbox) and refuses only time measures, so a failing sandbox A-caps row turns Q5
  FAILING; the Q6 cap lifts only on a transcript for every contract route; failed points with unknown passes
  print beside the count with no bound; P2's incidents and ch2 summaries are adapted into Q6 rows and open
  gaps; reruns and a suite's per-face `rows` are no longer counted (102 rows read as 30); the VL fit's negative
  slope (-0.502) is refused for the median read; the back-test states it scores timing rows, not the 6 h clock
  (still FAIL, 2 of 4). Report: CONFIDENCE_iter5.md. Correction: c229514's message says the doc tests passed
  61; that run passed 49.
- 2026-10-21 -- P5 review fixes (one round): a fault row lands at the key ITS fake reads (P3 `faults`, its
  seven kinds only; P4 `sdk_faults`, `worker_die_at`, `youtube: invalid_grant`; `brain_stream`; the harness's
  own `harness_faults`), so F2/F3/F6/F7/F7b/F15/F17 no longer die at supervisor start (the old shape was
  reproduced: `unknown fault kind 'rate_limit'`); every point gets A-served (a planted fault its fake never
  served fails the point); the brain's scripted stream answers the real brain.turn (brain_script.py);
  pre-registered checks for F1, F1b, F3, F6, F7, F7b, F8, F9, F13, F15, F17; F8 joins the table; sweeps run in
  4 h shards at the baseline's measured cost, resume on the same sandbox and report untried (never a pass);
  a missing status doc fails A-named; the rehearsal tests skip only on a scheduler refusal or an absent
  input.  No real-book scenario has run: the visurena-autopilot task is still Ready.
