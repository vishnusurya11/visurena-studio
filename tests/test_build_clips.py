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


def plan(sizes=("medium", "close")):
    return {"beats": [beat()],
            "shots": [{"beat_id": "B03", "size": s} for s in sizes] + [{"beat_id": "B99", "size": "wide"}]}


class TestBoundSlots:
    def test_characters_then_location_only_when_bound(self):
        assert clips.bound_slots(beat(), REFS) == ["char-holmes", "loc-baker"]
        assert clips.bound_slots(beat(cast=("watson",), loc="moor"), REFS) == []

    def test_two_slots_at_most(self):
        refs = dict(REFS, **{"char-watson": dict(REFS["char-holmes"], ref_id="char-watson")})
        assert clips.bound_slots(beat(cast=("holmes", "watson")), refs) == ["char-holmes", "char-watson"]


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

    def test_reference_sheet_language_is_refused(self):
        refs = {k: dict(v) for k, v in REFS.items()}
        refs["char-holmes"]["physical"] = "A tall thin man with a hawk nose, full figure on a mid-grey backdrop."
        with pytest.raises(ValueError, match="reference-sheet"):
            clips.take_values(beat(), plan(), refs, "noir", seed=7)


class TestRecipe:
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
