# Episode 14 -- The Conclusion: where it stands (2026-09-17)

The last chapter. Everything that does not need the paid image API is done;
the episode is stopped at the storyboard sheets.

## Done

- **Plan** clean under `plan_check`: 24 shots, 23 lines, 350 words, five
  setups (the cell at dawn, Baker Street by the fire, the garden path, the
  Lauriston front room, a cab rank), dialogue 16.3 %, turn at Watson's own
  decision to publish, button on Holmes's testimonial line.
- **Cast**: every face is already bound (Hope, Holmes, Watson); the street
  boys and cabmen are crowd, and the reasoning flashbacks are inserts with no
  faces at all, which is also why the chapter's explanation is narrated rather
  than spoken.
- **Lines**: 23/23 said their line, 158.0 s of runtime, speech 81 %.
- **Timing**: every shot inside a take, every shot its own take.
- **Plates**: five drawn and looked at (the cell, the fire-lit sitting room,
  the clay path, the peeling front room, the wet cab rank).

## Blocked

The image API answers `credit_balance_exhausted`. Five storyboard sheets are
needed, about $0.65 in all. They cannot move to the local drawer: a sheet is a
reference-conditioned EDIT that carries the cast cards, and the local
workflows take one or two reference images, not a plate plus two cards. Drawing
Holmes and Watson without their cards would break the faces the other thirteen
episodes established.

The title card is NOT blocked: `title.py --local` draws it on the owner's own
model (ep13 shipped that way).

## To finish, once there are credits

    uv run python scripts/episode/run.py <book> 14 sheets -- --approved
    uv run python scripts/episode/takes_r2v.py <book> 14 --prompts   # the dry build
    uv run python scripts/episode/run.py <book> 14 takes  -- --approved
    uv run python scripts/episode/run.py <book> 14 take_dq
    uv run python scripts/episode/run.py <book> 14 title  -- --local --approved
    uv run python scripts/episode/run.py <book> 14 assemble -- --engine=r2v
    uv run python scripts/episode/run.py <book> 14 qc       -- --engine=r2v
    uv run python scripts/episode/run.py <book> 14 eye_review -- --engine=r2v
    # fill the rubric, then publish with --watched=<sha8> --audited --approved=publish

`episodes/ep14/youtube.json` is already written.
