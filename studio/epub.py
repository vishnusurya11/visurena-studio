"""Minimal stdlib EPUB reader: metadata, spine documents, TOC, and HTML→blocks.

No third-party dependencies — an EPUB is a zip of XHTML plus an OPF manifest.
Used by analysis step 01 (and any future stage that reads books).
"""

from __future__ import annotations

import posixpath
import zipfile
from collections import Counter
from html.parser import HTMLParser
from xml.etree import ElementTree

_NS = {
    "cnt": "urn:oasis:names:tc:opendocument:xmlns:container",
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
    "ncx": "http://www.daisy.org/z3986/2005/ncx/",
}

HEADING_TAGS = {"h1", "h2", "h3", "h4"}
_CELL_TAGS = {"td", "th", "tr", "caption"}
_BLOCK_TAGS = HEADING_TAGS | {"p", "div", "li", "blockquote", "table"} | _CELL_TAGS

# A tag that RENDERS as a break must produce whitespace in the text. <br/> produced
# nothing, so "red,<br/>Violets" came out "red,Violets" — silent word corruption
# wherever the source html lacked stray whitespace. Inline tags (<i>, <em>, <span>)
# render inside the sentence and must NOT break it.
_LINE_BREAK_TAGS = {"br", "hr"}

# The break marker must be something the source text can NEVER contain. A newline is
# not: the XHTML's own cosmetic wrapping at ~70 columns then survives as hard line
# breaks — 2,668 of them in one book. NUL cannot appear in XML character data, so it
# marks a real <br/> and nothing else. (chr(0), not an escape — a literal NUL in a
# source file is a syntax error, not a constant.)
_BREAK = chr(0)


def read_epub(path) -> dict:
    """Whole book in one call: {title, author, spine: [{href, raw_html}], toc}.

    TOC: the EPUB3 nav document when the book has one, else the EPUB2 `toc.ncx`.
    Reading only the nav left EPUB2 books with an empty TOC — and an empty TOC means
    no chapter is ever recognised, so the whole novel became one front-matter blob."""
    with zipfile.ZipFile(path) as zf:
        opf_path = _opf_path(zf)
        meta = _parse_opf(zf, opf_path)
        toc = _read_toc(zf, opf_path, meta)
        spine = [
            {"href": href, "raw_html": _read_text(zf, opf_path, href)}
            for href in meta["spine"]
        ]
    return {"title": meta["title"], "author": meta["author"], "spine": spine, "toc": toc}


def _read_toc(zf: zipfile.ZipFile, opf_path: str, meta: dict) -> list[dict]:
    """EPUB3 nav first (the spec says reading systems must prefer it), NCX as fallback."""
    if meta["nav_href"]:
        entries = _parse_nav(zf, opf_path, meta["nav_href"])
        if entries:
            return entries
    if meta["ncx_href"]:
        return parse_ncx(_read_text(zf, opf_path, meta["ncx_href"]))
    return []


def parse_ncx(xml: str) -> list[dict]:
    """EPUB2 navMap -> [{title, href, level}], level 1-based by navPoint nesting."""
    root = ElementTree.fromstring(xml)
    entries: list[dict] = []

    def walk(node, depth):
        for point in node.findall("ncx:navPoint", _NS):
            label = point.find("ncx:navLabel/ncx:text", _NS)
            content = point.find("ncx:content", _NS)
            title = " ".join((label.text or "").split()) if label is not None else ""
            if title:
                entries.append({"title": title, "level": depth,
                                "href": content.attrib.get("src", "")
                                if content is not None else ""})
            walk(point, depth + 1)

    nav_map = root.find("ncx:navMap", _NS)
    if nav_map is not None:
        walk(nav_map, 1)
    return entries


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
    nav_href = ncx_href = None
    for item in root.findall(".//opf:manifest/opf:item", _NS):
        items[item.attrib["id"]] = item.attrib["href"]
        if "nav" in item.attrib.get("properties", ""):
            nav_href = item.attrib["href"]
        if item.attrib.get("media-type") == "application/x-dtbncx+xml":
            ncx_href = item.attrib["href"]
    spine = [
        items[ref.attrib["idref"]]
        for ref in root.findall(".//opf:spine/opf:itemref", _NS)
        if ref.attrib["idref"] in items
    ]
    return {"title": title, "author": author, "spine": spine,
            "nav_href": nav_href, "ncx_href": ncx_href}


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


