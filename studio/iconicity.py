"""External iconicity: what Wikiquote's editors kept of a book.

Text statistics cannot tell which line a culture remembers; that is a fact
about reproduction history, and Wikiquote is the one public, licensed,
API-reachable record of it (research 1.4).  Editors also BOLD the famous
clause inside a longer quotation, which is a human "compress to twelve words"
already done for us.

The resolver walks the three places a public-domain book's quotes live: its
own page, a section of the author's page, a section of a character's page.
A film or television page is refused outright -- its lines belong to a
screenwriter, not the book.  One fetch per page revision: the cache is keyed
by `revid`, and offline the last cache ships flagged.

The file this writes, `analysis/iconicity.json`, is shared with the moment
level scores `trailer_story.load_iconicity` reads; that key is preserved.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib import parse, request
from urllib.error import URLError

API = "https://en.wikiquote.org/w/api.php"
USER_AGENT = "VisurenaStudio/0.1 (trailer iconicity; github.com/visurena)"
SCREEN = re.compile(r"\b(film|television|tv series|directed by|screenplay by)\b", re.I)
HEADING = re.compile(r"^(=+)\s*(.*?)\s*=+\s*$", re.M)
NOT_THE_WORK = re.compile(r"^(about|quotes about|external links|see also|cast|misattributed"
                          r"|disputed|attributed|unsourced)", re.I)
MATCH_FLOOR = 0.8


def default_fetch(params: dict) -> dict:
    """One MediaWiki API call over urllib; raises URLError when offline."""
    query = parse.urlencode({**params, "format": "json", "redirects": 1})
    req = request.Request(f"{API}?{query}", headers={"User-Agent": USER_AGENT})
    with request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def strip_markup(text: str) -> str:
    """Wikitext to plain words: links keep their label, emphasis and refs go."""
    text = re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", "", text, flags=re.S)
    text = re.sub(r"</?br\s*/?>", " ", text)
    text = re.sub(r"\{\{.*?\}\}", "", text, flags=re.S)
    text = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"\[\[(?:w:|wikipedia:)?([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"'{2,}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def lead_of(wikitext: str) -> str:
    """The prose before the first heading, without templates or file boxes."""
    head = wikitext.split("\n==", 1)[0]
    head = re.sub(r"\{\{.*?\}\}", "", head, flags=re.S)
    head = re.sub(r"^\[\[File:.*$", "", head, flags=re.M)
    return strip_markup(head)


def is_screen_page(wikitext: str) -> bool:
    """A page whose lead says film or television is an adaptation's page."""
    return bool(SCREEN.search(lead_of(wikitext)))


def _sections(wikitext: str) -> list[tuple[int, str, str]]:
    """(level, plain heading, body) for every heading, in page order."""
    marks = list(HEADING.finditer(wikitext))
    out = []
    for i, mark in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(wikitext)
        out.append((len(mark.group(1)), strip_markup(mark.group(2)), wikitext[mark.end():end]))
    return out


def section_for(wikitext: str, title: str) -> str | None:
    """The body under the heading naming this work, with its sub-sections."""
    want = re.sub(r"[^a-z0-9]", "", title.lower())
    sections = _sections(wikitext)
    for i, (level, heading, body) in enumerate(sections):
        if want not in re.sub(r"[^a-z0-9]", "", heading.lower()):
            continue
        parts = [body]
        for deeper_level, _, deeper in sections[i + 1:]:
            if deeper_level <= level:
                break
            parts.append(deeper)
        return "\n".join(parts)
    return None


def own_page_body(wikitext: str) -> str:
    """Everything on a book's own page that is the book speaking, not others
    speaking about it."""
    return "\n".join(body for _, heading, body in _sections(wikitext)
                     if not NOT_THE_WORK.match(heading))


def quotes_in(section: str) -> list[dict]:
    """Top-level bullets are quotations; `**` lines beneath are citations."""
    kept = []
    for line in section.splitlines():
        if not re.match(r"^\*\s*[^*\s]", line):
            continue
        raw = line[1:].strip()
        bolds = [strip_markup(b) for b in re.findall(r"'''(.+?)'''", raw)]
        text = strip_markup(raw)
        if text:
            kept.append({"text": text, "bold": bolds[0] if bolds else None, "bolds": bolds})
    return kept


