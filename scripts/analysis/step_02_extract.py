"""Step 02 — extract: the analysis crew works each chapter (design: crew model,
owner-approved 2026-08-23).

02_01 breakdown   1st AD cuts scenes            -> call sheet     (LLM, per chapter)
02_02 specialists script supervisor / casting / story / dialogue   (LLM, 4 per chapter)
02_03 assemble    merge crew outputs by scene number -> analysis/extraction/ch_NN.json
02_04 checks      python: schema, anchors in range, quotes verbatim (grounding)
02_05 audit       auditor spot-checks chapters vs their extraction  (LLM)
02_06 improve     re-run flagged (chapter x dimension) specialists; max 2 rounds

Resume: chapters whose extraction file already exists are skipped (delete the
file to force re-extraction). Names/times recorded AS WRITTEN — steps 03/04
standardize and solve.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from studio import db, llm, paths, tracking

STEP_ID = "02"
NAME = "extract"

# --- configuration (hardcoded; no CLI args by convention) ---
RUN_UNTIL = "02_06"     # last substep to execute: "02_01" .. "02_06"
AUDIT_CHAPTERS = 3      # spot-audit count (first / middle / last); 0 = audit none
MAX_IMPROVE_ROUNDS = 2

_WS = re.compile(r"\s+")

SPECIALISTS = ("time", "characters", "events", "dialogue")  # dimension keys


def _load_chapters(book_dir: Path) -> list[dict]:
    """Real chapters from source/, in order. The n == 0 sentinel has no story.

    Selected by `n`, NOT by `part`. Selecting on part returned NOTHING for any book
    without Parts, so step 02 reported "0 chapters, 0 to extract" and exited CLEAN -
    and steps 03 to 06 then ran on an empty extraction and produced an empty analysis.
    Third place this assumption was found; the other two are in step_01_ingest and
    step_06_verify."""
    manifest = json.loads((book_dir / "source" / "book.json").read_text(encoding="utf-8"))
    chapters = []
    for entry in manifest["chapters"]:
        if entry["n"] > 0:
            chapters.append(json.loads(
                (book_dir / "source" / entry["file"]).read_text(encoding="utf-8")))
    return chapters


def clamp_scene_range(scene: dict, para_count: int) -> tuple[dict | None, str | None]:
    """Fit a scene's paragraph range to the chapter, or drop it.

    Five of thirty books died on "paragraph range outside chapter" - the breakdown agent
    returned a para_end past the end of the chapter and a raise threw away every other
    scene in the book, along with the paid extraction already on disk.

    Clamp what overlaps the chapter. DROP what does not: clamping 40-50 into 10-10 would
    invent a scene that is not there, and a wrong scene is worse than a missing one
    because nothing downstream can tell it is wrong.
    """
    start, end = scene.get("para_start"), scene.get("para_end")
    if not isinstance(start, int) or not isinstance(end, int) or start > end:
        return None, f"scene {scene.get('n')}: unusable range {start}-{end}, dropped"
    if start > para_count or end < 1:
        return None, f"scene {scene.get('n')}: range {start}-{end} is outside a "                     f"{para_count}-paragraph chapter, dropped"
    fixed = max(1, start), min(para_count, end)
    if fixed == (start, end):
        return scene, None
    return ({**scene, "para_start": fixed[0], "para_end": fixed[1]},
            f"scene {scene.get('n')}: range {start}-{end} clamped to "
            f"{fixed[0]}-{fixed[1]} ({para_count} paragraphs)")


def repair_ranges(extraction: dict, chapter: dict) -> tuple[dict, list[str]]:
    """Clamp or drop every out-of-range scene. Returns the extraction and what changed."""
    para_count = len(chapter["paragraphs"])
    scenes, notes = [], []
    for scene in extraction.get("scenes", []):
        fixed, note = clamp_scene_range(scene, para_count)
        if note:
            notes.append(note)
        if fixed is not None:
            scenes.append(fixed)
    return {**extraction, "scenes": scenes}, notes


def extractions_on_disk(chapters: list[dict], book_dir: Path) -> list[tuple[dict, dict]]:
    """(chapter, extraction) pairs for chapters that HAVE an extraction file.

    A chapter the content filter refused has no file. Three books died on
    FileNotFoundError for exactly that - the skip was half a fix and this is the other
    half, which I should have written at the same time.
    """
    pairs = []
    for chapter in chapters:
        path = _extraction_path(book_dir, chapter["n"])
        if path.exists():
            pairs.append((chapter, json.loads(path.read_text(encoding="utf-8"))))
    return pairs


def _extraction_path(book_dir: Path, n: int) -> Path:
    return book_dir / "analysis" / "extraction" / f"ch_{n:02d}.json"


def _norm(text: str) -> str:
    return _WS.sub(" ", text).strip().lower()


def assemble(call_sheet, time_report, cast_report, event_report, dialogue_report) -> dict:
    """Merge the crew's outputs by scene number. Pure code — no LLM."""
    by_scene = {
        "time": {s.n: s for s in time_report.scenes},
        "cast": {s.n: s for s in cast_report.scenes},
        "events": {s.n: s for s in event_report.scenes},
        "dialogue": {s.n: s for s in dialogue_report.scenes},
    }
    scenes = []
    for scene in call_sheet.scenes:
        time_s = by_scene["time"].get(scene.n)
        cast_s = by_scene["cast"].get(scene.n)
        events_s = by_scene["events"].get(scene.n)
        dlg_s = by_scene["dialogue"].get(scene.n)
        scenes.append({
            "n": scene.n,
            "para_start": scene.para_start,
            "para_end": scene.para_end,
            "type": scene.type,
            "location_text": scene.location_text,
            "int_ext": scene.int_ext,
            "time_of_day": scene.time_of_day,
            "story_day": scene.story_day,
            "frame": scene.frame.model_dump() if scene.frame else None,
            "summary": scene.summary,
            "boundary_reason": scene.boundary_reason,
            "time_evidence": [e.model_dump() for e in time_s.time_evidence] if time_s else [],
            "state_changes": [c.model_dump() for c in time_s.state_changes] if time_s else [],
            "characters": [c.model_dump() for c in cast_s.characters] if cast_s else [],
            "events": [e.model_dump() for e in events_s.events] if events_s else [],
            "dialogue": [x.model_dump() for x in dlg_s.exchanges] if dlg_s else [],
        })
    return {"chapter": call_sheet.chapter, "pov": call_sheet.pov.model_dump(),
            "scenes": scenes}


