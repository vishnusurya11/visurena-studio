"""G-TAKE-INPUTS: a kept take was rendered from the pictures the plan stages NOW.

Jekyll HEL ep01 iter4 (audit 2026-10-15, 01_staged_refs.md): T06.graph.json
staged the SUPERSEDED lace-bonnet girl sheet (`sheet_front_b54219a4.png`) and a
panel no longer on disk; `take_dq --attempts` kept that roll (95) over four
current rolls (10-40) because the rank was (passed, score) only, and the master
shipped it.  A score ranks renders of the same inputs, never across a changed
input.  No test here renders, calls ComfyUI or spends: tiny fake graphs and
dummy pngs under tmp_path.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.episode import take_dq
from studio import episode_home, take_currency as tc, take_inputs as ti
from studio import take_verdict as tv
from studio.comfy import staged_name

PROMPT = "the girl crosses"


def png(path: Path, body: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return path


def graph_with(take: Path, names: list[str]) -> Path:
    """A fake T<NN>.graph.json: the render node and one LoadImage per name."""
    nodes = {"1": {"class_type": tc.RENDER_NODE, "inputs": {"prompt": PROMPT, "width": 768, "height": 768}}}
    for k, n in enumerate(names, start=2):
        nodes[str(k)] = {"class_type": "LoadImage", "inputs": {"image": n}}
    path = tc.graph_of(take)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(nodes), encoding="utf-8")
    return path


def book_of(tmp_path: Path) -> SimpleNamespace:
    """A book with the girl's current sheet, her superseded lace sheet, and a panel."""
    book = tmp_path / "book"
    girl = book / "refs" / "characters" / "girl"
    new = png(girl / "sheet_front.png", b"grey bonnet, red blouse")
    old = png(girl / "superseded" / "sheet_front_2026-10-14_lace.png", b"black lace bonnet")
    panel = png(book / "episodes" / "ep01" / "storyboard" / "h3" / "shot_06.png", b"panel 08ba")
    # the lace sheet was staged while it was sheet_front.png: same stem, its own bytes
    lace_name = f"sheet_front_{ti.md5_8(old)}.png"
    return SimpleNamespace(book=book, new=new, old=old, panel=panel, lace=lace_name,
                           current=[new, panel], take=book / "episodes" / "ep01" / "takes" / "r2v" / "T06.mp4")


# ---- the pure comparison ----------------------------------------------------------------

def test_digest_of_reads_the_content_suffix():
    assert ti.digest_of("sheet_front_b54219a4.png") == "b54219a4"


def test_wanted_names_are_the_staged_names_of_the_current_pictures(tmp_path):
    b = book_of(tmp_path)
    assert ti.wanted_names(b.current) == {staged_name(b.new), staged_name(b.panel)}


def test_a_picture_not_on_disk_is_wanted_by_a_name_no_graph_holds(tmp_path):
    assert ti.wanted_names([tmp_path / "gone.png"]) == {"gone.png (not on disk)"}


def test_a_take_staging_exactly_the_current_pictures_is_current(tmp_path):
    b = book_of(tmp_path)
    png(b.take, b"render")
    graph_with(b.take, [staged_name(b.new), staged_name(b.panel)])
    got = ti.check(b.take, b.current)
    assert got.current and got.stale == [] and got.missing == [] and got.superseded == []


def test_the_jekyll_t06_graph_is_stale_and_names_the_superseded_sheet(tmp_path):
    b = book_of(tmp_path)
    png(b.take, b"render")
    graph_with(b.take, [b.lace, "shot_06_9529a05f.png"])
    got = ti.check(b.take, b.current)
    assert got.current is False
    assert got.stale == sorted([b.lace, "shot_06_9529a05f.png"])
    assert got.missing == sorted([staged_name(b.new), staged_name(b.panel)])
    assert got.superseded == [b.lace]
    assert "(superseded)" in got.said() and "missing" in got.said()


def test_a_take_with_no_graph_is_not_current(tmp_path):
    b = book_of(tmp_path)
    png(b.take, b"render")
    got = ti.check(b.take, b.current)
    assert got.current is False and got.unknown_provenance is True


def test_the_unknown_provenance_stub_is_not_current(tmp_path):
    b = book_of(tmp_path)
    png(b.take, b"render")
    tc.write_stub(tc.graph_of(b.take))
    assert ti.check(b.take, b.current).current is False
    assert tc.is_current(PROMPT, b.take) is False
    assert tc.staged_images(b.take) == set() and tc.recorded_canvas(b.take) is None


