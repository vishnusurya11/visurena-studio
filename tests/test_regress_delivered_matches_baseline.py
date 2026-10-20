"""Deadline retro item 6 (2026-10-20, package B2): the deciders replayed on DELIVERED ep01 at commit time.

`scripts/episode/regress_delivered.py` builds a stand-in of ep01 as delivered from its frozen records
(tests/fixtures/delivered/ep01/: copies of the named record files plus stat.json -- each file's size and
mtime, each kept take's sha8 and the signed eye's fingerprint; no video), asks package A's decider library
(scripts/episode/repair_dry_check: the render pass, the early round, the batched rung, the terminal swap,
the freeze) what each take would do -- `bare` with no repair window, `held` under the repair that governs --
and diffs that action table against actions.baseline.json.  A re-baseline is its own commit with a stated
reason.

INCIDENT 3 (2026-10-19 11:18 PDT): P03 reworded two sentences of every take's prompt (the unlettered
sentence lost "cheque", the night style line lost "low sun") and all 28 delivered takes read stale.  The
reword is DERIVED from the records: T00's delivered graph against its 11:18 graph
(tests/fixtures/ep01_replay/repair_rerun/T00.graph_1118.json).  On today's records it reaches 27 takes:
T01 was re-rendered in the repair on the post-P03 words (its first words are kept in
tests/fixtures/ep01_replay/P03/shots.json).  Put T01's first words back and the 11:18 launch is replayed:
28 renders.  The freeze holds every one of them.  No GPU, no ComfyUI, no library/ read: temp files only."""
from __future__ import annotations

import difflib
import json
import os
import re
import shutil
from pathlib import Path

import pytest

from scripts.episode import regress_delivered as rd
from scripts.episode import take_dq
from studio import episode_ref_official as ro
from studio import eye_verdict
from studio import take_currency as tc

FIX = Path(__file__).parent / "fixtures" / "delivered" / "ep01"
REPLAY = Path(__file__).parent / "fixtures" / "ep01_replay"
TAKES = 28
SENTENCE = re.compile(r"(?<=\.)[ ]+|\n")


def graph_prompt(path: Path) -> str:
    return tc.prompt_of(json.loads(path.read_text(encoding="utf-8")))


def sentence_swaps(before: str, after: str) -> list[tuple[str, str]]:
    """The sentences `after` rewords from `before`, pair by pair."""
    a, b = SENTENCE.split(before), SENTENCE.split(after)
    ops = difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes()
    return [(x, y) for op, i1, i2, j1, j2 in ops if op == "replace" for x, y in zip(a[i1:i2], b[j1:j2])]


P03_SWAPS = sentence_swaps(graph_prompt(FIX / "takes" / "r2v" / "T00.graph.json"),
                           graph_prompt(REPLAY / "repair_rerun" / "T00.graph_1118.json"))


def p03(prompt: str) -> str:
    """P03's two reworded sentences, as T00's 11:18 graph shows them, on any take's words."""
    for old, new in P03_SWAPS:
        prompt = prompt.replace(old, new)
    return prompt


UNLETTERED = re.compile(r"Every [^.]* in the picture is plain and unlettered\.")


def todays_unlettered(prompt: str) -> str:
    """Today's word rule (ro.unlettered_for) said over the take's own text in place of its recorded sentence."""
    rest = UNLETTERED.sub("", prompt)
    return UNLETTERED.sub(lambda _: ro.unlettered_for(rest), prompt)


def actions(rows: dict, column: str) -> dict[str, str]:
    """take -> the action word (render / keep / retake / swap) in one column."""
    return {take: row[column].split(":")[0] for take, row in rows.items()}


def flipped(rows: dict, column: str, base: dict | None = None) -> list[str]:
    base = rd.read_baseline(FIX)["rows"] if base is None else base
    return sorted(t for t, a in actions(rows, column).items() if a != actions(base, column)[t])


# ---- the baseline -----------------------------------------------------------------------------

def test_the_action_table_equals_the_committed_baseline():
    moved = rd.diff(rd.read_baseline(FIX)["rows"], rd.table(FIX))
    assert moved == [], "the deciders move delivered ep01 (re-baseline in its own commit, with a reason):\n" + \
        "\n".join(moved)


def test_the_baseline_keeps_all_28_delivered_takes_under_their_repair():
    rows = rd.read_baseline(FIX)["rows"]
    assert sorted(rows) == [f"T{i:02d}" for i in range(TAKES)]
    assert set(actions(rows, "held").values()) == {"keep"}
    assert rd.read_baseline(FIX)["reason"]


def test_without_the_freeze_the_early_round_still_retakes_t01():
    """Incident 4's decider, still there under the freeze: the gait row orders T01 when no repair holds it."""
    rows = rd.table(FIX)
    assert rows["T01"]["bare"].startswith("retake: early round")
    assert rows["T01"]["held"] == "keep: current"


def test_the_fixture_holds_no_video():
    assert not list(FIX.rglob("*.mp4"))
    assert len(json.loads((FIX / rd.STAT).read_text(encoding="utf-8"))["kept"]) == TAKES


