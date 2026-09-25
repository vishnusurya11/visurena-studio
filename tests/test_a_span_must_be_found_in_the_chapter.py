"""G-SOURCE: every `source` span is found in the chapter text by fuzzy match.

A span is the chapter's own words, so a verbatim span scores 1.0 and a span
with one slipped letter still clears the wall; a paraphrase does not, and a
paraphrase is exactly how a guessed count gets a span written for it."""
from pathlib import Path
from types import SimpleNamespace

from studio import plan_gates as pg
from studio.episode_spec import Setup, Shot

CHAPTER = (Path(__file__).parent / "fixtures" / "episodes" / "chapter_snippet.txt").read_text(encoding="utf-8")
SETUPS = {"lane": Setup(described="a lane at dusk", cast=["walker"])}


def shot(i: int, extras: int, *source: str) -> Shot:
    return Shot(index=i, section="setup", setup="lane", size="wide", frame="Wide on the riders at the turn.",
                motion="The camera holds a locked-off frame; a horse stamps; a rider turns his head",
                extras=extras, source=list(source))


def plan(*shots: Shot):
    return SimpleNamespace(shots=list(shots), setups=SETUPS)


def test_a_verbatim_span_scores_one():
    assert pg.span_match("Eight riders waited at the turn of the road, two of them dismounted", CHAPTER) == 1.0


def test_a_slipped_letter_still_clears_the_wall():
    got = pg.span_match("Eight riders waited at the turn of the raod, two of them dismounted", CHAPTER)
    assert pg.SPAN_MATCH <= got < 1.0


def test_a_paraphrase_is_not_in_the_chapter():
    faults = pg.source_faults(plan(shot(4, 6, "six riders stood about at the crossroads")), CHAPTER)
    assert len(faults) == 1
    assert faults[0].startswith("G-SOURCE shot 4: span 'six riders stood about at the crossroads' is not in the chapter, measured ")
    assert faults[0].endswith(f"against {pg.SPAN_MATCH}")


def test_a_sourced_count_passes():
    assert pg.source_faults(plan(shot(4, 8, "Eight riders waited at the turn of the road")), CHAPTER) == []


def test_no_chapter_text_is_a_refusal_not_a_pass():
    faults = pg.source_faults(plan(shot(4, 8, "Eight riders waited at the turn of the road")), chapter=None)
    assert faults == ["G-SOURCE shot 4: no chapter text to find its 1 span(s) in, measured 0 against 1"]
