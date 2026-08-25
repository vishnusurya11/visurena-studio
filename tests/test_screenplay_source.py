"""Source paragraph loading and canonical-id cues. Agent-free.

Both bugs here were found by the first real paid run, and both were mine:

  * paragraphs_for() looked in analysis/chapters/, but chapters live in source/chapters/.
    It silently returned {}, so the screenwriter never saw a word of the book and every
    one of 259 verbatim claims failed grounding against an empty string.
  * the writer put display NAMES in `character` ("Sherlock Holmes"), not canonical ids,
    so G2 reported 18 characters "not in the registry" who are plainly in it.
"""

from __future__ import annotations

import json

from scripts.screenplay import step_03_draft as s03

REGISTRY = [{"id": "sherlock_holmes", "name": "Sherlock Holmes", "aliases": ["Holmes"]},
            {"id": "john_watson", "name": "Dr. John Watson", "aliases": ["Watson"]}]


def _book(tmp_path):
    chapters = tmp_path / "source" / "chapters"
    chapters.mkdir(parents=True)
    (chapters / "ch_01.json").write_text(json.dumps({
        "n": 1, "paragraphs": [{"n": i, "text": f"Paragraph {i} of the chapter."}
                               for i in range(1, 11)]}), encoding="utf-8")
    return tmp_path


def test_paragraphs_are_read_from_the_source_tree(tmp_path):
    scenes = [{"chapter": 1, "scene": 1, "para_start": 2, "para_end": 4}]
    got = s03.paragraphs_for(_book(tmp_path), scenes)
    assert got["1:1"] == ["Paragraph 2 of the chapter.", "Paragraph 3 of the chapter.",
                          "Paragraph 4 of the chapter."]


def test_paragraph_span_is_inclusive_of_both_ends(tmp_path):
    scenes = [{"chapter": 1, "scene": 1, "para_start": 5, "para_end": 5}]
    assert len(s03.paragraphs_for(_book(tmp_path), scenes)["1:1"]) == 1


def test_a_missing_chapter_file_yields_nothing_rather_than_crashing(tmp_path):
    scenes = [{"chapter": 99, "scene": 1, "para_start": 1, "para_end": 2}]
    assert s03.paragraphs_for(_book(tmp_path), scenes) == {}


def test_paragraphs_are_never_silently_empty_for_a_real_scene(tmp_path):
    """The regression itself: an empty result here means every verbatim claim
    downstream fails grounding against nothing, and the writer works blind."""
    scenes = [{"chapter": 1, "scene": 1, "para_start": 1, "para_end": 3}]
    assert all(s03.paragraphs_for(_book(tmp_path), scenes).values())


# --- character cues must be canonical ids ------------------------------------------

def test_a_display_name_is_resolved_back_to_its_id():
    assert s03.canonical_cue("Sherlock Holmes", REGISTRY) == "sherlock_holmes"


def test_an_alias_is_resolved_too():
    assert s03.canonical_cue("Holmes", REGISTRY) == "sherlock_holmes"


def test_an_id_the_writer_already_got_right_passes_through():
    assert s03.canonical_cue("john_watson", REGISTRY) == "john_watson"


def test_an_unresolvable_cue_is_kept_rather_than_dropped():
    """A walk-on with a line is still a line. G2 will report it; losing it is worse."""
    assert s03.canonical_cue("A Railway Porter", REGISTRY) == "A Railway Porter"


def test_none_stays_none():
    assert s03.canonical_cue(None, REGISTRY) is None
