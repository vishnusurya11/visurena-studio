"""The mouth says the book's names (Jekyll ep01 review, 2026-10-13).

SOUND.md R5: "Enfield" was heard as "and field" (l28, in the master) and
"Anfield" (l20).  Commit 8c86859 taught the EAR to accept "and field" -- that
fixes the judge, not the mouth.  A book now files how its hard words are SAID in
`cast/say_lexicon.json`; the TTS input is respelled with it, while the line's
written text stays the text the ear scores against."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

from studio import voice_say
from studio.episode_spec import Line

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_say_lex", ROOT / "scripts" / "episode" / "say_lines.py")
say_lines = importlib.util.module_from_spec(spec)
sys.modules["ep_say_lex"] = say_lines
spec.loader.exec_module(say_lines)

LEXICON = {"Enfield": "Enn-feeld", "Utterson": "Utter-son"}


def file_lexicon(book: Path) -> None:
    (book / "cast").mkdir(parents=True, exist_ok=True)
    (book / "cast" / "say_lexicon.json").write_text(json.dumps(LEXICON), encoding="utf-8")


def test_a_book_files_how_its_names_are_said(tmp_path):
    file_lexicon(tmp_path)
    assert voice_say.say_lexicon(tmp_path) == LEXICON
    assert voice_say.say_lexicon(tmp_path / "nowhere") == {}


def test_the_spoken_text_is_respelled_whole_words_only():
    said = voice_say.respelled("Ashamed of his long tongue, Enfield held out his hand.", LEXICON)
    assert said == "Ashamed of his long tongue, Enn-feeld held out his hand."
    assert voice_say.respelled("Enfield's door; ENFIELD.", LEXICON) == "Enn-feeld's door; Enn-feeld."
    assert voice_say.respelled("Enfieldshire", LEXICON) == "Enfieldshire"


def test_the_tts_hears_the_respelling_and_the_record_keeps_the_book(tmp_path, monkeypatch):
    file_lexicon(tmp_path)
    sent = []

    def fake_say(text, timbre, emotion, seed, out, index=0, speaker=None, vector=None, **_):
        sent.append(text)
        return NS(seconds=2.0, seed=seed)

    monkeypatch.setattr(say_lines.voice_say, "say", fake_say)
    monkeypatch.setattr(say_lines, "line_reference", lambda book, records, line, attempt: tmp_path / "d.wav")
    line = Line(index=20, kind="narration", speaker="narrator", text="Enfield could see no harm.", shot=3)
    record = say_lines.render(tmp_path, NS(number=1), line, tmp_path, 0)
    assert sent == ["Enn-feeld could see no harm."]
    assert record["text"] == "Enfield could see no harm."
    assert record["said_as"] == "Enn-feeld could see no harm."
