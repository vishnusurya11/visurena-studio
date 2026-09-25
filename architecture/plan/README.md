# Plans

One file per initiative, named `YYYY-MM-DD_<slug>.md`. Each file has:

1. **Status** line at the top: `NOT STARTED | IN PROGRESS | BLOCKED (why) | DONE (date)`.
2. **Decision** it implements (a link into `../decisions/` or `docs/DECISIONS.md`).
3. **Done means** — the observable end state, in one paragraph.
4. **Steps** — a checkbox per commit, each with its tests named first (test-first) and
   its size; a step is ticked only when its commit is on master with the tests green.
5. **Log** — dated lines: what moved, what was learned, what the owner ruled.

The index of plans lives in [../README.md](../README.md). Book-specific work (an
episode, a series goal) is not planned here; it lives under `library/<book>/`.
