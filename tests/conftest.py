"""Shared fixtures. The fixture EPUB mimics Project Gutenberg epub3 structure:
front matter with the PG *** START *** marker + a preface, two PARTS with two
chapters each (headings), and a license doc after *** END ***. Never the real file."""

from __future__ import annotations

import zipfile

import pytest

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
<p>The Project Gutenberg eBook of A Study in Scarlet</p>
<p>*** START OF THE PROJECT GUTENBERG EBOOK A STUDY IN SCARLET ***</p>
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
<p>*** END OF THE PROJECT GUTENBERG EBOOK A STUDY IN SCARLET ***</p>
<p>Updated editions will replace the previous one. Full License terms follow.</p>
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
