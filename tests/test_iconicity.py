"""External iconicity: what Wikiquote's editors kept of a book.

The fixtures are RECORDED MediaWiki responses (2026-09-04): the book has no
page, the author's page has no section for it, and the character page carries
the section -- the same three-hop resolution the research measured on Scarlet.
Nothing here touches the network; `fetch` is injected.
"""
from __future__ import annotations

import json
from pathlib import Path
from urllib.error import URLError

import pytest

from studio import iconicity
from studio.iconicity import (fetch_wikiquote, is_screen_page, lead_of,
                              quotes_in, section_for)

FIXTURES = Path(__file__).parent / "fixtures"
PAGES = {
    "A Study in Scarlet": "wikiquote_a_study_in_scarlet.json",
    "A Study in Scarlet (novel)": "wikiquote_a_study_in_scarlet.json",
    "Arthur Conan Doyle": "wikiquote_arthur_conan_doyle.json",
    "Sherlock Holmes": "wikiquote_sherlock_holmes.json",
    "Sherlock (TV series)": "wikiquote_sherlock_tv_series.json",
}


def recorded(page: str) -> dict:
    name = PAGES.get(page, "wikiquote_a_study_in_scarlet.json")
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))["response"]


class FakeWiki:
    """Routes the two API shapes the module uses to the recorded responses."""

    def __init__(self, revid_override: dict | None = None):
        self.calls: list[dict] = []
        self.revid_override = revid_override or {}

    def __call__(self, params: dict) -> dict:
        self.calls.append(dict(params))
        if params["action"] == "parse":
            doc = json.loads(json.dumps(recorded(params["page"])))
            if "parse" in doc and params["page"] in self.revid_override:
                doc["parse"]["revid"] = self.revid_override[params["page"]]
            return doc
        page = params["titles"]
        doc = recorded(page)
        if "parse" not in doc:
            return {"query": {"pages": {"-1": {"title": page, "missing": ""}}}}
        revid = self.revid_override.get(page, doc["parse"]["revid"])
        return {"query": {"pages": {"1": {"title": page, "revisions": [{"revid": revid}]}}}}


def wikitext(page: str) -> str:
    return recorded(page)["parse"]["wikitext"]["*"]


class TestParsing:
    def test_lead_ignores_templates_and_file_captions(self):
        """The Holmes lead links to '(2009 film)' in a See-also template; the
        word must not make the page a film page."""
        lead = lead_of(wikitext("Sherlock Holmes"))
        assert "2009 film" not in lead
        assert "See also" not in lead

    def test_section_for_finds_the_book_heading(self):
        body = section_for(wikitext("Sherlock Holmes"), "A Study in Scarlet")
        assert "You have been in Afghanistan, I perceive" in body
        assert "The Sign of the Four" not in body

    def test_section_for_is_none_when_absent(self):
        assert section_for(wikitext("Arthur Conan Doyle"), "A Study in Scarlet") is None

    def test_quotes_in_keeps_bullets_and_bold(self):
        kept = quotes_in(section_for(wikitext("Sherlock Holmes"), "A Study in Scarlet"))
        assert len(kept) == 18
        assert sum(1 for q in kept if q["bold"]) == 9
        afghan = next(q for q in kept if "Afghanistan" in q["text"])
        assert afghan["bold"] == "You have been in Afghanistan, I perceive"

    def test_quotes_in_strips_markup(self):
        kept = quotes_in(section_for(wikitext("Sherlock Holmes"), "A Study in Scarlet"))
        nature = next(q for q in kept if "broad as" in q["text"])
        assert "[[" not in nature["text"] and "'''" not in nature["text"]
        assert nature["text"].startswith("One's ideas must be as broad as Nature")


class TestResolver:
    def test_resolver_walks_book_author_character(self, tmp_path):
        wiki = FakeWiki()
        doc = fetch_wikiquote("A Study in Scarlet", "Arthur Conan Doyle",
                              characters=("Sherlock Holmes",), book_dir=tmp_path, fetch=wiki)
        assert doc["source"] == "Sherlock Holmes"
        assert doc["where"] == "character"
        assert doc["n"] == 18
        assert doc["revid"] == 3986154

    def test_resolver_refuses_film_page(self):
        assert is_screen_page(wikitext("Sherlock (TV series)"))
        assert not is_screen_page(wikitext("Sherlock Holmes"))
        assert not is_screen_page(wikitext("Arthur Conan Doyle"))

    def test_resolver_refuses_film_page_as_a_character_hop(self, tmp_path):
        wiki = FakeWiki()
        doc = fetch_wikiquote("A Study in Pink", "Nobody", characters=("Sherlock (TV series)",),
                              book_dir=tmp_path, fetch=wiki)
        assert doc["source"] is None and doc["n"] == 0

    def test_iconicity_file_is_written_beside_the_analysis(self, tmp_path):
        fetch_wikiquote("A Study in Scarlet", "Arthur Conan Doyle",
                        characters=("Sherlock Holmes",), book_dir=tmp_path, fetch=FakeWiki())
        path = tmp_path / "analysis" / "iconicity.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        assert doc["kept"][1]["text"] == "You have been in Afghanistan, I perceive"
        assert doc["kept"][1]["page"] == "Sherlock Holmes"

    def test_existing_scene_scores_survive_a_fetch(self, tmp_path):
        """The file already carries the moment-level scores load_iconicity reads."""
        path = tmp_path / "analysis" / "iconicity.json"
        path.parent.mkdir()
        path.write_text(json.dumps({"scenes": {"5": {"score": 0.9}}}), encoding="utf-8")
        fetch_wikiquote("A Study in Scarlet", "Arthur Conan Doyle",
                        characters=("Sherlock Holmes",), book_dir=tmp_path, fetch=FakeWiki())
        assert json.loads(path.read_text(encoding="utf-8"))["scenes"] == {"5": {"score": 0.9}}


