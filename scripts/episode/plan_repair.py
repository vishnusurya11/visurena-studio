#!/usr/bin/env python
"""The automated plan repairer: plan_check -> the cure table -> clean, in
seconds, with no writer call.

    uv run python scripts/episode/plan_repair.py <codex_id> <episode> [--from-aside]

MEASURED (docs/audit/2026-10-01_plan_hours_debate.md): 97% of ep14-15's plan
hours were paid rewrites of MECHANICAL faults.  This loop applies the cure
table (studio/plan_cures) to every fault plan_check names, up to ROUNDS
times, writing through the contract each round.  It exits 0 on a clean
battery; on faults with no cure (the CREATIVE kind -- story, coverage,
invented) it exits 1 listing exactly what the writer must answer, one field
at a time."""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, plan_cures as pc  # noqa: E402
from studio.episode_home import episode_arg  # noqa: E402
from studio.episode_spec import Episode  # noqa: E402

ROUNDS = 6


HARD_LISTS = ("ONE PER TAKE : [", "TAKE LENGTH  : [", "CONTRACT:", "QUOTE        : [")
"""The checker's top-level rows that are HARD and list-formed; EXPECTS TEXT
and SHEET TEXT print the same way and are informational (ep16: TAKE LENGTH
was invisible to the repairer and three rounds deferred over 0.05 s).
'CONTRACT:' is the checker's OWN spelling (plan_check prints no space before
the colon); the old 'CONTRACT :' entry matched nothing, so no contract
refusal -- the bed-span one included -- ever reached this repairer."""


def fault_rows(stdout: str) -> list[str]:
    return [l.strip() for l in stdout.splitlines()
            if (l.startswith("    ") or any(k in l for k in HARD_LISTS))
            and "advisory" not in l and "not applicable" not in l and l.strip()]


def battery_rows(book_id: str, number: int) -> tuple[bool, list[str]]:
    rc = subprocess.run([sys.executable, "scripts/episode/plan_check.py", book_id, str(number)],
                        capture_output=True, text=True, cwd=str(Path(__file__).resolve().parents[2]))
    return "VERDICT      : clean" in rc.stdout, fault_rows(rc.stdout)


def series_pin_values(book) -> dict:
    """The series' look/aspect off the newest SIGNED episode, else the house."""
    from studio import plan_gates
    for n in range(27, 0, -1):
        p = episode_home.home(book, n) / "plan.json"
        v = episode_home.home(book, n) / "plan.verdict.json"
        if p.exists() and v.exists():
            doc = episode_home.read_json(p)
            if doc.get("look"):
                return {"look": doc["look"], "aspect": plan_gates.series_aspect(book)}
    return {"look": "", "aspect": plan_gates.series_aspect(book)}


def phantom_context(book) -> tuple[dict, set]:
    """(names, place_words) the phantom cures measure with -- the GATE'S own
    inputs, from the book's refs.json when it exists."""
    from studio import house_style, plan_gates
    path = book / "refs" / "refs.json"
    refs = episode_home.read_json(path).get("refs") or [] if path.exists() else []
    return plan_gates.person_tokens(refs), house_style.place_words()


def rewrite_round(book, path, rows: list[str]) -> bool:
    """The ONE paid round per repair run: setups whose G-PHANTOM / G-LIGHT rows
    survived the mechanical table are rewritten through the workhorse tier
    (guard_spend fires inside the caller), written through the contract."""
    import re
    bad = [r for r in rows if re.search(r"G-PHANTOM|G-LIGHT: setup", r)]
    setups = sorted({m.group(1) for r in bad if (m := re.search(r"setup '([^']+)'", r))})
    if not setups:
        return False
    doc = episode_home.read_json(path)
    doc, uncured = pc.rewrite_setups(doc, *phantom_context(book), setups)
    Episode(**doc)
    episode_home.write_plan(path, doc)
    print(f"llm round: {len(setups) - len(uncured)} setup(s) rewritten, "
          f"{len(uncured)} kept their faults for the writer")
    return True


def shot_indices(rows: list[str]) -> list[int]:
    import re
    return sorted({int(m.group(1)) for r in rows for m in [re.search(r"shot (\d+)", r)] if m})


