r"""Doyle's own "said Lestrade" splits a lift in two and the gate scores the halves.

`QUOTE_WALL = 8` counts CONSECUTIVE words shared with the book. Doyle writes
speech with the attribution inside it:

    "The old pattern is good enough," remarked Lestrade, "if we can only find
     the man to put them on."

Episode 7's closing line is that sentence with the tag deleted:

    The old pattern is good enough, if we can only find the man to put them on.

Every word of it is Doyle's. The gate measured **11**, because no run in the
source is longer than the half the tag left. Spliced, it measures **17** -- the
longest lift in ep02, ep03, ep06 or ep07, more than double the wall, and it is
the episode's last line.

MEASURED: the book carries 222 such tags. So the corpus gains a second copy of
itself with the attributions taken out, and a run that straddles a tag is then
present verbatim in that copy. `lifted_run` is unchanged; it is the corpus that
was incomplete.

This does not make the gate stricter for its own sake. It makes it measure the
thing it already claims to measure: how much of the line is Doyle's.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import episode_spec as es

SAID = ('“The old pattern is good enough,” remarked Lestrade, “if we can only '
        'find the man to put them on.”')
LIFT = "The old pattern is good enough, if we can only find the man to put them on."


def test_the_tag_is_taken_out():
    assert "remarked Lestrade" not in es.without_attribution(SAID)


def test_the_words_on_either_side_join_up():
    joined = es.without_attribution(SAID)
    assert es.lifted_run(LIFT, joined) == 17, es.lifted_run(LIFT, joined)


def test_the_gate_undercounts_without_it():
    """The measurement that found this: 11 against the raw source."""
    assert es.lifted_run(LIFT, SAID) == 11


def test_the_corpus_keeps_the_original_too():
    """A lift that does NOT straddle a tag must still be found, so the corpus is
    both copies -- never the spliced one alone."""
    said = "“He is upstairs in bed. He wished to be called at nine.”"
    corpus = es.quote_corpus(said)
    assert es.lifted_run("He is upstairs in bed. He wished to be called at nine.", corpus) == 12


def test_both_lifts_are_found_in_one_corpus():
    corpus = es.quote_corpus(SAID)
    assert es.lifted_run(LIFT, corpus) == 17


def test_narration_that_shares_nothing_is_untouched():
    corpus = es.quote_corpus(SAID)
    assert es.lifted_run("I carried the dying terrier up the stairs myself.", corpus) < 8


@pytest.mark.parametrize("tag", [
    "“Stangerson too,” said Lestrade, “the plot thickens.”",
    "“It is the old story,” he cried, exultantly, “and the last link.”",
    "“We have him,” answered Gregson slowly, “and the case is done.”",
])
def test_the_common_attribution_shapes_are_all_spliced(tag):
    assert es.without_attribution(tag).count("“") < tag.count("“") or \
        len(es.without_attribution(tag).split()) < len(tag.split()), tag


def test_the_delivered_episodes_are_re_measured_here():
    """What the completed corpus says about the seven plans. Episode 7's line 23
    is the worst lift in the series and it is the closing line."""
    from studio import episode_home
    book = episode_home.book_dir("20260822113400_a-study-in-scarlet")
    if not (book / "episodes/ep07/plan.json").exists():
        pytest.skip("the book is not on this disk")
    import glob
    import json
    said = []
    for p in sorted(glob.glob(str(book / "source/chapters/ch_*.json"))):
        doc = json.loads(Path(p).read_text(encoding="utf-8"))
        said += [x if isinstance(x, str) else x.get("text", "") for x in doc["paragraphs"]]
    corpus = es.quote_corpus(" ".join(said))
    episode = episode_home.load_plan(book, 7)
    worst = max((es.lifted_run(l.text, corpus), l.index) for l in episode.lines)
    assert worst == (17, 23), worst