# ---- incident 3: P03's reworded cheque ---------------------------------------------------------

def test_p03s_reword_is_two_sentences_read_off_the_records():
    assert [("cheque" in old, "cheque" in new) for old, new in P03_SWAPS] == [(True, False), (False, False)]
    assert "low sun" in P03_SWAPS[1][0] and "low sun" not in P03_SWAPS[1][1]


def test_p03s_reword_flips_27_of_todays_delivered_takes_without_the_freeze():
    rows = rd.table(FIX, reword=p03)
    assert flipped(rows, "bare") == [f"T{i:02d}" for i in range(TAKES) if i != 1]
    assert all(rows[t]["bare"] == "render: stale: prompt" for t in flipped(rows, "bare"))


def test_at_the_1118_launch_p03s_reword_flips_all_28():
    """T01 with the words it carried at 11:18 (before the repair re-rendered it): incident 3, 28 renders."""
    home, doc = rd.stand_in(FIX)
    try:
        first = json.loads((REPLAY / "P03" / "shots.json").read_text(encoding="utf-8"))[1]["prompt"]
        carried(home / "takes" / "r2v" / "T01.graph.json", first)
        rows = rd.replay(home, doc, reword=p03)
    finally:
        shutil.rmtree(home.parent, ignore_errors=True)
    assert [t for t, a in actions(rows, "bare").items() if a == "render"] == [f"T{i:02d}" for i in range(TAKES)]
    assert set(actions(rows, "held").values()) == {"keep"}


def carried(graph: Path, words: str) -> None:
    """The graph's render node set to `words`, its recorded mtime kept (a newer graph reads unfinished)."""
    st, doc = graph.stat(), json.loads(graph.read_text(encoding="utf-8"))
    next(n for n in doc.values() if isinstance(n, dict) and n.get("class_type") == tc.RENDER_NODE)["inputs"][
        "prompt"] = words
    graph.write_text(json.dumps(doc), encoding="utf-8")
    os.utime(graph, ns=(st.st_atime_ns, st.st_mtime_ns))


@pytest.mark.parametrize("reword", [p03, todays_unlettered], ids=["p03", "todays_unlettered_rule"])
def test_the_freeze_holds_every_reworded_take(reword):
    rows = rd.table(FIX, reword=reword)
    assert set(actions(rows, "held").values()) == {"keep"}
    assert flipped(rows, "bare"), "the reword reached no take: the replay would prove nothing"


# ---- the diff and the re-baseline ---------------------------------------------------------------

def test_a_diff_names_each_take_and_column_it_moves():
    base = {"T00": {"bare": "keep: current", "held": "keep: current"}}
    now = {"T00": {"bare": "render: stale: prompt", "held": "keep: current"}, "T01": {"bare": "x", "held": "x"}}
    assert rd.diff(base, now) == ["T00 bare: keep: current -> render: stale: prompt", "T01: not in the baseline"]
    assert rd.diff(now, base) == ["T00 bare: render: stale: prompt -> keep: current", "T01: gone from the table"]


@pytest.fixture
def copy(tmp_path, monkeypatch):
    """A copy of the ep01 fixture whose baseline may be rewritten; no guarded path moved."""
    dest = tmp_path / "delivered" / "ep01"
    shutil.copytree(FIX, dest)
    monkeypatch.setattr(rd, "changed_paths", lambda: [])
    return dest


def test_a_rebaseline_states_its_reason_and_the_rows_it_moved(copy):
    doc = rd.read_baseline(copy)
    doc["rows"]["T05"]["held"] = "render: stale: prompt"
    rd.write_json(copy / rd.BASELINE, doc)
    moved = rd.rebaseline(copy, "test: T05 put back")
    assert moved == ["T05 held: render: stale: prompt -> keep: current"]
    assert rd.read_baseline(copy)["reason"] == "test: T05 put back"
    assert rd.read_baseline(copy)["moved"] == moved and rd.diff(rd.read_baseline(copy)["rows"], rd.table(copy)) == []


def test_a_rebaseline_without_a_reason_is_refused(copy):
    with pytest.raises(SystemExit, match="reason"):
        rd.rebaseline(copy, "  ")


def test_a_rebaseline_is_refused_while_a_guarded_path_is_uncommitted(copy, monkeypatch):
    monkeypatch.setattr(rd, "changed_paths", lambda: ["studio/take_currency.py", "README.md"])
    with pytest.raises(SystemExit, match="studio/take_currency.py"):
        rd.rebaseline(copy, "a reason")


def test_the_baseline_file_is_written_with_lf(copy):
    rd.rebaseline(copy, "a reason")
    assert b"\r\n" not in (copy / rd.BASELINE).read_bytes()


# ---- the wiring: on commits touching prompt words, take_currency or the ladder --------------------

def test_the_replay_is_owed_only_when_a_guarded_path_moved():
    assert rd.touched(["README.md", "studio/face_gate.py"]) == []
    assert rd.touched(["studio/take_ladder.py", "studio/episode_ref_official.py"]) == \
        ["studio/episode_ref_official.py", "studio/take_ladder.py"]


