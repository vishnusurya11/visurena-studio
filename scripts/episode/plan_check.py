#!/usr/bin/env python
"""Every free gate on a plan, in one command, before anything renders.

    uv run python scripts/episode/plan_check.py <codex_id> <episode>

MEASURED on episode 11 (2026-09-17): thirteen line runs, because each edit --
the dialogue dial, the turn ratio, the projection, the sync rule, a shot longer
than a take, a landmark size off the ladder -- was found by the NEXT gate on
the road, after a GPU stage had already paid for the previous one.  This says
everything at once: the contract, G-LIGHT, the plan gates with G-NAMES and
G-RATE, the motion lints, the marks, the actor gate, the cast binding, the
per-shot take length at the narrator's measured rate, and the sheet gate's
text read.  Exit 1 on any refusal; advisories print.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from studio import actor_gate, cast_refs, episode_home, episode_spec as spec, house_style, pack_refs, plan_brief, plan_gates, timeline_fresh
from studio import episode_takes as tk
from studio.episode_takes import BUDGET

HANDLE, BREATH = 0.25, 0.70


def contract(book: Path, number: int):
    """The plan under the contract, or every distinct refusal printed and None."""
    doc = episode_home.read_json(episode_home.home(book, number) / "plan.json")
    try:
        return spec.Episode(**doc)
    except Exception as e:  # pydantic's message carries every refusal
        seen = set()
        for m in re.finditer(r"^(\S+)\n  (?:Value error, )?(.{0,170})", str(e), re.M):
            if (k := (m.group(1), m.group(2)[:60])) not in seen:
                seen.add(k)
                print("CONTRACT:", m.group(1), "::", m.group(2))
        if not seen:
            print("CONTRACT:", str(e)[:600])
        return None


def rendered(book: Path, number: int) -> bool:
    """Has anything been drawn or shot from this plan?  Then G-SETUP is advice:
    a wall raised after the render must not stop the run that made it."""
    home = episode_home.home(book, number)
    return (home / "storyboard" / "grids").exists() or (home / "takes").exists()


def setup_gate(episode, book: Path, number: int) -> int:
    """G-SETUP printed; counted as hard only before anything is rendered."""
    found = plan_gates.setup_faults(episode)
    advisory = bool(found) and rendered(book, number)
    print("G-SETUP      :", ("advisory (rendered plan): " if advisory else "") + (f"{len(found)}" if found else "clean"))
    for f in found:
        print("   ", f[:170])
    return 0 if advisory else len(found)


def long_shots(episode, rate: float, budget: float = BUDGET) -> list[tuple[int, float]]:
    """(shot, projected seconds) for every shot that projects past a take at the
    narrator's measured rate: handles, words, a breath between two lines, the
    beat and the coda.  The dry build finds these after the lines render."""
    out = []
    for s in episode.shots:
        words = [len(l.text.split()) for l in episode.lines if l.shot == s.index]
        seconds = 2 * HANDLE + sum(words) / rate + BREATH * max(0, len(words) - 1) + s.beat_s + s.coda_s
        if seconds > budget + 1e-6:
            out.append((s.index, round(seconds, 2)))
    return out


def projected(episode, rate: float) -> list[dict]:
    """Each shot as the timeline would place it, at the narrator's measured rate."""
    out = []
    for s in episode.shots:
        words = [len(l.text.split()) for l in episode.lines if l.shot == s.index]
        seconds = 2 * HANDLE + sum(words) / rate + BREATH * max(0, len(words) - 1) + s.beat_s + s.coda_s
        out.append({"index": s.index, "seconds": seconds, "setup": s.setup, "cuts": list(getattr(s, "cuts", []))})
    return out


def packed_shots(episode, rate: float) -> list[tuple[int, ...]]:
    """Runs of shots the take packer would put into ONE take (ep12 shot 21: a
    1.7 s reaction packed after a 5.5 s dialogue shot, an internal cut the
    model had to place).  One shot per take is the rule since episode 4."""
    return [tuple(run) for run in tk.groups(projected(episode, rate)) if len(run) > 1]


