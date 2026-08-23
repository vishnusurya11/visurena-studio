"""Minimal stdlib EPUB reader: metadata, spine documents, TOC, and HTML→blocks.

No third-party dependencies — an EPUB is a zip of XHTML plus an OPF manifest.
Used by analysis step 01 (and any future stage that reads books).
"""

from __future__ import annotations

import posixpath
import zipfile
from html.parser import HTMLParser
from xml.etree import ElementTree

_NS = {
    "cnt": "urn:oasis:names:tc:opendocument:xmlns:container",
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
}

HEADING_TAGS = {"h1", "h2", "h3", "h4"}
_BLOCK_TAGS = HEADING_TAGS | {"p", "div", "li", "blockquote"}


def read_epub(path) -> dict:
    """Whole book in one call: {title, author, spine: [{href, raw_html}], toc}."""
    with zipfile.ZipFile(path) as zf:
        opf_path = _opf_path(zf)
        meta = _parse_opf(zf, opf_path)
        toc = _parse_nav(zf, opf_path, meta["nav_href"]) if meta["nav_href"] else []
        spine = [
            {"href": href, "raw_html": _read_text(zf, opf_path, href)}
            for href in meta["spine"]
        ]
    return {"title": meta["title"], "author": meta["author"], "spine": spine, "toc": toc}


def _opf_path(zf: zipfile.ZipFile) -> str:
    root = ElementTree.fromstring(zf.read("META-INF/container.xml"))
    rootfile = root.find(".//cnt:rootfile", _NS)
    return rootfile.attrib["full-path"]


def _read_text(zf: zipfile.ZipFile, opf_path: str, href: str) -> str:
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(opf_path), href))
    return zf.read(resolved).decode("utf-8", "replace")


def _parse_opf(zf: zipfile.ZipFile, opf_path: str) -> dict:
    root = ElementTree.fromstring(zf.read(opf_path))
    title = getattr(root.find(".//dc:title", _NS), "text", None) or ""
    author = getattr(root.find(".//dc:creator", _NS), "text", None) or ""
    items = {}
    nav_href = None
    for item in root.findall(".//opf:manifest/opf:item", _NS):
        items[item.attrib["id"]] = item.attrib["href"]
        if "nav" in item.attrib.get("properties", ""):
            nav_href = item.attrib["href"]
    spine = [
        items[ref.attrib["idref"]]
        for ref in root.findall(".//opf:spine/opf:itemref", _NS)
        if ref.attrib["idref"] in items
    ]
    return {"title": title, "author": author, "spine": spine, "nav_href": nav_href}


def _parse_nav(zf: zipfile.ZipFile, opf_path: str, nav_href: str) -> list[dict]:
    parser = _NavParser()
    parser.feed(_read_text(zf, opf_path, nav_href))
    return parser.entries


class _NavParser(HTMLParser):
    """Extract the epub:type='toc' nav as [{title, href, level}] (level = ol depth)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.entries: list[dict] = []
        self._in_toc = False
        self._depth = 0
        self._href = None
        self._buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "nav":
            nav_type = attrs.get("epub:type", "toc")  # tolerate untyped single nav
            self._in_toc = nav_type == "toc"
        elif self._in_toc and tag == "ol":
            self._depth += 1
        elif self._in_toc and tag == "a":
            self._href = attrs.get("href", "")
            self._buf = []

    def handle_endtag(self, tag):
        if tag == "nav":
            self._in_toc = False
        elif self._in_toc and tag == "ol":
            self._depth -= 1
        elif self._in_toc and tag == "a" and self._href is not None:
            title = " ".join("".join(self._buf).split())
            if title:
                self.entries.append(
                    {"title": title, "href": self._href, "level": self._depth}
                )
            self._href = None

    def handle_data(self, data):
        if self._in_toc and self._href is not None:
            self._buf.append(data)


def html_to_blocks(html: str) -> list[dict]:
    """XHTML → [{kind: 'heading'|'para', text}] with whitespace normalized."""
    parser = _BlockParser()
    parser.feed(html)
    parser.close_pending()
    return parser.blocks


_SKIP_TAGS = {"head", "title", "style", "script"}  # never content (first real-run bug:
# each xhtml's <title> "Book | Project Gutenberg" leaked in as a paragraph)


class _BlockParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict] = []
        self._buf: list[str] = []
        self._kind = "para"
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag in _BLOCK_TAGS:
            self.close_pending()
            self._kind = "heading" if tag in HEADING_TAGS else "para"

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in _BLOCK_TAGS:
            self.close_pending()

    def handle_data(self, data):
        if not self._skip_depth:
            self._buf.append(data)

    def close_pending(self):
        text = " ".join("".join(self._buf).split())
        if text:
            self.blocks.append({"kind": self._kind, "text": text})
        self._buf = []
        self._kind = "para"
