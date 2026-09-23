"""A take stages only the people its setup declares.

MEASURED 2026-09-22 on ep09 T16, the episode's TURN -- the narrator gripping
his wife's arm. The take builder chose who the shot names from EVERY character
row in refs.json, including rows left over from other chapters, and matched
them by the last word of their display name. "the narrator's wife" matched
"the neighbour's wife" (last word "wife", matched case-sensitively, where the
wife's own display is "the Wife"). The built prompt defined <Subject 3> as the
neighbour's wife and told the model "the narrator takes his <Subject 3> by the
arm" -- the turn, rendered with the wrong woman, while the real wife was
defined and never referenced. No gate read the built prompt for it.

Who can be in a setup is the plan's to declare (`Setup.cast`); a shot adds
only its own `faces`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))

import takes_r2v  # noqa: E402


class Shot:
    def __init__(self, setup, faces, frame):
        self.setup, self.faces, self.frame, self.at_rest, self.cuts = setup, faces, frame, "", []


class Setup:
    def __init__(self, cast):
        self.cast = cast


class Episode:
    def __init__(self, setups):
        self.setups = setups


def test_candidates_are_the_setups_cast_and_the_shots_own_faces():
    ep = Episode({"lawn": Setup(["narrator", "narrators_wife", "hussar"])})
    shots = [Shot("lawn", ["narrator"], "the narrator takes his wife by the arm")]
    assert takes_r2v.staging_candidates(ep, shots) == ["narrator", "narrators_wife", "hussar"]


def test_a_character_from_another_chapter_is_never_a_candidate():
    ep = Episode({"lawn": Setup(["narrator", "narrators_wife"])})
    shots = [Shot("lawn", ["narrator", "narrators_wife"], "the narrator's wife")]
    assert "unnamed_neighbours_wife" not in takes_r2v.staging_candidates(ep, shots)


def test_a_face_the_setup_forgot_is_still_staged():
    ep = Episode({"inn": Setup(["landlord"])})
    shots = [Shot("inn", ["narrator"], "the narrator at the counter")]
    assert "narrator" in takes_r2v.staging_candidates(ep, shots)
