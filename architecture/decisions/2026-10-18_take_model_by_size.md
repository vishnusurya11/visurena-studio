# 2026-10-18 -- the take model follows the planned shot size (step 09, `scripts/episode/takes_r2v.py`)

Status: BUILT 2026-10-18 (main session, on measured evidence, for the owner's veto; the owner picked
Wuli V4's faces and approved Spark on 2026-10-17).
Evidence: `docs/audit/2026-10-16_model_tests/PART1_SUMMARY.md` (V2 Spark, V4 Wuli),
`docs/audit/2026-10-18_warping/WARPING.md`, and the proof `docs/audit/2026-10-18_wuli_spark/`
(`kawajiri/` holds the renders, `warp.json`, `identity.json`, the dq/content/eye verdicts and `times.json`).

## The ruling

| planned sizes of the take | graph |
|---|---|
| every segment close / extreme_close / medium_close / medium / insert | `video_minimax_h3_r2v_wuli8_hqint8_sandpies_spark_zechengtang` (WULI_BASE) |
| any wide or full segment, or no sizes on the card | `video_minimax_h3_r2v_turbo_ref8_crf_visurena_ckattn_comfyorg_spark_zechengtang` (SPARK_BASE) |
| rollback, every take | `video_minimax_h3_r2v_turbo_ref8_crf_visurena_ckattn_comfyorg` (ROLLBACK_BASE) |

The run queues Wuli's takes first, then Spark's (`by_model`): each model loads once a round.
The lane no longer picks the graph (the CK-narration / plain-dialogue split of 2026-10-11 is retired).

## Why, measured

- Wuli draws sharper faces (face Laplacian about 2x on T19/T22, bench V4), but on a small face that
  line work is redrawn every frame: G-WARP on the Kawajiri W wide S 4.13 / Se 7.22 vs Spark 2.65 / 3.12
  at the same seed (FAIL is S > 2.5 or Se > 3.0); WARPING.md T22 +2.4/+3.3 vs about -0.6.
- On close and medium Wuli+Spark is equal or cleaner: C 0.49 / 0.30 vs 0.98 / -0.90, M 1.46 / 1.32 vs
  1.30 / 1.64. Content clean 3/3 and 0 clone pairs on both arms; G-TAIL passes the speaking close on both.
- Close identity (facenet on a drawn face; the row is advisory): C 0.561 Wuli+Spark vs 0.531 Spark.
- Speed: Wuli+Spark is about +12 s a take over the CK base on 158-192 frame takes (T04 89.3, T22 107.5,
  T19 107.8 s warm vs 78.0 / 99.3 / 89.9); Spark alone is -9 s. At 28 shots, ~90 % on Wuli, 1.5 renders a
  shot and one extra cold load a round, the episode projects about 5.8 h against the 6 h limit.

## Open

- The GATES dialogue arm rule (WotW ep10/T21 and ep15/T21 controls) was not re-run on Wuli+Spark;
  G-TAIL, HARD on every dialogue take, is the net.
- The proof is three cards of one look; re-price `episode_capacity` after the first routed episode's clock.
