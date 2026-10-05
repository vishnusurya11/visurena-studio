# V04 — JSON / prompt / log viewer, inside the in-page viewer

Researcher V04, 2026-10-04. Scope: the doc pane of the popup viewer (brief v3). It opens prompt JSONs, unit
JSON, JSONL and logs, without leaving the page. Every file named below was opened read-only under
`library/20260827135508_the-war-of-the-worlds/episodes/{ep12,ep17}` and `logs/20260827135508/episode/`.

## 1. What the files actually are (measured, not assumed)

| File (real) | Size | Nodes | Shape | What the owner reads in it |
|---|---|---|---|---|
| `ep17/takes/r2v/prompts.json` | 111 KB | 587 | array of 22 take objects; `prompt` up to **5,310 chars** with `\n` | the prompt, as prose; `refs[]`; seed |
| `ep12/storyboard/eye_c7e3eb93.json` | **137 KB** | **5,005** | `{verdict, note (11,143 chars), faults[531]}`. Faults are 520 landmark, 9 framing, 2 hat | the verdict, then faults grouped by kind |
| `ep17/plan.json` | 60 KB | 947 | `setups{}` + `shots[24]` of the same keys | the shots, as a table |
| `ep12/plan.verdict.json` | 2 KB | — | `verdict`, `note`, `signed_by` | one line: APPROVE · judge:plan@1 |
| `ep12/qc_r2v.json` | 18 KB | — | flat scalars + `planned_cuts[23]` and `seen_cuts[27]` as float arrays | lufs_ok, tp_ok, missing_cuts |
| `ep12/takes/r2v/T00.dq.json` | 40 KB | 1,535 | `gates[24]{name,value,ok,hard,note}` + numeric arrays | which gate failed |
| `ep12/takes/r2v/T00.graph.json` | 8 KB | — | ComfyUI API graph, keys "1","2"… with `class_type` | the node list |
| `storyboard/grids/*.txt` + `*.json` | 1–6 KB | — | prose prompt with `PANEL n (row r left), SIZE:` and `<image1>`. The json holds seed, shots, plan hash | the panel prompts |
| `learnings.jsonl` (ep12 19 rows, ep17 40 KB) | ≤40 KB | — | 12 fixed keys: `ts step gate measured threshold action attempt seconds terminal note` | rows; the `note` field (up to 11 KB) |
| `timing.jsonl`, `drive.jsonl` | ≤4 KB | — | `{stage, started, seconds, ok}` / `{ts, event, sha, outcome}` | table |
| `logs/…/episode/*.log` (136 files, 1.1 MB in all, largest 46 KB) | ≤46 KB | — | **JSONL**: `{ts, level, codex_id, stage, step_id, msg}`. Levels seen: INFO 322, WARNING 681, no ERROR | level, step, the multi-line `msg` |
| `ep17/drive_run0N.log` | ≤2 KB | — | **plain text**: `[drive] …`, `warning: …`, a Python traceback, `ok` | the refusal line |
| book level (not per unit): `screenplay.json`, `casebook/labels.jsonl` | **2.1 MB / 1.0 MB** | — | — | rarely; this is the size ceiling to design for |

Three findings drive the design:
1. **The strings are the content.** The owner opens a prompt JSON to read the prompt, a verdict for its note, a
   log for its msg. Escaped one-liners (`"subject_definitions:\n<Subject 1> is…"`) are what generic viewers show.
2. **Most payloads are arrays of same-shaped objects** (faults, gates, shots, takes, learnings, log lines). A
   table reads them better than a tree.
3. **The strings hold angle-bracket tokens** (`<Subject 1>`, `<Picture 1>`, `<image1>`). `innerHTML` deletes them
   silently as unknown tags, so every value goes through `textContent`. This is a correctness rule, not only a
   security one.

## 2. What the outside world does (and what we take)