def find_coverage_gaps(extraction: dict) -> list[tuple[str, int]]:
    """Scenes a specialist never answered for.

    Defect found 2026-08-23: specialists return a LIST of per-scene entries and
    nothing required one entry PER SCENE, so a partial answer was silently filled
    with empties — ch3's whole murder scene ended up with no characters. Assemble
    can't tell 'nobody present' from 'never answered', so we check coverage here."""
    gaps = []
    for scene in extraction["scenes"]:
        if scene.get("type") == "nonscene":
            continue
        if not scene["characters"]:
            gaps.append(("characters", scene["n"]))
        if not scene["events"]:
            gaps.append(("events", scene["n"]))
    return gaps


_ELISION = re.compile(r"\u2026|\.\.\.|\n")
_MIN_FRAGMENT = 3        # words; a shorter piece of an elided quote proves nothing


def _words(text: str) -> list[str]:
    """What the text SAYS, stripped of how it is typeset.

    Grounding asks whether the book contains these words in this order. It does not
    ask whether the agent reproduced the typesetting: a closing quotation mark it added
    to round off an utterance, a dialogue comma rendered as a full stop, curly quotes
    against straight ones. Comparing normalized substrings conflated the two and
    reported 316 violations on a book with no fabricated quote in it — 285 of them
    (90%) fully present in their own scene, differing only in punctuation."""
    return re.findall(r"[a-z0-9]+", unicodedata.normalize("NFKD", text or "").casefold())


def _contains_run(haystack: list[str], needle: list[str]) -> bool:
    span = len(needle)
    return bool(span) and any(haystack[i:i + span] == needle
                              for i in range(len(haystack) - span + 1))


def is_grounded(quote: str, source: str) -> bool:
    """Does `source` say the words of `quote`, in order?

    An elision — "..." or a paragraph break — is allowed and splits the quote into
    fragments, each of which must appear. That is what a partial quotation IS, and the
    agents use it constantly for long passages. Fragments under `_MIN_FRAGMENT` words
    are ignored: "he" appearing somewhere is not evidence of anything. A quote with no
    elision must appear whole, however short — 'presently' and 'last night' were real
    findings that a short-phrase exemption would have hidden."""
    haystack = _words(source)
    pieces = [_words(f) for f in _ELISION.split(quote or "")]
    pieces = [f for f in pieces if f]
    if not pieces:
        return False
    if len(pieces) == 1:
        return _contains_run(haystack, pieces[0])
    return all(_contains_run(haystack, f) for f in pieces if len(f) >= _MIN_FRAGMENT)


def _locate(quote: str, chapter: dict) -> int | None:
    """Which paragraph of the chapter really contains this quote, if any."""
    for para in chapter["paragraphs"]:
        if is_grounded(quote, para["text"]):
            return para["n"]
    return None


