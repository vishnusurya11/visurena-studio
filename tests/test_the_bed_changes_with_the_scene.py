r"""One bed for a whole episode is why it reads as loud.

OWNER, 2026-09-14, after episode 5: "make sure audio is not too loud the BG ...
different types based on the context of background thrilling .. normal .. or
something".

MEASURED on the shipped `ep05/cut/master_r2v.mp4` before changing anything:

    speech                              -13.2 LUFS
    bed alone, un-ducked gap            -28.0 LUFS   (15 LU under)
    bed inside the voice band 300-3400  -34.9 LUFS   (22 LU under)

So it is NOT objectively loud, and lowering the number alone would not answer
the note. What makes it read as loud is that it NEVER STOPS AND NEVER CHANGES:
one solo violin in D minor, the same phrase shape, for 160 seconds under a
breakfast, a joke, a boast, a flashback and a murder. A constant is something
the ear stops being able to filter, and then everything it sits under sounds
the same temperature.

So: a bed PER SPAN, and each span quieter than the single bed was.

    plain      -31.0    the ordinary room; two men reading papers
    light      -30.5    comedy; the Irregulars on the carpet
    uneasy     -29.0    a man is wrong and does not know it
    grave      -29.0    a death, a seizure, a thing not recoverable
    thrilling  -27.5    the turn the episode was built to arrive at

Every one of them sits at or below the old -25.6, so the whole episode gets
quieter AND the loudest tone is reserved for the twenty seconds that earn it.
That is both halves of the owner's note with one mechanism.

THE TONE IS AUTHORED, NOT DERIVED. `section` is structural -- "friction" covers
both a comic invasion of street boys and a man's hand on a woman's wrist -- so a
tone derived from it would be confidently wrong. The plan names its own spans
and the default for an unnamed episode is `plain` throughout, which is exactly
what episodes 1-5 shipped.
"""
import pytest

from studio.episode_bed import TONES, bed_plan, spans, tone_style


# ---- the tones themselves ---------------------------------------------------

def test_every_tone_is_quieter_than_the_old_single_bed():
    """-25.6 LUFS was the level two shipped episodes were judged at."""
    assert TONES and all(t.lufs <= -25.6 for t in TONES.values())


def test_the_ordinary_tone_is_the_quietest():
    assert TONES["plain"].lufs == min(t.lufs for t in TONES.values())


def test_the_turn_is_the_loudest_and_still_under_the_old_level():
    assert TONES["thrilling"].lufs == max(t.lufs for t in TONES.values())
    assert TONES["thrilling"].lufs <= -25.6


def test_no_tone_asks_for_a_voice():
    """The trailer corpus taught this the expensive way: a style carrying vocal
    descriptors makes the model add a voice, and a negation is a summons."""
    for name, tone in TONES.items():
        low = tone.style.lower()
        for word in ("vocal", "voice", "sings", "singing", "choir", "lyric", "soprano"):
            assert word not in low, f"{name} names {word!r}"


def test_no_tone_asks_for_a_drum_kit_or_a_beat():
    for name, tone in TONES.items():
        assert "drum kit" not in tone.style.lower(), name


def test_a_style_is_prose_not_a_tag_list():
    for name, tone in TONES.items():
        assert len(tone.style.split()) > 25, f"{name} is too short to be a description"


# ---- the spans --------------------------------------------------------------

SHOTS = [{"index": i} for i in range(26)]
BEDS = [{"from_shot": 0, "tone": "plain"},
        {"from_shot": 10, "tone": "uneasy"},
        {"from_shot": 23, "tone": "thrilling"}]
AT = {i: float(i) * 5.0 for i in range(26)}          # shot i starts at 5i seconds


def test_the_spans_cover_the_whole_episode():
    got = spans(BEDS, AT, total=130.0)
    assert got[0].start == 0.0 and got[-1].end == 130.0


def test_the_spans_touch_with_no_hole():
    got = spans(BEDS, AT, total=130.0)
    for a, b in zip(got, got[1:]):
        assert a.end == b.start


def test_each_span_carries_its_tone():
    got = spans(BEDS, AT, total=130.0)
    assert [s.tone for s in got] == ["plain", "uneasy", "thrilling"]


def test_a_span_starts_where_its_first_shot_starts():
    got = spans(BEDS, AT, total=130.0)
    assert got[1].start == 50.0 and got[2].start == 115.0


def test_an_episode_with_no_beds_is_plain_throughout():
    """Episodes 1 to 5 carried no `beds` block and this is what they shipped."""
    got = spans([], AT, total=130.0)
    assert len(got) == 1 and got[0].tone == "plain"
    assert got[0].start == 0.0 and got[0].end == 130.0


def test_the_first_span_always_starts_at_zero():
    got = spans([{"from_shot": 4, "tone": "light"}], AT, total=130.0)
    assert got[0].start == 0.0


# ---- refusals ---------------------------------------------------------------

def test_an_unknown_tone_is_refused():
    with pytest.raises(ValueError, match="sombre"):
        spans([{"from_shot": 0, "tone": "sombre"}], AT, total=130.0)


def test_spans_out_of_order_are_refused():
    with pytest.raises(ValueError, match="order"):
        spans([{"from_shot": 10, "tone": "plain"}, {"from_shot": 4, "tone": "grave"}],
              AT, total=130.0)


def test_a_span_naming_a_shot_that_does_not_exist_is_refused():
    with pytest.raises(ValueError, match="99"):
        spans([{"from_shot": 99, "tone": "plain"}], AT, total=130.0)


# ---- one generation per DISTINCT tone, not per span ------------------------

def test_a_tone_used_twice_is_generated_once():
    beds = [{"from_shot": 0, "tone": "plain"},
            {"from_shot": 8, "tone": "grave"},
            {"from_shot": 16, "tone": "plain"}]
    got = bed_plan(beds, AT, total=130.0)
    assert sorted(got.needed) == ["grave", "plain"]


def test_each_generation_is_long_enough_for_its_longest_span():
    beds = [{"from_shot": 0, "tone": "plain"}, {"from_shot": 2, "tone": "grave"}]
    got = bed_plan(beds, AT, total=130.0)
    assert got.seconds["grave"] >= 120.0
    assert got.seconds["plain"] >= 10.0


def test_the_style_carries_the_tone_and_the_book():
    said = tone_style("thrilling")
    assert len(said.split()) > 25 and "violin" in said.lower()


# ---- each engine is handed what it reads ------------------------------------

def test_every_tone_carries_a_tag_list_for_acestep():
    """ACE-Step is `BED_ENGINE_DEFAULT` and it takes commas, not sentences."""
    for name, tone in TONES.items():
        assert tone.tags.count(",") >= 5, f"{name} is not a tag list"
        assert "." not in tone.tags, f"{name} has sentences in its tag list"


def test_every_tone_names_its_own_tempo_and_key():
    """`bpm` and `keyscale` are separate values on the ACE-Step request, so a
    tone that left them at the old 60 / D minor would differ in tags alone."""
    assert len({t.bpm for t in TONES.values()}) >= 4
    assert len({t.key for t in TONES.values()}) >= 2


def test_the_quiet_tone_is_slower_than_the_thrilling_one():
    assert TONES["plain"].bpm < TONES["thrilling"].bpm


def test_no_tag_list_asks_for_a_voice():
    for name, tone in TONES.items():
        for word in ("vocal", "voice", "choir", "sings", "lyric"):
            assert word not in tone.tags.lower(), f"{name} names {word!r}"
