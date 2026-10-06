# Build tracker — the self-curing pipeline (decision 2026-10-05)

**Status:** built 2026-10-05 — ten lanes, 27 commits, every lane green; integration pass done
(step 13 registered, row-word migration run on WotW, standing.json + publish seeds written).
Proof run: ep19. Specs in
[../decisions/research/2026-10-05_self_curing_pipeline/](../decisions/research/2026-10-05_self_curing_pipeline/).

- [x] 1 setup-light-geometry — G-PHANTOM + G-LIGHT dispatch fix + brief line
- [x] 2 source-quotes — G-SOURCE span-snap cure (free)
- [x] 3 camera-moves — G-MOVES/M2 head rewrites
- [x] 4 props-creatures — G-STAGE + auto prop sheets + creature-face refusal
- [x] 5 clone-text-gates — body-part + two-positions gates, post-writer re-cure
- [x] 6 timing-silences — projected-silence gate, hold trims, micro-lines
- [x] 7 prompt-lint-presign — lint in the battery + data-layer substitution cures
- [x] 8 duplicate-vision — faces N>M hard, G-TWIN VLM ask + ladder
- [x] 9 orchestration-clock — free re-sign, retake re-judge, dead-clock terminal, comfy retry, beds rule
- [x] 10 publish-signoff — metadata + sign-off from measured data
- [x] wire cross-lane hooks the lanes left as blockers; full pytest green
- [ ] ep19 proof run: drive.py alone to a published Short, zero hand edits, under $3

## Log
- 2026-10-05 — all ten lanes landed (103c60a..bf1381d); integration: step 13 in stages.yaml, migrate_row_words --write (4 fields), standing.json written at the owner's direction, org chart flipped; ep19 launched as the proof run.
- 2026-10-05 — decision filed; research fleet (10 specs, 1.28M tokens) done; build fleet launched.