| Tool (source) | What it does | What we take |
|---|---|---|
| Firefox JSON viewer — https://firefox-source-docs.mozilla.org/devtools-user/json_viewer/ | Tabs JSON / Raw Data / Headers; *Filter JSON* hides non-matching rows; Expand/Collapse all, Copy, Save; Pretty Print in Raw | A view tab strip and filter-to-matching-rows |
| Chrome DevTools Network Preview / Response — https://developer.chrome.com/docs/devtools/network/reference#preview | A lazily expanded tree whose children are built on open, a one-line preview of a collapsed object, and `{}` pretty-print on raw text | Build children on expand: never build all 5,005 verdict rows up front. Collapsed-object previews |
| VS Code Peek (`Alt+F12`) — https://code.visualstudio.com/docs/editing/editingevolved#_peek | An inline panel over the code that closes on `Esc` and never navigates | The doc pane is a peek beside the media, not a page |
| Postman response viewer — https://learning.postman.com/docs/sending-requests/response-data/responses/ | Pretty / Raw / Preview / Visualize; find with "3 of 41", next and previous | The `n of m` counter and Enter / Shift+Enter |
| Insomnia — https://docs.insomnia.rest/insomnia/responses · jqplay — https://jqplay.org | JSONPath / jq filters | Defer the filters, because the owner searches words. Take the jq path syntax for *copy path* |
| GitHub file view — https://docs.github.com/en/repositories/working-with-files/using-files/getting-permanent-links-to-files | Raw, copy-raw, line gutter, permalinks, soft wrap on prose | "Copy all" next to "Open raw", and a wrap toggle |
| Grafana Logs panel — https://grafana.com/docs/grafana/latest/panels-visualizations/visualizations/logs/ | A level colour bar per line; toggles for Wrap, Prettify JSON, Dedup and Newest first; a row expands to fields | Level bar plus chips, newest-first, row expand |
| Datadog Log Explorer — https://docs.datadoghq.com/logs/explorer/ | Status column, facet counts, click a facet to filter, a row opens its JSON attributes | Facet chips with counts that toggle a filter |
| Langfuse / LangSmith — https://langfuse.com/docs/observability/overview · https://docs.smith.langchain.com/observability | LLM input and output render as message cards with markdown; a toggle switches to raw JSON | **Prompts are prose by default**, with JSON one toggle away |
| WAI-ARIA tree pattern — https://www.w3.org/WAI/ARIA/apg/patterns/treeview/ · https://web.dev/articles/content-visibility | Keyboard model; cheap offscreen rows | Tree keys and `content-visibility: auto` |

## 3. The design: one pane, four views, picked by file

The doc pane lives inside the viewer dialog (owned by the lightbox researcher). It is full-height on the
right at ≥ 1024 px, and a full-screen sheet below that. Header: the file name in mono, then size · rows or
nodes · mtime. Then a segmented control holding only the views that make sense for the file:

| View | Key | Default for | What it is |
|---|---|---|---|
| **Read** | `1` | `prompts.json`, grid `*.txt`, `*.verdict.json`, `eye_*.json`, `speaker_check.json` | Lead fields as a header card, then prose fields as paragraphs, then everything else as a compact tree |
| **Table** | `2` | `*.jsonl`, `*.log`, and any array of ≥ 3 same-key objects | Columns from the union of keys; rows expand |
| **Tree** | `3` | `plan.json`, `qc_r2v.json`, `*.dq.json`, `*.graph.json`, `manifest.json` | Foldable tree, built lazily |
| **Raw** | `4` | — | The original bytes as fetched, tokenised and coloured, soft-wrapped, with a line gutter |

### 3a. Read view: prompts as prose
- **Prose-field rule:** a string is prose when it contains `\n` **or** has ≥ 120 chars **or** its key is in
  `{prompt, note, notes, msg, how, at_rest, motion, described, mode}`. It renders as a block in the text font
  (Plex Sans, 14/22), `white-space: pre-wrap`, `max-width: 72ch`, with real line breaks and no quotes or
  escapes. The key sits above it as a small mono label.
