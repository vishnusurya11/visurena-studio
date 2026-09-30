# Where ep14's hours went — three-agent debate, 2026-09-29

Owner: "clearly it was not taking this long when we did Sherlock or the first 10 episodes —
something is missing." Three agents, read-only, argued from timing.jsonl, the take graphs
and git history. They converged on three causes; none of them is "the render got slower".

## The numbers (timing.jsonl; takes-h/shot is the honest per-episode measure)

| ep | shots | takes h | retake rounds | retake h | judge h (dq+content) | takes-h/shot |
|---|---|---|---|---|---|---|
| SiS ep10 | 34 | 2.96 | 4 | 1.02 | 0.46 | 0.087 |
| SiS ep13 | 28 | 2.08 | 1 | 0.08 | 0.10 | 0.074 |
| WotW ep05 | 28 | 1.72 | 0 | 0 | 0.07 | 0.061 |
| WotW ep12 | 24 | 3.22 | 4 | 1.03 | 3.79 | 0.134 |
| WotW ep13 | 25 | 5.08 | 10 | 2.93 | 4.53 | 0.203 |
| **WotW ep14** | 30 | **14.75** | **14** | **8.79** | **7.66** | **0.492** |

ep14's 34.4 h wall was dense work (3.7 h idle); ep13's 60.5 h wall was 32.3 h idle with its
cost in grids/panels. The takes blow-up is ep14's own.

## Cause 1 — the canvas (~×1.75 on every rendered second)
ep14 is the studio's first portrait render: every take at **768×1344** (plan `aspect: 9:16`)
against **768×768** in every other episode of both books. Measured: 1.29–1.71 s/frame in
ep02/03/05/12/13 → **2.9–3.3 s/frame** in ep14 (~500 s/take vs ~200–300). The aspect came from
the WRITER'S DRAFT; the contract default is 1:1, the brief never told the writer the series
shape, and no gate checked it. Side effect: square panels staged into the portrait canvas is
where the brand-new `letterbox` failures came from — 0 before ep14. Model, LoRA, steps, fps,
frames/take, prompt length and reference count did NOT change in a costly direction (ep14's
prompts are the lightest of the six episodes measured).

## Cause 2 — the ladder churned (14 rounds, 88 renders for 30 shots)
The old process allowed **one batched retake round per master, chosen by a person** (ep10
synthesis F1, `retake_refusal` f412009). The automated ladder (2026-09-24) had no round cap,
no per-take attempt cap, and no memory across resumes; the 5 h budget is per PROCESS, and
drive.py's auto-resume opened a fresh one each time (~20 starts). T19 was retaken ×8, T05 ×7,
T18 ×6, T17 ×5, T20 ×5 — for faults (panel lettering, clones, letterbox) that live in the
INPUT, where the panel ladder had already capped out at `max_grids: 2`. `replan_cell` ran 4
identical rounds on the same four takes. Rounds 3–14 cost ~5.6 h of renders + ~2.6 h of reads
and ended with the identical terminal verdict.

## Cause 3 — the judge layer re-read everything (7.7 h vs Sherlock's 0.1–0.5)
`take_content` did not exist in Sherlock (0 h → 3.6 h); step 09 re-ran full 30-take
`take_dq` + `take_content` passes on every resume (8 + 8 full passes); take_dq had no cache;
verdicts are byte-fingerprinted so every round invalidated them; the VLM twice hung 600 s
behind the loaded H3.

## Fixed the same day (test-first, committed)
- **G-ASPECT** (`e6ff5a0`): the plan's aspect is the series' (series.json else 1:1); the brief
  tells the writer; the battery refuses a guess. ep14's plan flipped to 1:1 and re-rendered.
- **Ladder memory** (`e6ff5a0`): `takes/r2v/ladder.json` counts rounds ACROSS resumes,
  `ROUNDS_CAP = 4`; a take with `MAX_TAKE_ATTEMPTS = 3` archived attempts is never retaken;
  the climb is incurable past either cap (F1 restored as code).
- **take_dq byte-cache** (`e6ff5a0`): a `T<NN>.dq.json` naming the kept file's sha8 is the
  measure of those bytes; full passes skip unchanged takes. (take_content already cached, 4bbd0fc.)
- Earlier the same episode: content-check frees the render model before its first read
  (`055aaed`), resume prices only missing takes (`4d57ffe`), a shot board is never redrawn
  under rendered takes (`e35d569`), no name is written where the drawer can letter it (`14874e0`).

## What a 30-shot square episode should now cost
Round 1 ~2 h + ≤4 capped rounds ~1 h + judges ~1 h (cached) + board/lines/edit/QC ~1.5 h ≈ **4–5 h**.
