"""A line the ear heard as rushed is said next time with one written pause; the ear still
scores the book's words.

Jekyll ep04 l17/l26 and ep05 l05 ("You have not been mad enough to hide this fellow.", 8 tries at
4.41-4.59 words/s against 3.8) read fast on every delivery and every seed; ep04's "I think... I
can take you" passed.  The pause rides on the MOUTH's text (`said_as`, beside the respelling),
never on the plan, so the signed plan does not move.
"""
import importlib.util
import sys
from pathlib import Path

from studio.voice_say import paced

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_say_paced", ROOT / "scripts" / "episode" / "say_lines.py")
say = importlib.util.module_from_spec(spec)
sys.modules["ep_say_paced"] = say
spec.loader.exec_module(say)

L05 = "You have not been mad enough to hide this fellow."


def test_the_pause_goes_before_the_first_linking_word():
    assert paced(L05) == "You have not been mad enough... to hide this fellow."


def test_an_inner_comma_becomes_the_pause():
    assert paced("Well, I shall consider it carefully.") == "Well... I shall consider it carefully."


def test_a_line_with_no_joint_pauses_at_its_middle():
    assert paced("Utterson stared hard at the strange signature.") == \
        "Utterson stared hard... at the strange signature."


def test_a_line_already_paused_is_left_alone():
    assert paced("I think... I can take you.") == "I think... I can take you."


def test_the_mouth_gets_the_pause_only_after_a_rushed_try():
    rushed = {5: {"why": "rushed (4.53 words/s > 3.8)"}}
    assert say.mouth_text(L05, {}, rushed.get(5)) == paced(L05)
    assert say.mouth_text(L05, {}, {"why": "said something else (wer 0.40 > 0.2)"}) == L05
    assert say.mouth_text(L05, {}, None) == L05
