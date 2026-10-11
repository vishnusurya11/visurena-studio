"""The book-video retro (owner 2026-10-11: "build them and update skills"): every
fault of the first two book videos becomes a check that runs by itself.
WotW and Scarlet are not re-made; these hold for every book after."""
from __future__ import annotations

import py_compile
from pathlib import Path

import pytest

from studio import book_compilation as bc
from studio import book_title as bt

ROOT = Path(__file__).resolve().parents[1]


# ---- the door: nothing uploads that a check can catch ---------------------------

def test_a_title_piece_longer_than_its_card_is_refused_at_the_door():
    """Scarlet ep12's 'title' was 175 frames for a 107-frame card: chapter inside it."""
    pieces = {1: 107, 2: 105, 12: 175}
    cards = {1: 107, 2: 107, 12: 107}
    faults = bc.door_faults(title_frames=pieces, card_frames=cards, order_ok=True, title_verdict={"refused": []})
    assert faults == ["ep12: title piece is 175 frames for a 107-frame card"]


def test_the_door_refuses_a_wrong_running_order_and_a_refused_main_title():
    faults = bc.door_faults(title_frames={}, card_frames={}, order_ok=False,
                            title_verdict={"refused": ["-17.5 LUFS"]})
    assert "the running order is not main title, then title + main per chapter" in faults
    assert any("G-BOOKTITLE refused" in f for f in faults)


def test_a_card_older_than_its_file_is_let_through_when_shorter():
    """Scarlet ep01 carries an older 90-frame card: shorter is a different card, not picture."""
    assert bc.door_faults(title_frames={1: 90}, card_frames={1: 107}, order_ok=True, title_verdict={"refused": []}) == []


def test_the_running_order_check_reads_the_concat_list():
    order = [Path("title/book/main_title.mp4"), Path("ch/ep01_title.mp4"), Path("ch/ep01_main.mp4"),
             Path("ch/ep02_title.mp4"), Path("ch/ep02_main.mp4")]
    assert bc.title_first_order(order)
    assert not bc.title_first_order([order[0], order[2], order[1]] + order[3:])
    assert not bc.title_first_order(order[1:])


# ---- run safety -------------------------------------------------------------------

def test_a_lock_held_by_a_live_process_refuses_a_second_run(tmp_path):
    """Two runs raced on one folder (a 'detached' job survived its shell, 2026-10-11)."""
    lock = tmp_path / ".lock"
    lock.write_text("4242", encoding="utf-8")
    assert bc.lock_holder(lock, alive=lambda pid: pid == 4242) == 4242
    assert bc.lock_holder(lock, alive=lambda pid: False) is None          # a dead holder is stale
    assert bc.lock_holder(tmp_path / "none", alive=lambda pid: True) is None


def test_every_module_still_compiles(tmp_path):
    """A backslash through a heredoc reached disk as a raw newline three times; the
    import failed only when the run reached it."""
    bad = []
    for folder in ("studio", "scripts"):
        for path in (ROOT / folder).rglob("*.py"):
            try:
                py_compile.compile(str(path), doraise=True, cfile=str(tmp_path / f"{len(bad)}_{path.stem}.pyc"))
            except py_compile.PyCompileError as why:
                bad.append(f"{path.relative_to(ROOT)}: {why.msg.splitlines()[-1]}")
    assert bad == []


# ---- image checks -------------------------------------------------------------------

def test_a_plate_is_routed_by_the_books_look_not_judged_by_a_reader():
    """A VLM asked PHOTOGRAPH / PAINTING / 3D RENDER called Scarlet's correct photoreal
    plate a '3D RENDER' (2026-10-11): it cannot judge the look, so the look is routed."""
    assert bt.plate_request("", wide=True)["values"]["enable_lora"] is False
    assert not hasattr(bt, "look_matches")


def test_the_writer_falls_back_to_the_books_own_logline_when_it_cannot_be_reached():
    """The Claude SDK hung at start-up on every call (2026-10-11); the title must not wait on it."""
    def down(*a, **k):
        raise RuntimeError("Control request timeout: initialize")
    spec = bt.spec({"title": "A Study in Scarlet", "author": "Arthur Conan Doyle"},
                   synopsis="A detective and an army doctor hunt a killer through London.", ask=down)
    assert spec.title == "A Study in Scarlet"
    assert "hunt a killer through London" in spec.hero and "one person" in spec.thumb.lower()
    assert spec.sting


def test_staging_an_image_puts_back_a_missing_comfy_temp_folder(tmp_path, monkeypatch):
    """A second ComfyUI deleted ComfyUI/temp on exit; every Qwen3-VL read then failed."""
    from studio import comfy
    monkeypatch.setattr(comfy, "COMFY_ROOT", tmp_path)
    img = tmp_path / "a.png"
    img.write_bytes(b"x")
    comfy.stage_image(img)
    assert (tmp_path / "temp").is_dir()


def test_this_process_is_alive_and_a_made_up_one_is_not():
    import os
    from scripts.publish import book_compilation as script
    assert script.pid_alive(os.getpid()) and not script.pid_alive(4_000_000)


def test_a_chapter_cards_art_follows_the_books_look_and_redraws_a_doubled_person(tmp_path, monkeypatch):
    """series_title.base_art drew every book in WotW's LoRA look -- the fault Scarlet's
    main title had -- and nothing checked it for a person drawn twice."""
    import importlib.util, json, sys
    loader = importlib.util.spec_from_file_location("st_retro", ROOT / "scripts" / "episode" / "series_title.py")
    st = importlib.util.module_from_spec(loader); sys.modules["st_retro"] = st; loader.loader.exec_module(st)
    book = tmp_path / "book"
    (book / "title").mkdir(parents=True)
    (book / "title" / "motif.txt").write_text("a lamp on a desk", encoding="utf-8")
    from studio import episode_home
    monkeypatch.setattr(episode_home, "home", lambda b, n: Path(b) / "episodes" / f"ep{n:02d}")
    (book / "episodes" / "ep01").mkdir(parents=True)
    (book / "episodes" / "ep01" / "plan.json").write_text(json.dumps({"look": ""}), encoding="utf-8")
    calls, reads = [], iter(['["deerstalker; coat; dark hair\ndeerstalker; coat; dark hair"]', "NONE"])
    def run(name, values, **kw):
        calls.append((name, values))
        out = tmp_path / f"made_{len(calls)}.png"; out.write_bytes(b"png"); return [out]
    monkeypatch.setattr(st, "run", run)
    monkeypatch.setattr(st, "run_text", lambda name, values, **kw: next(reads))
    monkeypatch.setattr(st, "stage_image", lambda p: str(p))
    out = st.base_art(book / "title")
    assert [c[0] for c in calls] == ["image_krea2_turbo_t2i", "image_krea2_turbo_t2i"]   # photoreal, redrawn once
    assert calls[0][1]["enable_lora"] is False and calls[1][1]["seed"] == calls[0][1]["seed"] + 1
    assert out.read_bytes() == b"png"
