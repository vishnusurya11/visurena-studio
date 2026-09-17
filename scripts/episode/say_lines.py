#!/usr/bin/env python
"""Every line of an episode, in its character's designed voice, and LISTENED to.

    uv run python scripts/episode/say_lines.py <codex_id> <episode>

The voice is the book-level cast voice (`cast/<who>/voice/design.wav`), cloned
per line by Qwen3-TTS so thirteen lines are one speaker.  Two things are never
trusted from text: the seconds (measured from the file) and the words (Whisper
reads the clip back; a line that came out wrong is re-rolled once, then
refused).  Brigham Young's hallucinated line is why the second one exists.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, voice, voice_ear, voice_qc, voice_say
from studio.episode_spec import Episode, Line

SEED_BASE = 71000
TRIES = 2
ENGINE = "indextts2"
"""MEASURED 2026-09-10 on one Watson line against his designed voice (ECAPA
cosine): IndexTTS2 0.799, Qwen3-TTS clone 0.728; both word-perfect.  IndexTTS2
is ~4x slower (111 s vs 26 s cold) and the more accurate voice, which is
what the owner asked for."""
SIMILAR = 0.70
"""ECAPA cosine a line of four seconds or more must reach against the designed
voice.  Between the two engines' measured scores; a line under it is not that
character.  Shorter lines get `similar_floor`."""

FLOORS = ((4.0, SIMILAR), (2.0, 0.65), (0.0, 0.60))
"""(at least this many seconds, this floor).

MEASURED on episode 10 by truncating a GENUINE line and scoring the truncation
against its own design -- same voice, less audio:

    Ferrier ep08/l25  5.27 s 0.815 | 1.5 s 0.690 | 2.5 s 0.771 | 4.0 s 0.819
    Watson  ep10/l26  5.84 s 0.824 | 1.5 s 0.640 | 2.5 s 0.709 | 4.0 s 0.796
    Young   ep10/l16  5.42 s 0.853 | 1.5 s 0.677 | 2.5 s 0.708 | 4.0 s 0.826

A correct voice loses ~0.05 at 2.5 s and 0.12-0.18 at 1.5 s.  Lucy's four lines
run 1.5-2.6 s and three sit under 0.75 with a design that reads 0.864 on a
2.6 s line.  A flat 0.70 refuses the TRUE voice under two seconds; a line that
short cannot be judged harder than the encoder can hear it."""

EPISODE_VOICE = 0.75
"""Line-vs-line ECAPA cosine an ALTERNATE-reference render must reach against
the speaker's other passed lines in the same episode.

MEASURED on episode 10: Ferrier's l27, cloned from ep08/l25 on its fourth try,
passed the design floor at 0.701 -- by 0.001 -- and measured 0.585 / 0.589 /
0.588 against the two lines he speaks 25 s earlier in the same room, while
those two sit at 0.839 against each other and his lines across two episodes
at 0.79-0.90.  The listener never hears the design clip; the listener hears
this line after the last one.  0.75 is under every genuine pair and over the
one that was a different man."""


def similar_floor(seconds: float) -> float:
    """The similarity a line of `seconds` must reach: the measured truncation loss."""
    return next(floor for at, floor in FLOORS if seconds >= at)


def episode_voice(book: Path, records: dict, record: dict, similarity=None) -> float | None:
    """Mean line-vs-line similarity of an alternate-reference render against the
    speaker's other PASSED lines in this episode.  None for a design-clip render
    (nothing to judge) and when there is no other passed line (nothing to
    compare it to)."""
    if record.get("reference", "design.wav") == "design.wav":
        return None
    score = similarity or voice_ear.similarity
    mine = book / record["rel_path"]
    others = [book / r["rel_path"] for i, r in records.items()
              if r.get("speaker") == record["speaker"] and r.get("passed")
              and i != record["index"] and (book / r["rel_path"]).exists()]
    if not others:
        return None
    return round(sum(float(score(mine, other)) for other in others) / len(others), 3)


def alternate_ok(score: float | None) -> bool:
    """An alternate-reference render is the man in the room, or it is not kept."""
    return score is None or score >= EPISODE_VOICE


def reference_for(book: Path, speaker: str) -> Path:
    """The cast voice, with its spoken passage written beside it for the clone."""
    folder = book / "cast" / speaker / "voice"
    clip = folder / "design.wav"
    if not clip.exists():
        raise FileNotFoundError(f"{speaker} has no cast voice at {clip}")
    text = clip.with_suffix(".txt")
    if not text.exists():
        sheet = episode_home.read_json(folder / "voice.json")
        text.write_text(sheet["passage"], encoding="utf-8")
    return clip


BEST_REFERENCE_FLOOR = 0.75


def best_line_reference(records: dict, speaker: str, exclude: int | None) -> int | None:
    """The index of the speaker's best PASSED line (similarity >= 0.75), or None."""
    good = [(r["similarity"], i) for i, r in records.items()
            if r.get("speaker") == speaker and r.get("passed") and i != exclude
            and r.get("similarity", 0.0) >= BEST_REFERENCE_FLOOR]
    return max(good)[1] if good else None


