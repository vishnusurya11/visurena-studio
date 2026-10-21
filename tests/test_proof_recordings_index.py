"""The recordings index (DESIGN 2026-10-21_ep02_proof 2.1; package P2).

recordings.json is built ONCE per source episode, read-only, from NAMED files (no walk): every
take keyed (index, tries) with its graph's fields, every refine crop keyed by its staged _src
bytes, every grid, place master, TTS line, VL text read, transcript memo and SDK stream, each
with the seconds its record carries.  The fixture is a copy of a few of Jekyll ep01's named
records; the media they name are made here as small byte files, so no media is in git and no
test reads the HDD library."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

import pytest

from studio.rehearsal import recordings as rec

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "proof" / "recordings" / "library"
REPO = Path(__file__).resolve().parents[1]
MEDIA = ["takes/r2v/T02.mp4", "takes/r2v/T03.mp4", "takes/r2v/attempts/T02_fail1.mp4",
         "takes/r2v/attempts/T02_fail2.mp4", "takes/r2v/refine/T06_p0.mp4", "takes/r2v/refine/T06_p0_src.mp4",
         "takes/r2v/refine/T06_p1.mp4", "takes/r2v/refine/T06_p1_src.mp4",
         "storyboard/grids/ep01_grid_night_door_2x2.png", "storyboard/grids/ep01_grid_night_corner_1x1_a.png",
         "storyboard/h3/shot_00.png", "storyboard/h3/shot_06.png", "storyboard/anchors/night_door.png",
         "audio/lines/l00.wav", "audio/lines/l01.wav", "audio/lines/l02.wav",
         "takes/work/content/T02_0.png", "takes/work/content/T02_1.png", "takes/work/content/T02_2.png"]
PLACES = ["refs/locations/black_mail_house_door/wide_establishing.png",
          "refs/locations/london_sunday_walks/wide_establishing.png"]


def fake_key(name: str, values: dict) -> str:
    return hashlib.sha256(json.dumps([name, values], sort_keys=True).encode()).hexdigest()


@pytest.fixture
def lib(tmp_path):
    root = tmp_path / "library"
    shutil.copytree(FIXTURE, root)
    home = root / "jekyll" / "episodes" / "ep01"
    for rel in MEDIA:
        (home / rel).parent.mkdir(parents=True, exist_ok=True)
        (home / rel).write_bytes(rel.encode())
    for rel in PLACES:
        (root / "jekyll" / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / "jekyll" / rel).write_bytes(rel.encode())
    return root


def kind(entries: list[dict], k: str) -> list[dict]:
    return [e for e in entries if e["kind"] == k]


def build(lib: Path) -> dict:
    return rec.build(lib / "jekyll", 1, lib, text_key=fake_key)


def test_a_graph_gives_its_seed_frames_prompt_loras_staged_names_and_classes():
    graph = {"1": {"class_type": "RandomNoise", "inputs": {"noise_seed": 82204}},
             "2": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {"prompt": "a man", "length": 158}},
             "3": {"class_type": "LoraLoaderModelOnly", "inputs": {"lora_name": "turbo.safetensors",
                                                                   "strength_model": 0.7}},
             "4": {"class_type": "LoadImage", "inputs": {"image": "sheet_front_c367d8b2.png"}},
             "5": {"class_type": "LoadAudio", "inputs": {"audio": "silence_02_3e24c635.wav"}}}
    f = rec.graph_fields(graph)
    assert (f["seed"], f["frames"], f["prompts"]) == (82204, 158, ["a man"])
    assert f["loras"] == [["turbo.safetensors", 0.7]]
    assert f["staged"] == ["sheet_front_c367d8b2.png", "silence_02_3e24c635.wav"]
    assert f["node_classes"] == sorted({"RandomNoise", "MiniMaxH3ReferenceToVideo", "LoraLoaderModelOnly",
                                        "LoadImage", "LoadAudio"})


def test_tries_come_from_the_seed_rule_of_takes_r2v(lib):
    assert rec.tries_from_seed(82103, base=82002) == 1
    assert rec.tries_from_seed(82002, base=82002) == 0
    assert rec.tries_from_seed(82050, base=82002) is None
    src = (REPO / "scripts" / "episode" / "takes_r2v.py").read_text(encoding="utf-8")
    assert re.search(r'c\["seed"\] \+= 101 \* tries', src), "the retake seed rule moved: re-derive TRY_STEP"


def test_every_take_is_keyed_by_index_and_tries_kept_and_attempts(lib):
    takes = kind(build(lib)["entries"], "take")
    keys = sorted(tuple(e["key"]) for e in takes)
    assert keys == [(2, 0), (2, 1), (2, 2), (3, 0)]
    kept = next(e for e in takes if e["key"] == [2, 2])
    assert kept["path"] == "jekyll/episodes/ep01/takes/r2v/T02.mp4" and kept["fields"]["seed"] == 82204
    fail = next(e for e in takes if e["key"] == [2, 0])
    assert fail["path"] == "jekyll/episodes/ep01/takes/r2v/attempts/T02_fail1.mp4"
    assert all(e["workflow_fp"] for e in takes)


def test_take_seconds_pair_with_their_try_when_the_phase_rows_count_the_tries(lib):
    takes = {tuple(e["key"]): e for e in kind(build(lib)["entries"], "take")}
    assert [takes[(2, t)]["seconds"] for t in (0, 1, 2)] == [86.8, 87.5, 91.3]
    assert takes[(3, 0)]["seconds"] == 80.9 and takes[(3, 0)]["seconds_basis"] == "phases.jsonl row, try order"


def test_a_refine_crop_is_keyed_by_the_sha_of_its_staged_src_bytes(lib):
    crops = kind(build(lib)["entries"], "refine_crop")
    assert len(crops) == 2
    src = lib / "jekyll" / "episodes" / "ep01" / "takes" / "r2v" / "refine" / "T06_p0_src.mp4"
    first = next(e for e in crops if e["path"].endswith("T06_p0.mp4"))
    assert first["key"] == hashlib.sha256(src.read_bytes()).hexdigest()
    assert first["fields"]["take"] == "T06" and first["fields"]["who"] == "richard_enfield"
    assert first["seconds"] > 0


def test_each_grid_is_keyed_by_setup_seed_and_prompt_sha_with_its_draw_seconds(lib):
    grids = {e["fields"]["name"]: e for e in kind(build(lib)["entries"], "grid")}
    door = grids["ep01_grid_night_door_2x2"]
    txt = (lib / "jekyll" / "episodes" / "ep01" / "storyboard" / "grids" / "ep01_grid_night_door_2x2.txt")
    assert door["key"] == ["night_door", 40533, hashlib.sha256(txt.read_bytes()).hexdigest()]
    assert door["seconds"] == 78.8 or door["seconds"] == 77.5
    assert door["fields"]["panels"] == ["jekyll/episodes/ep01/storyboard/h3/shot_00.png"]
    assert door["fields"]["anchor"] == "jekyll/episodes/ep01/storyboard/anchors/night_door.png"


def test_each_place_master_is_keyed_by_place_seed_and_prompt_sha(lib):
    places = kind(build(lib)["entries"], "place")
    drawn = [e for e in places if e["path"]]
    assert {e["fields"]["master_id"] for e in drawn} == {"black_mail_house_door/wide_establishing",
                                                         "london_sunday_walks/wide_establishing"}
    one = drawn[0]
    assert one["key"][0] in ("black_mail_house_door", "london_sunday_walks") and one["seconds"] > 0
    assert all(e["path"] is None for e in places if e not in drawn)


def test_each_tts_line_is_keyed_by_speaker_and_text_sha_with_its_measured_seconds(lib):
    lines = kind(build(lib)["entries"], "tts_line")
    first = next(e for e in lines if e["fields"]["index"] == 0)
    said = "Only one man holds the key to this door."
    assert first["key"] == ["narrator", hashlib.sha256(said.encode()).hexdigest()]
    assert first["fields"]["measured_seconds"] == 3.15
    assert first["path"] == "jekyll/episodes/ep01/audio/lines/l00.wav"


def test_a_transcript_points_at_the_whisper_memo_p4_fills(lib):
    out = build(lib)
    wav = lib / "jekyll" / "episodes" / "ep01" / "audio" / "lines" / "l00.wav"
    memo = next(e for e in kind(out["entries"], "transcript") if e["fields"]["wav"].endswith("l00.wav"))
    assert memo["key"] == hashlib.sha256(wav.read_bytes()).hexdigest()
    assert memo["path"] == f"memos/whisper/{memo['key']}.json" and memo["fields"]["filled"] is False


def test_vl_text_keys_every_recorded_picture_by_each_constant_ask_and_opens_the_cache_by_name(lib):
    home = lib / "jekyll" / "episodes" / "ep01"
    panel = home / "storyboard" / "h3" / "shot_00.png"
    ask = next(a for a in rec.asks() if a["id"] == "panel_content")
    key = fake_key(ask["workflow"], rec.ask_values(ask, panel))
    (lib / ".vlm_cache" / key[:2]).mkdir(parents=True)
    (lib / ".vlm_cache" / key[:2] / f"{key}.txt").write_text('{"people": []}', encoding="utf-8")
    texts = kind(build(lib)["entries"], "vl_text")
    hit = [e for e in texts if e["path"]]
    assert [e["key"] for e in hit] == [key]
    assert hit[0]["fields"]["ask"] == "panel_content" and hit[0]["seconds"] > 0
    frames = [e for e in texts if e["fields"]["picture"].endswith("T02_1.png")]
    assert {e["fields"]["ask"] for e in frames} == {"take_frame", "take_twin"}
    assert {e["fields"]["seed"] for e in frames} == {12, 24}


def test_the_ask_seeds_are_the_ones_the_readers_use(lib):
    take = (REPO / "scripts" / "episode" / "take_content_check.py").read_text(encoding="utf-8")
    panel = (REPO / "scripts" / "episode" / "panel_content_check.py").read_text(encoding="utf-8")
    assert "seed=11 + i" in take and '"seed": seed, "max_new_tokens": 256' in take
    assert "def read(path: Path, seed: int = 11)" in panel and "def read_twins(path: Path, seed: int = 17)" in panel
    assert re.search(r"^SAMPLES = 3$", take, re.MULTILINE)


def test_the_vl_seconds_fit_is_least_squares_on_the_logged_reads(lib):
    a, b = rec.vl_fit(rec.read_rows(lib / "vlm_calls.jsonl"))
    rows = [r for r in rec.read_rows(lib / "vlm_calls.jsonl") if r.get("answer_tokens")]
    mean_err = sum(r["seconds"] - (a + b * r["answer_tokens"]) for r in rows) / len(rows)
    assert abs(mean_err) < 1e-6


def test_a_retired_brain_attempt_is_an_sdk_stream_marked_incomplete(lib):
    streams = kind(build(lib)["entries"], "sdk_stream")
    assert len(streams) == 1
    assert streams[0]["path"] == "jekyll/episodes/ep01/brain_retired_01/attempt_01.json"
    assert streams[0]["fields"]["complete"] is False and streams[0]["key"][0] == "brain verdict"


def test_the_index_stores_no_absolute_path_and_counts_each_kind(lib):
    out = build(lib)
    assert out["source"] == "jekyll/episodes/ep01"
    assert out["counts"]["take"] == 4 and out["counts"]["refine_crop"] == 2
    for e in out["entries"]:
        assert set(e) >= {"kind", "workflow_fp", "key", "fields", "tries", "path", "seconds", "source"}
        assert e["path"] is None or not Path(e["path"]).is_absolute()


def test_the_script_writes_recordings_json_and_prints_its_path_first(lib, tmp_path, capsys, monkeypatch):
    from scripts.proof import index_recordings as script
    monkeypatch.setattr(rec, "default_text_key", lambda: fake_key)
    out = tmp_path / "recordings" / "recordings.json"
    assert script.main(["jekyll", "1", "--root", str(lib), "--out", str(out)]) == 0
    said = capsys.readouterr().out.splitlines()
    assert said[0] == str(out.resolve())
    assert json.loads(out.read_text(encoding="utf-8"))["counts"]["take"] == 4
