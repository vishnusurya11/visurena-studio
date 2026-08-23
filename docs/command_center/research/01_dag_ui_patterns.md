# Research — DAG pipeline UIs & the command-center stack

*Subagent report, 2026-08-22.*

## 1. What each best-in-class UI teaches

### Dagster asset graph (closest to our ask)
- Collapsed **groups that expand on click** (shipped after users demanded it at 100+ assets); expand/collapse-all control.
- **Sidebar tree mirroring the canvas** — tree = fast navigator, canvas = mental model. Best drill-down UX idea to copy.
- Status strip on every node; **roll-up summaries on collapsed group nodes**.
- **Partition status bars — the crucial insight**: a 27-way fan-out is NOT 27 nodes; it's ONE node with a horizontal segmented bar (green done / gray missing / red failed) + "24/27" count.
- Weaknesses: layout hung at ~200 assets; users couldn't find the expand affordance; shift-scroll zoom confused people. → obvious chevron + count badge, plain scroll zoom, small graphs.

### Airflow Graph + Grid
- **Grid view = runs × tasks matrix of colored cells** — the canonical "many productions × many stages" view; our books list is an Airflow Grid.
- Fixed, widely-memorized color legend (green success, red failed, yellow running, gray queued, purple retry…). Copy it.
- TaskGroups collapse; dynamic task mapping renders as `task [27]` — fan-out collapsed to a count node.
- Weakness: Graph and Grid feel like separate apps.

### Prefect
- Subflows = single nodes you **click through into** the child graph with breadcrumb ("navigate-into" pattern).
- **Approval gates reference design**: `Paused` state + a Resume button that pops a typed form (approve/reject + comment). Distinct paused color + inline affordance.
- Weakness: graph derives from execution records → breaks/drops edges.

### Temporal — the anti-lesson
- Cannot show the planned DAG at all (only executed history); users beg for it. → **Render the graph from a static pipeline definition; SQLite supplies only status overlays.**

### Argo / n8n / ComfyUI / Deadline
- Argo: click a node → preview the artifact it produced.
- n8n: per-node status on the editor canvas; lesson — persist per-substep status as it happens.
- ComfyUI: executing node highlighted with progress bar; **output image shown on the node**; subgraphs = navigate-into with breadcrumbs. → thumbnails are the fastest status indicator a content pipeline can have.
- **Deadline render-farm monitor = the template for the books list**: one row per job, row color drifts green→red with errors, **segmented mini-bar of all task states per row**, per-frame thumbnails, cost columns.

**Status-encoding consensus**: color + icon (never color alone), fixed visible legend, roll-up counts on parents, and a global "needs attention" list so failures never hide inside a graph.

## 2. Drill-down: two proven patterns, use both

