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

## Run findings → changes (living; one row per thing that cost time or a hand)

| # | Seen | Cost | Change (code or skill) | State |
|---|------|------|------------------------|-------|
| F1 | Full test suite serial: step-runner tests wait real ComfyUI/lease timeouts; one run sat 30 min at 63 CPU-s, looked hung | ~1 h of wall time before ep19 | `uv add --dev pytest-xdist==<pin> pytest-timeout==<pin>`; mark the comfy/lease-waiting tests `@pytest.mark.slow` (excluded by default like `local`); a default `--timeout=60` in pyproject so a hang names itself | proposed |
| F2 | Pipe `pytest ... \| tail` buffers everything until exit — no progress visible | the hang was invisible | skill INFRA note: always `> file` with `-v`, never `\| tail`, for any run > 2 min | proposed |
| F3 | Owner standing hand (publish/standing.json) was the one input step 13 needs per book | would park every book's first publish | write it at book setup (`titles_batch` / refs stage first run), from the 2026-10-01 ruling; G-STANDING then never parks in production | done for WotW; propose for book setup |
| F4 | `migrate_row_words.py` cures pre-existing stillness words in cast rows/prop cards — a one-time pass per book | prompts step refusals on ep17/18 | run it inside `refs` stage step 04 verdict (idempotent; "nothing to cure" on a clean book) so a new book never needs it by hand | proposed |
| F5 | SKILL.md "THE RUN" table still says step 02 stops on battery faults and step 05 on measured holes — both now self-cure | an agent reading the skill would still intervene by hand | rewrite THE RUN table after ep19 proves it: 02 = battery + cures (code first, one guarded workhorse rewrite), 05 = one bounded auto-trim, 08/09 = G-TWIN ladder, 13 = publish to the public URL; the agent's job becomes WATCH + report, not fix | pending ep19 proof |
| F6 | Non-negotiable #3 forbids bare step scripts mid-run, but ep18 needed them (dead clock, unjudged retakes) | ep18 hand-driving | both causes now code (18f147c dead clock → terminal, 26dbf12 retakes re-judged); keep the rule, delete the exceptions | done in code |
