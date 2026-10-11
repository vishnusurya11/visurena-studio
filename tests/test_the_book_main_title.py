"""The book's main title (owner 2026-10-11, decision
architecture/decisions/2026-10-11_book_main_title_and_thumbnail.md): 7 s,
a widescreen band inside the book's square, a cold open cut from the book's
own Shorts, black on the sting's hit, then a text-free key-art plate with the
title SET BY CODE -- no model ever draws a letter."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from studio import book_compilation as bc
from studio import book_title as bt

FONT = Path(__file__).resolve().parents[1] / "assets" / "fonts" / "bebas_neue" / "BebasNeue-Regular.ttf"


def test_the_band_is_a_scope_frame_centred_in_the_square():
    assert bt.band_box(1536) == (0, 447, 1536, 642)
    x, y, w, h = bt.band_box(768)
    assert (w, h % 2, y) == (768, 0, (768 - h) // 2)


def test_the_title_comes_from_the_book_never_from_the_writer():
    class Writer:
        def __call__(self, tier, prompt, schema, **kw):
            return schema(title="THE WRONG BOOK", hero="a tripod over the burning Thames at dawn",
                          thumb="a tripod on the right, empty dark sky on the left",
                          sting="epic orchestral sting, brass, timpani")
    spec = bt.spec({"title": "The war of the worlds", "display_title": "The War of the Worlds",
                    "author": "H. G. Wells"}, synopsis="Martians land in Surrey.", ask=Writer())
    assert (spec.title, spec.author) == ("The War of the Worlds", "H. G. Wells")
    assert spec.hero.startswith("a tripod")


def test_a_long_title_wraps_and_shrinks_to_fit():
    lines, px = bt.fit_lines("Twenty Thousand Leagues Under the Sea", FONT, max_w=900, start_px=200, min_px=40)
    assert len(lines) == 2 and px <= 200
    from PIL import ImageFont
    font = ImageFont.truetype(str(FONT), px)
    assert all(font.getlength(line) <= 900 for line in lines)


def test_a_short_title_stays_on_one_line():
    assert bt.fit_lines("Dracula", FONT, max_w=900, start_px=200, min_px=40)[0] == ["DRACULA"]


def test_a_letter_the_font_lacks_is_named():
    assert bt.glyphs_missing("THE WAR OF THE WORLDS", FONT) == []
    assert "Ж" in bt.glyphs_missing("ЖУК", FONT)


def test_the_title_tracks_in_from_wide_to_set():
    assert bt.tracking_em(0.0) == pytest.approx(bt.TRACK_FROM)
    assert bt.tracking_em(1.0) == pytest.approx(bt.TRACK_TO)
    assert bt.TRACK_TO < bt.tracking_em(0.5) < bt.TRACK_FROM


def test_one_cold_open_segment_per_fifth_of_the_book_the_sharpest_first():
    cands = [{"episode": e, "start_s": 1.0, "end_s": 6.0, "sharp": float(e % 3)} for e in range(1, 11)]
    picks = bt.pick_segments(cands, episodes=10, n=5, clean=lambda c: True)
    assert [p["episode"] for p in picks] == [2, 4, 5, 8, 10]       # sharp = e % 3 within each fifth
    fifths = [(p["episode"] - 1) * 5 // 10 for p in picks]
    assert fifths == [0, 1, 2, 3, 4]


def test_a_lettered_segment_is_passed_over_for_the_next():
    cands = [{"episode": 1, "start_s": 0, "end_s": 5, "sharp": 9.0},
             {"episode": 1, "start_s": 9, "end_s": 14, "sharp": 1.0}]
    picks = bt.pick_segments(cands, episodes=1, n=1, clean=lambda c: c["sharp"] < 5)
    assert picks[0]["start_s"] == 9


def test_a_fifth_with_nothing_clean_is_left_out():
    cands = [{"episode": 1, "start_s": 0, "end_s": 5, "sharp": 9.0}]
    assert bt.pick_segments(cands, episodes=1, n=1, clean=lambda c: False) == []


def test_the_segment_is_cut_from_the_middle_of_the_shot():
    assert bt.segment_window({"start_s": 10.0, "end_s": 14.0}, frames=12, fps=24) == (11.75, 12.25)


def test_the_sting_hit_is_the_strongest_onset():
    rate = 1000
    sound = np.zeros(rate * 4)
    sound[int(1.5 * rate):] = 0.1
    sound[int(2.7 * rate):int(3.0 * rate)] = 0.9
    assert bt.sting_hit(sound, rate) == pytest.approx(2.7, abs=0.06)


def test_white_on_the_scrim_has_contrast_and_on_white_does_not():
    assert bt.contrast_ratio(1.0, 0.0) == pytest.approx(21.0)
    assert bt.contrast_ratio(1.0, 0.9) < 7.0


def test_the_running_order_is_fixed_in_frames():
    t = bt.TIMELINE
    assert t["total"] == 168 and t["cold_end"] < t["black_end"] < t["presents_end"] < t["total"]


def test_every_later_chapter_stamp_moves_by_the_main_title():
    parts = [(1, "A", 150.0), (2, "B", 160.0), (3, "C", 170.0)]
    assert bc.chapter_lines(parts, lead_s=7.0) == ["0:00 Ep 1 — A", "2:37 Ep 2 — B", "5:17 Ep 3 — C"]


def test_cold_open_candidates_are_faceless_wides_and_inserts_long_enough_to_cut():
    plan = {"shots": [{"index": 0, "size": "wide", "faces": []},
                      {"index": 1, "size": "medium_close", "faces": ["narrator"]},
                      {"index": 2, "size": "insert", "faces": []},
                      {"index": 3, "size": "wide", "faces": ["curate"]},
                      {"index": 4, "size": "wide", "faces": []}],
            "omit": [4]}
    placed = {"shots": [{"index": 0, "t_start": 0.0, "t_end": 7.5}, {"index": 1, "t_start": 7.5, "t_end": 9.0},
                        {"index": 2, "t_start": 9.0, "t_end": 9.5}, {"index": 3, "t_start": 9.5, "t_end": 15.0}]}
    assert bt.candidates(7, plan, placed) == [{"episode": 7, "shot": 0, "start_s": 0.0, "end_s": 7.5}]


def test_the_overlay_sets_the_title_only_in_the_hero_and_presents_only_in_the_black():
    spec = bt.BookTitleSpec(title="The War of the Worlds", author="H. G. Wells", hero="h", thumb="t", sting="s")
    cold = bt.overlay_frame(spec, 10, width=768, height=322, font=FONT)
    presents = bt.overlay_frame(spec, 80, width=768, height=322, font=FONT)
    hero = bt.overlay_frame(spec, 160, width=768, height=322, font=FONT)
    assert cold.getbbox() is None                                  # nothing over the cold open
    assert presents.getbbox() is not None and hero.getbbox() is not None
    assert hero.size == (768, 322) and hero.mode == "RGBA"


def test_the_thumbnail_is_1280_by_720_with_the_title_on_the_dark_left():
    from PIL import Image
    spec = bt.BookTitleSpec(title="The War of the Worlds", author="H. G. Wells", hero="h", thumb="t", sting="s")
    plate = Image.new("RGB", (2560, 1440), (200, 200, 200))
    thumb = bt.thumbnail(plate, spec, episodes=27, font=FONT)
    assert thumb.size == (1280, 720)
    left, right = thumb.crop((0, 0, 400, 720)).convert("L"), thumb.crop((900, 0, 1280, 720)).convert("L")
    assert left.getextrema()[1] == 255 and max(right.getdata()) < 255       # white type only on the left


def test_the_stream_signature_ignores_bitrate_and_duration():
    a = ("  Duration: 00:00:07.00, start: 0.000000, bitrate: 9000 kb/s\n"
         "  Stream #0:0[0x1](und): Video: h264 (High) (avc1 / 0x31637661), yuv420p(progressive), 1536x1536 [SAR 1:1 DAR 1:1], 8000 kb/s, 24 fps, 24 tbr, 12288 tbn (default)\n"
         "  Stream #0:1[0x2](und): Audio: aac (LC) (mp4a / 0x6134706D), 48000 Hz, stereo, fltp, 256 kb/s (default)\n")
    b = a.replace("8000 kb/s", "1200 kb/s").replace("00:00:07.00", "00:02:31.00")
    assert bt.stream_signature(a) == bt.stream_signature(b)
    assert bt.stream_signature(a) != bt.stream_signature(a.replace("1536x1536", "768x768"))


def test_a_reader_saying_none_is_no_lettering_and_any_word_is():
    for said in ("NONE", "None.", '["NONE"]', "", "There is no lettering in this image."):
        assert not bt.has_lettering(said), said
    for said in ('["THE WAR OF\nTHE WORLDS"]', "GLOBE TAVERN", "No. 7"):
        assert bt.has_lettering(said), said


def test_a_hit_first_sting_is_laid_with_its_hit_on_the_black_and_a_riser_before_it():
    rate = 1000
    ace = np.zeros(rate * 10)
    ace[int(0.68 * rate):int(3.0 * rate)] = 0.8                     # ACE-Step: the hit at 0.68 s
    laid = bt.align_sting(ace, rate, hit_s=0.68, at_s=2.5, total_s=7.0)
    assert laid.shape == (7 * rate, 2)
    assert bt.sting_hit(laid, rate) == pytest.approx(2.5, abs=0.06)
    assert np.abs(laid[int(1.0 * rate):int(2.4 * rate)]).max() > 0.01  # the riser fills the cold open


def test_a_late_hit_is_trimmed_to_the_black():
    rate = 1000
    ace = np.zeros(rate * 10)
    ace[int(4.0 * rate):int(6.0 * rate)] = 0.8
    laid = bt.align_sting(ace, rate, hit_s=4.0, at_s=2.5, total_s=7.0)
    assert bt.sting_hit(laid, rate) == pytest.approx(2.5, abs=0.06)


def test_the_shortlist_keeps_the_sharpest_few_of_each_fifth():
    cands = [{"episode": e, "start_s": float(k), "end_s": k + 5.0, "sharp": float(k)} for e in (1, 10) for k in range(6)]
    short = bt.shortlist(cands, episodes=10, n=5, k=2)
    assert sorted((c["episode"], c["sharp"]) for c in short) == [(1, 4.0), (1, 5.0), (10, 4.0), (10, 5.0)]


def test_the_most_cinematic_clean_shot_wins_its_fifth():
    cands = [{"episode": 1, "start_s": 0, "end_s": 5, "sharp": 9.0, "drama": 2},
             {"episode": 1, "start_s": 9, "end_s": 14, "sharp": 3.0, "drama": 8}]
    assert bt.pick_segments(cands, episodes=1, n=1, clean=lambda c: True)[0]["drama"] == 8


def test_the_title_fits_with_its_widest_letter_spacing():
    from PIL import ImageFont
    lines, px = bt.fit_lines("The War of the Worlds", FONT, max_w=1300, start_px=200, min_px=40, tracking=0.4)
    font = ImageFont.truetype(str(FONT), px)
    assert all(font.getlength(l) + 0.4 * px * (len(l) - 1) <= 1300 for l in lines)


def test_a_square_pixel_tag_is_the_same_stream_as_none():
    line = ("  Stream #0:0[0x1](und): Video: h264 (High) (avc1 / 0x31637661), yuv420p(tv, bt709/bt709/iec61966-2-1, "
            "progressive), 1536x1536{sar}, 24 fps, 24 tbr, 12288 tbn (default)\n")
    assert bt.stream_signature(line.format(sar=" [SAR 1:1 DAR 1:1]")) == bt.stream_signature(line.format(sar=""))


def test_the_readers_drama_score_is_its_first_number_capped_at_ten():
    assert bt.drama_score("8") == 8 and bt.drama_score('["7/10"]') == 7
    assert bt.drama_score("Score: 12") == 10 and bt.drama_score("no idea") == 0


def test_the_hero_title_and_the_judge_read_the_same_layout():
    lines, px = bt.hero_layout("The War of the Worlds", FONT, width=1536, height=642)
    assert lines == ["THE WAR OF", "THE WORLDS"] and px > 100