def take_lint_gate(book: Path, episode, number: int, rate: float) -> int:
    """G-TAKELINT, HARD: episode_ref_official's REAL lint on take cards
    dry-built from the projection (takes_r2v.dry_faults), each fault remapped
    to its plan shot and tagged with the data layer that carries the word.
    Supersedes the old unpaced_shots advisory, which read raw plan fields the
    builder then rewrote.  A dry build the adoptions refuse is itself a row."""
    import takes_r2v
    try:
        rows = takes_r2v.dry_faults(book, episode, number, projected(episode, rate), rate=rate)
    except SystemExit as why:
        rows = [f"G-TAKELINT dry build refused: {str(why)[:150]}"]
    print("G-TAKELINT   :", len(rows) or "clean")
    for f in rows:
        print("   ", str(f)[:170])
    return len(rows)


def row_text_rows(book: Path) -> list[str]:
    """G-ROWTEXT at read: every refs.json character physical and every
    analysis/props card profile text under the row lint, tagged for the cure."""
    from studio import row_lint
    path = book / "refs" / "refs.json"
    rows = (episode_home.read_json(path).get("refs") or []) if path.exists() else []
    out = [f"G-ROWTEXT {fault} [row {r.get('entity_id')}]" for r in rows
           if r.get("kind") == "character"
           for fault in row_lint.row_faults(r.get("physical") or "")]
    folder = book / "analysis" / "props"
    for card in sorted(folder.glob("*.json")) if folder.exists() else []:
        if card.stem == "index":
            continue
        prof = episode_home.read_json(card).get("profile") or {}
        said = " ".join(str(prof.get(k) or "") for k in ("physical", "scale"))
        out += [f"G-ROWTEXT {fault} [card {card.stem}]" for fault in row_lint.row_faults(said)]
    return out


def row_text_gate(book: Path) -> int:
    """The ROW TEXT section, HARD: these texts are injected verbatim into
    every take prompt that stages them, so a dirty row poisons the episode."""
    found = row_text_rows(book)
    print("ROW TEXT     :", len(found) or "clean")
    for f in found:
        print("   ", f[:170])
    return len(found)


def catalog_gates(episode, chapter: str | None) -> int:
    """G-MOVES, G-STILL and G-SOURCE, the deterministic plan judges: HARD on a plan of
    the new form (a `source` span on any shot), printed as advisories on an
    older one -- every plan written before the camera catalog fails G-MOVES,
    and reading a historical plan is not endorsing it.  Hard count."""
    found = (plan_gates.moves_faults(episode) + plan_gates.still_faults(episode)
             + plan_gates.source_faults(episode, chapter))
    hard = episode.new_form()
    said = (len(found) or "clean") if hard else f"{len(found)} advisory (no `source` span on any shot; hard once one is written)"
    print("MOVES/SOURCE :", said)
    for f in found:
        print("   " if hard else "  advisory:", f[:170])
    return len(found) if hard else 0


def cover_gates(episode, book, number: int) -> int:
    """G-COVER, G-ORDER and G-SHOUT, HARD (root cause 2026-09-26; G-ORDER from the
    ten-agent debate 2026-09-27): the shots follow the chapter across scenes, the plan reaches the
    chapter's end and its title event, and no shout is filed as narration.
    ep12 reached paragraph 57 of 69 and read "Get under the water!" calmly."""
    title, paragraphs = plan_brief.chapter_paragraphs(book, number)
    found = (plan_gates.cover_faults(episode, paragraphs, title) + plan_gates.order_faults(episode, paragraphs)
             if paragraphs else [f"G-COVER plan: no source chapter for {number} to measure coverage against"])
    found += plan_gates.shout_faults(episode)
    print("COVER/SHOUT  :", len(found) or "clean")
    for f in found:
        print("   ", f[:170])
    return len(found)


def sound_gates(episode) -> int:
    """G-SOUND, HARD (root cause 2026-09-26, D10): every setup names its
    ambience and every shot whose prose names a loud event carries a sound."""
    from studio import episode_sound
    found = episode_sound.sound_faults(episode)
    print("SOUND        :", len(found) or "clean")
    for f in found:
        print("   ", f[:170])
    return len(found)


