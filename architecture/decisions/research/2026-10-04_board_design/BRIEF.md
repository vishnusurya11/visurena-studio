# Brief — the board, redesigned as a premium studio tracking UI

**Owner's ask (2026-10-04):** "use 10 sub agents to research in UX and UI .. to be like premium
studio tracking UI and graphics ... research and plan it first."

**Owner's answers to scoping:**
- Scope: **the whole board** — home `/`, floor `/floor`, department `/d/{stage}`, unit
  `/d/{stage}/{codex}/{unit}`, book `/b/{codex}`, org chart `/org` — as one design system.
- Look: **all four, blended** — film-studio tools (ShotGrid/Flow, ftrack, Kitsu, Frame.io),
  modern SaaS (Linear, Vercel, Raycast), pipeline/ops monitors (Dagster, Temporal, Grafana),
  AND keep/refine the current warm "paper" editorial look of the org chart. The research must
  reconcile these, not pick one by taste.
- Deliverable before any build: **a plan + clickable static HTML mockups** of the key pages
  with real data, for the owner's review. Nothing is built until he says so.

## What the board is

A local, single-user studio board for a one-person AI studio that turns book chapters into
~2.5-minute square video episodes on one local GPU. Repo:
`D:\Projects\KingdomOfViSuReNa\alpha\visurena_studio`. Board: `uv run python command_center.py`
→ http://127.0.0.1:8700 (FastAPI + Jinja2 + htmx, no build step, `studio/command_center/`).
Data: SQLite ledger (`work_orders` per (book, department, unit), `work_steps`, `orders`,
`holds`, `events`, `usage`) + the library on disk (`library/<book>/episodes/epNN/`: plan.json,
storyboard/shot_NN.png panels, takes/r2v/T??.mp4 takes, cut/master_iterN.mp4, verdict JSONs,
learnings.jsonl, timing.jsonl). Departments: analysis, screenplay, trailer, refs, episode.
An episode unit runs 12 steps (bind, plan, places, record, timeline, prompts, board, panels,
shoot, edit, qc, deliver); judges sign gates (PLAN, LAYOUT, EYE_PANELS, EYE_TAKES, MASTER,
RENDER) as pass or flagged; runs loop, defer, get refused, take hours on the GPU.

The owner glances at it many times a day next to a terminal; he wants to know: what is
running and when it ends, what is stuck and why, what it looks like so far, what to do.

## Evidence

- Screenshots of every current page: `current/*.png` in this folder (home, floor, dept,
  unit_ep17 — a unit mid-plan with the new live "now" panel — unit_ep12 finished, book, refs,
  unit_ep17_phone). Read them.
- Earlier specs: `../2026-09-25_command_center/D_ui_design.md`, `F_unit_page.md`,
  `G_unit_data.md`; the decision `../../2026-09-25_command_center.md`.
- Code: `studio/command_center/` (app.py, views.py, unit_view.py, unit_parse.py, templates/,
  static/htmx.min.js). Tokens: `architecture/index.html` `:root` block (a test currently
  holds the board's tokens byte-equal to it).
- Live board: http://127.0.0.1:8700 (read-only browsing is fine; do NOT click action buttons).

## Rules for every researcher

- Research the outside world (web sources, product docs, design write-ups, screenshots you can
  describe) AND apply it to THIS board with its real data. Cite sources with URLs.
- Be concrete: named components, sizes, colours as tokens, states, interactions, the field each
  element reads. No generic advice ("use whitespace") without the specific instance.
- Respect: single user, local, one GPU, no npm/build step (vendored JS only), htmx, light and
  dark themes, phone width ≥ 400 px, accessibility (contrast, not colour alone).
- Do not edit code, do not commit. Write ONE report in this folder: `NN_<topic>.md`, ≤ 300
  lines, ending with **"Top 10 recommendations for this board"** (ranked, each one line with
  the page it applies to) and **"3 disagreements I expect with other researchers"**.
- Return a 15-line summary.