_VOID_TAGS = {"img", "br", "hr", "meta", "link", "input", "source", "col"}

# Content that renders beside the prose rather than as part of it. Ebookmaker glues
# illustration captions INTO chapter headings — 34 of Pride and Prejudice's 65 — which
# is why its nav reads "I hope Mr. Bingley will like it. CHAPTER II."; and it injects
# 496 page-number spans mid-sentence into the same book.
_DROP_CLASSES = {"caption", "x-ebookmaker-pageno"}


def _classes(attrs: dict) -> set[str]:
    return set((attrs.get("class") or "").split())


def _drop_cap(attrs: dict) -> str:
    """An image standing in for a single letter contributes that letter.

    Pride and Prejudice sets the opening capital of 60 of its 61 chapters as an image,
    so every chapter began a letter short: "R. BENNET was among the earliest...". A
    one-character `alt` is a drop cap; anything longer is a described illustration and
    is not part of the prose."""
    alt = (attrs.get("alt") or "").strip()
    return alt if len(alt) == 1 else ""


MIN_DEPTH_ENTRIES = 3        # a level carrying fewer entries than this is not the unit


def boundary_depth(entries: list[dict]) -> int | None:
    """Which nav nesting level holds the book's divisions: the shallowest one that
    actually carries the book.

    Only 3 of 11 books nest at all, and in two of those the nesting is noise rather
    than structure — Sherlock Holmes has three depth-2 sections inside story I alone,
    Moby-Dick has sub-headings inside chapters 100 and 108. Treating every nav entry as
    a division promotes those to chapters; this keeps them inside their parent.

    A share-of-the-nav threshold was tried first and is wrong: in a deeply nested book
    the deepest level holds most of the entries, so Shakespeare's 812 SCENES outvoted
    its 44 works. Entry count alone gets every book in the corpus right, and it is one
    threshold instead of two."""
    levels = Counter(entry["level"] for entry in entries)
    if not levels:
        return None
    qualifying = [lv for lv in sorted(levels) if levels[lv] >= MIN_DEPTH_ENTRIES]
    return qualifying[0] if qualifying else min(levels)


class _BlockParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict] = []
        self._buf: list[str] = []
        self._kind = "para"
        self._skip_depth = 0
        self._pending_ids: list[str] = []

    def handle_starttag(self, tag, attrs):
        if self._skip_depth:                  # inside dropped content
            if tag not in _VOID_TAGS:         # track nesting so we close at the right depth
                self._skip_depth += 1
            return
        attrs = dict(attrs)
        if attrs.get("id"):
            # Held until a block is actually emitted, so a wrapper's id lands on the
            # heading it wraps — the Ebookmaker case, and the difference between
            # resolving 27% of this corpus's nav anchors and resolving 100%.
            self._pending_ids.append(attrs["id"])
        if tag == "img":
            self._buf.append(_drop_cap(attrs))
        elif tag in _LINE_BREAK_TAGS:
            self._buf.append(_BREAK)
        elif tag in _SKIP_TAGS or _classes(attrs) & _DROP_CLASSES:
            self._skip_depth = 1
        elif tag in _BLOCK_TAGS:
            self.close_pending()
            self._kind = "heading" if tag in HEADING_TAGS else "para"

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)      # <br/> never reaches handle_starttag

    def handle_endtag(self, tag):
        if self._skip_depth:
            self._skip_depth -= 1
        elif tag in _BLOCK_TAGS:
            self.close_pending()

    def handle_data(self, data):
        if not self._skip_depth:
            self._buf.append(data)

    def close_pending(self):
        text = _normalize_lines("".join(self._buf), self._kind)
        if text:
            self.blocks.append({"kind": self._kind, "text": text,
                                "ids": self._pending_ids})
            self._pending_ids = []       # only a real block consumes the ids
        self._buf = []
        self._kind = "para"


def _normalize_lines(raw: str, kind: str) -> str:
    """Collapse whitespace WITHIN each line, then keep the lines.

    Verse, letters and telegrams are line-structured, and a paragraph that renders as
    four lines should not arrive downstream as one. A heading is the exception: a title
    broken across two lines for typography ("CHAPTER I.<br/>MR. SHERLOCK HOLMES.") is
    still one title."""
    lines = [" ".join(line.split()) for line in raw.split(_BREAK)]
    lines = [line for line in lines if line]
    return (" " if kind == "heading" else "\n").join(lines)
