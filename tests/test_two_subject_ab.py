"""The two-face A/B: one beat, the same seeds, bound to (principal, place)
and to (principal, second person); both faces read back.  Nothing here
touches the engine: render and read are injected."""
from __future__ import annotations

import json

from scripts.trailer import two_subject_ab as ab

REFS = {"char-holmes": {"physical": "tall, hawk nose", "rel_path": "h.png"},
        "char-watson": {"physical": "stocky, moustache", "rel_path": "w.png"},
        "loc-bar": {"name": "the bar", "rel_path": "b.png"}}
BEAT = {"beat_id": "B05", "cast": ["holmes"], "location_id": "bar"}


def test_the_pair_beat_casts_both_people_and_the_place_falls_off_the_slots():
    pair = ab.pair_beat(BEAT, "watson")
    assert pair["cast"] == ["holmes", "watson"] and BEAT["cast"] == ["holmes"]
    assert ab.variants(BEAT, REFS, "watson") == {
        "one": (BEAT, ["char-holmes", "loc-bar"]),
        "two": (pair, ["char-holmes", "char-watson"])}


def test_the_cue_that_singles_a_person_out_comes_from_their_sheet(monkeypatch):
    monkeypatch.setattr(ab, "visual_description", lambda physical: f"seen: {physical}")
    assert ab.cue_for(REFS["char-watson"]) == "seen: stocky, moustache"


def test_summarise_reports_each_face_per_variant():
    rows = [{"variant": "one", "faces": {"char-holmes": {"distance": 1.0, "bound": True}}},
            {"variant": "one", "faces": {"char-holmes": {"distance": 3.0, "bound": False}}},
            {"variant": "two", "faces": {"char-holmes": {"distance": 2.0, "bound": True},
                                         "char-watson": {"distance": 4.0, "bound": False}}}]
    summary = ab.summarise(rows)
    assert summary["one"]["char-holmes"] == {"n": 2, "mean_distance": 2.0, "bound": 1}
    assert summary["two"]["char-watson"] == {"n": 1, "mean_distance": 4.0, "bound": 0}


def test_run_ab_renders_every_seed_through_both_bindings_and_reads_every_face(tmp_path, monkeypatch):
    calls, reads = [], []

    def render(values, bound, refs, book, dest):
        calls.append((values["seed"], list(bound)))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"mp4")
        return dest
    monkeypatch.setattr(ab, "render_take", render)
    monkeypatch.setattr(ab, "take_values", lambda beat, plan, refs, style, seed: {"seed": seed})
    monkeypatch.setattr(ab, "clip_seconds", lambda video: 7.0)
    monkeypatch.setattr(ab, "frames_of", lambda video, seconds, work: ["f.png"])
    monkeypatch.setattr(ab, "describe_frames", lambda frames, seed, whom: reads.append(whom) or "card")
    monkeypatch.setattr(ab, "distance", lambda card, reference: 0.5)
    people = {"char-holmes": ("holmes-card", "hawk"), "char-watson": ("watson-card", "moustache")}
    rows = ab.run_ab(tmp_path, tmp_path / "ab", ab.variants(BEAT, REFS, "watson"), {"shots": []},
                     REFS, "noir", people, seeds=[1, 2])
    assert [c for c in calls] == [(1, ["char-holmes", "loc-bar"]), (2, ["char-holmes", "loc-bar"]),
                                  (1, ["char-holmes", "char-watson"]), (2, ["char-holmes", "char-watson"])]
    assert set(rows[0]["faces"]) == {"char-holmes"} and set(rows[2]["faces"]) == {"char-holmes", "char-watson"}
    assert reads == ["hawk", "hawk", "hawk", "moustache", "hawk", "moustache"]
    assert rows[2]["faces"]["char-watson"] == {"distance": 0.5, "bound": True}
    logged = (tmp_path / "ab/two_subject.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(logged) == 4 and json.loads(logged[3])["variant"] == "two"
