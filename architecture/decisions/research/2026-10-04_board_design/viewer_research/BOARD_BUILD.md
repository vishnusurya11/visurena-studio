# Building the redesign into the real board (owner: "do it, finish all, using sub agents, debate")

Repo: D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio (on master). Board package:
`studio/command_center/` (FastAPI + Jinja2 + htmx, `uv run python command_center.py` → :8700).
The approved design is the mockups in the work folder
D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\9340346d-60b6-4248-b569-c5a6fe035ef8\scratchpad\board_v3\mockups\
(served at http://127.0.0.1:8710/): `assets/board.css` + `assets/v2.css` (+ `unit.css`, `viewer.css`)
are the design system; `index.html` (Home), `queue.html`, `department.html`, `book.html`, `books.html`,
`unit-running.html`, `unit-finished.html` are the pages; `assets/viewer.js` + `docview.js` the Viewer.
Rulings: `research/SPEC_v3.md` and
D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\architecture\decisions\research\2026-10-04_board_design\SPEC.md;
tracker: D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\architecture\plan\2026-10-04_premium_board_build.md.

## Rules for every builder
- CLAUDE.md: test-first; one function does one thing in 10–20 lines; every function tested; no
  test touches a GPU/model/paid API; book-neutral code; never an absolute path in data.
- The web process stays read-only (writes only through `studio/work_orders` for orders), never
  runs a step, never decodes video; files only under the book folder (guarded routes).
- **The mockup is the visual target; the live data comes from the existing view functions**
  (`views.py`, `unit_view.py`, `unit_parse.py`, `progress_view.py`, `/api/*.json`). Add view
  functions where the mockup shows something the views don't compute yet (tested).
- Another session is driving an episode from this repo and needs the tree clean at its checks:
  stay inside your files, finish green, report — the lead commits immediately.
- The progress-tracker files (`templates/_live_*.html`, `static/progress.js`, `progress_view.py`)
  belong to another session's design: restyle their CSS classes, keep their behaviour and data.
- Verify every page live: restart the board (stop the process whose command line contains
  `command_center.py`, then `uv run python command_center.py --port 8700` in the background),
  screenshot with C:\Users\vishn\.claude\skills\gstack\browse\dist\browse.exe using `chain`
  (goto + screenshot in one call — the daemon tab is shared) at 1440 and 400, Studio black and
  Graphite, absolute output paths under the work folder's `shots\board\`; Read them and compare
  with the mockup screenshot; `console --errors` clean; no horizontal scroll at any width.
- **HARD RULE (an episode is being driven from this repo right now): touch only
  `studio/command_center/**`, `command_center.py`, board tests under `tests/`, and additive read
  helpers in `studio/db.py`. Never `scripts/`, never `studio/` outside `command_center/` (other
  than additive `db.py` reads) — that would change code under a live run.**
