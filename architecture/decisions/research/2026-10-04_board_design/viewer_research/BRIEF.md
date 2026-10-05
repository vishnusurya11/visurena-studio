# Brief v3 — the in-page media + file viewer, and Home in the sidebar

**Owner (2026-10-04), after approving the v2 mockups ("very good ui .. that is the direction"):**
"add home to left panel ... ability to click on images inside episode and view them .. not a new
page .. regular and navigate between images and videos ... also json files of prompts to be
viewable ... popup on the page but not a new page .. which we can close .. design and research and
implement, use 10 more agents, research, debate and improve."
Scoping answers: implement in the **mockups first** (the real board adopts it after); the viewer
opens **pictures + videos, prompt JSONs, and all unit JSON + logs**; **keep the Activity window**
(owner: "there is activity window, keep it, it is good").

## Where things are

- **Work folder (NOT the repo — another session's episode drive needs the repo tree clean):**
  `D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\9340346d-60b6-4248-b569-c5a6fe035ef8\scratchpad\board_v3\`
  - `mockups\` — the v2 mockups (served live at http://127.0.0.1:8710/): `index.html` (Now),
    `queue.html`, `department.html`, `book.html`, `books.html`, `unit-running.html` (ep17),
    `unit-finished.html` (ep12), `assets\{board.css, v2.css, unit.css, shell.js, unit.js, dept.js,
    icons.svg, data_*.js}`, `DIRECTION_v2.md`, `SHELL.md`.
  - `research\` — write your report here.
- Previous research and the ruling (read-only): `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\architecture\decisions\research\2026-10-04_board_design\` (`SPEC.md`, `02_media_review.md`, `08_media_grids.md`, `03_saas_craft.md`, `09_liveness_motion.md`, `10_feasibility.md`).
- Real data (READ-ONLY): the library `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\library\20260827135508_the-war-of-the-worlds\episodes\ep12` (finished) and `ep17` (running) — panels `storyboard/shot_NN.png`, grids `storyboard/grids/`, takes `takes/r2v/T??.mp4`, masters `cut/master_iter*.mp4`, prompt JSONs (find them: `takes/r2v/prompts.json`, grid prompts, `plan.json` shots, `*.json` beside media), verdicts (`plan.verdict.json`, `storyboard/eye_*.json`, `takes/r2v/eye_*.json`, `review/eye_*.json`), `qc_r2v.json`, `learnings.jsonl`, `timing.jsonl`, logs under `D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\logs\20260827135508\episode\`.
- The live board serves files: `http://127.0.0.1:8700/thumb/20260827135508/{160|320}/<rel path>` (WebP thumbs) and `http://127.0.0.1:8700/lib/20260827135508/<rel path>` (originals incl. JSON and mp4 with range requests). GET only.

## Rules for every researcher

- Research the outside world (cite URLs) AND apply it to THESE files and THESE pages. Concrete:
  components, sizes, keys, states, the exact files each view opens.
- Constraints: static mockups now, the FastAPI+htmx board later; no npm/build, vendored JS only
  (small); Studio black theme (+ Graphite light); phone ≥ 400 px; accessible (focus trap, Esc,
  aria); one `<video>` playing at a time; the board's web process never decodes video.
- Do NOT edit the mockups or anything in the repo. Write ONE report:
  `research\NN_<topic>.md` (≤ 250 lines), ending with **"Top 8 recommendations"** and
  **"2 disagreements I expect"**. Return a 12-line summary.