def ghost_names(book) -> dict:
    """The unique-token table the two clone-text cures measure with -- the
    GATE'S own (`plan_gates.names_from_refs`); {} (both cures disabled, the
    rows stay creative) for a book without refs.json."""
    from studio import plan_gates
    path = book / "refs" / "refs.json"
    if not path.exists():
        return {}
    return plan_gates.names_from_refs(episode_home.read_json(path).get("refs") or [])


def spend_guard(book, number: int):
    """The repair's OWN spend context: plan_repair runs as a subprocess, so
    the runner's context never reaches it and guard_spend would silently
    no-op around the llm cures.  A missing db degrades loudly, never crashes."""
    from contextlib import nullcontext
    try:
        from studio import db, episode_run, llm
        return llm.spend_context(db.get_connection(), book.name.split("_", 1)[0],
                                 "episode", "02", unit=episode_run.unit_of(number))
    except Exception as why:
        print(f"WARNING: no spend guard for this repair ({str(why)[:120]}); "
              f"llm cures would run unguarded")
        return nullcontext()


def stage_vocab_of(book, number: int) -> dict:
    """The G-STAGE vocabulary -- the GATE'S own (`pack_refs.stage_vocab`),
    built from the book's refs.json; empty tables when the book has none."""
    from studio import pack_refs
    path = book / "refs" / "refs.json"
    rows = (episode_home.read_json(path).get("refs") or []) if path.exists() else []
    return pack_refs.stage_vocab(book, rows, number)


def pick_rows(doc: dict, unresolved: list, vocab: dict, book) -> dict:
    """Each >= 2-candidate creature row settled by ONE workhorse pick
    (guard_spend fires inside studio.llm's caller), then the rename rerun
    MECHANICALLY with the picked pid; a refused pick leaves the fault row
    standing for the next round."""
    from studio import plan_cures, stage_pick
    title = book.name.split("_", 1)[-1].replace("-", " ").title()
    for shot_index, term, cands in unresolved:
        shot = next((s for s in doc.get("shots") or [] if s.get("index") == shot_index), {})
        prose = " ".join(shot.get(f) or "" for f in plan_cures.SHOT_FIELDS)
        rows = [{"pid": p, **vocab["machines"][p]} for p in cands]
        try:
            pid = stage_pick.pick_machine(prose, rows, term=term, book_title=title)
        except Exception as why:
            print(f"  stage pick for shot {shot_index} {term!r} refused: {str(why)[:140]}")
            continue
        doc = plan_cures.rename_creature(doc, shot_index, term, pid, vocab)
    return doc


def cast_rows_text(book) -> str:
    """Every bound cast row's physical, joined -- L18's own exemption text."""
    path = book / "refs" / "refs.json"
    rows = (episode_home.read_json(path).get("refs") or []) if path.exists() else []
    return " ".join(str(r.get("physical") or "") for r in rows)


def cure_row_rows(book, rows: list[str]) -> list[str]:
    """Every [row <id>]/[card <pid>] fault cured in ITS OWN file via the
    shared table (studio.row_lint); the rows the table left unchanged come
    back uncured for the llm pass."""
    import re
    from studio import row_lint
    left = []
    for row in rows:
        m = re.search(r"\[(row|card) ([\w-]+)\]", row)
        if not (m and row_lint.cure_row_file(book, m.group(1), m.group(2))):
            left.append(row)
    return left


