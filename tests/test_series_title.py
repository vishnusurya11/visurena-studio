"""A series title card: one picture for the book, lettered per episode."""
from studio.series_title import (card_lines, chapter_name, lines_read,
                                 missing_lines)


def test_chapter_name_drops_the_roman_numeral_and_full_stop():
    assert chapter_name("I. THE EVE OF THE WAR.") == "THE EVE OF THE WAR"
    assert chapter_name("XVII. THE “THUNDER CHILD”.") == "THE “THUNDER CHILD”"


def test_card_lines_are_series_episode_then_chapter():
    assert card_lines("The War of the Worlds", 1, "I. THE EVE OF THE WAR.") == [
        "THE WAR OF THE WORLDS", "EPISODE 1", "THE EVE OF THE WAR"]


def test_lines_read_is_forgiving_of_case_space_and_punctuation():
    ocr = "The War of the  Worlds\nEPISODE 1\nThe Eve of the War."
    assert lines_read(["THE WAR OF THE WORLDS", "EPISODE 1", "THE EVE OF THE WAR"], ocr)


def test_a_misspelt_line_is_named():
    ocr = "THE WAR OF THE WORLOS\nEPISODE 1\nTHE EVE OF THE WAR"
    assert missing_lines(["THE WAR OF THE WORLDS", "EPISODE 1", "THE EVE OF THE WAR"], ocr) == [
        "THE WAR OF THE WORLDS"]


def test_the_vlm_json_list_with_escaped_newlines_is_read_as_lines():
    raw = '[\n    "THE WAR OF\\nTHE WORLDS\\nEPISODE 1\\nTHE EVE OF THE WAR"\n]'
    assert lines_read(["THE WAR OF THE WORLDS", "EPISODE 1", "THE EVE OF THE WAR"], raw)


def test_a_doubled_word_in_the_series_line_is_caught():
    raw = '["THE WAR OF\\nWHE THE WORLDS\\nEPISODE 1\\nTHE EVE OF THE WAR"]'
    assert missing_lines(["THE WAR OF THE WORLDS", "EPISODE 1", "THE EVE OF THE WAR"], raw) == [
        "THE WAR OF THE WORLDS"]


def test_a_wrong_episode_number_is_caught():
    assert not lines_read(["EPISODE 1"], "EPISODE 11")


def test_the_ideogram_plate_quotes_each_line_on_plain_black():
    import json
    from studio.series_title import plate_caption
    lines = ["THE WAR OF THE WORLDS", "EPISODE 1", "THE EVE OF THE WAR"]
    caption = json.loads(plate_caption(lines))
    texts = [e["desc"] for e in caption["compositional_deconstruction"]["elements"]]
    assert all(any(f'"{line}"' in t for t in texts) for line in lines)
    assert "black" in caption["compositional_deconstruction"]["background"].lower()


def test_the_plate_is_screened_over_the_art_so_black_leaves_it_untouched():
    from PIL import Image
    from studio.series_title import screen_over
    art = Image.new("RGB", (8, 8), (40, 60, 90))
    plate = Image.new("RGB", (8, 8), (0, 0, 0))
    plate.putpixel((0, 0), (255, 255, 255))
    out = screen_over(art, plate)
    assert out.size == art.size
    assert screen_over(art, Image.new("RGB", (4, 4))).size == art.size
    assert out.getpixel((7, 7)) == (40, 60, 90)
    assert out.getpixel((0, 0)) == (255, 255, 255)
