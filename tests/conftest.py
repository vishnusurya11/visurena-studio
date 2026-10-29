"""Shared fixtures. The fixture EPUB mimics Project Gutenberg epub3 structure:
front matter with the PG *** START *** marker + a preface, two PARTS with two
chapters each (headings), and a license doc after *** END ***. Never the real file."""

from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path

import pytest


def fast_tempdir() -> str | None:
    """%LOCALAPPDATA%\\Temp (the NVMe) when it exists, else None: a session that inherited
    TEMP=D:\\temp wrote every test's tmp_path to the D: hard disk (2026-10-11)."""
    base = os.environ.get("LOCALAPPDATA")
    temp = Path(base) / "Temp" if base else None
    return str(temp) if temp and temp.is_dir() else None


tempfile.tempdir = fast_tempdir() or tempfile.tempdir

_CONTAINER = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"""

_OPF = """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">test-244</dc:identifier>
    <dc:title>A Study in Scarlet</dc:title>
    <dc:creator>Arthur Conan Doyle</dc:creator>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="front" href="front.xhtml" media-type="application/xhtml+xml"/>
    <item id="contents" href="contents.xhtml" media-type="application/xhtml+xml"/>
    <item id="p1" href="part1.xhtml" media-type="application/xhtml+xml"/>
    <item id="p2" href="part2.xhtml" media-type="application/xhtml+xml"/>
    <item id="lic" href="license.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="front"/><itemref idref="contents"/><itemref idref="p1"/><itemref idref="p2"/><itemref idref="lic"/>
  </spine>
</package>"""

_NAV = """<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><body>
<nav epub:type="toc"><ol>
  <li><a href="part1.xhtml">PART I. THE REMINISCENCES</a><ol>
    <li><a href="part1.xhtml#c1">Chapter I. The Meeting</a></li>
    <li><a href="part1.xhtml#c2">Chapter II. The Science of Deduction</a></li>
  </ol></li>
  <li><a href="part2.xhtml">PART II. THE COUNTRY</a><ol>
    <li><a href="part2.xhtml#c3">Chapter III. On the Great Plain</a></li>
    <li><a href="part2.xhtml#c4">Chapter IV. The Avenging Angels</a></li>
  </ol></li>
</ol></nav>
<nav epub:type="landmarks"><ol><li><a href="front.xhtml">Front</a></li></ol></nav>
</body></html>"""

_FRONT = """<html><body>
<header class="pg-boilerplate pgheader" id="pg-header">
<h1>The Project Gutenberg eBook of A Study in Scarlet</h1>
<div id="pg-start-separator">
<span>*** START OF THE PROJECT GUTENBERG EBOOK A STUDY IN SCARLET ***</span>
</div></header>
<p>This preface paragraph introduces the tale to the reader.</p>
</body></html>"""

_CONTENTS = """<html><head><title>A Study in Scarlet | Project Gutenberg</title></head><body>
<h2>CONTENTS</h2>
<table><tbody><tr><td><a href="part1.xhtml#c1">Chapter I. The Meeting</a></td></tr></tbody></table>
</body></html>"""

_PART1 = """<html><head><title>A Study in Scarlet | Project Gutenberg</title></head><body>
<h1>PART I. THE REMINISCENCES</h1>
<h2 id="c1">Chapter I. The Meeting</h2>
<p>In the year 1878 I took my degree of Doctor of Medicine.</p>
<p>The campaign brought honours to many, but for me it held misfortune.</p>
<h2 id="c2">Chapter II. The Science of Deduction</h2>
<p>We met next day and inspected the rooms at Baker Street.</p>
</body></html>"""

_PART2 = """<html><body>
<h1>PART II. THE COUNTRY</h1>
<h2 id="c3">Chapter III. On the Great Plain</h2>
<p>In the central portion of the great continent lies an arid desert.</p>
<h2 id="c4">Chapter IV. The Avenging Angels</h2>
<p>All night their course lay through intricate defiles.</p>
<p>The pursuit continued at first light without mercy.</p>
</body></html>"""

_LICENSE = """<html><body>
<section class="pg-boilerplate pgfooter" id="pg-footer">
<div id="pg-end-separator">
<span>*** END OF THE PROJECT GUTENBERG EBOOK A STUDY IN SCARLET ***</span>
</div>
<p>Updated editions will replace the previous one. Full License terms follow.</p>
</section>
</body></html>"""


def build_fixture_epub(path):
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", _CONTAINER)
        zf.writestr("OEBPS/content.opf", _OPF)
        zf.writestr("OEBPS/nav.xhtml", _NAV)
        zf.writestr("OEBPS/front.xhtml", _FRONT)
        zf.writestr("OEBPS/contents.xhtml", _CONTENTS)
        zf.writestr("OEBPS/part1.xhtml", _PART1)
        zf.writestr("OEBPS/part2.xhtml", _PART2)
        zf.writestr("OEBPS/license.xhtml", _LICENSE)
    return path


@pytest.fixture()
def fixture_epub(tmp_path):
    return build_fixture_epub(tmp_path / "test.epub")


# ---- the money and live-DB trap (board review 2026-10-12) -----------------------
#
# A test faked the brain's turn but not its ledger, and wrote 33 rows into the
# live usage table.  No test may write the live DB, resolve a remote host (every
# paid API is one) or spawn the claude CLI; tests/guards.py says why on refusal.

@pytest.fixture(autouse=True)
def paid_and_live_trap(monkeypatch):
    from tests import guards

    guards.install(monkeypatch)


# ---- the ComfyUI trap ----------------------------------------------------------
#
# No test may reach ComfyUI (a GPU, a model, a queue).  Every judge and every
# reader takes an injected callable; one constructed without injection trips
# here, and the failure names the reason.

@pytest.fixture(scope="session")
def comfy_root_in_tmp(tmp_path_factory):
    """One stand-in ComfyUI root per session: `stage_image` copied every test's
    picture into the REAL `ComfyUI/input/` (426 tmp*_cdc0bebf.png, 2026-10-21)."""
    return tmp_path_factory.mktemp("comfy_root")


@pytest.fixture(autouse=True)
def comfy_trap(monkeypatch, comfy_root_in_tmp):
    """`studio.comfy.run` and `run_text` raise for the whole test, and the root
    `stage_image` copies under is a session folder, never the engine's.  The
    real functions come back as the fixture's value, for `real_comfy` only."""
    from studio import comfy

    real = {"run": comfy.run, "run_text": comfy.run_text, "free_models": comfy.free_models}

    def trip(*_args, **_kwargs):
        raise RuntimeError("a test reached ComfyUI")

    monkeypatch.setattr(comfy, "COMFY_ROOT", comfy_root_in_tmp)
    monkeypatch.setattr(comfy, "run", trip)
    monkeypatch.setattr(comfy, "run_text", trip)
    monkeypatch.setattr(comfy, "VLM_CALLS", None)       # the read log never writes under library/ in a test
    monkeypatch.setattr(comfy, "CHANGEOVERS", None)     # nor the model-load ledger (craft ruling A27)
    from studio import routed_whisper                   # nor the ear's per-clip log (fleet E A2)
    monkeypatch.setattr(routed_whisper, "WHISPER_CALLS", None)
    # A test's `model_kept()` ends with /free: it must never unload the live
    # engine's models under a running render (speed plan #6).
    monkeypatch.setattr(comfy, "free_models", lambda: None)
    from studio.command_center import comfy_tap        # the board's GPU card reads /queue (2026-10-12)
    monkeypatch.setattr(comfy_tap, "fetch_queue", trip)
    return real