- **A. Expand-in-place** (Dagster groups, Airflow TaskGroups, Cytoscape compound nodes): good ≤~15 children; pitfalls all documented — layout jump, cross-hierarchy edge routing (elk `INCLUDE_CHILDREN` still buggy; dagre can't), affordance discoverability, fan-out explosion.
- **B. Navigate-into + breadcrumb** (Prefect, ComfyUI subgraphs): canvas replaced by child graph; each level is a small flat graph — no compound-layout hell; scales to any depth.
- **Sweet spot for our 3 levels**: navigate-into for Architecture→Stage (click "Analysis" → A0-A9 page); **partition bar** for Stage→fan-out (A3 shows 27-segment bar; clicking opens a TABLE of the 27 chapter tasks — a table beats a graph for homogeneous fan-out every time).

## 3. Library comparison

| Library | Verdict |
|---|---|
| **Cytoscape.js** + `cytoscape-dagre` + `cytoscape-expand-collapse` | **Winner**: dagre auto-layout, true compound nodes, off-the-shelf expand/collapse, click handlers — all from plain `<script>` CDN tags, zero build |
| React Flow | Prettiest, but React + vite build + the expand-collapse example is **paywalled (Pro)** |
| Mermaid | Zero-build interim for the level-1 static view (`classDef` status colors, `click` callbacks with `securityLevel:'loose'`); weak interactivity; fine to start, upgrade later |
| vis-network / d3-dag / dagre-d3 | Pass (weak DAG layout / unmaintained / high effort) |
| Svelte Flow | Same build cost as React Flow, no advantage |

**Live updates**: single local user → **2s htmx polling is entirely sufficient**; SSE is the clean upgrade; WebSockets buy nothing (approvals are plain POSTs).

## 4. Dashboard base patterns

- **FastAPI + Jinja2 + htmx (+ SSE)** — the reference no-build stack; proven on a 1.4M-doc SQLite app. htmx handles every non-graph page; graph pages get one JS library.
- **Datasette** on a second port = free read-only raw-DB debug console (`datasette studio.db`).
- Streamlit: fights a live stateful canvas (rerun model); throwaway-v0 only. NiceGUI: best pure-Python fallback (`ui.mermaid`, `ui.timer`). Textual TUI: DAG edges in a terminal — skip.

## 5. Recommended stack

> **FastAPI + Jinja2 + htmx (2s polling → SSE later) + Cytoscape.js (vendored locally, dagre + expand-collapse) + existing SQLite. Zero npm, zero build, ~5 frontend files.**

Design decisions distilled:
1. Graph shape from a **static pipeline definition** (Python/YAML); DB overlays status only.
2. **Navigate-into + breadcrumb** between levels; each page a small flat dagre graph.
3. **Fan-out = partition bar** + count; click → htmx table with per-row status/cost/retry.
4. **Fixed palette** (Airflow + one): green=done, blue pulsing=running, gray=pending, bold outline=next-up (deps met), red=failed, **amber+pause=awaiting_approval**. Icon + color + always-visible legend + roll-ups.
5. **Approvals = Prefect pattern**: inline Approve/Reject (htmx POST) + a global "Needs attention" strip on every page.
6. **Thumbnails on nodes/rows** for media-producing substeps (ComfyUI/Deadline lesson).
7. Status patching in place — statuses change, shape doesn't → no re-layout flicker.
8. Cost = plain columns + a topline credits/budget meter (no OSS orchestrator does in-graph cost well; Deadline's ledger columns are the model).

Component list: `app.py` (3 page routes + `/api/graph`, `/api/status`, `/api/approve|reject`), `templates/` (base, books_list, book_detail, graph), `static/graph.js` (~150 lines), vendored htmx+cytoscape, pipeline-definition module.

## 6. Wireframes (words)

- **Screen 1 — Architecture (home)**: top bar with credits/budget meter + amber "Needs attention (2)" strip (all paused/failed items, jump links). Canvas: L→R DAG of big steps (Parse → Analysis → … → Publish); each node = card with status icon, "7/10 substeps", mini segmented bar, active-book badge. Book-selector scopes to one book or aggregate. Click → Screen 2.
- **Screen 2 — Stage detail** (*All books › Moby-Dick › Analysis*): A0-A9 sub-DAG; A3 carries the 27-segment bar; awaiting_approval nodes show inline Approve/Reject; failed show error snippet + Retry. Right panel on node click: timestamps, duration, cost, log tail, thumbnails, approve with comment. Clicking A3's bar swaps panel to the 27-row chapter table.
- **Screen 3 — Books list**: Deadline-style table — thumbnail, title, current stage, **one segmented bar of all big steps per row**, attention badge, credits spent, last activity. "Attention first" default sort. Header totals.

Estimated build: htmx pages + API ≈ a day; Cytoscape graph page ≈ a day; Mermaid interim Screen 1 ≈ an hour.

(Source links preserved in the task transcript; key ones: Dagster discussions #16657/#14182, Airflow UI docs, Prefect interactive docs, Temporal DAG-view gap thread, cytoscape.js-expand-collapse, FastAPI+htmx guides, Deadline Monitor manual, ComfyUI frontend internals.)
