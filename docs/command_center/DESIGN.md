# Command Center — Proposed Design

**Status: PROPOSAL, v0.1 — 2026-08-22. Nothing built. Owner reviews.**

The studio's tracking UI: the whole architecture as a DAG of big steps; click a step to see its
sub-step DAG; statuses at a glance; per-book views. Evidence:
[research/01_dag_ui_patterns.md](research/01_dag_ui_patterns.md). Name note: `.gitignore`
already reserves `visurena_command_center/` from an earlier plan — the name slot exists.

## Stack (solo-maintainable, local-first, zero build step)

> **FastAPI + Jinja2 + htmx (2s polling; SSE later) + Cytoscape.js** (vendored locally, with
> `cytoscape-dagre` layout + `cytoscape-expand-collapse`) **over the stepwise SQLite DB.**
> No npm, no bundler, ~5 frontend files.

Why not the alternatives: React Flow is prettier but demands React + a build toolchain and its
expand-collapse example is paywalled; Mermaid is the zero-effort interim for the static
architecture view (server-emitted text, `classDef` status colors) but weak at interaction;
Streamlit fights live stateful canvases; NiceGUI is the pure-Python fallback. Free bonus:
`datasette studio.db` on a second port as the raw-DB debug console.

## Core principles (each traced to research)

1. **Graph shape from the static pipeline definition; DB overlays status only** (Temporal's
   documented weakness inverted). The stepwise definition DAG *is* the UI's graph source.
2. **Drill-down = navigate-into with breadcrumb** (Prefect/ComfyUI pattern): Architecture page →
   click "Analysis" → its A0-A9 page. Every page is a small flat dagre graph — no compound-edge
   routing problems, any nesting depth (`A3.extract` dot-namespaces become levels for free).
3. **Fan-out = Dagster partition bar, never 27 nodes**: A3 renders as ONE node with a
   27-segment bar + "24/27"; clicking opens an htmx **table** of chapter tasks (status,
   duration, cost, retry button per row). A table beats a graph for homogeneous fan-out.
4. **Fixed status palette** (Airflow's, memorized by thousands): 🟢 succeeded · 🔵 pulsing
   running · ⬜ pending · bold outline **ready/next-up** (all deps met) · 🔴 failed ·
   🟠+⏸ **parked/awaiting approval** · ⬜🚫 upstream_failed · ➖ skipped · 🟣 unsynced (stale).
   Always icon + color, legend always visible, roll-up counts on every parent node.
5. **Approvals = Prefect's pattern**: inline Approve/Reject buttons (htmx POST to
   `/api/gate/{id}`) on parked nodes/rows, plus a global amber **"Needs attention"** strip on
   every page listing all parked+failed items — nothing hides inside a graph.
6. **Thumbnails on nodes/rows** for media-producing substeps (ComfyUI/Deadline lesson) — the
   fastest status signal a *content* pipeline can show. Click = lightbox.
7. **Status patches in place** — statuses change, shape doesn't → no re-layout flicker.
8. **Cost is visible everywhere**: per-substep cost column, per-book credits, topline
   credits-spent/budget meter (Deadline ledger-column model).

## Screens

**1 — Architecture (home).** Top: credits/budget meter + "Needs attention (N)" strip with jump
links. Canvas: L→R DAG of big steps (Parse → Analysis → … → Publish), each node a card: name,
status icon, "7/10 substeps", mini segmented bar, active-book count. Book-selector scopes to one
book or aggregate-across-books. Click → Screen 2.

**2 — Stage detail** (breadcrumb *Books › Dracula › Analysis*). The stage's sub-DAG (A0-A9);
fan-out nodes carry partition bars; parked nodes show inline Approve/Reject; failed show error
snippet + Retry (= stepwise *clear*). Right panel on node click: timestamps, duration, cost,
attempt history, log tail, thumbnails, gate payload + decision form. Clicking a partition bar
swaps the panel to the per-chapter table.

**3 — Books list.** Deadline-style table: thumbnail · title · current stage · **one segmented
bar of all big steps per row** (whole pipeline in a glance) · attention badge · credits spent ·
last activity. Default sort: attention first. Header totals: books in flight, credits this
month, approvals waiting.

## API (thin — everything reads stepwise tables)

`GET /` `/book/{codex_id}` `/book/{codex_id}/stage/{stage}` (pages) ·
`GET /api/graph?book&stage` (nodes+edges from definition, status from `step_run`) ·
`GET /api/status?since` (poll patch) · `POST /api/gate/{id}` (approve/reject + note) ·
`POST /api/step/{id}/clear?downstream=bool` · `GET /api/artifact/{id}/thumb`.

All mutations = the same stepwise operations the CLI uses — the UI is a *view + button panel*
over stepwise, never a second brain.

## Build phases

| | | Effort |
|---|---|---|
| CC0 | Mermaid interim: server-rendered architecture view with status colors — works the day stepwise's tables exist | ~1 hour |
| CC1 | Books list + stage detail pages, htmx polling, gate buttons | ~1 day |
| CC2 | Cytoscape graph pages with navigate-into + partition bars | ~1 day |
| CC3 | Thumbnails, SSE, attempt-history panel, Datasette side-mount | later |

## Open questions for review

1. Name: `visurena_command_center` (already in .gitignore) — keep, or name it something with more soul?
2. Confirm navigate-into (breadcrumb) over expand-in-place as the primary drill-down.
3. Port/launch: `uv run studio ui` on localhost:8700, auto-open browser?
4. Does CC0 (Mermaid interim) ship with stepwise's first milestone, or wait for CC2?
