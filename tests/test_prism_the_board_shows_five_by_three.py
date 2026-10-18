"""The Prism board: per style, the 5 subjects down and the models across, each image's
time under it, the model's warm median in the head, and a pick of the best model."""
from __future__ import annotations

from prism import board
from prism.plan import jobs
from tests.prism_fixtures import guide, style, subjects

GUIDES = {"krea2": guide("krea2"), "flux3_klein": guide("flux3_klein"), "qwen_image_2_1": guide("qwen_image_2_1")}


def page(tmp_path, rows=()):
    planned = jobs([style(), style("live_sin_city_noir", "Sin <City>")], subjects(), GUIDES)
    for job in planned[:1]:
        (tmp_path / job.out).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / job.out).write_bytes(b"png")
    return board.page([style(), style("live_sin_city_noir", "Sin <City>")], subjects(), GUIDES,
                      planned, list(rows), tmp_path)


def test_every_style_has_its_section_and_names_are_escaped(tmp_path):
    html = page(tmp_path)
    assert 'id="anime_hellsing_gothic"' in html and 'id="live_sin_city_noir"' in html
    assert "Sin &lt;City&gt;" in html and "Sin <City>" not in html


def test_a_rendered_image_shows_and_a_missing_one_says_so(tmp_path):
    html = page(tmp_path)
    assert 'src="renders/anime_hellsing_gothic/count__krea2.png"' in html
    assert html.count('class="missing"') == 2 * 5 * 3 - 1


def test_each_image_carries_its_prompt_and_time(tmp_path):
    row = {"style": "anime_hellsing_gothic", "subject": "count", "model": "krea2", "seconds": 7.5, "cold": False}
    html = page(tmp_path, [row])
    assert "7.5 s" in html and "The count." in html


def test_the_warm_median_ignores_the_cold_load():
    rows = [{"style": "s", "model": "m", "seconds": 90.0, "cold": True},
            {"style": "s", "model": "m", "seconds": 8.0, "cold": False},
            {"style": "s", "model": "m", "seconds": 10.0, "cold": False}]
    assert board.warm_median(rows, "s", "m") == 9.0
    assert board.warm_median(rows, "s", "other") is None


def test_a_style_offers_one_pick_per_model(tmp_path):
    html = page(tmp_path)
    assert html.count('name="pick-anime_hellsing_gothic"') == 3


def test_a_failed_jobs_row_is_skipped(tmp_path):
    row = {"style": "anime_hellsing_gothic", "subject": "count", "model": "krea2", "error": "RuntimeError: x"}
    assert 'class="missing"' in page(tmp_path, [row])


def test_a_portable_board_embeds_each_image_through_its_source(tmp_path):
    planned = jobs([style()], subjects(), GUIDES)
    (tmp_path / planned[0].out).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / planned[0].out).write_bytes(b"png")
    html = board.page([style()], subjects(), GUIDES, planned, [], tmp_path, src=lambda out: "data:image/jpeg;base64,AA")
    assert 'src="data:image/jpeg;base64,AA"' in html and 'src="renders/' not in html


def test_a_thumbnail_is_a_small_jpeg_data_uri(tmp_path):
    from PIL import Image
    Image.new("RGB", (1024, 1024), (200, 30, 30)).save(tmp_path / "a.png")
    uri = board.thumbnail(tmp_path / "a.png", 64)
    assert uri.startswith("data:image/jpeg;base64,") and len(uri) < 4000


def test_a_model_shows_only_in_the_styles_it_has_jobs_for(tmp_path):
    from prism.catalog import ModelWords
    guides = {**GUIDES, "pup": guide("pup", captions_only=True)}
    held = style(models={"pup": ModelWords(style="", captions={s.id: "c" for s in subjects().subjects})})
    other = style("anime_b", "B")
    html = board.page([held, other], subjects(), guides, jobs([held, other], subjects(), guides), [], tmp_path)
    assert html.count('name="pick-anime_hellsing_gothic"') == 4 and html.count('name="pick-anime_b"') == 3


def test_the_board_is_dark_by_default(tmp_path):
    assert "#0f1012" in page(tmp_path)