class TestCache:
    def _fetch(self, tmp_path, wiki):
        return fetch_wikiquote("A Study in Scarlet", "Arthur Conan Doyle",
                               characters=("Sherlock Holmes",), book_dir=tmp_path, fetch=wiki)

    def test_iconicity_cache_invalidates_on_new_revid(self, tmp_path):
        first = FakeWiki()
        self._fetch(tmp_path, first)
        parses = [c for c in first.calls if c["action"] == "parse"]
        assert len(parses) == 4           # book, book (novel), author, character

        same = FakeWiki()
        self._fetch(tmp_path, same)
        assert [c["action"] for c in same.calls] == ["query"]   # one revid check, no parse

        newer = FakeWiki(revid_override={"Sherlock Holmes": 4000000})
        doc = self._fetch(tmp_path, newer)
        assert any(c["action"] == "parse" for c in newer.calls)
        assert doc["revid"] == 4000000

    def test_offline_returns_the_cache_flagged(self, tmp_path):
        self._fetch(tmp_path, FakeWiki())

        def offline(params):
            raise URLError("no network")
        doc = self._fetch(tmp_path, offline)
        assert doc["n"] == 18 and doc["offline"] is True

    def test_offline_with_no_cache_is_empty_and_flagged(self, tmp_path):
        def offline(params):
            raise URLError("no network")
        doc = self._fetch(tmp_path, offline)
        assert doc["n"] == 0 and doc["kept"] == [] and doc["offline"] is True


class TestMatching:
    def test_token_overlap_is_symmetric_and_bounded(self):
        a = "You have been in Afghanistan, I perceive."
        b = "You have been in Afghanistan I perceive"
        assert iconicity.token_overlap(a, b) == 1.0
        assert iconicity.token_overlap(a, "Nothing at all here.") < 0.2

    def test_a_bold_clause_matches_the_screenplay_line(self):
        kept = [{"text": "I had neither kith nor kin in England, and was therefore free.",
                 "bold": "You have been in Afghanistan, I perceive", "page": "x"}]
        hit = iconicity.match_kept("You have been in Afghanistan, I perceive.", kept)
        assert hit is not None and hit["bold"]

    def test_a_line_short_of_the_threshold_does_not_match(self):
        kept = [{"text": "It is a capital mistake to theorize before you have all the evidence.",
                 "bold": None, "page": "x"}]
        assert iconicity.match_kept("It is a mistake.", kept) is None


def test_default_fetch_is_urllib_and_sets_a_user_agent(monkeypatch):
    seen = {}

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b'{"ok": true}'

    def fake_urlopen(req, timeout=None):
        seen["ua"] = req.get_header("User-agent")
        seen["url"] = req.full_url
        return Resp()
    monkeypatch.setattr(iconicity.request, "urlopen", fake_urlopen)
    assert iconicity.default_fetch({"action": "parse", "page": "X Y"}) == {"ok": True}
    assert "VisurenaStudio" in seen["ua"]
    assert "page=X+Y" in seen["url"] and "format=json" in seen["url"]


class TestCoverageScript:
    def _book(self, tmp_path):
        from scripts.analysis import iconicity_coverage as script
        book = tmp_path / "20260901000001_book"
        (book / "screenplay/feature").mkdir(parents=True)
        scenes = [{"number": 1, "elements": [
            {"kind": "dialogue", "text": "You have been in Afghanistan, I perceive.", "character": "h"},
            {"kind": "dialogue", "text": "Whatever have you been doing with yourself?", "character": "s"},
            {"kind": "action", "text": "A hansom rolls through London traffic."}]}]
        (book / "screenplay/feature/screenplay.json").write_text(
            json.dumps({"scenes": scenes}), encoding="utf-8")
        fetch_wikiquote("A Study in Scarlet", "Arthur Conan Doyle",
                        characters=("Sherlock Holmes",), book_dir=book, fetch=FakeWiki())
        return script, book

    def test_coverage_counts_matched_screenplay_lines(self, tmp_path):
        script, book = self._book(tmp_path)
        row = script.coverage(book)
        assert row["lines"] == 2 and row["kept"] == 18
        assert row["matched"] == 1 and row["bold"] == 1
        assert row["examples"] == ["You have been in Afghanistan, I perceive."]

    def test_book_identity_reads_title_author_and_leads(self, tmp_path):
        script, book = self._book(tmp_path)
        (book / "source").mkdir()
        (book / "source/book.json").write_text(json.dumps(
            {"title": "A Study in Scarlet", "author": "Arthur Conan Doyle"}), encoding="utf-8")
        (book / "analysis/registry.json").write_text(json.dumps({"characters": [
            {"name": "Sherlock Holmes", "role": "protagonist"},
            {"name": "Wiggins", "role": "minor"}]}), encoding="utf-8")
        assert script.book_identity(book) == ("A Study in Scarlet", "Arthur Conan Doyle",
                                              ("Sherlock Holmes",))

    def test_main_prints_one_row_per_book(self, tmp_path, capsys, monkeypatch):
        script, book = self._book(tmp_path)
        monkeypatch.setattr(script, "analysed_books", lambda: [book])
        script.main([])
        out = capsys.readouterr().out
        assert "20260901000001_book" in out and "thin" in out