def test_superseded_by_digest_looks_only_in_each_pictures_own_superseded_room(tmp_path):
    b = book_of(tmp_path)
    assert ti.superseded_by_digest(b.current) == {ti.digest_of(b.lace): b.old}


# ---- the master roll-up: refusals, the count line, the wall ------------------------------

def audited_pair(tmp_path: Path) -> dict:
    return {5: ti.Inputs(True, staged=["a.png"]),
            6: ti.Inputs(False, staged=["sheet_front_b54219a4.png"], stale=["sheet_front_b54219a4.png"],
                         missing=["sheet_front_45becc16.png"], superseded=["sheet_front_b54219a4.png"])}


def test_the_count_line_names_all_takes_current():
    assert ti.count_line({i: ti.Inputs(True) for i in range(23)}) == "inputs: all 23 takes current"


def test_the_count_line_names_how_many_are_stale(tmp_path):
    assert ti.count_line(audited_pair(tmp_path)) == "inputs: 1 of 2 takes stale"


def test_refusals_name_each_stale_take_and_its_pictures(tmp_path):
    (line,) = ti.refusals(audited_pair(tmp_path))
    assert line.startswith("T06:") and "sheet_front_b54219a4.png (superseded)" in line
    assert "missing sheet_front_45becc16.png" in line


def test_the_wall_refuses_a_stale_take_and_passes_a_current_set(tmp_path):
    with pytest.raises(SystemExit, match="T06: stale sheet_front_b54219a4.png"):
        ti.wall(audited_pair(tmp_path))
    ti.wall({1: ti.Inputs(True)})


def test_report_carries_ok_the_count_and_the_stale_takes(tmp_path):
    doc = ti.report(audited_pair(tmp_path))
    assert doc["ok"] is False and doc["of"] == 2 and doc["current"] == 1
    assert set(doc["stale"]) == {"T06"} and doc["line"] == "inputs: 1 of 2 takes stale"


def test_audit_reads_each_record_against_its_card_and_skips_stills(tmp_path):
    b = book_of(tmp_path)
    png(b.take, b"render")
    graph_with(b.take, [b.lace, "shot_06_9529a05f.png"])
    rec = {"index": 6, "rel_path": "episodes/ep01/takes/r2v/T06.mp4", "anchors": [],
           "refs": ["refs/characters/girl/sheet_front.png", "episodes/ep01/storyboard/h3/shot_06.png"]}
    assert ti.audit([rec], b.book, 1)[6].superseded == [b.lace]
    assert ti.audit([rec], b.book, 1, skip={6}) == {}
    assert ti.audit([{"index": 2, "rel_path": "x.mp4"}], b.book, 1) == {}   # no card of references


# ---- the take gate's row and settle --------------------------------------------------------

def verdict(passed: bool, score: float) -> tv.TakeVerdict:
    v = tv.TakeVerdict(6, 0, "T06.mp4", 5.0, "narration", [], [])
    v.score, v.passed = score, passed
    return v


def test_the_inputs_row_is_hard_and_fails_a_stale_take():
    g = ti.row(ti.Inputs(False, stale=["x_1.png"]))
    assert g.name == "inputs" and g.hard and not g.ok
    assert ti.row(ti.Inputs(True)).ok


def test_with_inputs_row_fails_a_stale_attempt_and_keeps_a_current_pass():
    assert take_dq.with_inputs_row(verdict(True, 95.0), ti.Inputs(False, stale=["x.png"])).passed is False
    v = take_dq.with_inputs_row(verdict(True, 95.0), ti.Inputs(True))
    assert v.passed is True and v.gates[-1].name == "inputs"


def test_rankable_keeps_only_current_attempts_when_any_is(tmp_path):
    a, b = tmp_path / "T06.mp4", tmp_path / "T06_fail4.mp4"
    verdicts = {a: verdict(False, 40.0), b: verdict(True, 95.0)}
    assert take_dq.rankable(verdicts, {a: ti.Inputs(True), b: ti.Inputs(False)}) == {a: verdicts[a]}
    assert take_dq.rankable(verdicts, {a: ti.Inputs(False), b: ti.Inputs(False)}) == verdicts
    assert take_dq.rankable(verdicts, None) == verdicts