def apply(doc: dict, rows: list[str], book, number: int = 0,
          rate: float = 3.0) -> tuple[dict, list[str], list[str]]:
    """Every cured family once per round; the rows nothing cures come back,
    and so do the SORTED NAMES of the cures that ran -- what the provenance
    ledger records so a re-sign can prove the bytes moved mechanically.
    `rate` is the narrator's measured words/s -- THE CHECKER'S RATE, or the
    holds algebra cures numbers the battery never measures (ep16: 8.05 s at
    2.54 read as 7.5 s at the default 3.0 and the clamp saw nothing)."""
    legal = {p[:-5] for p in os.listdir(book / "analysis" / "props")} \
        if (book / "analysis" / "props").exists() else set()
    uncured, names = [], set()
    for row in rows:
        name = pc.cure_for(row)
        (names.add(name) if name else uncured.append(row))
    chapter = None
    if names & {"source_spans", "quote_trim"}:
        from studio import plan_brief
        chapter = plan_brief.chapter_text(book, number)
        if chapter is None:     # never a silent pass: the rows come back uncured
            uncured += [r for r in rows if pc.cure_for(r) in ("source_spans", "quote_trim")]
            names -= {"source_spans", "quote_trim"}
    vocab = stage_vocab_of(book, number) if names & {
        "stage_machines", "strip_creatures", "drop_creature_faces", "prop_spans"} else None
    for name in names:
        if name == "renumber":
            doc = pc.renumber(doc)
        elif name == "light_directions":
            doc = pc.light_directions(doc)
        elif name == "head_fractions":
            doc = pc.head_fractions(doc)
        elif name == "pace_words":
            doc = pc.pace_words(doc)
        elif name == "button_beat":
            doc = pc.button_beat(doc)
        elif name == "rebalance_heads":
            own = [r for r in rows if pc.cure_for(r) == "rebalance_heads"]
            doc, unfixed = pc.rebalance_heads(doc, shot_indices(own))
            if unfixed:
                import re
                from studio import move_llm
                doc, still = move_llm.cure_unfixed(doc, unfixed, doc.get("setups") or {})
                uncured += [r for r in own
                            if (m := re.search(r"shot (\d+)", r)) and int(m.group(1)) in set(still)]
        elif name == "legal_props":
            doc = pc.legal_props(doc, legal)
        elif name == "close_crowds":
            doc = pc.close_crowds(doc)
        elif name == "strip_phantoms":
            doc, _ = pc.strip_phantoms(doc, *phantom_context(book))
        elif name == "holds":
            doc = pc.holds(doc, rate=rate)
        elif name == "edge_cases":
            doc = pc.edge_cases(doc)
        elif name == "source_spans":
            doc = pc.source_spans(doc, chapter)
        elif name == "quote_trim":
            import seq_boards  # sibling module, lazy so the importlib-loaded test never needs it
            doc = pc.quote_trim(doc, seq_boards.book_words(book))
        elif name == "pin_series":
            doc = pc.pin_series(doc, **series_pin_values(book))
        elif name == "stage_machines":
            doc, unresolved = pc.stage_machines(doc, vocab)
            if unresolved:
                doc = pick_rows(doc, unresolved, vocab, book)
        elif name == "strip_creatures":
            doc = pc.strip_creatures(doc, vocab)
        elif name == "drop_creature_faces":
            doc = pc.drop_creature_faces(doc, set(vocab["creatures"]))
        elif name == "prop_spans":
            from studio import plan_brief
            doc = pc.prop_spans(doc, plan_brief.chapter_paragraphs(book, number)[1], vocab)
        elif name == "ghost_limbs":
            from studio import plan_llm_cures
            names_table = ghost_names(book)
            if names_table:
                doc = pc.ghost_limbs(doc, names_table,
                                     rewrite=plan_llm_cures.rewriter(doc, names_table))
            else:
                uncured += [r for r in rows if pc.cure_for(r) == "ghost_limbs"]
        elif name == "one_position":
            from studio import plan_llm_cures
            names_table = ghost_names(book)
            own = [r for r in rows if pc.cure_for(r) == "one_position"]
            if names_table:
                doc = plan_llm_cures.one_position(doc, own, names_table)
            else:
                uncured += own
        elif name == "stillness_words":
            doc = pc.stillness_words(doc)
        elif name == "figurative_gaits":
            # the swap first, the pace append on the person clauses it spared
            # in the SAME round -- the order the two cures were designed in
            doc = pc.pace_words(pc.figurative_gaits(doc))
        elif name == "drop_thing_pace":
            doc = pc.drop_thing_pace(doc)
        elif name == "strip_slow":
            doc = pc.strip_slow(doc)
        elif name == "arrival_ends":
            own = [r for r in rows if pc.cure_for(r) == "arrival_ends"]
            doc = pc.arrival_ends(doc, shot_indices(own))
        elif name == "apply_limp":
            own = [r for r in rows if pc.cure_for(r) == "apply_limp"]
            doc = pc.apply_limp(doc, shot_indices(own))
        elif name == "strip_banned_prop":
            doc = pc.strip_banned_prop(doc, cast_rows_text(book))
        elif name == "row_words":
            own = [r for r in rows if pc.cure_for(r) == "row_words"]
            uncured += cure_row_rows(book, own)
        elif name == "clamp_beds":
            doc = pc.clamp_beds(doc)
    return doc, uncured, sorted(names)


