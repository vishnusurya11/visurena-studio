"""The cast rows a picture is drawn from are this episode's chapter.

Audit item 9, measured 2026-09-22: refs.json holds ONE chapter's clothes per
character -- cast_rows.py rewrites it for each episode and stamps the chapter
-- and nothing ever read the stamp. It says chapter 9 now, so a retake of
episode 8 would dress the narrator's wife in her chapter-9 travelling costume
and give the neighbour his chapter-9 gardening apron, silently.
"""
import json

from studio.cast_refs import chapter_refusal


def refs(tmp_path, chapter):
    (tmp_path / "refs").mkdir()
    body = {"refs": []} if chapter is None else {"chapter": chapter, "refs": []}
    (tmp_path / "refs" / "refs.json").write_text(json.dumps(body))
    return tmp_path


def test_rows_for_this_chapter_may_be_used(tmp_path):
    assert chapter_refusal(refs(tmp_path, 9), 9) is None


def test_rows_for_another_chapter_refuse_and_say_how_to_fix_it(tmp_path):
    why = chapter_refusal(refs(tmp_path, 9), 8)
    assert "chapter 9" in why and "cast_rows.py" in why


def test_unstamped_rows_refuse(tmp_path):
    assert chapter_refusal(refs(tmp_path, None), 8) is not None


def test_a_book_with_no_cast_rows_has_nothing_to_dress_wrongly(tmp_path):
    assert chapter_refusal(tmp_path, 8) is None