def test_settle_never_ranks_a_stale_95_over_a_current_40(tmp_path):
    """The Jekyll T06 swap at 11:32, replayed: the lace roll must stay archived."""
    kept = png(tmp_path / "T06.mp4", b"current, 40")
    stale = png(tmp_path / "attempts" / "T06_fail4.mp4", b"lace, 95")
    inputs = {kept: ti.Inputs(True), stale: ti.Inputs(False, stale=["sheet_front_b54219a4.png"])}
    best = take_dq.settle(tmp_path, 6, {kept: verdict(False, 40.0), stale: verdict(True, 95.0)}, inputs)
    assert best == kept and kept.read_bytes() == b"current, 40" and stale.exists()


def test_settle_with_no_current_roll_swaps_nothing_in(tmp_path):
    kept = png(tmp_path / "T06.mp4", b"stale, 30")
    other = png(tmp_path / "attempts" / "T06_fail4.mp4", b"stale, 95")
    inputs = {kept: ti.Inputs(False), other: ti.Inputs(False)}
    best = take_dq.settle(tmp_path, 6, {kept: verdict(False, 30.0), other: verdict(False, 95.0)}, inputs)
    assert best == kept and kept.read_bytes() == b"stale, 30" and other.exists()


def test_inputs_record_marks_a_stale_kept_take():
    doc = take_dq.inputs_record(ti.Inputs(False, stale=["x_1.png"]))
    assert doc["inputs_stale"] is True and doc["inputs"]["stale"] == ["x_1.png"]
    assert take_dq.inputs_record(ti.Inputs(True))["inputs_stale"] is False


def test_a_cached_verdict_stands_only_while_it_knew_the_same_currency():
    assert take_dq.cache_agrees({"inputs_stale": False}, ti.Inputs(True))
    assert not take_dq.cache_agrees({"inputs_stale": False}, ti.Inputs(False))
    assert not take_dq.cache_agrees({}, ti.Inputs(False))
    assert take_dq.cache_agrees({"inputs_stale": True}, ti.Inputs(False))


# ---- the swap: each roll carries ITS OWN graph, or the stub ---------------------------------

def graph(prompt: str) -> dict:
    return {"5": {"class_type": tc.RENDER_NODE, "inputs": {"prompt": prompt}}}


def put_graph(path: Path, prompt: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph(prompt)), encoding="utf-8")


def test_an_archived_attempt_never_carries_another_renders_graph(tmp_path):
    """LESSONS (3ae4584, open): swap_in of a graphless roll COPIED the displaced
    take's graph beside it; displaced again, the roll was archived carrying
    render A's graph -- a record that lies about what it ran with."""
    png(tmp_path / "T05.mp4", b"render A")
    put_graph(tmp_path / "T05.graph.json", "A words")
    roll_b = png(tmp_path / "attempts" / "T05_fail1.mp4", b"render B")         # legacy: no graph
    episode_home.swap_in(tmp_path, 5, roll_b)
    episode_home.swap_in(tmp_path, 5, tmp_path / "attempts" / "T05_fail2.mp4")  # A back in
    archived_b = tmp_path / "attempts" / "T05_fail3.mp4"
    assert archived_b.read_bytes() == b"render B"
    assert tc.provenance_unknown(archived_b) and tc.recorded_prompt(archived_b) is None
    assert tc.recorded_prompt(tmp_path / "T05.mp4") == "A words"


def test_a_graphless_winner_gets_the_stub_not_the_displaced_graph(tmp_path):
    png(tmp_path / "T05.mp4", b"render A")
    put_graph(tmp_path / "T05.graph.json", "A words")
    roll_b = png(tmp_path / "attempts" / "T05_fail1.mp4", b"render B")
    episode_home.swap_in(tmp_path, 5, roll_b)
    kept = tmp_path / "T05.mp4"
    assert json.loads(tc.graph_of(kept).read_text(encoding="utf-8")) == tc.STUB
    assert tc.recorded_prompt(tmp_path / "attempts" / "T05_fail2.mp4") == "A words"


def test_displace_writes_the_stub_over_an_orphan_graph(tmp_path):
    """A take with no graph of its own must not inherit one left at its fail name."""
    png(tmp_path / "T05.mp4", b"graphless")
    put_graph(tmp_path / "attempts" / "T05_fail1.graph.json", "someone else")
    moved = episode_home.displace(tmp_path / "T05.mp4", 5)
    assert tc.provenance_unknown(moved)


def test_carry_graph_moves_its_own_or_writes_the_stub(tmp_path):
    own, dest = tmp_path / "a.graph.json", tmp_path / "b.graph.json"
    put_graph(own, "mine")
    tc.carry_graph(own, dest)
    assert not own.exists() and json.loads(dest.read_text(encoding="utf-8")) == graph("mine")
    tc.carry_graph(own, dest)
    assert json.loads(dest.read_text(encoding="utf-8")) == tc.STUB