- **Structure inside a prompt:** a line matching `^[a-z_]+:$` (`subject_definitions:`) or `^PANEL \d+ \(` (grid
  txt) becomes a heading-weight line. Nothing else is parsed, so it stays honest.
- **Token chips:** `<Subject n>`, `<Picture n>` and `<imageN>` render as inline chips (mono 12 px, surface-2,
  rule-2 border). In `prompts.json` a `<Picture n>` chip maps to `refs[n-1]`. Hovering or focusing it shows the
  160 px thumb from `/thumb/<id>/160/<rel>`, and clicking it opens that picture in the same viewer. This is
  the one thing no generic viewer can do, and it answers "which picture did the model see?".
- **Lead-field header card:** any of `verdict, terminal, action, ok, outcome, signed_by, signed_at, score,
  lufs_ok, tp_ok` that is present renders first as label:value chips. Verdict values reuse the status tokens
  (APPROVE → done, keep_best / flag → flagged, REFUSE → failed). `plan.verdict.json` reads in one glance.
- **Big arrays inside Read** (531 faults) become a group summary: `landmark 520 · framing 9 · hat 2`, grouped by
  the first low-cardinality string key (`kind`, `name`, `gate`, `step`). Each chip opens Table view filtered to
  that group.
- **Long prose clamp:** above 1,200 chars, show 12 lines, then a "Show all 11,143 characters" button (a
  `<button>` with `aria-expanded`). Search hits inside a clamped block unclamp it.

### 3b. Table view: JSONL, logs and homogeneous arrays
- Columns come from key order in the first row, plus later new keys. Columns that are null in every row are
  hidden. Prose columns (`note`, `msg`) get the remaining width as **one clamped line**, and a row click
  expands it to a full-width prose block under the row (Grafana, Datadog).
- **Logs** (`logs/…/*.log`, JSONL with `level`): a 3 px left bar plus a level chip per row, and facet chips in
  the toolbar, `INFO 322 · WARNING 681`, which toggle a filter (Datadog). Also: `ts` shown as local `HH:MM:SS`
  with the full ISO time on hover, a `step_id` column, newest-first by default (Grafana), and a wrap toggle (`w`).
- **Plain-text logs** (`drive_run0N.log`): lines are classified by regex, never re-levelled by guess.
  `^warning:` → WARNING, `^Traceback|^\s+File ".+", line \d+` → folded into one "traceback (6 lines)" block,
  `^\w+Error:` → ERROR, `^\[drive\]` → INFO. One more marker appears whatever the level: an **outcome chip** on
  any line that contains `refused` / `REFUSED`, because the episode logs emit refusals at WARNING (681 of them),
  and the refusal is what the owner is looking for.
- **learnings.jsonl**: columns are `ts · step · gate · measured/threshold · action · attempt · note`, with
  `action` rendered as a chip (improve, keep_best, flag).
- Rows past 200 render in pages of 200 behind a "Show 200 more", with `content-visibility: auto;
  contain-intrinsic-size: auto 32px` on every row. No virtual scroller is needed at these sizes (largest log:
  hundreds of lines).
- **Phone (< 600 px):** each row becomes a 2-line card: chip, time, step on line 1, the clamped prose on line 2.

### 3c. Tree view
- Rows: `▸ key: value`, 12 px indent per level, with indent depth capped visually at 8 and the deeper levels
  shown by a depth number. Arrays of scalars render inline and wrap: `planned_cuts [23] 0.0, 2.91, 5.75, …`.
  They never become 23 rows.
- **A collapsed object shows a preview** (Chrome): `{kind: "landmark", where: "shot_00", …}`, and a label from
  the first of `name, class_type, kind, step, setup, index` that is present. With that, `T00.graph.json` reads as
  `"7" · KSampler`, and plan shots read as `#4 · road_east · MEDIUM`.
- **Default depth:** expand to depth 2 when there are < 300 nodes, otherwise depth 1. Children are built on
  first expand (Chrome Preview). Expand-all on a node with > 2,000 descendants asks first, as an inline line,
  not a modal.
