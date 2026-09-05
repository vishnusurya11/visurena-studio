"""The take a beat renders: which sheets bind it, what the model is asked,
and the recipe that identifies the file.  Nothing here touches ComfyUI."""
from __future__ import annotations

import pytest

from scripts.trailer import build_clips as clips

REFS = {"char-holmes": {"ref_id": "char-holmes", "kind": "character", "rel_path": "refs/c.png",
                        "physical": "A tall thin man with a hawk nose.", "name": "Holmes"},
        "loc-baker": {"ref_id": "loc-baker", "kind": "location", "rel_path": "refs/l.png",
                      "physical": "A cluttered sitting room.", "name": "221B Baker Street"}}


def beat(cast=("holmes",), loc="baker"):
    return {"beat_id": "B03", "cast": list(cast), "location_id": loc, "arc": "quiet",
            "image_prompt": "He crosses to the window.", "motion": "The camera pushes in slowly."}


def plan(sizes=("medium", "close"), seconds=(2.0, 1.5)):
    return {"beats": [beat()],
            "shots": [{"beat_id": "B03", "size": s, "seconds": t} for s, t in zip(sizes, seconds)]
            + [{"beat_id": "B99", "size": "wide", "seconds": 9.0}]}


class TestBoundSlots:
    def test_characters_then_location_only_when_bound(self):
        assert clips.bound_slots(beat(), REFS) == ["char-holmes", "loc-baker"]
        assert clips.bound_slots(beat(cast=("watson",), loc="moor"), REFS) == []

    def test_two_slots_at_most(self):
        refs = dict(REFS, **{"char-watson": dict(REFS["char-holmes"], ref_id="char-watson")})
        assert clips.bound_slots(beat(cast=("holmes", "watson")), refs) == ["char-holmes", "char-watson"]


class TestTakeSeconds:
    """Scarlet run 6: the final hold asked 7.667s of B09, every take was
    `CLIP_SECONDS` (7.29s), so `extract` ran off the end, the cut started at
    0.0 inside the reference leak, and the picture came up 0.42s short --
    REFUSED at the drift gate after five hours of rendering."""

    def test_a_take_holds_its_longest_shot_past_the_head_trim(self):
        long_hold = plan(("medium", "close"), (2.0, 7.667))
        assert clips.take_seconds("B03", long_hold) == pytest.approx(7.667 + clips.HEAD_TRIM)
        assert clips.take_values(beat(), long_hold, REFS, "noir", seed=7)["frames"] ==             clips.frames_for(7.667 + clips.HEAD_TRIM)

    def test_short_shots_keep_the_standard_take(self):
        assert clips.take_seconds("B03", plan()) == clips.CLIP_SECONDS
        assert clips.take_seconds("B77", plan()) == clips.CLIP_SECONDS


class TestTakeValues:
    def test_opens_wide_and_arrives_tight_on_the_beats_own_shots(self):
        values = clips.take_values(beat(), plan(), REFS, "noir", seed=7)
        assert values["seed"] == 7 and values["frames"] == clips.frames_for(clips.CLIP_SECONDS)
        assert clips.FRAMING["medium"] in values["prompt"] and clips.FRAMING["close"] in values["prompt"]
        assert clips.FRAMING["wide"] not in values["prompt"]

    def test_tightest_framing_overrides_the_plan(self):
        values = clips.take_values(beat(), plan(), REFS, "noir", seed=7, tightest="close")
        assert clips.FRAMING["medium"] not in values["prompt"]
        assert values["prompt"].count(clips.FRAMING["close"]) == 2

    def test_two_cast_members_become_two_subjects_not_one_person(self):
        refs = dict(REFS, **{"char-watson": dict(REFS["char-holmes"], ref_id="char-watson",
                                                  physical="A stocky man with a moustache.")})
        prompt = clips.take_values(beat(cast=("holmes", "watson")), plan(), refs, "noir", seed=7)["prompt"]
        assert "<Subject 2>: The second person" in prompt and "moustache" in prompt
        assert "hawk nose" in prompt.split("<Subject 2>")[0]

    def test_reference_sheet_language_is_refused(self):
        refs = {k: dict(v) for k, v in REFS.items()}
        refs["char-holmes"]["physical"] = "A tall thin man with a hawk nose, full figure on a mid-grey backdrop."
        with pytest.raises(ValueError, match="reference-sheet"):
            clips.take_values(beat(), plan(), refs, "noir", seed=7)


class TestRecipe:
    def test_recipe_names_the_workflow_and_lora_only_when_they_are_not_the_default(self, tmp_path):
        """Takes on disk were fingerprinted before a LoRA could be chosen; the
        default render must still match them, and any other must not."""
        (tmp_path / "refs").mkdir()
        for name in ("c.png", "l.png"):
            (tmp_path / "refs" / name).write_bytes(name.encode())
        values = clips.take_values(beat(), plan(), REFS, "noir", seed=7)
        plain = clips.recipe_for(values, ["char-holmes", "loc-baker"], REFS, tmp_path)
        assert "lora" not in plain and plain["workflow"] == clips.WORKFLOW
        other = clips.recipe_for(dict(values, lora_name="x.safetensors"), ["char-holmes", "loc-baker"],
                                 REFS, tmp_path, workflow="video_minimax_h3_r2v_turbo_lxref")
        assert other["lora"] == "x.safetensors" and other["workflow"].endswith("lxref")

    def test_render_take_runs_the_workflow_it_is_given(self, tmp_path, monkeypatch):
        (tmp_path / "refs").mkdir()
        for name in ("c.png", "l.png"):
            (tmp_path / "refs" / name).write_bytes(name.encode())
        made = tmp_path / "out.mp4"
        made.write_bytes(b"mp4")
        seen = {}
        monkeypatch.setattr(clips, "stage_image", lambda p: p.name)
        monkeypatch.setattr(clips, "run", lambda name, values, timeout: seen.update(name=name) or [made])
        values = clips.take_values(beat(), plan(), REFS, "noir", seed=7)
        dest = tmp_path / "takes/B00-7.mp4"
        clips.render_take(values, ["char-holmes", "loc-baker"], REFS, tmp_path, dest, workflow="wf-b")
        assert seen["name"] == "wf-b" and dest.read_bytes() == b"mp4"

    def test_recipe_changes_with_seed_and_sheet(self, tmp_path):
        (tmp_path / "refs").mkdir()
        for name in ("c.png", "l.png"):
            (tmp_path / "refs" / name).write_bytes(name.encode())
        values = clips.take_values(beat(), plan(), REFS, "noir", seed=7)
        first = clips.recipe_for(values, ["char-holmes", "loc-baker"], REFS, tmp_path)
        second = clips.recipe_for(dict(values, seed=8), ["char-holmes", "loc-baker"], REFS, tmp_path)
        assert first != second and first["refs"] == ["char-holmes", "loc-baker"]
        (tmp_path / "refs/c.png").write_bytes(b"new sheet")
        assert clips.recipe_for(values, ["char-holmes", "loc-baker"], REFS, tmp_path) != first
