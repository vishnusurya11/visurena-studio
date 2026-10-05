# UX panel brief — make the board dynamic and better (owner, 2026-10-04)

Owner: "make the website more dynamic .. refresh and updating and all .. create 10 agents who focus
on UI and user experience and best practices, who debate to improve it and implement the new changes."

## What exists (look at both)
- **Real board (live data):** http://127.0.0.1:8700 — `/`, `/floor`, `/d/episode`,
  `/d/episode/20260827135508/ep17` (running), `/d/episode/20260827135508/ep12` (finished),
  `/b/20260827135508`, `/org`. Code: D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\studio\command_center\
  (app.py, views.py, unit_view.py, progress_view.py, templates/, static/progress.js, htmx.min.js).
  It is being re-skinned right now to the approved design (a foundation builder is mid-way: CSS
  out to static/css, Studio black tokens, sidebar shell) — expect it to change under you.
- **Approved design (mockups, static snapshot data):** http://127.0.0.1:8710 — work folder
  D:\temp\claude\d--Projects-KingdomOfViSuReNa-alpha-visurena-studio\9340346d-60b6-4248-b569-c5a6fe035ef8\scratchpad\board_v3\mockups\
  (index.html Home, queue, department, book, books, unit-running, unit-finished, architecture;
  assets/v2.css, viewer.js in progress). Owner's verdict on them: "very good UI, that is the
  direction". Palette: Studio black (#0f1012) default, Graphite light.
- Prior rulings: research\SPEC_v3.md (the Viewer) and
  D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio\architecture\decisions\research\2026-10-04_board_design\SPEC.md
  (+ its reports 01–10, especially 09_liveness_motion.md: pulse + morph, no SSE, one animation
  per viewport, notification table).
- Screenshot tool: C:\Users\vishn\.claude\skills\gstack\browse\dist\browse.exe — use `chain`
  (goto + screenshot in one call; the daemon tab is shared) and absolute output paths under the
  work folder's `shots\panel\`. Read your PNGs.

## Your job (read-only: change nothing)
Through YOUR lens, find what would make this board feel like a premium, living studio tool used
many times a day by one owner on one GPU. Cite outside best practice (URLs). Be concrete: the
page, the element, the change, the data it reads, how it updates, and how to know it worked.
Write `research\P<NN>_<lens>.md` (≤ 200 lines) ending with:
- **"Proposals"** — ranked, each with an id `P<NN>.<k>`, the page, a one-line change, effort S/M/L,
  and the files it would touch.
- **"I will argue against"** — 2–3 likely proposals from other lenses you think are wrong, and why.
Return a 10-line summary.
