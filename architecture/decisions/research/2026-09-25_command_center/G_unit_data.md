# G — The unit page's data: structure inside the raw text

2026-09-26 · research, read-only · measured on `episode/ep13` (running, 24 passes) and `episode/ep12` (finished).
Prototype parsers (scratch, not committed) ran against every real row; the numbers below are theirs.

## 0. What the page dumps today, and the brick under it

`views.unit()` hands the template `learnings` (last 8 rows, `note` verbatim — ep13 notes run 0 B to 11 KB,
the file is 90 KB / 64 rows), `log` (last 20 WARNING+ rows of the run's log — 82 % of all log bytes are
`plan_check refused:` bodies), `timing` (151 rows keyed by *script* name, not step) and the step chips
(`work_steps.seconds` is **0.0 on every ep13 row** — the runner never writes it).

The brick: **every line of that text is a Fault** — `(kind, where, note)` from `studio/judges/verdict.py` —
serialised by exactly two writers:

| writer | grammar |
|---|---|
| `verdict.summary()` → learning `note`, `plan.verdict.json.note`, `events.detail` (DEFERRED) | `fault_line ( "; " fault_line )* [ " -> " terminal ]`, `fault_line = kind " at " where [ ": " note ]` |
| `plan_check.py` stdout → a `battery` fault's `note` (one line each), and the whole log msg | `SECTION_NAME<pad>: head` lines, items indented 3–4 spaces: `CODE where: text`, `  advisory: …` |

So one parser per writer, composed: `split_note` → faults; a fault of kind `battery` → `battery_item`.
The trap: `"; "` also occurs *inside* notes (ep13 row 14: `'slowly'); the owner's rule…`) — a plain
`split("; ")` shreds them. Split on the **lookahead of the next fault head** instead.

## 1. A learning row → a row with faults

Shape:
```
{ts, step, gate, rung: action, attempt, seconds, terminal: bool, ended_as: str,   # " -> x" suffix, else action if terminal
 measured, threshold, faults: [{code, kind, where, text, advisory: bool}]}
```
Rules (tested):
```python
TERMINAL    = re.compile(r" -> (?P<terminal>[a-z_]+)$")
FAULT_START = re.compile(r"(?:^|; )(?P<kind>[a-z][a-z_-]*) at (?P<where>[^\s:;]+(?::\d+(?:\.\d+)?)?)(?=: |; |$)")
SECTION     = re.compile(r"^(?P<name>[A-Z][A-Za-z /-]*?[A-Za-z])\s*:\s?(?P<head>.*)$")
ITEM        = re.compile(r"^\s{2,}(?P<code>[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*|L\d+) "
                         r"(?P<where>plan|shots? \d+(?:-\d+)?|setup '[^']+'|lines?[ .]\d+)[: ] ?(?P<text>.*)$")
ADVISORY    = re.compile(r"^\s+advisory:? (?:(?P<code>[A-Z][A-Z0-9-]*) )?(?P<where>shot \d+|plan|setup '[^']+')?:? ?"
                         r"(?:(?P<code2>[A-Z]\d+): )?(?P<text>.*)$")
INFO        = re.compile(r"^\s{3,}(?P<text>(?:not applicable|the sheet gate).*)$")
CONTRACT    = re.compile(r"^CONTRACT (?P<where>(?:shots|lines)\.\d+|OK|:)?:? ?(?P<text>.*)$")
```
Order inside `battery_item`: ITEM (unless it starts `advisory`) → ADVISORY → INFO → CONTRACT → SECTION.
A SECTION hit inside a learning becomes `{code: <section name>, where: "plan", text: head, head: True}` —
the template shows heads as a grey sub-row, never as a fault badge.

