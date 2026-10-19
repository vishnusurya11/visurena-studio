"""take_currency.currency: a take is stale only when ITS OWN inputs differ (RUNLOG row 43,
Jekyll Kawajiri ep01: after the owner restored the old 2x2_a and 1x1_b renders the board said
2 of 28 takes stale, T02 and T27 -- the audits' fan-out said 7).  Early cutoff: a redrawn
grid whose cut panels came back byte-equal stales nothing after it.  $0, tmp files."""
from __future__ import annotations

import json

from studio import take_currency as tc

NAMES = [f"T{i:02d}" for i in range(1, 29)]


def _graph(prompt: str, images: list[str], canvas=(1024, 1024)) -> dict:
    nodes = {"1": {"class_type": tc.RENDER_NODE, "inputs": {"prompt": prompt, "width": canvas[0], "height": canvas[1]}}}
    nodes |= {f"i{n}": {"class_type": "LoadImage", "inputs": {"image": name}} for n, name in enumerate(images)}
    return nodes


def _room(tmp_path) -> dict[str, dict]:
    """28 takes rendered from their own prompt and one picture each."""
    now = {}
    for n in NAMES:
        now[n] = {"prompt": f"prompt {n}", "pictures": [f"pic_{n}_a1.png"], "canvas": (1024, 1024)}
        (tmp_path / f"{n}.mp4").write_bytes(b"v")
        (tmp_path / f"{n}.graph.json").write_text(json.dumps(_graph(now[n]["prompt"], now[n]["pictures"])),
                                                  encoding="utf-8")
    return now


def test_two_redrawn_pictures_make_exactly_two_takes_stale(tmp_path):
    now = _room(tmp_path)
    now["T02"] = {**now["T02"], "pictures": ["pic_T02_b2.png"]}
    now["T27"] = {**now["T27"], "pictures": ["pic_T27_b2.png"]}
    got = tc.currency({n: tc.recorded_inputs(tmp_path / f"{n}.mp4") for n in NAMES}, now)
    assert sorted(n for n, why in got.items() if why) == ["T02", "T27"]
    assert got["T02"] == "pictures" and tc.stale_count(got) == 2


def test_restored_bytes_un_stale_the_rest(tmp_path):
    now = _room(tmp_path)                                       # every picture back to the recorded bytes
    got = tc.currency({n: tc.recorded_inputs(tmp_path / f"{n}.mp4") for n in NAMES}, now)
    assert tc.stale_count(got) == 0


def test_an_mtime_change_with_equal_bytes_stays_current(tmp_path):
    now = _room(tmp_path)
    (tmp_path / "T05.mp4").touch()
    got = tc.currency({"T05": tc.recorded_inputs(tmp_path / "T05.mp4")}, {"T05": now["T05"]})
    assert got == {"T05": None}


def test_the_first_differing_input_is_named(tmp_path):
    now = _room(tmp_path)
    now["T03"] = {**now["T03"], "prompt": "another", "canvas": (576, 1024)}
    rec = tc.recorded_inputs(tmp_path / "T03.mp4")
    assert tc.first_difference(rec, now["T03"]) == "prompt"


def test_a_take_with_no_provable_graph_is_unknown_never_current(tmp_path):
    now = _room(tmp_path)
    (tmp_path / "T09.graph.json").unlink()
    got = tc.currency({"T09": tc.recorded_inputs(tmp_path / "T09.mp4")}, {"T09": now["T09"]})
    assert got == {"T09": "unknown"} and tc.stale_count(got) == 0


def test_a_verdict_counts_only_when_its_sha_is_the_file_now():
    assert tc.verdict_current({"take_sha8": "ab12cd34"}, "ab12cd34")
    assert not tc.verdict_current({"take_sha8": "ab12cd34"}, "ffffffff")
    assert not tc.verdict_current(None, "ab12cd34")
