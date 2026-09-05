"""A clip is identified by what produced it, not by the slot it sits in."""
from __future__ import annotations

import json

import pytest

from studio.clip_cache import (fingerprint, fresh, is_current, record,
                               stored_fingerprint)

RECIPE = {"prompt": "a man in fog", "refs": ["char-holmes", "loc-baker"],
          "seed": 51000, "frames": 243, "steps": 8, "width": 1344, "height": 768}


class TestFingerprint:
    def test_the_same_recipe_gives_the_same_fingerprint(self):
        assert fingerprint(RECIPE) == fingerprint(dict(RECIPE))

    def test_key_order_does_not_change_it(self):
        assert fingerprint(RECIPE) == fingerprint(dict(reversed(list(RECIPE.items()))))

    def test_a_changed_prompt_changes_it(self):
        assert fingerprint({**RECIPE, "prompt": "a man in rain"}) != fingerprint(RECIPE)

    def test_a_changed_seed_changes_it(self):
        assert fingerprint({**RECIPE, "seed": 51007}) != fingerprint(RECIPE)

    def test_reordered_refs_change_it(self):
        """<Subject 1> and <Subject 2> bind POSITIONALLY; swapping them is a
        different clip, not the same clip described differently."""
        assert fingerprint({**RECIPE, "refs": list(reversed(RECIPE["refs"]))}) \
            != fingerprint(RECIPE)

    def test_a_changed_reference_sheet_changes_it(self):
        """Regenerating a colliding cast must invalidate every clip bound to it."""
        assert fingerprint({**RECIPE, "ref_digest": "abc"}) \
            != fingerprint({**RECIPE, "ref_digest": "def"})


class TestIsCurrent:
    def test_a_clip_with_no_sidecar_is_not_current(self, tmp_path):
        """Every clip rendered before this existed must re-render once."""
        assert not is_current(tmp_path / "B00.mp4", RECIPE)

    def test_a_clip_whose_recipe_matches_is_current(self, tmp_path):
        video = tmp_path / "B00.mp4"
        record(video, RECIPE)
        assert is_current(video, RECIPE)

    def test_a_clip_whose_recipe_changed_is_not_current(self, tmp_path):
        """The defect this exists for: the plan was rebuilt from scratch, the
        beat ids stayed B00..B08, and every clip was skipped as 'exists'."""
        video = tmp_path / "B00.mp4"
        record(video, RECIPE)
        assert not is_current(video, {**RECIPE, "prompt": "a wholly new shot"})

    def test_the_sidecar_never_stores_an_absolute_path(self, tmp_path):
        video = tmp_path / "B00.mp4"
        record(video, {**RECIPE, "staged": "D:/somewhere/ref.png"})
        written = json.loads((tmp_path / "B00.recipe.json").read_text(encoding="utf-8"))
        assert ":" not in json.dumps(written).replace('":', "").replace(': ', "")

    def test_a_corrupt_sidecar_is_treated_as_missing(self, tmp_path):
        video = tmp_path / "B00.mp4"
        (tmp_path / "B00.recipe.json").write_text("{not json", encoding="utf-8")
        assert not is_current(video, RECIPE)


class TestFresh:
    """Run 10 cut 24% of its picture from clips left over from earlier plans.
    A clip counts only when the file is there AND its sidecar still says what
    step 07 recorded when it promoted it."""

    def doc(self, rel_path="trailer/main/clips/B00.mp4", fingerprint_=None):
        return {"clips": [{"beat_id": "B00", "rel_path": rel_path,
                           "fingerprint": fingerprint_ or fingerprint(RECIPE)}]}

    def written(self, book, rel_path="trailer/main/clips/B00.mp4", recipe=RECIPE):
        video = book / rel_path
        video.parent.mkdir(parents=True, exist_ok=True)
        video.write_bytes(b"mp4")
        record(video, recipe)
        return video

    def test_a_clip_on_disk_from_this_recipe_is_fresh(self, tmp_path):
        self.written(tmp_path)
        assert fresh(self.doc(), tmp_path) == ["B00"]

    def test_a_clip_whose_file_is_gone_is_not_fresh(self, tmp_path):
        assert fresh(self.doc(), tmp_path) == []

    def test_a_clip_left_over_from_an_earlier_plan_is_not_fresh(self, tmp_path):
        """The file is there under the right name and it is the OLD render."""
        self.written(tmp_path, recipe={**RECIPE, "prompt": "last plan's shot"})
        assert fresh(self.doc(), tmp_path) == []

    def test_a_clip_with_no_recorded_fingerprint_is_not_fresh(self, tmp_path):
        self.written(tmp_path)
        assert fresh(self.doc(fingerprint_="none"), tmp_path) == []


class TestStoredFingerprint:
    def test_a_clip_with_no_sidecar_answers_nothing(self, tmp_path):
        assert stored_fingerprint(tmp_path / "B00.mp4") is None

    def test_it_reads_back_what_record_wrote(self, tmp_path):
        video = tmp_path / "B00.mp4"
        record(video, RECIPE)
        assert stored_fingerprint(video) == fingerprint(RECIPE)