def check_extraction(extraction: dict, chapter: dict) -> list[dict]:
    """Deterministic grounding checks. Returns violations (dimension-tagged) —
    structural problems raise instead.

    Two distinct failures, reported as such. `wrong-scene` means the words ARE in the
    chapter but not in the paragraphs this scene claims — a mis-attribution, and the
    signal that produced today's `clock-reversed` timeline findings. `ungrounded` means
    the chapter does not contain them at all."""
    para_count = len(chapter["paragraphs"])
    violations = []
    for scene in extraction["scenes"]:
        if not (1 <= scene["para_start"] <= scene["para_end"] <= para_count):
            # repair_ranges clamps or drops these at write time, so reaching here means
            # an extraction written before that existed. Skip the scene rather than
            # throwing away the book - the other scenes are still good.
            violations.append({"chapter": extraction["chapter"], "scene": scene["n"],
                               "dimension": "breakdown", "kind": "range",
                               "note": "paragraph range outside chapter"})
            continue
        scene_text = " ".join(
            p["text"] for p in chapter["paragraphs"]
            if scene["para_start"] <= p["n"] <= scene["para_end"])
        # .get, not [] - a specialist that returns nothing for a dimension leaves the
        # key absent, and a KeyError here would throw away a whole book's extraction over
        # one missing list. Same lesson as the range and the refused chapter.
        for dimension, items, field in (
            ("events", scene.get("events") or [], "quote"),
            ("time", scene.get("state_changes") or [], "quote"),
            ("time", scene.get("time_evidence") or [], "text"),
            ("dialogue", scene.get("dialogue") or [], "notable_quote"),
        ):
            for item in items:
                quote = item[field]
                if not quote or is_grounded(quote, scene_text):
                    continue
                found_at = _locate(quote, chapter)
                if found_at is not None:
                    note = (f"belongs to paragraph {found_at}, outside this scene's "
                            f"{scene['para_start']}-{scene['para_end']}: {quote[:60]!r}")
                    kind = "wrong-scene"
                else:
                    note = f"not in the chapter text: {quote[:60]!r}"
                    kind = "ungrounded"
                violations.append({"chapter": extraction["chapter"],
                                   "scene": scene["n"], "dimension": dimension,
                                   "kind": kind, "note": note})
    return violations


def _run_crew(chapter: dict, tracker) -> dict:
    """One chapter through 1st AD + the four specialists -> assembled extraction."""
    from agents import (casting_director, dialogue_editor, scene_breakdown,
                        script_supervisor, story_analyst)
    n = chapter["n"]
    usage_total = 0
    usage = {}
    print(f"    ch {n:>2} breakdown...", end="", flush=True)
    call_sheet = scene_breakdown.analyze(chapter, usage=usage)
    usage_total += usage.get("total_tokens", 0)
    print(f" {len(call_sheet.scenes)} scenes", flush=True)
    reports = {}
    for key, module in (("time", script_supervisor), ("characters", casting_director),
                        ("events", story_analyst), ("dialogue", dialogue_editor)):
        usage = {}
        print(f"    ch {n:>2} {key}...", flush=True)
        tracker.log(f"ch {n}: running {key}", step_id="02_02")
        reports[key] = module.analyze(chapter, call_sheet, usage=usage)
        usage_total += usage.get("total_tokens", 0)
    tracker.log(f"ch {n}: {len(call_sheet.scenes)} scenes, tokens={usage_total}",
                step_id="02_02")
    return assemble(call_sheet, reports["time"], reports["characters"],
                    reports["events"], reports["dialogue"])


def _rerun_dimension(chapter: dict, extraction: dict, dimension: str) -> dict:
    """Improve remedy: re-run ONE specialist for one chapter, keep the rest."""
    from agents import (casting_director, dialogue_editor, scene_breakdown,
                        script_supervisor, story_analyst)
    call_sheet = scene_breakdown.CallSheet.model_validate(
        {"chapter": extraction["chapter"], "pov": extraction["pov"],
         "scenes": [{"n": s["n"], "para_start": s["para_start"],
                     "para_end": s["para_end"], "location_text": s["location_text"],
                     "summary": s["summary"]} for s in extraction["scenes"]]})
    modules = {"time": script_supervisor, "characters": casting_director,
               "events": story_analyst, "dialogue": dialogue_editor}
    report = modules[dimension].analyze(chapter, call_sheet)
    fields = {"time": ("time_evidence", "state_changes"), "characters": ("characters",),
              "events": ("events",), "dialogue": ("dialogue",)}[dimension]
    by_n = {s.n: s for s in report.scenes}
    for scene in extraction["scenes"]:
        fresh = by_n.get(scene["n"])
        if fresh is None:
            continue
        if dimension == "time":
            scene["time_evidence"] = [e.model_dump() for e in fresh.time_evidence]
            scene["state_changes"] = [c.model_dump() for c in fresh.state_changes]
        elif dimension == "characters":
            scene["characters"] = [c.model_dump() for c in fresh.characters]
        elif dimension == "events":
            scene["events"] = [e.model_dump() for e in fresh.events]
        else:
            scene["dialogue"] = [x.model_dump() for x in fresh.exchanges]
    return extraction