def rate_blocked(doc: dict, rate: float) -> bool:
    """The G-RATE guard on insertion: 14 more words at the measured rate must
    not push the projection past MAX_SECONDS -- that residual IS creative (the
    plan must lose picture, the writer's call)."""
    from studio.episode_spec import MAX_SECONDS
    words = sum(len(str(l.get("text") or "").split()) for l in doc.get("lines") or [])
    rest = sum(float(s.get("beat_s") or 0) + float(s.get("coda_s") or 0) + 0.5
               for s in doc.get("shots") or [])
    return (words + 14) / rate + rest > MAX_SECONDS


def micro_targets(doc: dict, rate: float) -> list[tuple[int, tuple]]:
    """(shot, hole) for every residual projected hole an insertion can bridge,
    then for every ONE PER TAKE pair no hole headroom lets split."""
    from studio import speech_gap
    wall = speech_gap.MAX_GAP_S - speech_gap.HOLE_MARGIN_S
    out = []
    for hole in speech_gap.over_wall(pc._projection(doc, rate), wall):
        shot = pc.insertion_shot(doc, hole, rate)
        if shot is not None:
            out.append((shot, hole))
    _, unsplit = pc.holds_and_unsplit(json.loads(json.dumps(doc)), rate)
    for pair in unsplit:
        target = pc.pair_insertion_shot(doc, pair, rate)
        if target is not None and target[0] not in [t[0] for t in out]:
            out.append(target)
    return out


def grounding(book, number: int, doc: dict, shot_index: int, hole: tuple,
              rate: float) -> dict:
    """What the micro-line prompt needs: the shot, the paragraph its LATEST
    span places it on, the lines either side of the hole, the hole's seconds."""
    from types import SimpleNamespace
    from studio import plan_brief, plan_gates
    start, end, _ = hole
    shot = next(s for s in doc["shots"] if s["index"] == shot_index)
    paragraphs = plan_brief.chapter_paragraphs(book, number)[1] or []
    at = plan_gates.event_paragraph(SimpleNamespace(source=shot.get("source") or []),
                                    paragraphs)
    placed = pc._projection(doc, rate)
    before = [l for l in placed["lines"] if l["at"] + l["seconds"] <= start + 1e-6]
    after = [l for l in placed["lines"] if l["at"] >= end - 1e-6]
    return {"shot": shot, "source_paragraph": paragraphs[at - 1] if at else "",
            "prev_text": before[-1]["text"] if before else "",
            "next_text": after[0]["text"] if after else "",
            "gap_s": round(end - start, 2)}


def micro_fill(book):
    """The real micro-line caller: the book's words once, then the agent (its
    `studio.llm` caller runs guard_spend before anything is sent)."""
    import seq_boards
    from agents import line_filler
    words = seq_boards.book_words(book)

    def call(ground: dict) -> str | None:
        return line_filler.fill(ground["shot"], ground["source_paragraph"],
                                ground["prev_text"], ground["next_text"],
                                ground["gap_s"], words)
    return call


def fill_holes(book, number: int, max_inserts: int = 3, _fill=None) -> bool:
    """The LLM micro-line round: residual G-HOLE holes and unsplit ONE PER
    TAKE pairs bridged by one 8-14-word narration sentence each, spliced with
    the exact reindex, written through the contract.  True when the plan
    changed (the caller re-runs the battery); `_fill` is the test seam."""
    from studio import plan_gates
    path = episode_home.home(book, number) / "plan.json"
    doc = episode_home.read_json(path)
    rate = plan_gates.series_rate(book, number)
    speaker = pc.narration_speaker(doc)
    if speaker is None:
        return False
    fill, wrote = _fill or micro_fill(book), 0
    for shot_index, hole in micro_targets(doc, rate)[:max_inserts]:
        if rate_blocked(doc, rate):
            break
        text = fill(grounding(book, number, doc, shot_index, hole, rate))
        if text is not None:
            doc = pc.insert_line(doc, shot_index, text, speaker)
            wrote += 1
    if wrote:
        Episode(**doc)
        episode_home.write_plan(path, doc)
        print(f"micro-line round: {wrote} narration bridge(s) inserted")
    return bool(wrote)


def l14_need(row: str) -> int:
    """How many words an L14 shortfall is missing, off the row's own numbers."""
    import re
    m = re.search(r"(\d+) words; the (?:floor is|gate is) (\d+)", row)
    return max(0, int(m.group(2)) - int(m.group(1))) if m else 40