def measured_or_projected(book: Path, number: int, episode, rate: float) -> list[dict]:
    """The timeline's own shots when it has been written and is current, else
    the projection.  A STALE timeline is not a plan fault (ep13): the plan step
    runs before the timeline step, and refusing here meant an edited plan could
    never reach the step that rebuilds it."""
    placed = episode_home.home(book, number) / "placed.json"
    if placed.exists():
        try:
            episode_home.load_placed(book, number, episode)
        except SystemExit as why:
            print(f"TIMELINE     : {why} (advisory: projected from the plan; step 05 rebuilds it)")
            return projected(episode, rate)
        by = {s.index: s for s in episode.shots}
        return [dict(s, setup=by[s["index"]].setup, cuts=list(by[s["index"]].cuts))
                for s in episode_home.read_json(placed)["shots"] if s["index"] in by]
    return projected(episode, rate)


def sheet_text(book_id: str, number: int) -> int:
    """The sheet gate's text-only read, as `sheet_dq.py` prints it; hard count.

    It checks the prompts of the PAID seq_boards sheets, which only a book cast
    by bust and card draws. A book cast from one sheet per character draws
    storyboard grids instead, and on WotW this gate crashed on its size words --
    and the crash was counted as one hard fault with nothing printed, so every
    WotW plan was REFUSED for a reason nobody could see (audit 2026-09-22)."""
    if cast_refs.casts_from_sheets(episode_home.book_dir(book_id)):
        print("    not applicable: this book draws storyboard grids, not seq_boards sheets")
        return 0
    run = subprocess.run([sys.executable, str(Path(__file__).with_name("sheet_dq.py")), book_id, str(number)],
                         capture_output=True, text=True, errors="replace")
    tail = [l for l in run.stdout.splitlines() if l.strip()][-8:]
    for line in tail:
        print("   ", line[:150])
    m = re.search(r"(PASS|FAIL)\s+hard (\d+)", run.stdout)
    if m:
        return int(m.group(2))
    said = [l for l in (run.stderr or "").splitlines() if l.strip()][-3:]
    print("    the sheet gate did not report -- it CRASHED:", *(f"\n      {l[:150]}" for l in said))
    return 1