# ---- the walls: assemble, QC, step 09 --------------------------------------------------------

def stale_room(tmp_path: Path) -> SimpleNamespace:
    b = book_of(tmp_path)
    png(b.take, b"render")
    graph_with(b.take, [b.lace, "shot_06_9529a05f.png"])
    rec = {"index": 6, "rel_path": "episodes/ep01/takes/r2v/T06.mp4", "anchors": [],
           "refs": ["refs/characters/girl/sheet_front.png", "episodes/ep01/storyboard/h3/shot_06.png"]}
    episode_home.write_json(b.take.parent / "shots.json", [rec])
    return SimpleNamespace(**vars(b), rec=rec, room=b.take.parent)


def test_assemble_refuses_a_master_with_a_stale_take(tmp_path):
    from scripts.episode import assemble
    s = stale_room(tmp_path)
    with pytest.raises(SystemExit, match=r"T06: stale .*\(superseded\)"):
        assemble.refuse_stale_inputs(s.book, 1, s.room)


def test_assemble_lets_a_current_master_through(tmp_path):
    from scripts.episode import assemble
    s = stale_room(tmp_path)
    graph_with(s.take, [staged_name(s.new), staged_name(s.panel)])
    assemble.refuse_stale_inputs(s.book, 1, s.room)


def test_qc_carries_the_inputs_row_and_its_count_line(tmp_path):
    from scripts.episode import qc
    s = stale_room(tmp_path)
    i = SimpleNamespace(book=s.book, number=1, take_dir=s.room, records=[s.rec])
    doc = qc.inputs_rows(i, {})["inputs"]
    assert doc["ok"] is False and doc["line"] == "inputs: 1 of 1 takes stale"
    graph_with(s.take, [staged_name(s.new), staged_name(s.panel)])
    assert qc.inputs_rows(i, {})["inputs"]["line"] == "inputs: all 1 takes current"


def test_qc_fails_the_master_on_the_inputs_row():
    from scripts.episode import qc
    assert "inputs" in qc.failed_rows({"inputs": {"ok": False}})
    assert "inputs" not in qc.failed_rows({"inputs": {"ok": True}})
    assert qc.inputs_ok({"inputs": {"ok": False}}) is False
    assert qc.inputs_ok({"inputs": {"ok": True}}) is True


def test_step_09_prints_the_staged_ids_and_stops_on_a_stale_take(tmp_path, capsys):
    from scripts.episode import step_09_shoot as shoot
    s = stale_room(tmp_path)
    ctx = SimpleNamespace(home=s.book / "episodes" / "ep01", book_dir=s.book, number=1)
    with pytest.raises(SystemExit, match="T06"):
        shoot.inputs_wall(ctx)
    assert s.lace in capsys.readouterr().out
    graph_with(s.take, [staged_name(s.new), staged_name(s.panel)])
    shoot.inputs_wall(ctx)
    assert "inputs: all 1 takes current" in capsys.readouterr().out


# ---- the words are an input too (Jekyll ep01 iter7, 2026-10-16) --------------------------------

def test_reworded_marks_an_attempt_rendered_from_other_words_not_current(tmp_path):
    """iter7 T06: the plan aimed Enfield's run (the duplicate-Enfield cure); the round-1 render
    carried the new words, and `--attempts` swapped back the iter6 render (90, OLD words, the
    duplicate) because G-TAKE-INPUTS read only the pictures."""
    old, new = png(tmp_path / "T06.mp4", b"old words"), png(tmp_path / "attempts" / "T06_fail13.mp4", b"new")
    put_graph(old.with_suffix(".graph.json"), "Enfield runs forward from the LEFT edge")
    put_graph(new.with_suffix(".graph.json"), "Enfield runs forward from the LEFT edge toward the fallen girl")
    now = take_dq.reworded({old: ti.Inputs(True), new: ti.Inputs(True)},
                           "Enfield runs forward from the LEFT edge toward the fallen girl")
    assert now[new].current and not now[old].current and now[old].reworded
    assert "older words" in now[old].said()


def test_reworded_with_no_prompt_leaves_the_inputs_alone(tmp_path):
    a = png(tmp_path / "T06.mp4", b"x")
    assert take_dq.reworded({a: ti.Inputs(True)}, "")[a].current