def llm_cure_round(book, number: int, rows: list[str]) -> bool:
    """The ONE guarded llm pass, run only after a round in which the
    mechanical tables changed nothing: every lint-family row left, one
    `plan_cures.llm_field_cure` each (L14 shortfalls take the enrich lever),
    capped at MAX_LLM_CURES; each accepted only through G-CURE-VERIFY.
    True when the plan or a row file changed."""
    import re
    from studio import plan_cures as pc
    path = episode_home.home(book, number) / "plan.json"
    doc, cured = episode_home.read_json(path), 0
    for row in [r for r in rows if re.search(r"\bL\d+ ", r)][:pc.MAX_LLM_CURES]:
        if "L14 LENGTH" in row and (m := re.search(r"shot (\d+)", row)):
            doc, did = pc.enrich_at_rest(doc, int(m.group(1)), l14_need(row))
        else:
            doc, did = pc.llm_field_cure(book, doc, row)
        cured += bool(did)
    if cured:
        Episode(**doc)
        episode_home.write_plan(path, doc)
        print(f"llm cure round: {cured} field(s) rewritten under G-CURE-VERIFY")
    return bool(cured)


def apply_each(doc: dict, rows: list[str], book, number: int = 0, rate: float = 3.0,
               valid=lambda d: Episode(**d)) -> tuple[dict, list[str], set]:
    """One cure family at a time, each kept only if the contract still holds:
    a cure that breaks it is dropped ALONE and its rows come back uncured
    (ep19: one cure's "slowly" voided the light, crowd and move cures with it)."""
    groups: dict = {}
    for row in rows:
        groups.setdefault(pc.cure_for(row) or row, []).append(row)
    uncured, names = [], set()
    for group in groups.values():
        trial, left, ran = apply(json.loads(json.dumps(doc)), group, book, number, rate=rate)
        try:
            valid(trial)
        except Exception:
            uncured += group
            continue
        doc, uncured, names = trial, uncured + left, names | set(ran)
    return doc, uncured, names


def main(book_id: str, number: int, from_aside: bool = False, no_llm: bool = False) -> int:
    book = episode_home.book_dir(book_id)
    home = episode_home.home(book, number)
    path = home / "plan.json"
    if from_aside or not path.exists():
        aside = home / "plan.deferred.json"
        if not aside.exists():
            raise SystemExit(f"no plan and no aside under {home}")
        doc = json.load(io.open(aside, encoding="utf-8"))["draft"]
        Episode(**doc)
        episode_home.write_plan(path, doc)
        print("aside draft restored to plan.json")
    with spend_guard(book, number):
        for round_ in range(1, ROUNDS + 1):
            clean, rows = battery_rows(book_id, number)
            if clean:
                print(f"BATTERY CLEAN after {round_ - 1} repair round(s)")
                return 0
            doc = episode_home.read_json(path)
            from studio import plan_gates, plan_provenance, plan_verdict
            before_sha8 = plan_verdict.plan_sha8(path)
            doc, uncured, names = apply_each(doc, rows, book, number, rate=plan_gates.series_rate(book, number))
            try:
                Episode(**doc)
                episode_home.write_plan(path, doc)
            except Exception as bad:
                print(f"round {round_}: a cure broke the contract, draft kept: {str(bad)[:140]}")
                return 1
            # THE LEDGER ROW, only after the write LANDED: step 02's re-sign
            # walks these rows; a crash before this line leaves a chain gap,
            # which fails safe (the critic reads once).
            plan_provenance.record(path, before_sha8, names)
            print(f"round {round_}: {len(rows) - len(uncured)} fault row(s) cured, "
                  f"{len(uncured)} creative row(s) remain")
            if (uncured and len(uncured) == len(rows)) or not rows:
                break   # nothing this table cures, or nothing collected: stop looping
        clean, rows = battery_rows(book_id, number)
        if not clean and not no_llm and llm_cure_round(book, number, rows):
            clean, rows = battery_rows(book_id, number)
        if not clean and rewrite_round(book, path, rows):
            clean, rows = battery_rows(book_id, number)
        if not clean and any("G-HOLE" in r or "ONE PER TAKE" in r for r in rows) \
                and fill_holes(book, number):
            clean, rows = battery_rows(book_id, number)
    if clean:
        print("BATTERY CLEAN")
        return 0
    print("CREATIVE faults remain -- the writer's, one field at a time:")
    for r in rows:
        print("  ", r[:160])
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], episode_arg(sys.argv), "--from-aside" in sys.argv,
                          "--no-llm" in sys.argv))