- Strings in the tree follow the prose rule from 3a but clamp to 2 lines. Escapes are never shown.

### 3d. Raw view
- Shows **the fetched text**, not `JSON.stringify`, so key order, float spelling (`6.833333`) and whitespace are
  exactly what is on disk. A **Pretty** toggle (Firefox) re-indents minified files, which is only needed for
  `*.graph.json`. Line-number gutter, soft wrap on by default, **Open raw** opens
  `/lib/<id>/<rel>` in a new tab (the one place a new tab is right).

## 4. Colour tokens (Studio black + Graphite), measured WCAG contrast

Strings are not given a loud hue: they are the prose, so they take the ink colour. Keys and scalars carry the
colour. Status hues (blue, green, amber, violet, red) stay with their status meaning. Token hues sit at a
different lightness or saturation, and verdict chips use the status tokens themselves.

| Token | Studio black | on `--code` #1b1d21 | on `--overlay` #24262b | Graphite | on #ffffff | on `--code` #eceef2 |
|---|---|---|---|---|---|---|
| `--tok-key` | #9ec1ff | 9.26 | 8.31 | #1d4fa8 | 7.68 | 6.61 |
| `--tok-str` (prose) | #e3e5e8 | 13.37 | 12.00 | #111318 | 18.58 | 16.00 |
| `--tok-num` | #f2a679 | 8.44 | 7.57 | #9a3412 | 7.31 | 6.29 |
| `--tok-bool` / null (italic) | #d0a8ff | 8.62 | 7.73 | #6b21a8 | 8.72 | 7.51 |
| `--tok-punct`, gutter, `▸` | #8e9199 (=ink-3) | 5.35 | 4.80 | #5f6672 | 5.78 | 4.98 |
| level INFO / WARNING / ERROR | st-running / st-flagged / st-failed | 7.77 / 8.92 / 5.93 | | #1f5a86 / #8a5a00 / #b42d1a | 7.33 / 5.93 / 6.30 | |
| search hit (bg / current) | `#5a4a12` / `#7a5a00` with ink text | 7.41 / 6.38 | | #fde68a / #f59e0b, ink text | 14.92 / 8.65 | |

