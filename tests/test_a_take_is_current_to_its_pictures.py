"""A take is current only if it was rendered from the same PICTURES, not just
the same words.

MEASURED 2026-09-22 (audit item 10): take currency compared the prompt text
alone. ep05 has 16 takes whose reference sheet was redrawn after they
rendered, and ep07 six whose storyboard panel was redrawn -- all still
"current", so a retake round would skip them and DQ would keep measuring
pictures they were never made from.

The staged file names are content-addressed (`<stem>_<md5[:8]>.png`), so the
graph a take ran with already records which bytes it saw.
"""
import json

from studio.comfy import staged_name
from studio.take_currency import is_current, staged_images


def picture(tmp_path, name, body):
    p = tmp_path / name
    p.write_bytes(body)
    return p


def graph(tmp_path, prompt, images):
    take = tmp_path / "T00.mp4"
    take.write_bytes(b"mp4")
    nodes = {"1": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {"prompt": prompt}}}
    for k, name in enumerate(images, start=2):
        nodes[str(k)] = {"class_type": "LoadImage", "inputs": {"image": name}}
    take.with_suffix(".graph.json").write_text(json.dumps(nodes))
    return take


def test_the_staged_name_is_the_content(tmp_path):
    a = picture(tmp_path, "sheet.png", b"one")
    b = picture(tmp_path, "sheet2.png", b"one")
    assert staged_name(a).split("_")[-1] == staged_name(b).split("_")[-1]
    assert staged_name(a) != staged_name(picture(tmp_path, "sheet3.png", b"two")).replace("sheet3", "sheet")


def test_the_graph_says_which_pictures_it_ran_with(tmp_path):
    take = graph(tmp_path, "p", ["a_1.png", "b_2.png"])
    assert staged_images(take) == {"a_1.png", "b_2.png"}


def test_same_words_and_same_pictures_is_current(tmp_path):
    sheet = picture(tmp_path, "sheet.png", b"v1")
    take = graph(tmp_path, "the prompt", [staged_name(sheet)])
    assert is_current("the prompt", take, pictures=[sheet])


def test_a_redrawn_picture_is_not_current(tmp_path):
    sheet = picture(tmp_path, "sheet.png", b"v1")
    take = graph(tmp_path, "the prompt", [staged_name(sheet)])
    sheet.write_bytes(b"v2, redrawn")
    assert not is_current("the prompt", take, pictures=[sheet])


def test_changed_words_are_still_not_current(tmp_path):
    sheet = picture(tmp_path, "sheet.png", b"v1")
    take = graph(tmp_path, "old words", [staged_name(sheet)])
    assert not is_current("new words", take, pictures=[sheet])


def test_without_pictures_it_asks_only_about_the_words(tmp_path):
    take = graph(tmp_path, "the prompt", ["whatever_0.png"])
    assert is_current("the prompt", take)