def test_every_guarded_path_exists():
    root = Path(rd.ROOT)
    assert [p for p in rd.GUARDED if not (root / p).exists()] == []
    assert {"studio/take_currency.py", "studio/take_ladder.py", "studio/episode_ref_official.py"} <= set(rd.GUARDED)


def test_the_command_skips_when_no_guarded_path_moved(monkeypatch, capsys):
    monkeypatch.setattr(rd, "changed_paths", lambda: ["README.md"])
    monkeypatch.setattr(rd, "check", lambda *a: pytest.fail("the replay is not owed"))
    assert rd.main(["--touched"]) == 0
    assert "not owed" in capsys.readouterr().out


def test_the_command_exits_1_on_a_diff_and_0_on_a_match(copy, monkeypatch, capsys):
    monkeypatch.setattr(rd, "FIXTURES", copy.parent)
    assert rd.main([]) == 0
    doc = rd.read_baseline(copy)
    doc["rows"]["T00"]["bare"] = "render: stale: prompt"
    rd.write_json(copy / rd.BASELINE, doc)
    assert rd.main([]) == 1
    assert "T00 bare: render: stale: prompt -> keep: current" in capsys.readouterr().out


def test_the_command_rebaselines_with_its_reason(copy, monkeypatch):
    monkeypatch.setattr(rd, "FIXTURES", copy.parent)
    assert rd.main(["--rebaseline", "ep01", "a stated reason"]) == 0
    assert rd.read_baseline(copy)["reason"] == "a stated reason"


# ---- the stand-in -------------------------------------------------------------------------------

def test_the_replay_leaves_the_fixture_untouched_and_restores_the_hashes():
    before = {p: p.stat().st_mtime_ns for p in FIX.rglob("*")}
    seams = (tc.sha8_of, take_dq.take_sha8, eye_verdict.fingerprint)
    rd.table(FIX)
    assert {p: p.stat().st_mtime_ns for p in FIX.rglob("*")} == before
    assert (tc.sha8_of, take_dq.take_sha8, eye_verdict.fingerprint) == seams


def test_a_stand_in_carries_each_recorded_size_and_mtime():
    home, doc = rd.stand_in(FIX)
    try:
        for rel, row in list(doc["files"].items())[:5] + list(doc["kept"].items())[:3]:
            st = (home / rel).stat()
            assert (st.st_mtime_ns, st.st_size if rel.endswith(".mp4") else row["size"]) == \
                (row["mtime_ns"], row["size"])
    finally:
        shutil.rmtree(home.parent, ignore_errors=True)


def test_under_the_stand_in_a_take_hashes_to_its_recorded_bytes():
    home, doc = rd.stand_in(FIX)
    try:
        with rd.recorded_bytes(home, doc):
            room = home / "takes" / "r2v"
            assert tc.sha8_of(room / "T00.mp4") == doc["kept"]["takes/r2v/T00.mp4"]["sha8"]
            assert eye_verdict.fingerprint(sorted(room.glob("T??.mp4"))) == doc["eye"]
    finally:
        shutil.rmtree(home.parent, ignore_errors=True)


@pytest.fixture
def delivered(tmp_path):
    """A small delivered episode: two takes with graph and dq records, one archived draw, a manifest."""
    home = tmp_path / "ep09"
    room = home / "takes" / "r2v"
    (room / "attempts").mkdir(parents=True)
    for name in ("manifest.json", "repair.jsonl", "attempts.json"):
        (home / name).write_text("{}", encoding="utf-8")
    (room / "shots.json").write_text("[]", encoding="utf-8")
    for i in (0, 1):
        (room / f"T{i:02d}.mp4").write_bytes(f"take {i}".encode())
        (room / f"T{i:02d}.graph.json").write_text("{}", encoding="utf-8")
        (room / f"T{i:02d}.dq.json").write_text("{}", encoding="utf-8")
    (room / "attempts" / "T01_fail1.mp4").write_bytes(b"an archived draw")
    return home


def test_a_freeze_copies_records_and_never_a_video(delivered, tmp_path):
    dest = tmp_path / "fixture"
    doc = rd.freeze(delivered, dest)
    assert not list(dest.rglob("*.mp4"))
    assert (dest / "takes" / "r2v" / "T01.dq.json").exists() and (dest / "manifest.json").exists()
    assert doc["kept"]["takes/r2v/T01.mp4"]["sha8"] == tc.sha8_of(delivered / "takes" / "r2v" / "T01.mp4")
    assert doc["draws"]["takes/r2v/attempts/T01_fail1.mp4"]["size"] == len(b"an archived draw")
    assert doc["eye"] == eye_verdict.fingerprint(sorted((delivered / "takes" / "r2v").glob("T??.mp4")))
    assert json.loads((dest / rd.STAT).read_text(encoding="utf-8")) == doc


def test_a_freeze_skips_a_record_the_episode_never_wrote(delivered, tmp_path):
    doc = rd.freeze(delivered, tmp_path / "fixture")
    assert "clock.jsonl" not in doc["files"] and "manifest.json" in doc["files"]