def main(book_id: str, number: int) -> int:
    book = episode_home.book_dir(book_id)
    ep = contract(book, number)
    if ep is None:
        return 1
    print("CONTRACT OK:", ep.title, "|", len(ep.shots), "shots |", f"{ep.projected_seconds():.0f}s projected")
    hard = 0
    unlit = house_style.faults(ep)
    print("G-LIGHT      :", len(unlit) or "clean"); hard += len(unlit)
    for f in unlit:
        print("   ", f[:170])
    rate = plan_gates.series_rate(book, number)
    refs = episode_home.read_json(book / "refs" / "refs.json")["refs"]
    for n in plan_gates.advisories(ep, plan_gates.series_lines(book, number), rate=rate):
        print("  advisory:", n[:150])
    pg = plan_gates.faults(ep, plan_gates.quote_share(plan_brief.chapter_paragraphs(book, number)[1]))
    print("PLAN GATES   :", len(pg) or "clean"); hard += len(pg)
    for f in pg:
        print("   ", f[:170])
    hard += setup_gate(ep, book, number)
    asp = plan_gates.aspect_faults(ep, plan_gates.series_aspect(book))
    print("G-ASPECT     :", asp or "clean"); hard += len(asp)
    cf = plan_gates.crowd_faults(ep)
    print("G-CROWD      :", cf or "clean"); hard += len(cf)
    for f in cf:
        print("   ", f[:170])
    cc = plan_gates.close_crowd_faults(ep)
    print("G-CROWD-CLOSE:", cc or "clean"); hard += len(cc)
    for f in cc:
        print("   ", f[:170])
    vocab = pack_refs.stage_vocab(book, refs, number)
    sf = plan_gates.stage_faults(ep, vocab)
    print("G-STAGE      :", len(sf) or "clean"); hard += len(sf)
    for f in sf:
        print("   ", f[:170])
    ff = plan_gates.creature_face_faults(ep, set(vocab["creatures"]))
    print("G-FACE-KIND  :", len(ff) or "clean"); hard += len(ff)
    for f in ff:
        print("   ", f[:170])
    pf = plan_gates.phantom_faults(ep, plan_gates.person_tokens(refs), house_style.place_words())
    print("G-PHANTOM    :", len(pf) or "clean"); hard += len(pf)
    for f in pf:
        print("   ", f[:170])
    names = plan_gates.names_from_refs(refs)
    gg = plan_gates.ghost_limb_faults(ep, names)
    print("G-GHOST      :", len(gg) or "clean"); hard += len(gg)
    for f in gg:
        print("   ", f[:170])
    gt = plan_gates.double_position_faults(ep, names)
    # ADVISORY until calibrated (2026-10-06): ten false faults on ep18's delivered
    # plan -- adjectives read as positions; duplicates are caught at the picture (G-TWIN).
    print("G-TWICE      :", f"{len(gt)} advisory" if gt else "clean")
    for f in gt:
        print("  advisory:", f[:170])
    print("EXPECTS TEXT :", plan_gates.expects_text(ep) or "no shot stages printed matter")
    bad, folded = plan_gates.bed_faults(ep)
    print("G-BED        :", len(bad) or "clean"); hard += len(bad)
    for f in bad + folded:
        print("   " if f in bad else "  advisory:", f[:170])
    hard += catalog_gates(ep, plan_brief.chapter_text(book, number))
    hard += cover_gates(ep, book, number)
    hard += sound_gates(ep)
    from studio import cell_gates
    cg = cell_gates.faults(ep, cell_gates.pack_prompts(book))
    print("CELL GATES   :", len(cg) or "clean"); hard += len(cg)
    for f in cg:
        print("   ", f[:170])
    for n in cell_gates.advisories(ep):
        print("  advisory:", n[:150])
    mf = ep.still_motions()
    bad = [(i, c) for i, c, w in mf if c in spec.HARD_MOTION]
    print("MOTION hard  :", bad or "clean"); hard += len(bad)
    for i, c, w in mf:
        print(f"    {c} shot {i}: {w[:140]}")
    crossed, vague = spec.plan_marks(ep, refs)
    print("MARKS        :", crossed or "clean", "| unmeasured", len(vague)); hard += len(crossed)
    actors = actor_gate.hard_episode(ep)
    print("ACTOR        :", actors or "clean"); hard += len(actors)
    hard += row_text_gate(book)
    import seq_boards  # noqa: E402
    unbound = seq_boards.unbound_cast(book, ep)
    print("CAST BOUND   :", unbound or "all bound"); hard += len(unbound)
    lifted, _ = spec.quoted_lines([l.model_dump() for l in ep.lines], seq_boards.book_words(book))
    print("QUOTE        :", [(l["index"], l["lifted"]) for l in lifted] or "clean"); hard += len(lifted)
    packed = [tuple(run) for run in tk.groups(measured_or_projected(book, number, ep, rate)) if len(run) > 1]
    print("ONE PER TAKE :", packed or "every shot its own take"); hard += len(packed)
    hf = plan_gates.hole_faults(ep, rate)
    print("G-HOLE       :", len(hf) or "clean"); hard += len(hf)
    for f in hf:
        print("   ", f[:170])
    long = long_shots(ep, rate)
    print(f"TAKE LENGTH  : {long or 'every shot inside a take'} (at {rate:.2f} words/s, budget {BUDGET} s)")
    hard += len(long)
    import takes_r2v  # noqa: E402  -- the take builder's own refusals, before it is asked to build
    for refuse in (takes_r2v.refuse_long_shots, takes_r2v.refuse_still_motions):
        try:
            refuse(ep)
        except SystemExit as e:
            print("TAKE BUILDER :", str(e)[:170]); hard += 1
    hard += take_lint_gate(book, ep, number, rate)
    print("SHEET TEXT   :")
    hard += sheet_text(book_id, number)
    print("VERDICT      :", "REFUSED" if hard else "clean -- lines may render")
    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], int(sys.argv[2])))