@pytest.fixture(autouse=True)
def router_trap(monkeypatch, comfy_root_in_tmp):
    """No test asks the live compute router or writes under the real library's
    `.device/`: an unrouted `card_free` slept 300 s per test and wrote 21 rows
    into the real decisions file (2026-10-21).  The default probe trips (the
    router answers cpu, naming it), and `card_free` without a route raises."""
    from studio import compute_device as cd
    from studio import master_upscale as mu

    real_card_free = mu.card_free

    def trip(*_args, **_kwargs):
        raise RuntimeError("a test reached the compute router")

    def card_free(job, need_gb, route=None, sleep=None, clock=None):
        if route is None:
            trip()
        return real_card_free(job, need_gb, route=route, sleep=sleep, clock=clock)

    monkeypatch.setattr(cd, "LOG", comfy_root_in_tmp / "device" / "decisions.jsonl")
    monkeypatch.setattr(cd, "CLAIMS", comfy_root_in_tmp / "device" / "claims")
    monkeypatch.setattr(cd, "default_probe", trip)
    monkeypatch.setattr(mu, "card_free", card_free)


@pytest.fixture()
def real_comfy(comfy_trap, monkeypatch):
    """For the tests OF `comfy.run` / `run_text` themselves, with the server
    mocked underneath them (submit, wait_record); nothing else asks for this."""
    from studio import comfy

    for name, fn in comfy_trap.items():
        monkeypatch.setattr(comfy, name, fn)


@pytest.fixture(autouse=True)
def lanes_on_a_bare_double(monkeypatch):
    """Step 09's two lanes (studio/take_overlap.py) launch processes through
    `ctx.command`.  The ladder's tests drive a bare context double that only
    records `run_script` and advances a clock; for such a double the lanes
    collapse to the one render launch they replace, so those tests keep
    testing the LADDER.  The lanes themselves are tested with a full double in
    tests/test_take_lanes_run_side_by_side.py."""
    from studio import take_ladder, take_overlap

    real = take_overlap.shoot

    def shoot(ctx, base, **kw):
        if hasattr(ctx, "command"):
            return real(ctx, base, **kw)
        indices, why = kw.get("retake") or ((), "")
        args = [*base, *kw.get("extra", ())] + (take_ladder.retake_args(list(indices), why) if indices else [])
        if indices:
            take_ladder.clear_heads(ctx.home, list(indices))
        ctx.run_script(take_overlap.RENDER, *args, gpu=True, clock="takes")
        return None

    monkeypatch.setattr(take_overlap, "shoot", shoot)


@pytest.fixture(autouse=True)
def face_refine_tests_keep_the_refine(monkeypatch):
    """The 2K pass switches the face refine off in production (studio/regen_2k, owner 2026-10-29); the
    refine is kept, not deleted, so its tests run it with the pass off.  The pass's own tests set the
    switch themselves (tests/test_the_2k_pass_replaces_the_face_fix_and_upscale.py)."""
    from studio import regen_2k
    monkeypatch.setenv(regen_2k.SETTING, "0")