def page_quotes(page: str, title: str, where: str, fetch) -> tuple[int, list[dict]] | None:
    """Parse one page; None when it is missing, a screen page, or has no
    section for this work."""
    doc = fetch({"action": "parse", "page": page, "prop": "wikitext|revid"})
    if "parse" not in doc:
        return None
    wikitext = doc["parse"]["wikitext"]["*"]
    if is_screen_page(wikitext):
        return None
    body = own_page_body(wikitext) if where == "book" else section_for(wikitext, title)
    if body is None:
        return None
    kept = [{**q, "page": page} for q in quotes_in(body)]
    return (int(doc["parse"]["revid"]), kept) if kept else None


def hops(title: str, author: str, characters: tuple[str, ...]) -> list[tuple[str, str]]:
    """The pages to try, in order of how directly they belong to the book."""
    out = [(title, "book"), (f"{title} (novel)", "book"), (author, "author")]
    out += [(name, "character") for name in characters]
    return out


def resolve(title: str, author: str, characters: tuple[str, ...], fetch) -> dict:
    """First page in hop order that yields quotations for this work."""
    for page, where in hops(title, author, characters):
        found = page_quotes(page, title, where, fetch)
        if found is not None:
            revid, kept = found
            return {"source": page, "where": where, "revid": revid, "n": len(kept), "kept": kept}
    return {"source": None, "where": None, "revid": None, "n": 0, "kept": []}


def revid_of(page: str, fetch) -> int | None:
    """The cheap call: the page's current revision, or None if it is gone."""
    doc = fetch({"action": "query", "prop": "revisions", "rvprop": "ids", "titles": page})
    for entry in doc.get("query", {}).get("pages", {}).values():
        if entry.get("revisions"):
            return int(entry["revisions"][0]["revid"])
    return None


def cache_path(book_dir: Path) -> Path:
    return Path(book_dir) / "analysis" / "iconicity.json"


def load_cache(book_dir: Path) -> dict:
    path = cache_path(book_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_cache(book_dir: Path, doc: dict) -> None:
    """Merge over the existing file so the scene-level scores survive."""
    path = cache_path(book_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    merged = {**load_cache(book_dir), **doc}
    path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_wikiquote(title: str, author: str, characters: tuple[str, ...] = (),
                    book_dir: Path | None = None, fetch=default_fetch) -> dict:
    """The book's kept quotations, from the cache unless its page moved on.

    Offline, the cache ships with `offline: True`; with no cache the result is
    empty and flagged, and the slate runs on text signals alone.
    """
    cached = load_cache(book_dir) if book_dir else {}
    try:
        if cached.get("source") and revid_of(cached["source"], fetch) == cached.get("revid"):
            return {**cached, "offline": False}
        doc = {**resolve(title, author, characters, fetch), "offline": False}
    except URLError:
        doc = {**cached, "offline": True} if cached.get("kept") else \
            {"source": None, "where": None, "revid": None, "n": 0, "kept": [], "offline": True}
    if book_dir and not doc["offline"]:
        write_cache(book_dir, doc)
    return doc


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", text.lower().replace("’", "'")))


def token_overlap(a: str, b: str) -> float:
    """Jaccard over word sets: order-free, so a re-punctuated line still hits."""
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def units_of(text: str) -> list[str]:
    """The pieces a quotation can be reproduced by: its sentences and any
    quoted span, since editors keep the speech tag ("...," he said) and a
    screenplay drops it."""
    sentences = [u for u in re.split(r"(?<=[.!?])\s+", text) if u.strip()]
    quoted = re.findall(r"[\"“]([^\"”]{6,})[\"”]", text)
    return [text] + sentences + quoted


def match_kept(line: str, kept: list[dict], floor: float = MATCH_FLOOR) -> dict | None:
    """The kept quotation this line reproduces, if any.

    Both sides are compared unit by unit, because a screenplay line is usually
    ONE sentence of a longer bullet and a bullet is often one sentence of a
    longer speech.  Returns {"kept": True, "bold": bool, "page": ...}.
    """
    mine = units_of(line)
    for quote in kept:
        bolds = bold_clauses(quote)
        theirs = units_of(quote["text"]) + bolds
        if any(token_overlap(a, b) >= floor for a in mine for b in theirs):
            is_bold = any(token_overlap(a, b) >= floor for a in mine for b in bolds)
            return {"kept": True, "bold": is_bold, "page": quote.get("page")}
    return None


def bold_clauses(quote: dict) -> list[str]:
    """Every editor-emphasised clause; older caches carry only the first."""
    if quote.get("bolds"):
        return list(quote["bolds"])
    return [quote["bold"]] if quote.get("bold") else []