def other_episode_records(book: Path) -> list[dict]:
    """Every line record in every OTHER episode's lines.json on disk."""
    out = []
    for path in sorted(book.glob("episodes/ep*/audio/lines/lines.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        rows = doc["lines"] if isinstance(doc, dict) and "lines" in doc else doc
        out += [r for r in rows if isinstance(r, dict)]
    return out


def book_best_reference(book: Path, records: dict, speaker: str, exclude: int | None) -> Path | None:
    """The speaker's best PASSED line anywhere in the BOOK, at or over the floor,
    with its text written beside it for the clone. None if nothing qualifies.

    MEASURED building episode 10: John Ferrier's line 27 rendered at 0.63-0.69
    against the 0.70 floor eight times, under four wordings and three redo seeds.
    The third-try rule wanted his own best line (>= 0.75) and this episode had
    none -- his two passing lines sit at 0.71 and 0.74 -- so every third try
    went back to the design clip and came back the same. Episode 8 has him at
    0.815. A cast voice is a book-level asset, so the rule sees the book."""
    here = [(r.get("similarity", 0.0), r["rel_path"], r["text"]) for i, r in records.items()
            if r.get("speaker") == speaker and r.get("passed") and i != exclude]
    there = [(r.get("similarity", 0.0), r["rel_path"], r["text"]) for r in other_episode_records(book)
             if r.get("speaker") == speaker and r.get("passed") and (book / r["rel_path"]).exists()]
    good = [g for g in here + there if g[0] >= BEST_REFERENCE_FLOOR]
    if not good:
        return None
    _, rel, text = max(good)
    clip = book / rel
    clip.with_suffix(".txt").write_text(text, encoding="utf-8")
    return clip


def line_reference(book: Path, records: dict, line: Line, attempt: int) -> Path:
    """The design clip for the first two tries; from the third, the speaker's own
    best line anywhere in the book (its text written beside it for the clone)."""
    best = book_best_reference(book, records, line.speaker, line.index) if attempt >= 2 else None
    return best if best is not None else reference_for(book, line.speaker)


def seed_for(episode: int, line: Line, attempt: int) -> int:
    return SEED_BASE + episode * 1000 + line.index * 10 + attempt


def render(book: Path, episode: Episode, line: Line, out_dir: Path, attempt: int,
           records: dict | None = None) -> dict:
    """One line's file and its measured seconds; nothing listened to yet."""
    out = out_dir / f"l{line.index:02d}.wav"
    reference = line_reference(book, records or {}, line, attempt)
    seed = seed_for(episode.number, line, attempt)
    if ENGINE == "indextts2":
        said = voice_say.say(line.text, reference, reference, seed, out,
                             index=line.index, speaker=line.speaker)
    else:
        said = voice.clone_line(reference, line.text, seed, out, index=line.index, speaker=line.speaker)
    return {"index": line.index, "speaker": line.speaker, "kind": line.kind, "shot": line.shot,
            "text": line.text, "rel_path": episode_home.relative(book, out), "seconds": said.seconds,
            "seed": said.seed, "tries": attempt + 1, "reference": reference.name}


def listen_all(records: list[dict], book: Path, listen, among: dict | None = None) -> list[int]:
    """Read every clip back; return the indices that did not say their line.

    All the renders first, then all the listening: every swap between the
    TTS and the Whisper model costs minutes off the HDD, so thirteen lines
    pay two swaps here instead of twenty-six.  `among` is the whole episode's
    records, which an alternate-reference render is judged against."""
    among = among if among is not None else {r["index"]: r for r in records}
    failed = []
    for record in records:
        clip = book / record["rel_path"]
        verdict = voice_qc.check(clip, record["text"], transcribe=listen)
        similarity = voice_ear.similarity(reference_for(book, record["speaker"]), clip)
        floor, room = similar_floor(verdict.seconds), episode_voice(book, among, record)
        passed = verdict.passed and similarity >= floor and alternate_ok(room)
        record.update(heard=verdict.heard, error_rate=verdict.error_rate, why=verdict.why,
                      similarity=round(float(similarity), 3), floor=floor,
                      episode_voice=room, passed=passed)
        if not passed:
            failed.append(record["index"])
    return failed


def keep_best(new: dict, previous: dict | None, wav: Path) -> dict:
    """A redo never makes a line worse: the try with the higher similarity
    stays on disk as l{NN}.wav, the other is deleted.  An alternate-reference
    render that is not the man in the room never wins, whatever it scored
    against the design clip."""
    prev_wav = wav.with_suffix(".prev.wav")
    if previous is None or not prev_wav.exists():
        return new
    if alternate_ok(new.get("episode_voice")) and \
            new.get("similarity", 0.0) >= previous.get("similarity", 0.0):
        prev_wav.unlink()
        return new
    wav.unlink(missing_ok=True)
    prev_wav.rename(wav)
    return dict(previous, tries=new.get("tries", previous.get("tries", 0)))


def main(book_id: str, number: int, redo: list[int] | None = None) -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    out_dir = episode_home.lines_dir(book, number)
    sheet = out_dir / "lines.json"
    records = {r["index"]: r for r in episode_home.read_json(sheet)} if sheet.exists() else {}
    for line in episode.lines:  # a line whose TEXT changed is a new line (reviewer 5's re-cut)
        have = records.get(line.index)
        if have and have.get("text") != line.text:
            records.pop(line.index)
            (out_dir / f"l{line.index:02d}.wav").unlink(missing_ok=True)
    previous = {}
    for index in redo or []:  # a fresh seed for a line the ear rejected (l32 "naughty", l20 clipped)
        if index in records:
            previous[index] = dict(records[index])
            records[index]["tries"] = records[index].get("tries", 0) + 1
            records[index].pop("passed", None)
            wav = out_dir / f"l{index:02d}.wav"
            if wav.exists():
                wav.replace(wav.with_suffix(".prev.wav"))
    todo = [line for line in episode.lines if not records.get(line.index, {}).get("passed")]
    for attempt in range(TRIES):
        for line in todo:
            have = records.get(line.index)
            if attempt == 0 and have and "passed" not in have and (out_dir / f"l{line.index:02d}.wav").exists():
                have["rel_path"] = episode_home.relative(book, out_dir / f"l{line.index:02d}.wav")
                continue  # rendered but never listened to: reuse the file
            prior = records.get(line.index, {}).get("tries", 0) if attempt == 0 else 0
            records[line.index] = render(book, episode, line, out_dir, attempt + prior, records)  # a redo gets a new seed
            print(f"  said l{line.index:02d} {line.speaker:16} {records[line.index]['seconds']:.2f}s",
                  flush=True)
            episode_home.write_json(sheet, [records[k] for k in sorted(records)])
        failed = listen_all([records[line.index] for line in todo], book, voice_qc.any_transcriber(),
                            among=records)
        for line in todo:  # a redo keeps whichever try scored higher, across every attempt
            if line.index in previous:
                wav = out_dir / f"l{line.index:02d}.wav"
                records[line.index] = keep_best(records[line.index], previous.pop(line.index), wav)
                if line.index in failed and attempt < TRIES - 1:
                    previous[line.index] = dict(records[line.index])
                    wav.replace(wav.with_suffix(".prev.wav"))
        episode_home.write_json(sheet, [records[k] for k in sorted(records)])
        for line in todo:
            r = records[line.index]
            room = f" room {r['episode_voice']:.2f}" if r.get("episode_voice") is not None else ""
            print(f"  {'ok ' if r['passed'] else 'BAD'} l{line.index:02d} wer {r['error_rate']:.2f} "
                  f"sim {r['similarity']:.2f}/{r['floor']:.2f}{room}  {r['why']}  heard: {r['heard'][:50]}",
                  flush=True)
        todo = [line for line in todo if line.index in failed]
        if not todo:
            break
    print(f"{len(records) - len(todo)}/{len(records)} lines said their line -> {sheet}", flush=True)
    if todo:
        raise SystemExit(f"{len(todo)} line(s) failed the listen gate twice")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    redo = [int(v) for a in sys.argv if a.startswith("--redo=") for v in a.split("=", 1)[1].split(",") if v]
    main(args[0], int(args[1]) if len(args) > 1 else 1, redo)
