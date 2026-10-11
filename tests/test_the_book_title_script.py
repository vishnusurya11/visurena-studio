"""The main title's runner (scripts/episode/book_title.py): the parts that
need no GPU.  The renders themselves are local and free, run on WotW first."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from studio import book_title as bt

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_book_title", ROOT / "scripts" / "episode" / "book_title.py")
runner = importlib.util.module_from_spec(spec)
sys.modules["ep_book_title"] = runner
spec.loader.exec_module(runner)


def test_the_cold_open_is_always_sixty_frames_however_many_segments_survive():
    assert runner.cold_lengths(5) == list(bt.COLD_FRAMES)
    assert sum(runner.cold_lengths(3)) == sum(runner.cold_lengths(4)) == bt.TIMELINE["cold_end"]
    assert runner.cold_lengths(0) == []


def test_a_square_chapter_is_cropped_to_the_band():
    assert "crop=1536:642:0:447" in runner.band_filter()


def test_the_fallback_sting_hits_on_the_cut_to_black():
    sound = runner.synth_sting()
    assert sound.shape == (7 * 48000, 2)
    assert bt.sting_hit(sound, 48000) == pytest.approx(runner.STING_AT_S, abs=0.05)


def test_the_laid_sting_is_only_cut_to_length_faded_and_levelled():
    chain = runner.audio_chain()
    assert "atrim=end=7.0000" in chain and "afade=t=out" in chain
    assert "loudnorm=I=-16.0" in chain and chain.endswith("[a]")


def test_the_level_gain_is_the_distance_to_the_target():
    assert runner.level_gain(-17.5) == pytest.approx(1.5)
    assert runner.level_gain(-16.2) == 0.0                     # inside the band: left alone


def test_the_hero_prompt_gives_the_video_model_no_words_to_letter():
    assert '"' not in runner.hero_prompt() and "title" not in runner.hero_prompt().split("key art")[1].lower()


def test_the_encode_is_the_chapter_pieces_encode():
    from studio import book_compilation as bc
    piece = bc.cut_argv(Path("a.mp4"), (0, 1), Path("b.mp4"), fps=24, side=1536)
    tail = piece[piece.index("-c:v"):-1]
    assert runner.ENCODE == tail


def test_the_series_look_is_read_off_episode_one(tmp_path, monkeypatch):
    import json
    from studio import episode_home
    ep = tmp_path / "episodes" / "ep01"
    ep.mkdir(parents=True)
    monkeypatch.setattr(episode_home, "home", lambda book, n: Path(book) / "episodes" / f"ep{n:02d}")
    (ep / "plan.json").write_text(json.dumps({"look": "Angular stylised 3D"}), encoding="utf-8")
    assert runner.book_look(tmp_path) == "Angular stylised 3D"
    (ep / "plan.json").write_text(json.dumps({"look": ""}), encoding="utf-8")
    assert runner.book_look(tmp_path) == ""                 # photoreal (Scarlet)


def test_a_reader_that_fails_is_a_flag_never_a_crash():
    """2026-10-11: Qwen3_VQA lost its temp image and the whole upload run died at
    a read that can only flag."""
    def broken(_):
        raise RuntimeError("Qwen3_VQA: No such file or directory: temp_image_42.png")
    flags = runner.read_flags(["A STUDY IN", "SCARLET"], broken)
    assert len(flags) == 1 and flags[0].startswith("the reader failed")
    assert runner.read_flags(["A STUDY IN", "SCARLET"], lambda _: "A STUDY IN\nSCARLET") == []
    assert runner.read_flags(["A STUDY IN"], lambda _: "A STUDY") == ["the reader did not find ['A STUDY IN'] on the held frame"]
