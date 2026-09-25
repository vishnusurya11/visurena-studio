"""GroundingDINO over the closed MAJOR list: a landmark word with a box in the
picture and no mention in the place's words is invented.  Kin words (an arch
for a bridge) are the same landmark, not an invention."""
import json
from pathlib import Path

from studio.measure import boxes

FIX = Path(__file__).parent / "fixtures" / "measures"


def test_a_landmark_the_setup_lacks_is_invented():
    found = json.load((FIX / "gdino_landmarks.json").open())
    assert boxes.invented(found, "a level lawn before a brick tower, evening") == ["arch", "bridge"]


def test_a_kin_word_of_a_named_landmark_is_not_invented():
    found = json.load((FIX / "gdino_landmarks.json").open())
    assert boxes.invented(found, "the lawn under the railway bridge") == []


def test_detection_asks_once_per_word_and_keeps_only_hits():
    asked = []

    def detect(image, word):
        asked.append(word)
        return [[1, 2, 3, 4]] if word == "tower" else []

    found = boxes.detect_words("panel.png", ["bridge", "tower"], detect)
    assert asked == ["bridge", "tower"] and found == {"tower": [[1, 2, 3, 4]]}