def _audit_sample(chapters: list[dict]) -> list[dict]:
    if AUDIT_CHAPTERS <= 0 or not chapters:
        return []
    if len(chapters) <= AUDIT_CHAPTERS:
        return chapters
    return [chapters[0], chapters[len(chapters) // 2], chapters[-1]][:AUDIT_CHAPTERS]


def runnable_targets(issues, chapters) -> list:
    """(chapter, dimension) pairs this run can actually re-run.

    The auditor returns a chapter NUMBER and can name one absent from this run's list -
    a hallucinated number, or a chapter filtered upstream. `next(...)` raised
    StopIteration and killed the step AFTER the extraction had been bought and written,
    losing paid work over a bad index. An agent's output is input, not a guarantee.
    """
    known = {c["n"] for c in chapters}
    return sorted({(i["chapter"], i["dimension"]) for i in issues
                   if i["dimension"] in SPECIALISTS and i["chapter"] in known})


def extract_chapters(todo: list[dict], book_dir, tracker) -> tuple[list[dict], list[int]]:
    """Extract each chapter, writing immediately. Returns (extractions, skipped).

    A chapter the provider REFUSES is skipped, not fatal. Three of five books died with
    "rejected by the content filter", one of them 90% through at $0.93 of paid work,
    because this loop let ContentFiltered escape. A provider refusing one chapter of Moby
    Dick is not a reason to lose the other 134.

    It is recorded loudly rather than swallowed: an analysis that looks complete and is
    quietly missing a chapter is worse than one that failed.
    """
    done, skipped = [], []
    for chapter in todo:
        try:
            extraction = _run_crew(chapter, tracker)
        except llm.ContentFiltered as exc:
            skipped.append(chapter["n"])
            if tracker:
                tracker.log(f"ch {chapter['n']}: REFUSED by the content filter, skipped: "
                            f"{exc}", level="WARNING", step_id="02_02")
            print(f"  ch {chapter['n']:>2}: SKIPPED (content filter)")
            continue
        # Repair BEFORE writing, so nothing downstream ever sees a bad range and the
        # repair is not re-done on every resume.
        extraction, notes = repair_ranges(extraction, chapter)
        for note in notes:
            if tracker:
                tracker.log(f"ch {chapter['n']}: {note}", level="WARNING",
                            step_id="02_01")
            print(f"  ch {chapter['n']:>2}: {note}")
        # WRITE IMMEDIATELY (resume rule): a crash at ch N keeps ch 1..N-1 paid work
        path = _extraction_path(book_dir, chapter["n"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(extraction, ensure_ascii=False, indent=2),
                        encoding="utf-8")
        done.append(extraction)
        print(f"  ch {chapter['n']:>2}: {len(extraction['scenes'])} scenes -> written")
    return done, skipped


def run(codex_id: str) -> None:
    conn = db.get_connection()
    db.get_codex(conn, codex_id)
    book_dir = paths.book_dir(codex_id)
    tracker = tracking.Tracker(conn, codex_id, "analysis")
    chapters = _load_chapters(book_dir)
    out_dir = book_dir / "analysis" / "extraction"
    out_dir.mkdir(parents=True, exist_ok=True)
    todo = [c for c in chapters if not _extraction_path(book_dir, c["n"]).exists()]
    print(f"[{STEP_ID}] {NAME}: {len(chapters)} chapters, {len(todo)} to extract "
          f"(existing skipped)  run_id={tracker.run_id}  until={RUN_UNTIL}")

    with tracker.step("02_01"), tracker.step("02_02"), tracker.step("02_03"):
        _, filtered = extract_chapters(todo, book_dir, tracker)
    if filtered:
        print(f"  02_03: {len(filtered)} chapter(s) refused by the content filter: "
              f"{filtered}")
    if RUN_UNTIL < "02_04":
        return

    for round_no in range(1 + MAX_IMPROVE_ROUNDS):
        with tracker.step("02_04"):
            violations = []
            gaps = []
            # Only chapters that HAVE an extraction. A chapter the content filter
            # refused has no file, and this read is what actually killed Beowulf,
            # Tom Sawyer and Pride and Prejudice.
            for chapter, extraction in extractions_on_disk(chapters, book_dir):
                violations += check_extraction(extraction, chapter)
                for dimension, scene_n in find_coverage_gaps(extraction):
                    gaps.append({"chapter": chapter["n"], "scene": scene_n,
                                 "dimension": dimension,
                                 "note": "specialist returned no entry for this scene"})
            for gap in gaps:
                tracker.log(f"coverage gap: ch={gap['chapter']} scene={gap['scene']} "
                            f"dim={gap['dimension']}", level="WARNING", step_id="02_04")
            for v in violations:
                tracker.log(f"grounding: ch={v['chapter']} scene={v['scene']} "
                            f"dim={v['dimension']}: {v['note']}",
                            level="WARNING", step_id="02_04")
        print(f"  02_04 checks: {len(violations)} grounding violation(s), "
              f"{len(gaps)} coverage gap(s)")
        if RUN_UNTIL < "02_05":
            return

        # Grounding violations are logged and reported but do NOT gate the stage:
        # a paraphrased quote does not corrupt the who/where/when data downstream
        # steps consume. Only auditor-flagged issues drive the improve loop.
        # Coverage gaps DO gate: a scene with no cast is missing data, not noise.
        issues = list(gaps)
        with tracker.step("02_05"):
            from agents import extraction_auditor
            present = extractions_on_disk(_audit_sample(chapters), book_dir)
            for chapter, extraction in present:
                usage = {}
                try:
                    verdict = extraction_auditor.audit(chapter, extraction, usage=usage)
                except llm.ContentFiltered as exc:
                    tracker.log(f"audit ch {chapter['n']}: content-filtered, skipped: {exc}",
                                level="WARNING", step_id="02_05")
                    print(f"  02_05 audit ch {chapter['n']}: SKIPPED (content filter)")
                    continue
                tracker.log(f"audit ch {chapter['n']}: ok={verdict.ok} "
                            f"({usage.get('total_tokens')} tokens): {verdict.summary}",
                            step_id="02_05")
                for issue in verdict.issues:
                    tracker.log(f"issue ch={issue.chapter} scene={issue.scene} "
                                f"dim={issue.dimension} sev={issue.severity}: {issue.note}",
                                level="WARNING", step_id="02_05")
                    issues.append({"chapter": issue.chapter, "scene": issue.scene,
                                   "dimension": issue.dimension, "note": issue.note})
                print(f"  02_05 audit ch {chapter['n']}: ok={verdict.ok} "
                      f"issues={len(verdict.issues)}")
        if not issues:
            print(f"  {STEP_ID} extract: clean")
            return
        if round_no == MAX_IMPROVE_ROUNDS:
            tracker.log(f"{len(issues)} issue(s) remain after {MAX_IMPROVE_ROUNDS} rounds; "
                        f"proceeding (logged for review)", level="WARNING", step_id="02_06")
            print(f"  {STEP_ID} extract: {len(issues)} issue(s) remain after "
                  f"{MAX_IMPROVE_ROUNDS} rounds — logged, proceeding")
            return
        if RUN_UNTIL < "02_06":
            return

        with tracker.step("02_06"):
            targets = runnable_targets(issues, chapters)
            if not targets:
                tracker.log(f"no re-runnable dimension in {len(issues)} issue(s); "
                            f"logging and proceeding", level="WARNING", step_id="02_06")
                print(f"  02_06 improve: {len(issues)} issue(s) with no re-runnable "
                      f"dimension - logged, proceeding")
                return
            by_number = {c["n"]: c for c in chapters}
            for ch_n, dimension in targets:
                chapter = by_number[ch_n]
                path = _extraction_path(book_dir, ch_n)
                if not path.exists():
                    continue          # refused by the content filter; nothing to re-run
                extraction = json.loads(path.read_text(encoding="utf-8"))
                try:
                    extraction = _rerun_dimension(chapter, extraction, dimension)
                except llm.ContentFiltered as exc:
                    tracker.log(f"re-run {dimension} ch {ch_n}: content-filtered, keeping "
                                f"existing extraction: {exc}", level="WARNING",
                                step_id="02_06")
                    continue
                path.write_text(json.dumps(extraction, ensure_ascii=False, indent=2),
                                encoding="utf-8")
                tracker.log(f"round {round_no + 1}: re-ran {dimension} on ch {ch_n}",
                            step_id="02_06")
        print(f"  02_06 improve: re-ran {len(targets)} (chapter x dimension); re-checking")