```python
def split_note(note: str) -> tuple[list[dict], str]:
    """(faults, terminal) from a verdict.summary() string; '; ' inside a note stays in its note."""
    m = TERMINAL.search(note or "")
    body, terminal = (note[:m.start()], m["terminal"]) if m else (note or "", "")
    heads = list(FAULT_START.finditer(body))
    out = []
    for a, b in zip(heads, heads[1:] + [None]):
        text = body[a.end():b.start() if b else len(body)]
        out.append({"kind": a["kind"], "where": a["where"], "text": text.removeprefix(": ")})
    return out, terminal

def battery_item(line: str) -> dict | None:            # ~15 lines, the order above
def learning_row(row: dict) -> dict:
    """The row with `faults` parsed and `note` dropped; a battery fault becomes its plan_check item."""
    faults, ended = split_note(row.get("note", ""))
    parsed = [expand(f) for f in faults]                # battery -> battery_item(text) or {code:"", text}
    return {**{k: row.get(k) for k in KEEP}, "rung": row.get("action"), "faults": parsed,
            "ended_as": ended or (row.get("action") if row.get("terminal") else "")}
```
**Measured**: ep13 **64/64 rows parse cleanly**, ep12 **19/19**; 726 ep13 fault items, 12 without a code —
all 12 are the bare `battery at plan` (a battery fault with an empty note; rows 0–4: "battery at plan" ×5,
the very case `fault_line`'s docstring complains about). First pass before fixes: 53/64 — the 11 failures
were the full-refusal rows (G-LIGHT has a hyphen the SECTION regex lacked; `  advisory shot 13 M6:` is the
MOTION advisory form; `not applicable: …` is an info line). `battery at plan` count == battery faults on
every row (0 mis-splits). ep13 codes: G-SOURCE 74, G-SIZE 56, CONTRACT 40, G-AIM 31, G-FIRSTFRAME 25,
G-SYNC 18, G-VARIETY 16, TAKE BUILDER 12, G-STORY 9, M2 9, G-MOVES 8, G-LAID 7, M6 6; non-battery kinds:
posture 85, framing 85, blur 14, invented 11, people 5, stacked 4, missing 4, banned 4, clones 1.

Caveats the template must carry: (a) plan_check truncates items at 140–170 chars (`measured non…`) — show
the text as-is with a trailing `…` when it is exactly at the cap; (b) `ended_as` can differ from `action`
(ep13 row 4: action `keep_best`, note `-> defer`) — the note's suffix is the truth; (c) G-LIGHT's head is a
Python list repr — `ast.literal_eval` it into items (`setup 'x'`), fallback raw.

Tests: `test_split_note_keeps_semicolons_inside_a_note` (row-14 shape), `test_split_note_reads_the_terminal`,
`test_battery_item_reads_each_form` (parametrised: ITEM, `advisory:`, `advisory shot N M6:`, info, CONTRACT
`shots.8`, `CONTRACT OK`, `CONTRACT :`, SECTION with hyphen), `test_learning_row_prefers_the_note_suffix`.
Fixtures: one line per form, copied from the real rows above with the book words replaced.

## 2. A plan_check refusal → sections

Shape: `{title, shots, projected_s, verdict: "REFUSED"|"clean", sections: [{name, count, items:[{code, where, text, advisory}]}],
counts: {code: n}}`. `count` is the head's integer, `0` for `clean`/`all bound`/`every shot …`, `len(list)` for
a list repr (MOTION hard `[(16, 'M2')]`).
```python
def refusal_sections(text: str) -> list[dict]:
    """plan_check stdout as sections; an unindented line opens one, an indented line is its item."""
    sections = []
    for raw in text.splitlines():
        if not raw.strip() or raw.startswith("plan_check refused"):
            continue
        item = battery_item(raw)
        if raw[:1] != " " and item and "section" in item:
            sections.append({"name": item["section"], "head": item["head"], "items": []})
        elif sections:
            sections[-1]["items"].append(item or {"code": "", "where": "", "text": raw.strip()})
    return sections

def refusal_counts(sections: list[dict]) -> dict[str, int]:     # Counter over item codes, info excluded
def refusal_title(sections) -> dict:                            # CONTRACT OK: <title> | N shots | Ns projected
```
**Measured**: all **27/27** refusal messages in the 29 episode logs of this book parse; 425 items, **135 unique
(code, where)**; 187 items are carried unchanged from the previous refusal. Codes across all 27:
G-SOURCE 126, G-SIZE 95, G-AIM 59, G-FIRSTFRAME 42, G-VARIETY 25, M6 22, CONTRACT 20, G-SYNC 20, M2 17,
G-MOVES 16, G-LAID 14, G-STORY 13, M5 12, M4 6, G-PLACE 5, G-ANCHOR 4, G-MOVE 1 (+14 info lines).
Test: `test_refusal_sections_reads_a_full_body` (fixture = one real body, book words neutralised),
`test_refusal_counts_skip_info`, `test_a_head_with_a_list_counts_its_length`.

Finding: the `CONTRACT OK:` title varies inside one unit — ep13's drafts were titled "The Path Northward",
"The Smoke and the Signal", "How I Fell into the Hands of the Enemy", "The Destruction of Weybridge" before
landing on its own chapter. The page should show the title per refusal: it is how the owner sees the writer
drafting the *wrong chapter*.

## 3. Attempt history → one row per PASS

`work_orders.attempts = 24` is `count(distinct run_id)` in `events` for the unit. A pass is a run_id.
Shape: `{run_id, started, ended, ended_on: step_id, how: completed|failed|deferred|running|killed, detail,
done: [step_ids completed], ladder: ["PLAN:improve", …], learnings: n, script_s, wall_s}`.
```python
def passes(events: list[dict], learnings: list[dict], timing: list[dict], live_run: str | None) -> list[dict]:
    """One row per run_id, in order; a run with no closing event ends where the next run starts."""
    runs = group_by_run(events)                                   # OrderedDict run_id -> events, skipped kept
    starts = [es[0]["event_ts"] for es in runs.values()] + [None]
    out = []
    for (rid, es), nxt in zip(runs.items(), starts[1:]):
        acted = [e for e in es if e["event"] != "skipped"] or es
        last = acted[-1]
        how = last["event"] if last["event"] in ENDS else ("running" if rid == live_run else "killed")
        end = es[-1]["event_ts"] if how in ENDS else (nxt or now_utc())
        out.append({"run_id": rid, "started": es[0]["event_ts"], "ended": end, "ended_on": last["step_id"],
                    "how": how, "detail": one_line(last["detail"]), "done": completed(es),
                    "ladder": rungs_between(learnings, es[0]["event_ts"], end),
                    "script_s": seconds_between(timing, es[0]["event_ts"], end)})
    return out
```
Joins: learnings `ts` are UTC `Z` (join directly); **timing `started` is naive LOCAL time**
(`datetime.fromtimestamp` in `episode_clock.stamp`) — convert with `.astimezone(timezone.utc)` or the join is
7 h off. `ladder` drops `action == "pass"` rows. Query (read-only):
`SELECT event_ts, step_id, event, run_id, detail FROM events WHERE codex_id=? AND stage=? AND unit=? ORDER BY id`
(24 of ep13's 170 events have `order_id` NULL — filter on `unit`, not `order_id`).

ep13's real passes, first 10 of 24 (UTC; `script s` = timing rows inside the window):

| # | run (…suffix) | started → ended | ended on | how | ladder climbed | script s | wall s |
|---|---|---|---|---|---|---|---|
| 1 | 20260925174025 | 09-25 17:40 → 17:40 | 01 | completed | — | 0 | 0 |
| 2 | 20260925201818 | 20:18 → 20:26 | 03 | failed: `places.py exit 1` | PLAN improve, improve, fresh_brief, model_tier, keep_best | 0 | 479 |
| 3 | 20260925204331 | 20:43 → 20:54 | 02 | deferred: `CONTRACT lines.6` 19 words | PLAN ×4 rungs → keep_best | 0 | 656 |
| 4 | 20260925205821 | 20:58 → 21:00 | 02 | failed: StructuredOutputException | — | 0 | 151 |
| 5 | 20260925210339 | 21:03 → 21:15 | 02 | deferred: `CONTRACT shots.5` 'slowly' | PLAN ×4 → keep_best | 0 | 706 |
| 6 | 20260925211920 | 21:19 → 21:36 | 02 | deferred: 80 battery faults | PLAN ×4 → keep_best | 0 | 1033 |
| 7 | 20260925213938 | 21:39 → 22:10 | 02 | deferred: `CONTRACT : a line's shot…` | PLAN ×4 → keep_best | 0 | 1878 |
| 8 | 20260925221204 | 22:12 → (next run) | 02 | killed (no closing event) | PLAN improve, improve (learnings 25–26) | 0 | — |
| 9 | 20260926101419 | 09-26 10:14 → 10:14 | 01 | completed | — | 0 | 0 |
| 10 | 20260926104048 | 10:40 → 10:51 | 04 | failed: `say_lines.py exit 1` | (PLAN pass) | 603 | 636 |

The rest, compressed: 11 fail at 06 (`takes_r2v.py`), 12 killed in 08, 13 fail 08 (`panels.py`), 14 fail 07
(`grids.py`, 1204 s), 15–16 killed, 17 fail 02 `INVALID VERDICT: … battery at plan x13`, 18 killed in 08,
19 bind only, **20–23: four passes of 1.5–1.7 h each** all ending on 08/09 (EYE_PANELS redraw_grid_seed →
reprose → keep_best, then 09 refuses "the takes wait on the panels"; 21 ends `DEFERRED: EYE_PANELS needs 102 s`),
24 = the live run. The table turns "24 attempts" into: 8 plan passes on day 1, 11 infrastructure failures /
kills on day 2, 4 panel-ladder loops. Tests: `test_passes_close_an_open_run_at_the_next_start`,
`test_passes_mark_the_live_run_running`, `test_timing_joins_in_utc` (local-naive fixture),
`test_ladder_skips_pass_rows`.

## 4. Faults per shot (panel and take badges)

Shape: `{shot_index: [{kind, text, n}]}` + a panel → shot map `{file, index, section, size, setup, frame}`.
```python
SHOT_WHERE = re.compile(r"^(?:shot_|T)(?P<n>\d+)$")

def shot_faults(verdict: dict) -> dict[int, list[dict]]:
    """Faults keyed by shot index; one kind repeated on a shot collapses to one badge with n."""
    by = defaultdict(Counter)
    for f in verdict.get("faults", []):
        m = SHOT_WHERE.match(f.get("where", ""))
        key = int(m["n"]) if m else f.get("where")       # 'master', a character id, 'plan' stay as strings
        by[key][(f["kind"], f.get("note") or evidence_line(f))] += 1
    return {k: collapse(c) for k, c in by.items()}      # kinds with >3 distinct notes -> {kind, text: first 3, n}

def panel_shot(path: Path, plan: dict) -> dict | None:
    """storyboard/shot_NN.png -> the plan shot NN (index is a string in plan.json)."""
```
Which verdict: **not a glob** — ep13 has three `storyboard/eye_*.json`; the live one is
`work_orders.verdicts[gate].path` (`EYE_PANELS` → `eye_f3ba61bc.json`, `TAKE`/take eye for ep12 via its gate).
Take eye `where` is `TNN`; with `ONE PER TAKE: every shot its own take` T index == shot index (true on ep12).
`evidence_line` for a note-less fault: `missing` → `sharp 0.58, cast_faces 0/1 (panel_dq)`.
**Measured**: ep13 eye (17 faults) → 13 shots badged: shot 4 missing; 3, 12 framing; 11, 15, 17, 22 framing+posture;
9, 16, 19, 21 posture; 18, 24 framing. ep12 panel eye → **520 `landmark` faults, 20–29 per shot on all 24
shots** (a vocabulary list: arch, barn, bridge … windmill) — without collapse the badge is unreadable;
collapsed it is `landmark ×27`. ep12 take eye → T16 face-at-end + lag, T19 cut/jump/cut-vote. plan.json
`shots[i].index == str(i)` on both. `panel_dq.json` / `panel_content.json` are lists keyed by `shot`; their
flags already surface inside the eye (source `panel_dq`) except when the dq row passed (ep13 shot 5 `blur`
flag, passed) — show dq flags as a second, grey badge.
Tests: `test_shot_faults_key_by_index`, `test_repeated_kind_collapses`, `test_non_shot_where_stays_a_string`,
`test_panel_shot_reads_the_plan_row`, `test_the_live_verdict_comes_from_the_row_not_a_glob`.

## 5. Timing per step

Shape: `{id, name, state, runs, total_s, last_s, scripts: {script: n}}`.
```python
def step_timing(steps: list[dict], events: list[dict], timing: list[dict]) -> list[dict]:
    """Per registry step: runs = its `started` events, seconds = timing rows inside its windows."""
    wins = step_windows(events)                         # (step_id, start_utc, end_utc) — end = next event in the run
    per = defaultdict(lambda: {"runs": 0, "total_s": 0.0, "last_s": 0.0, "scripts": Counter()})
    for sid, *_ in wins:
        per[sid]["runs"] += 1
    for row in timing:
        sid = window_of(wins, local_to_utc(row["started"]))
        if sid:
            p = per[sid]; p["total_s"] += row["seconds"]; p["last_s"] = row["seconds"]; p["scripts"][row["stage"]] += 1
    return [{**s, **per.get(s["id"], {})} for s in steps]
```
**Measured on ep13**: 141/151 timing rows fall inside a step window, 10 do not (8 `panels`, 1 `bind`, 1 `lines`),
and some land in the wrong step (7 `prompts` rows counted under 02 because the timing row's whole-second
`started` precedes step 06's `started` event by < 1 s). Totals: 07 ≈ 4180 s (56 grids), 08 ≈ 15 489 s
(panel_content alone 13 767 s over 15 runs). **Recommendation**: the join is lossy by construction — the real
fix is one field: `episode_clock.stamp()` writes `step` (the runner exports it) and the runner writes
`work_steps.seconds`; then this function is a group-by. Until then, pad windows ±1 s and label the column
"≈". Test: `test_step_timing_groups_by_window`, `test_a_row_outside_every_window_is_counted_unplaced`.

## 6. Log tail worth showing

Today: last 20 WARNING+ rows. Log rows carry `ts, level, codex_id, stage, step_id, msg` — **no unit**
(the file name is the run_id, so the run pins it). Of 165 rows across 29 logs, 112 WARNING; 27 are full
refusals = 88 539 of 108 382 msg bytes. The rest are one-liners worth keeping as-is
(`PLAN: measured 21.0 vs None -> improve`, `EYE_PANELS: … -> keep_best (terminal)`, `panel_check.py: faults found`).
```python
def log_rows(rows: list[dict]) -> list[dict]:
    """Each msg to one line + parsed body; a refusal carries its sections and counts."""
    out = []
    for r in rows:
        if r["msg"].startswith("plan_check refused"):
            secs = refusal_sections(r["msg"])
            out.append({**r, "kind": "refusal", "line": summary_line(secs), "items": flat_items(secs)})
        else:
            out.append({**r, "kind": "line", "line": r["msg"].splitlines()[0][:160]})
    return out

def dedupe_refusals(rows: list[dict]) -> list[dict]:
    """Consecutive refusals: an item seen in the previous one becomes ×N on its first row, not a new row."""
```
`summary_line` = `REFUSED · <title> · G-SOURCE 6 · G-SIZE 4 · M2 1` (codes by count). Dedupe key
`(code, where)` — measured: 187 of 425 items repeat the previous refusal verbatim; keyed across the whole
tail 425 → 135 rows. Show `new` / `still ×N` / `gone` per item between consecutive refusals — the "gone"
column is the only evidence a rung fixed anything. Include INFO ladder lines (`-> improve`) — they are the
climb; drop the level filter for `step_id == "ladders"`.
Tests: `test_log_rows_summarise_a_refusal`, `test_dedupe_marks_still_and_gone`, `test_plain_line_keeps_first_line`.

## Book-neutrality and placement

All regexes key on grammar written by `verdict.summary()` and `plan_check.py` — no book, chapter or character
word appears in any rule; fixtures are real rows with nouns replaced. Put the pure functions in a new
`studio/command_center/unit_parse.py` (views.py is 506 lines); `views.unit()` calls `learning_row`,
`passes`, `shot_faults`, `step_timing`, `log_rows`. Two writer-side fixes would delete half this parsing:
(1) learnings keep `faults` as a list (they are Fault objects before `summary()` flattens them);
(2) `timing.jsonl` rows carry `step`. Both are architecture changes → the Future tab + a decision file.
