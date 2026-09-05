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
    """RENDER ONLY WHAT THE CUT USES.  Run 10 rendered 175 frames (7.29s) a
    take and cut 2.0s out of it past a 2.6s head trim: 65 frames of every
    take, ~50 minutes of the run, sampled and thrown away.  One take, one
    shot, so a take is exactly its shot plus the leak it has to skip."""

    def test_a_take_is_its_shot_past_the_head_trim_with_a_handle(self):
        assert clips.take_seconds("B03", plan(seconds=(2.0, 1.5))) == pytest.approx(
            2.0 + clips.HEAD_TRIM + clips.HANDLE)
        assert clips.take_values(beat(), plan(seconds=(2.0, 1.5)), REFS, "noir", seed=7)[
            "frames"] == clips.frames_for(2.0 + clips.HEAD_TRIM + clips.HANDLE) == 124

    def test_a_take_holds_its_longest_shot_past_the_head_trim(self):
        """Scarlet run 6: the final hold asked 7.667s of B09, every take was
        7.29s, so `extract` ran off the end and the picture came up short."""
        long_hold = plan(("medium", "close"), (2.0, 7.667))
        assert clips.take_seconds("B03", long_hold) == pytest.approx(
            7.667 + clips.HEAD_TRIM + clips.HANDLE)

    def test_no_seven_second_floor_under_a_short_shot(self):
        """The 7.0s floor was there so ONE take could hold FOUR shots.  It
        holds one now, and the floor was 65 wasted frames a take."""
        assert clips.take_seconds("B03", plan(seconds=(1.2, 1.0))) < 7.0
        assert clips.take_values(beat(), plan(seconds=(1.2, 1.0)), REFS, "noir",
                                 seed=7)["frames"] < clips.frames_for(7.0)

    def test_a_take_never_falls_under_what_the_identity_reader_can_sample(self):
        """The reader takes three stills from the take PAST the head trim; a
        take with no usable stretch left cannot be read at all."""
        assert clips.take_seconds("B03", plan(seconds=(0.5, 0.5))) == pytest.approx(
            clips.READ_WINDOW + clips.HEAD_TRIM + clips.HANDLE)
        assert clips.take_seconds("B77", plan()) == pytest.approx(
            clips.READ_WINDOW + clips.HEAD_TRIM + clips.HANDLE)

    def test_a_reroll_of_the_same_beat_renders_the_same_frame_count(self):
        """A rung changes the FORM, never the length: the alternate setup is
        the same shot read closer, so the cut still gets its seconds."""
        first = clips.take_values(beat(), plan(), REFS, "noir", seed=7)
        again = clips.take_values(beat(), plan(), REFS, "noir", seed=8, tightest="close")
        assert first["frames"] == again["frames"]


class TestSteps:
    """Eight sampling steps, four only for an insert too short to read a
    smear in -- and only once a take has measured that it holds up."""

    def test_the_fast_insert_path_is_off_until_a_take_measures_it(self):
        assert clips.FAST_INSERTS is False
        assert clips.steps_for("B03", plan(("insert",), (0.6,))) == clips.STEPS == 8

    def test_four_steps_for_an_insert_the_cut_holds_a_second_or_less(self):
        for size in ("insert", "extreme_close"):
            assert clips.steps_for("B03", plan((size,), (0.8,)), fast=True) == clips.FAST_STEPS == 4

    def test_a_longer_or_larger_shot_keeps_all_eight(self):
        assert clips.steps_for("B03", plan(("insert",), (1.4,)), fast=True) == clips.STEPS
        assert clips.steps_for("B03", plan(("close",), (0.8,)), fast=True) == clips.STEPS
        assert clips.steps_for("B03", plan(("insert", "medium"), (0.6, 0.8)), fast=True) == clips.STEPS

    def test_a_beat_with_no_shot_of_its_own_keeps_all_eight(self):
        assert clips.steps_for("B77", plan(), fast=True) == clips.STEPS

    def test_the_take_asks_for_the_steps_its_shot_earns(self, monkeypatch):
        monkeypatch.setattr(clips, "FAST_INSERTS", True)
        values = clips.take_values(beat(), plan(("insert",), (0.6,)), REFS, "noir", seed=7)
        assert values["steps"] == clips.FAST_STEPS


class TestTakeValues:
    def test_opens_wide_and_arrives_tight_on_the_beats_own_shots(self):
        values = clips.take_values(beat(), plan(), REFS, "noir", seed=7)
        assert values["seed"] == 7
        assert values["frames"] == clips.frames_for(clips.take_seconds("B03", plan()))
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

    def test_a_longer_shot_is_a_different_recipe(self, tmp_path):
        """The frame count is part of what the model draws: a beat whose shot
        grew needs more frames than the take on disk has, and a take that is
        too short is not the take this plan asks for."""
        (tmp_path / "refs").mkdir()
        for name in ("c.png", "l.png"):
            (tmp_path / "refs" / name).write_bytes(name.encode())
        short = clips.take_values(beat(), plan(seconds=(2.0, 1.0)), REFS, "noir", seed=7)
        longer = clips.take_values(beat(), plan(seconds=(3.5, 1.0)), REFS, "noir", seed=7)
        assert short["frames"] < longer["frames"]
        assert (clips.recipe_for(short, ["char-holmes"], REFS, tmp_path)
                != clips.recipe_for(longer, ["char-holmes"], REFS, tmp_path))

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
