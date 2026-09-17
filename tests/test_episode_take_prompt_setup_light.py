"""The Start Frame take prompt takes the SETUP's own light in its style line
(dq10/J.md §6 item 6): a lamp room under a sun episode says the lamp."""
import pytest

from studio import episode_take_prompt as take
from studio import house_style as hs
from studio.episode_spec import Episode, Line, Setup, Shot

LAMP = Setup(described=("Interior, the parlour on the same evening, 1860: the one oil lamp burning on "
                        "the pine table is the only light and it comes from the lamp alone, low and "
                        "warm, the far corners in darkness"))


@pytest.fixture(autouse=True)
def _farm():
    hs.adopt("Ferrier's farm, Utah, 1860", "low side sun, deep black shadow")
    yield
    hs.adopt("", "")


def shot() -> Shot:
    return Shot(index=0, section="hook", setup="lamp", size="close", frame="Close on the hand.",
                motion="Tracking beside the hand; the stick plants once.")


def test_the_style_line_takes_the_setups_light_when_the_setup_burns_a_lamp():
    assert "lamp" in take.style_line(LAMP) and "sun" not in take.style_line(LAMP)
    assert "sun" in take.style_line()


def test_the_built_prompt_carries_the_setups_light():
    ep = Episode.model_construct(shots=[shot()], lines=[], setups={"lamp": LAMP})
    text = take.build(ep, shot())
    assert "oil lamp" in text and "sun" not in text
    assert "35 mm film grain" in text


def test_a_speaking_shot_carries_it_too():
    sh = Shot(index=0, section="hook", setup="lamp", size="medium_close", faces=["stamford"],
              frame="Medium close-up of Stamford.", motion="He speaks; his eyes flick away.")
    ep = Episode.model_construct(shots=[sh], setups={"lamp": LAMP},
                                 lines=[Line(index=0, kind="dialogue", speaker="stamford",
                                             text="You must not blame me.", shot=0)])
    text = take.build(ep, sh)
    assert "oil lamp" in text and "sun" not in text and "(S1)" in text


def test_no_episode_or_no_setup_keeps_the_episode_line():
    assert "low side sun" in take.build(None, shot())
    bare = Episode.model_construct(shots=[shot()], lines=[])
    assert "low side sun" in take.build(bare, shot())
