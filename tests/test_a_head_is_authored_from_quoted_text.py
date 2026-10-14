"""A dossier head is authored from the book's quoted words (FINAL §1 Open, C1_L §3).

Jekyll, Hyde and Utterson were refused "head unauthored": the profile writer
found no hair, beard or hat in Stevenson, so their sheets came out three
near-identical men.  `analysis/heads.json` authors each head with the quotes it
rests on; `studio.head_author` lands it in the dossier's `physical` (where the
look table reads a head) only when every quote is in its chapter at 0.85, the
words name hair, facial hair and a hat, and no two bound characters share a
face (hair family + facial hair).  Deterministic: no model call.
"""
from __future__ import annotations

import json

import pytest

from studio import head_author

TEXT = {3: "a large, well-made, smooth-faced man of fifty, with something of a slyish cast",
        2: "Mr. Hyde was pale and dwarfish, he gave an impression of deformity"}
JEKYLL = {"words": "A large, well-made man of fifty. Iron-grey hair; smooth-faced and clean-shaven; a black silk top hat.",
          "sources": [{"chapter": 3, "quote": "a large, well-made, smooth-faced man of fifty"}]}
HYDE = {"words": "Small, pale and dwarfish. Coarse black hair; short black side-whiskers; a low black felt hat.",
        "sources": [{"chapter": 2, "quote": "Hyde was pale and dwarfish"}]}


def test_a_quote_not_in_its_chapter_is_named():
    bad = [{"chapter": 3, "quote": "a tall red-bearded sailor"}, *JEKYLL["sources"]]
    assert head_author.unquoted(bad, TEXT.get) == ["ch3: a tall red-bearded sailor"]


def test_words_must_name_hair_face_and_hat():
    assert head_author.missing_layers(JEKYLL["words"]) == []
    assert head_author.missing_layers("A small man. Coarse black hair.") == ["face", "headwear"]


def test_two_characters_with_one_face_clash():
    faces = {"jekyll": head_author.face_of(JEKYLL["words"]), "hyde": head_author.face_of(HYDE["words"]),
             "enfield": head_author.face_of("receding grey hair, clean-shaven")}
    assert faces["jekyll"] == ("grey", "none") and faces["hyde"] == ("dark", "sideburns")   # side-whiskers, never a moustache (2026-10-14)
    assert head_author.clashes(faces, authored={"jekyll", "hyde"}) == ["jekyll and enfield share grey hair, none"]


def test_the_head_replaces_the_profile_writers_silence():
    physical = "A lawyer who walks London. It gives no confirmed description of his hair, face, or clothing."
    out = head_author.with_head(physical, "Lank fair hair; clean-shaven; a black bowler hat.", old="")
    assert out == "A lawyer who walks London. Lank fair hair; clean-shaven; a black bowler hat."


def test_a_re_run_replaces_the_old_head():
    physical = head_author.with_head("A doctor.", "Grey hair; clean-shaven; a top hat.", old="")
    out = head_author.with_head(physical, "White hair; clean-shaven; a top hat.", old="Grey hair; clean-shaven; a top hat.")
    assert out == "A doctor. White hair; clean-shaven; a top hat."


def book(tmp_path, heads):
    chars = tmp_path / "analysis" / "characters"
    chars.mkdir(parents=True)
    (tmp_path / "analysis" / "chapters").mkdir()
    for n, text in TEXT.items():
        (tmp_path / "analysis" / "chapters" / f"ch_{n:02d}.json").write_text(json.dumps({"text": text}), encoding="utf-8")
    for who in heads:
        (chars / f"{who}.json").write_text(json.dumps({"id": who, "profile": {"physical": "A man."}}), encoding="utf-8")
    (tmp_path / "analysis" / "heads.json").write_text(json.dumps(heads), encoding="utf-8")
    return tmp_path


def test_apply_writes_every_head_and_its_sources(tmp_path):
    root = book(tmp_path, {"henry_jekyll": JEKYLL, "edward_hyde": HYDE})
    assert head_author.apply(root, rows=[]) == ["henry_jekyll", "edward_hyde"]
    card = json.loads((root / "analysis" / "characters" / "edward_hyde.json").read_text(encoding="utf-8"))
    assert card["profile"]["physical"] == f"A man. {HYDE['words']}"
    assert card["profile"]["head"] == HYDE


def test_apply_refuses_before_it_writes(tmp_path):
    twin = {**HYDE, "words": "Iron-grey hair; clean-shaven; a bowler hat."}
    root = book(tmp_path, {"henry_jekyll": JEKYLL, "edward_hyde": twin})
    with pytest.raises(SystemExit, match="share grey hair"):
        head_author.apply(root, rows=[])
    card = json.loads((root / "analysis" / "characters" / "henry_jekyll.json").read_text(encoding="utf-8"))
    assert card["profile"]["physical"] == "A man."


def test_a_bound_row_counts_as_a_face(tmp_path):
    root = book(tmp_path, {"edward_hyde": HYDE})
    rows = [{"entity_id": "poole", "physical": "thick black hair, with short black side-whiskers"}]
    with pytest.raises(SystemExit, match="edward_hyde and poole"):
        head_author.apply(root, rows=rows)


def test_the_script_authors_against_the_bound_rows(tmp_path, monkeypatch, capsys):
    from scripts.refs import author_heads
    root = book(tmp_path, {"edward_hyde": HYDE})
    (root / "refs").mkdir()
    (root / "refs" / "refs.json").write_text(json.dumps({"refs": [
        {"kind": "character", "entity_id": "poole", "physical": "thinning sandy hair, with a short greying beard"}]}),
        encoding="utf-8")
    monkeypatch.setattr(author_heads.episode_home, "book_dir", lambda book_id: root)
    assert author_heads.main("jh") == 0
    assert "head: edward_hyde" in capsys.readouterr().out


def test_a_woman_and_a_man_never_share_a_face(tmp_path):
    """Jekyll's walk-ons (2026-10-12): the silvery-haired housekeeper and grey,
    clean-shaven Jekyll share hair family and 'none', yet no reader confuses them.
    A head names its `kind` (default man); a row its gender; faces clash within a kind."""
    keeper = {"kind": "woman", "words": "An old woman. Silvery-grey hair; smooth-cheeked; a black lace cap.",
              "sources": [{"chapter": 2, "quote": "Hyde was pale and dwarfish"}]}
    root = book(tmp_path, {"henry_jekyll": JEKYLL, "hyde_housekeeper": keeper})
    assert head_author.apply(root, rows=[]) == ["henry_jekyll", "hyde_housekeeper"]
    rows = [{"entity_id": "maid", "gender": "female", "physical": "iron-grey hair, clean-shaven"}]
    with pytest.raises(SystemExit, match="hyde_housekeeper and maid"):
        head_author.apply(root, rows=rows)
