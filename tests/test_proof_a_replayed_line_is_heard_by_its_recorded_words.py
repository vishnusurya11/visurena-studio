"""A replayed line is heard by the words it was recorded with (rehearsal window 2, 2026-10-21).

The whisper memo is keyed by a wav's BYTES, filled from ep01's delivered lines.  In a sandbox the
fake ComfyUI serves the recorded line re-encoded (`stretch_wav`, even at tempo 1), and voice_say
post-processes and pads it, so no l{NN}.wav of a replay ever has the recorded bytes: window 2's
first ask (l00, sha 68f55678) was `canned`, an EMPTY transcript.  Every line would then fail the
words gate on every round, and step 04 refuses.  So a byte miss falls back to the line's own text
(lines.json beside the clip): when it is a recorded line's text, the ear answers that recording's
transcript, labelled `substituted` (a stand-in, so a quality row on it is mechanism).  Other words
stay canned."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.proof import rehearse
from studio.rehearsal import asserts, fake_workers, workers

WORDS = "Only one man holds the key to this door."


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def a_line(tmp_path: Path, text: str = WORDS, data: bytes = b"re-encoded") -> Path:
    lines = tmp_path / "book" / "episodes" / "ep01" / "audio" / "lines"
    lines.mkdir(parents=True)
    (lines / "l00.wav").write_bytes(data)
    rows = [{"index": 0, "text": text, "rel_path": "episodes/ep01/audio/lines/l00.wav"}]
    (lines / "lines.json").write_text(json.dumps(rows), encoding="utf-8")
    return lines / "l00.wav"


def memo() -> dict:
    return {sha(b"recorded"): WORDS, workers.text_key(WORDS): WORDS + " (heard)"}


def test_a_line_whose_bytes_moved_is_heard_by_its_recorded_words(tmp_path):
    clip = a_line(tmp_path)
    assert workers.answer_whisper({"clip": str(clip)}, memo()) == (
        {"text": WORDS + " (heard)"}, "substituted", workers.text_key(WORDS))


def test_a_line_with_other_words_is_still_canned(tmp_path):
    clip = a_line(tmp_path, text="Indeed. And what was that?")
    said, label, _ = workers.answer_whisper({"clip": str(clip)}, memo())
    assert (said, label) == ({"text": ""}, "canned")


def test_the_recorded_bytes_still_answer_exact(tmp_path):
    clip = a_line(tmp_path, data=b"recorded")
    assert workers.answer_whisper({"clip": str(clip)}, memo())[:2] == ({"text": WORDS}, "exact")


def test_the_cpu_ear_hears_a_moved_line_the_same_way(tmp_path):
    clip, box = a_line(tmp_path), tmp_path / "box"
    (box / "memos").mkdir(parents=True)
    (box / "memos" / "whisper.json").write_text(json.dumps(memo()), encoding="utf-8")
    listen = fake_workers.memo_ear({"memos": str(box / "memos")}, box)()
    assert listen(clip) == WORDS + " (heard)"
    row = json.loads((box / "workers.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert row["label"] == "substituted"


def index_doc() -> dict:
    wav = "book/episodes/ep01/audio/lines/l00.wav"
    return {"entries": [{"kind": "tts_line", "path": wav, "fields": {"index": 0, "text": WORDS}},
                        {"kind": "transcript", "key": sha(b"recorded"), "fields": {"wav": wav}},
                        {"kind": "tts_line", "path": "book/episodes/ep01/audio/lines/l09.wav",
                         "fields": {"text": "never heard"}}]}


def test_each_recorded_line_gives_the_sandbox_memo_one_row_by_its_words():
    assert rehearse.text_rows(index_doc(), {sha(b"recorded"): WORDS}) == {workers.text_key(WORDS): WORDS}


def test_the_staged_whisper_memo_carries_the_rows_by_words(tmp_path, monkeypatch):
    memos, index, box = tmp_path / "memos", tmp_path / "rec.json", tmp_path / "box"
    memos.mkdir()
    box.mkdir()
    (memos / "whisper.json").write_text(json.dumps({sha(b"recorded"): WORDS}), encoding="utf-8")
    index.write_text(json.dumps(index_doc()), encoding="utf-8")
    (box / "rehearsal.json").write_text(json.dumps({"run_id": "x"}), encoding="utf-8")
    monkeypatch.setattr(rehearse, "MEMOS", memos)
    monkeypatch.setattr(rehearse, "RECORDINGS", index)
    rehearse.stage_inputs(box)
    staged = json.loads((box / "memos" / "whisper.json").read_text(encoding="utf-8"))
    assert staged == {sha(b"recorded"): WORDS, workers.text_key(WORDS): WORDS}
    assert json.loads((memos / "whisper.json").read_text(encoding="utf-8")) == {sha(b"recorded"): WORDS}


def test_a_transcript_heard_by_its_words_is_a_stand_in():
    assert asserts.stands_in({"worker_substituted": 3})
