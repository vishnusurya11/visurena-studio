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
| F7 | ep19 plan DEFERRED: the cylinder's alias "the shot" made the FILM word "shot" a G-STAGE term — 20 false faults, every shot | ep19's first plan | film words (shot, frame, take, cut, scene, view, camera, lens) can never be prop aliases (`pack_refs.GENERIC`); skill: a new gate's vocabulary is run against the last 3 real plans before it ships (one false positive per shot would have shown at once) | fixed + tested |
| F8 | The G-STAGE cure pasted the card's first clause "the top turning slowly" into shot 10 — the contract refuses slow words | ep19's first plan | `physical_clause` returns "" when the clause carries a slow word; general rule: any cure that IMPORTS text runs the contract's own word checks on what it imports | fixed + tested |
| F9 | plan_repair applied every cure as ONE round; one contract break voided ALL cures (light, crowd, moves) and the unit deferred | ep19's first plan; the root of "cures never fire" | `apply_each`: one cure family at a time, each kept only if the contract holds; a breaking cure is dropped alone and its rows go to the llm/writer pass | fixed + tested |
| F10 | Build lanes each ran their own suites; nobody ran a REAL plan through the new battery before launch | ep19 deferred within 25 min | pre-launch dry check: run `plan_check` + `plan_repair --dry` over the last delivered plan (ep18) after any battery change — catches F7/F8/F9 class bugs for $0 in seconds | proposed |
| F11 | Between writer rounds only `ghost_limbs` runs for free; every other mechanical cure (close crowds, light, phantoms, machine names, moves) waits until the whole ladder has failed — so the paid writer is re-asked about $0 faults every round and re-adds them (ep19: G-CROWD-CLOSE on the same four shots through every round) | ~4 min + $0.05–0.10 per round; ep19 ran improve, improve, fresh_brief | `Desk.write`: after each draft, run `plan_repair` mechanical-only (`--no-llm`, `apply_each`) BEFORE the battery re-judges; the writer only ever sees creative faults | proposed (after ep19: no step-02 code change on a live episode) |
| F12 | Registering step 13 moved the episode's final step and deliverable; 15 tests and the board's fixtures hard-coded "12" and manifest.json | the integration pass | a stage-level `deliverable:` key in stages.yaml (the episode stays delivered by its manifest); every test derives the final step from the registry, never a literal | in progress (agent) |
| F13 | My own watcher matched "written" inside a refusal message and fired early | one false alarm | watchers match the exact event message (`PLAN: plan.verdict.json written`), never a bare word | applied |