Everything is ≥ 4.5:1 (AA for body text). Pane background: `--code`. Selected or focused row: `--focus-bg`
plus a 2 px `--focus` left rule (the sidebar's `aria-current` idiom).

## 5. Search, fold, copy, keys

- **Search** (`/` or `Ctrl+F` while focus is inside the dialog; the browser's find bar stays reachable with a
  second `Ctrl+F`): it searches **the data model, not the DOM**, so unbuilt tree nodes and clamped prose are
  found too. The counter shows `3 of 41`, with `Enter` / `Shift+Enter` for next and previous and `Esc` to clear.
  The counter is an `aria-live="polite"` region. Each hit expands its ancestors, unclamps its block, and
  scrolls `block: center`. Scope chips are *keys · values* (both on by default). In Table view a
  **Filter rows** checkbox hides non-matching rows (Firefox's Filter JSON). Debounce is 120 ms. A query
  under 2 chars matches nothing.
- **Fold:** click the row or press `←`/`→`. `*` expands siblings (APG). `Alt+click` expands the subtree.
  `[`/`]` collapse or expand all. Fold state is kept per file path in `sessionStorage`, inside try/catch.
- **Copy:** a row menu (hover icon, or `c` on the focused row) offers **Copy value** (a string copies raw,
  without quotes or escapes, so a prompt pastes as a paragraph; an object copies pretty-printed JSON),
  **Copy path** in jq form `.faults[12].note` (a key that is not an identifier becomes `["7"]`), and **Copy row
  as JSON** in Table view. Toolbar: **Copy all** (the original text) and **Open raw**. Writes go through
  `navigator.clipboard.writeText`, since 127.0.0.1 counts as a secure context. Fallback: a hidden textarea plus
  `execCommand('copy')`. Each copy confirms with the existing `.toast`: "Copied .faults[12].note".
- **Key ownership:** when focus is in the tree or table, `←`/`→` belong to it, so the lightbox's previous/next
  file moves to `J`/`K` (and `PageUp`/`PageDown`) inside a doc pane. When focus is on the pane header, `←`/`→`
  navigate files as for images. Flag for the lightbox researcher: this is the one collision.
- **ARIA:** Tree uses `role="tree"`, rows `treeitem` with `aria-expanded`, `aria-level`, `aria-setsize` and
  `aria-posinset`, and a roving `tabindex`. Table uses a real `<table>` with `<th scope=col>`, and an expanded
  row's detail sits in a `<tr>` with `colspan`. Read view uses `<section>`s with a `<h3>` per lead group. The
  dialog's focus trap and `Esc` come from the shell. `Esc` clears search first, then closes.

## 6. Size limits and lazy rendering

| Fetched size | Behaviour |
|---|---|
| ≤ 256 KB (every unit file today; the max is 137 KB) | parse, open the default view, depth-2 tree |
| 256 KB – 2 MB (book-level `screenplay.json` 2.1 MB, `labels.jsonl` 1.0 MB) | parse in a `requestIdleCallback` slice (JSON.parse runs at about 1 ms per 100 KB, so it is fine), tree at depth 1, tables paged by 200 |
| 2 – 10 MB | Raw view only, first 512 KB, with "Load the rest (n MB)". Tree is offered after an explicit click |
| > 10 MB, or non-UTF-8 | no render: size, mtime, **Open raw**, **Copy path** |

- **Fetch:** `GET /lib/<id>/<rel>` as text, kept for Raw and Copy all, parsed once. Navigating away aborts the
  fetch (`AbortController`). An LRU of the last 8 files makes `J`/`K` back and forth instant.
- **Running units (ep17):** a **Follow** toggle refetches `Range: bytes=<lastSize>-` every 5 s and appends only new
  lines to `learnings.jsonl` and logs. It pauses when `document.hidden`. The route already serves ranges for mp4.
- **DOM budget:** about 1,500 live rows at most. Tree children are built on expand, tables paged, prose clamped.

## 7. Vendor or hand-write? (measured from jsDelivr, 2026-10-04)

| Option | Raw | gzip | Covers |
|---|---|---|---|
| renderjson 1.4.0 | 11.5 KB | 3.3 KB | tree only, innerHTML-free, no search, no table, no prose |
| json-formatter-js 2.5.23 (UMD) | 14.3 KB | 3.3 KB | tree plus a preview line; no search; its own CSS theme to override |
| @alenaksu/json-viewer 2.1.2 (web component) | 44.3 KB | 11.9 KB | tree plus search; shadow DOM fights our tokens |
| @andypf/json-viewer 2.1.10 | 33.9 KB | 11.4 KB | tree plus themes |
| highlight.js 11.11 core + json | 20.4 + 0.5 KB | 8.2 + 0.4 KB | colours text only (Raw view) |
| Prism 1.30 core + json | 19.7 + 0.4 KB | 7.4 + 0.3 KB | colours text only |
| vanilla-jsoneditor 3.3.1 | 1,222 KB | 356 KB | everything; absurd here |
| **Hand-written `docview.js` (estimate)** | **≈ 9–11 KB** | **≈ 3.5 KB** | tree, Read, Table, Raw, search, copy, logs, chips |

**Recommendation: hand-write it.** No library ships the parts that matter here: prose lifting, `<Picture n>`
chips, homogeneous-array → table, log facets, outcome chips. All of them would need wrapping, and still need
their CSS overridden. Tokenising is free: the Tree, Read and Table views render from the parsed object, so a type
check *is* the highlighter. Raw view needs one ~25-line regex tokenizer for JSON text
(`/"(?:\\.|[^"\\])*"(?=\s*:)|"(?:\\.|[^"\\])*"|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null|[{}\[\],:]/g`),
emitting text nodes into `<span class>`, never innerHTML. That is cheaper than 8 KB gz of highlight.js core.
Split it per the repo's 10–20-line-function rule into about 30 functions (`isProse`, `leadFields`, `groupKey`,
`buildRow`, `jqPath`, `classifyLogLine`…). Each is pure and unit-testable without a browser except the DOM
builders. The real board serves the same file from `static/`, with no build step.

**Publishable:** a dependency-free ~10 KB "prompt-aware JSON/JSONL/log viewer" (prose lifting, ref-token chips,
log facets). It generalizes to any LLM pipeline's artefacts and could ship as a standalone MIT package once it is
stable in the board.

## Top 8 recommendations

1. **Render every value with `textContent`, never `innerHTML`.** `<Subject 1>`, `<Picture 1>` and `<image1>`
   in the real prompts otherwise vanish silently. Make it a test: render `prompts.json[0]` and assert that the
   `<Picture 1>` text survives.
2. **Read view is the default for prompt and verdict files.** Prose fields (newline, ≥ 120 chars, or a named key)
   render as wrapped Plex Sans paragraphs at 72ch, with no quotes or escapes. Lead fields (`verdict, terminal,
   signed_by, action, ok, score`) go in a header card.
3. **`<Picture n>` chips in `prompts.json` resolve to `refs[n-1]`**: a thumb on hover, a click opens the picture
   in the same viewer. This is the cross-link between prompt and image that the owner's request implies.
4. **An array of ≥ 3 same-key objects becomes a table**, with group chips on its first low-cardinality key.
   eye_c7e3eb93's 531 faults read as `landmark 520 · framing 9 · hat 2`, not as 531 tree rows.
5. **Logs are JSONL tables with level facets** (`INFO 322 · WARNING 681`), plus an outcome chip for
   `refused`/`REFUSED`. Plain `drive_run*.log` lines are classified by regex, with tracebacks folded into one
   block. Newest-first, a wrap toggle, and Follow via Range requests for running units.
6. **Search runs over the data model with an `n of m` counter** (aria-live). It expands ancestors, unclamps
   prose, and has an optional Filter rows. Copy value (raw string), Copy path (jq `.faults[12].note`) and Copy
   all (the original bytes) are confirmed by the existing toast.
7. **Size tiers:** at ≤ 256 KB do everything; up to 2 MB, depth-1 and paged; up to 10 MB, Raw-first with 512 KB
   shown; above that, Open raw only. Build tree children lazily, page table rows by 200, and use
   `content-visibility: auto` on rows.
8. **Hand-write `docview.js`** (≈ 10 KB raw / 3.5 KB gz, about 30 small pure functions with tests) rather than
   vendoring renderjson (11.5 KB) plus highlight.js core (20.4 KB). Use the token colours in §4: all of them are
   ≥ 4.8:1 on Studio black and ≥ 4.98:1 on Graphite.

## 2 disagreements I expect

1. **Default view: Read (lifted prose) versus Tree (faithful structure).** A debugger-minded reviewer will say
   that hiding quotes and escapes misrepresents the data, and that a trailing space or a `\n\n` difference in a
   prompt can matter to the model. My answer: Raw is one key away (`4`) and shows the exact bytes, and Copy value
   copies the exact string. But the owner opens these files to *read* them, and Langfuse and LangSmith made the
   same call. If the debate goes the other way, keep Read as the default only for `prompts.json` and grid `.txt`.
2. **Hand-written versus vendored.** Reviewers will say renderjson is 3.3 KB gz and already tested. My answer: it
   covers only the tree, the least important of the four views, and still needs a theme override plus a wrapper
   for chips and search. The custom parts are the bulk of the code either way. A smaller dispute sits alongside:
   **`←`/`→` fold the tree inside the doc pane, so file navigation moves to `J`/`K`**, and the lightbox researcher
   may want arrows to always mean previous/next.
