# 2026-10-21 -- The proof harness: confidence is a counted pass rate from the real pipeline code, never an opinion

Status: **APPROVED BY ORDER, IN BUILD.** The owner's order (2026-10-21): "build a system or test framework
to build that confidence first; I don't need confidence out of thin air; I need proof-backed confidence."
The design and its skeptic live outside git: `docs/audit/2026-10-21_ep02_proof/DESIGN.md` (iteration 2),
`DESIGN_SKEPTIC.md` (19 required changes) and `DESIGN_iter1.md`. Tracker:
`architecture/plan/2026-10-21_proof_harness.md`.

## The question it answers

Before ep02 (Jekyll ch2) runs, eight questions: are its faces better than ep01's first master (Q1), as good as
iter3 the first time (Q2), do mid faces get drawn eyes (Q3), do tiny faces look good (Q4), does it fit the
owner's 6 h (Q5), does it reach upload-ready unattended (Q6), the same day with an operator (Q7), are its
story and staging better (Q8). Each answer is a status with its count, or the named real run that would
give one.

## The brick

A rehearsal is ONE rule at every boundary: **the real step code runs, and at each point where it would
leave the machine it is answered from a recording, labelled with how good the match was** (`exact`,
`substituted`, `canned`). A step is its calls, an episode its steps, a scenario an episode plus one
injected fault at one point. Every result reduces to counted calls and counted distinct fault points; a
check resting on a `canned` answer proves the mechanism only.

## What changes in the org (architecture)

- **A new shared service, the rehearsal harness** (Platform, on the architecture page). It is not a stage
  and runs no episode: it runs the REAL steps against a sandbox library.
- **One library-root setting** (`studio/settings.py`): `VISURENA_LIBRARY` plus the sandbox manifest
  `rehearsal.json`; fail-closed both ways (the variable without a manifest raises at import; a manifest
  over a real root or port 8188 raises; an enabled `visurena-autopilot` task or an unpaused real series
  refuses the rehearsal). Every path that writes (library, DB, ComfyUI root, git, temp) follows it.
- **The fence** (`studio/rehearsal/fence.py`): one audit hook refuses every write, rename, delete, SQLite
  open, process launch, socket and SDK transport that would reach the real studio, BEFORE it happens; a stat
  guard is the second check.
- **Fakes at the outermost seam**: ComfyUI at the HTTP socket (a real server serving ep01's recorded
  outputs), Claude at the SDK transport, the workers at the process boundary; nothing in the pipeline's own
  call graph is replaced. A canned answer REFUSES (an unread VL text, the schema's refusing instance), and a
  gate that passes on one is a FAILING row.
- **The proof report** (`scripts/proof/confidence.py` + `scripts/proof/questions.yaml`): rows
  `{check, question, passed, n_points, n_distinct, evidence, match_classes, instrument, instrument_state,
  kind}`; statuses PROVEN / PARTIAL / FAILING / REAL-RUN with the Wilson lower bound; writes
  `CONFIDENCE_iterN.md`, never overwritten.
- **The time back-test** (`studio/rehearsal/time_model.py`, `scripts/proof/time_backtest.py`): a predictor
  from an episode's inputs only, scored leave-one-out on delivered episodes' timing.jsonl.
- No production stage, gate, cap or owner gate changes. The OPERATOR page gains one "how to rehearse"
  line; the board is not run during a rehearsal (its ComfyUI tap is outside the fence).

## The rulings on the skeptic (DESIGN section 8)

All 19 changes were taken; five with a change:
- **R1** the "100 % exact" brick test failed on today's tree (47 commits move the take code; seeds depend
  on the try count) and is withdrawn; the regression measure is UNEXPLAINED field differences over n takes.
- **R2** S0b ending upload-ready with unresolved content refusals and an auto-clearable lock is FAILING
  under Q6. Under the 2026-10-01 auto-clear ruling this is the expected finding: a production change for the
  owner to rule on, not a harness bug.
- **R3** canned answers refuse; canned rows are mechanism.
- **R6 (with a change)** an instrument gate: Wilson lower bound >= 0.70 over n >= 30 OWNER labels (26 of 30
  passes, 25 of 30 fails); below it every eye row is INSTRUMENT FAILED and Q1-Q3 are REAL-RUN. The production
  EYE judge may be measured against the labels, never supply them (calibrating one uncalibrated instrument
  against another is circular).
- **R12 (with a change)** the ComfyUI transcript proxy is built, but recording needs a real job (SR-5);
  until then the fake is `shape: uncalibrated` and Q6 is capped at PARTIAL.
- **R13, R14 (with a change)** n is DISTINCT points: a kill point or take position counts only if its
  recovery trace (executed recovery lines, `sys.monitoring`) is distinct; write sites, not every write.
- **R15** a rehearsal clock never feeds a time answer; Q5/Q7 rows from a sandbox or a `recorded` clock are
  refused.
- **R16** every step no record measures is UNMEASURED with its share of the p90; Q5 cannot be PROVEN while
  any share is above 0.05 or unbounded. **R17** Q8-compliance is printed apart; Q8 is the owner's.
- **R18 (with a change)** one import-time rule in settings.py instead of three entry-point edits.

## Staged real runs (each waits for the owner's explicit go)

SR-0 owner face labels (2-5 owner min); SR-1 the first-pass refine rendered on ep01's iter1 takes (about
20 GPU min, priced); SR-2 one real step-02 session for ch2 in a sandbox (about 40 min); SR-3 three more
recorded refine graphs re-rendered for byte determinism (about 6 GPU min); SR-4 ep02 steps 01-08 in a
sandbox under the real engine (about 2 h, no takes); SR-5 the transcript proxy during the next real job.

## First measured results (2026-10-21)

- Time back-test (pre-registered set Jekyll ep01, WotW ep24/25/26): **FAIL, 2 of 4** held-out totals within
  0.15 (needs 3); the measured total sat under the predicted p90 on 4 of 4; the loop steps miss most (plan,
  step 09, QC). UNMEASURED: the first-pass refine (0.079 of the p90), the uncovered clock (0.123), the GPU
  whisper worker (unbounded). Base rate: 0 of 1 clocked episodes under 6 h (ep01 6.02 h). Q5 is therefore
  not provable from records today.

## Publishable (EB-1 note)

The recorded-engine rehearsal harness (a fake ComfyUI at the HTTP seam, exact/substituted/canned labels with
canned-refuses, the audit-hook write fence, swept faults counted by distinct recovery traces) is general
beyond this repo: a standalone "comfy-replay" package for ComfyUI pipelines, and the distinct-trace rule for
counting fault-injection samples is a short paper's method. Not scheduled; noted.
