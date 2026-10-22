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
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio.episode_home import episode_arg
from studio import cast_home, episode_emotion, episode_home, step_attempts, step_caps, voice, voice_ear, voice_qc, voice_say
from studio.episode_spec import Episode, Line

SEED_BASE = 71000
TRIES = 2
ENGINE = "indextts2"
"""MEASURED 2026-09-10 on one Watson line against his designed voice (ECAPA
cosine): IndexTTS2 0.799, Qwen3-TTS clone 0.728; both word-perfect.  IndexTTS2
is ~4x slower (111 s vs 26 s cold) and the more accurate voice, which is
what the owner asked for."""
SIMILAR = 0.60
"""ECAPA cosine (voice_ear.RULER, 16 kHz) a calm line of four seconds or more must
reach against the designed voice: the BACKSTOP under the cast margin (`CAST_MARGIN`),
which is what tells one character from another.  Shorter lines get `similar_floor`.

RE-SET 2026-10-21 on the 16 kHz ruler (voice bench fix/, 411 trusted owner-watched
lines of three books + 18 bench takes): the lowest genuine calm line of 4 s or more
reads Scarlet 0.626, WotW 0.728, Jekyll 0.785.  The old 0.70 refused 2 of 300 real
Scarlet lines on the new ruler."""

FLOORS = ((4.0, SIMILAR), (2.0, 0.55), (0.0, 0.50))
"""(at least this many seconds, this floor), on voice_ear.RULER.

RE-SET 2026-10-21: the lowest genuine calm 2-4 s line reads Scarlet 0.601, WotW
0.691, Jekyll 0.713; 1.5 s slices of long genuine lines read p1 0.524 / 0.596 /
0.689 (the last band only shapes `similar_floor`; under SIM_MEASURABLE_S nothing is
gated).  On the old 24 kHz ruler the floors were 0.70 / 0.65 / 0.60 (ep10's
truncations: a correct voice loses ~0.05 at 2.5 s and 0.12-0.18 at 1.5 s)."""

EPISODE_VOICE = 0.60
"""Line-vs-line ECAPA cosine (voice_ear.RULER) an ALTERNATE-reference render must
reach, on average, against the speaker's other passed lines in the same episode; a
line said with feeling sits `feeling_drop` under it.

RE-SET 2026-10-21 on the 16 kHz ruler: a calm line's mean against its own speaker's
other lines is never under Scarlet 0.622, WotW 0.746, Jekyll 0.646, and a line's mean
against ANOTHER speaker's lines never over 0.566 / 0.569 / 0.508.  Jekyll's urgent
l19 reads 0.514 against Enfield's calm lines, hence the drop.  The case it was set on
(Scarlet ep10 l27, 0.585/0.589 on the old ruler) reads 0.717/0.650 on this one and
leads Brigham Young by 0.16: on the correct ruler it was Ferrier."""


def similar_floor(seconds: float) -> float:
    """The similarity a line of `seconds` must reach: the measured truncation loss."""
    return next(floor for at, floor in FLOORS if seconds >= at)


SIM_MEASURABLE_S = 2.0
"""Under this a line's similarity is recorded, never gated.  MEASURED 2026-09-26:
one-second slices of the narrator's OWN passing lines scored min 0.07, p10 0.32
against his cast clip; 2.5 s slices min 0.51.  ep13's 'What are we?' failed as
three different men.  Words and pace still gate a short line."""


def feeling_drop(delivery: str) -> float:
    """How far a line said with feeling sits under a calm floor: FEELING_FLOOR_DROP, else 0."""
    return 0.0 if delivery in ("", "calm") else episode_emotion.FEELING_FLOOR_DROP


def line_floor(seconds: float, delivery: str) -> float:
    """The floor for THIS line: none when it is too short to measure; a line said
    with feeling sits FEELING_FLOOR_DROP under the calm floor (the embedding moves
    with pitch and effort)."""
    if seconds < SIM_MEASURABLE_S:
        return 0.0
    return round(similar_floor(seconds) - feeling_drop(delivery), 2)


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


def voice_fit(book: Path, records: dict, index: int, wav: Path, similarity=None) -> float | None:
    """A try's mean similarity to its speaker's OTHER passed lines in this
    episode, whatever its reference (keep_best's fit); None when unmeasurable."""
    if not Path(wav).exists() or index not in records:
        return None
    score = similarity or voice_ear.similarity
    speaker = records[index].get("speaker")
    others = [book / r["rel_path"] for i, r in records.items()
              if i != index and r.get("speaker") == speaker and r.get("passed")
              and (book / r["rel_path"]).exists()]
    if not others:
        return None
    return round(sum(float(score(Path(wav), o)) for o in others) / len(others), 3)


def alternate_ok(score: float | None, seconds: float = SIM_MEASURABLE_S, delivery: str = "calm") -> bool:
    """An alternate-reference render is the man in the room, or it is not kept.

    Under SIM_MEASURABLE_S the encoder cannot hear enough voice to judge
    (one-second slices of a TRUE voice score 0.07-0.32), the design gate
    already records-never-gates there, and ep16's l18 (1.75 s) was refused at
    0.74 against 0.75 on exactly that unmeasurable read.  The score is kept
    in the record either way; words and pace still gate a short line."""
    return score is None or seconds < SIM_MEASURABLE_S or score >= EPISODE_VOICE - feeling_drop(delivery)


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


BEST_REFERENCE_FLOOR = 0.70
"""The similarity (voice_ear.RULER) a passed line needs to be cloned from.  RE-SET
2026-10-21 by rank: the old 0.75 sat at the 2.9th percentile of the genuine
owner-watched lines on the 24 kHz ruler; the same percentile on 16 kHz is 0.708."""

BEST_REFERENCE_FLOORS = {voice_ear.OLD_RULER: 0.75, voice_ear.RULER: BEST_REFERENCE_FLOOR}
"""Each stored score is judged on its own ruler's floor, never the other's."""


def good_reference(row: dict) -> bool:
    """A passed line's stored score clears the reference floor of the ruler it was taken on."""
    return row.get("similarity", 0.0) >= BEST_REFERENCE_FLOORS[voice_ear.ruler_of(row)]


def reference_rank(row: dict) -> tuple[bool, float]:
    """Current-ruler rows first, then the higher score: two rulers' numbers are not ranked together."""
    return voice_ear.ruler_of(row) == voice_ear.RULER, row.get("similarity", 0.0)


def best_line_reference(records: dict, speaker: str, exclude: int | None) -> int | None:
    """The index of the speaker's best PASSED line over its ruler's reference floor, or None."""
    good = [(reference_rank(r), i) for i, r in records.items()
            if r.get("speaker") == speaker and r.get("passed") and i != exclude and good_reference(r)]
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
    here = [(reference_rank(r), r["rel_path"], r["text"]) for i, r in records.items()
            if r.get("speaker") == speaker and r.get("passed") and i != exclude and good_reference(r)]
    there = [(reference_rank(r), r["rel_path"], r["text"]) for r in other_episode_records(book)
             if r.get("speaker") == speaker and r.get("passed") and (book / r["rel_path"]).exists()
             and good_reference(r)]
    good = here + there
    if not good:
        return None
    _, rel, text = max(good)
    clip = book / rel
    clip.with_suffix(".txt").write_text(text, encoding="utf-8")
    return clip


def line_reference(book: Path, records: dict, line: Line, attempt: int) -> Path:
    """The design clip for the first two tries; from the third, the speaker's own
    best line anywhere in the book (its text written beside it for the clone), taking turns
    with the design clip so a resume can try either again (Jekyll l15, 2026-10-14)."""
    best = book_best_reference(book, records, line.speaker, line.index) if attempt >= 2 and attempt % 2 == 0 else None
    return best if best is not None else reference_for(book, line.speaker)


TERMINAL_TRIES = 8
"""After this many tries a line said right keeps its best try, flagged (the step parks on nothing)."""
TERMINAL_MARGIN = 0.10
"""How far under its floor a kept best try may sit: the floor is the instrument's, not the ear's
verdict on a word (Jekyll l15: 10 tries at 0.42-0.63 against 0.65, every word heard).  RE-SET
2026-10-21: the old ruler's 0.08 times the genuine scores' spread ratio, 0.0535 / 0.0394 = 1.36,
is 0.109 on 16 kHz, set at 0.10 (two decimals, like every floor); a try that does not lead its
cast by CAST_MARGIN is far whatever its score."""


def leads_cast(row: dict) -> bool:
    """A stored try passes the cast-margin test the gate applies (`margin_ok`): it leads
    every other cast voice by CAST_MARGIN, or its margin cannot be measured."""
    near = None if row.get("margin") is None else (row.get("rival"), row["margin"])
    return margin_ok(near, float(row.get("seconds") or SIM_MEASURABLE_S))


def try_rank(row: dict) -> tuple[bool, bool, float]:
    """How two tries of one line are ordered: a current-ruler score first (two rulers'
    numbers are not ranked together), then a try that leads its cast, then the score."""
    return voice_ear.ruler_of(row) == voice_ear.RULER, leads_cast(row), row.get("similarity", 0.0)


def remember_best(record: dict, wav: Path, best: dict | None, out_dir: Path) -> dict | None:
    """The best failing try whose words were heard right (`try_rank`), its file kept as l{NN}.best.wav."""
    import shutil
    if not record.get("words_ok") or (best is not None and try_rank(best) >= try_rank(record)):
        return best
    source = Path(wav) if Path(wav).exists() else Path(wav).with_suffix(".prev.wav")   # a redo parks the kept try
    shutil.copyfile(source, Path(out_dir) / f"{Path(wav).stem}.best.wav")
    return {k: v for k, v in record.items() if k != "best_try"}


def carried(old: dict, new: dict) -> dict:
    """A fresh render's record, still carrying the line's best try (ep01 l15 forgot its 0.63)
    and the transcript the last try was heard as (`prior_heard`: two alike is a ruler fault)."""
    out = dict(new, best_try=old["best_try"]) if old.get("best_try") else new
    return dict(out, prior_heard=old["heard"]) if old.get("heard") else out


LINES_WALL_DEFAULT_S = 600.0
"""The lines wall until stages.yaml carries the `lines` cap row (K1: episode, 10 min)."""


def lines_wall_s() -> float:
    """The lines wall, seconds: the cap table's `lines` row, its own bucket apart from `voice`."""
    try:
        return step_caps.wall_s("lines")
    except KeyError:
        return LINES_WALL_DEFAULT_S


def wall_spent(home: Path) -> bool:
    """The seconds the line loop has already used (persisted per episode) reached the lines wall."""
    return step_attempts.seconds(home, "lines") >= lines_wall_s()


def round_bucket(attempt: int, redo: list[int], records: dict, todo: list[int]) -> str:
    """Where a round's seconds are booked: `say` (the cap table's first-saying row) when it is the
    first round of a run that redoes nothing and no line in it was ever listened to, else `lines`,
    the re-say wall.  Deadline retro 2026-10-20: ep01's first pass (22 lines, 1,075 s with l11's
    'cheque' re-says) spent the whole 10 min re-say wall, so the wall cut the cure, not the work."""
    if attempt or redo:
        return "lines"
    return "lines" if any("passed" in records.get(i, {}) for i in todo) else "say"


def ear_cure(book: Path, record: dict, among: dict, listen) -> bool:
    """Two identical wrong transcripts whose one differing word sounds like the line's
    (cmudict) are the ear's fault, not the mouth's: file the pair in the book's ear lexicon
    and listen to the SAME wav again -- no render.  True when the line now passes."""
    heard = record.get("heard") or ""
    if not heard or heard != record.get("prior_heard"):
        return False
    if not voice_qc.file_homophone(book, heard, record["text"]):
        return False
    return not listen_all([record], book, listen, among=among)


def terminal(record: dict, best: dict | None, force: bool = False) -> dict | None:
    """keep_best flagged: the best rightly heard try once the line has had TERMINAL_TRIES;
    `keep_best_far` when it sits more than TERMINAL_MARGIN under its floor or does not lead
    its cast by CAST_MARGIN (step caps, 2026-10-18: voice is tier 2, it never parks the
    episode).  None while it may still be cured, or when no try's words were heard right."""
    if (record.get("tries", 0) < TERMINAL_TRIES and not force) or best is None:
        return None
    far = best.get("similarity", 0.0) < best.get("floor", 0.0) - TERMINAL_MARGIN or not leads_cast(best)
    return dict(best, passed=True, flagged="keep_best_far" if far else "keep_best", tries=record["tries"])


def attempts_from(tries: int, rounds: int = TRIES) -> list[int]:
    """This run's attempt numbers for a line already tried `tries` times: every one new.
    A resume zeroed the prior after the first pass and re-said a refused seed (l15, 2026-10-14)."""
    return [tries + a for a in range(rounds)]


def rounds_for(start: dict[int, int]) -> int:
    """This run's rounds: as many as the least-tried refused line still needs to reach
    TERMINAL_TRIES, never fewer than TRIES -- the terminal fires inside one run, not after
    four runs each parked by the brain (Jekyll ep01 v2 l15, 2026-10-14)."""
    return max(TRIES, TERMINAL_TRIES - min(start.values(), default=TERMINAL_TRIES))


def seed_for(episode: int, line: Line, attempt: int) -> int:
    return SEED_BASE + episode * 1000 + line.index * 10 + attempt


def render(book: Path, episode: Episode, line: Line, out_dir: Path, attempt: int,
           records: dict | None = None) -> dict:
    """One line's file and its measured seconds; nothing listened to yet."""
    out = out_dir / f"l{line.index:02d}.wav"
    reference = line_reference(book, records or {}, line, attempt)
    seed = seed_for(episode.number, line, attempt)
    # HOW, NOT ONLY WHO (root cause 2026-09-26, D11): every line in twelve
    # episodes was one temperature.  The delivery rides as IndexTTS2's emotion
    # VECTOR on the speaker's own clip -- a designed emotion clip was another
    # voice (ep13: the narrator's shouts at 0.25-0.54 similarity).
    delivery = episode_emotion.delivery_of(line)
    # THE MOUTH KNOWS THE BOOK'S NAMES (Jekyll ep01 review): the TTS is told how a
    # filed word is said; the record keeps the book's text, which the ear scores.
    spoken = voice_say.respelled(line.text, voice_say.say_lexicon(book))
    if ENGINE == "indextts2":
        said = voice_say.say(spoken, reference, reference, seed, out, index=line.index,
                             speaker=line.speaker, vector=episode_emotion.vector_for(delivery))
    else:
        said = voice.clone_line(reference, spoken, seed, out, index=line.index, speaker=line.speaker)
    return {"index": line.index, "speaker": line.speaker, "kind": line.kind, "shot": line.shot,
            "text": line.text, "said_as": spoken, "rel_path": episode_home.relative(book, out),
            "seconds": said.seconds, "seed": said.seed, "tries": attempt + 1,
            "reference": reference.name, "delivery": delivery}


def listen_all(records: list[dict], book: Path, listen, among: dict | None = None) -> list[int]:
    """Read every clip back; return the indices that did not say their line.

    All the renders first, then all the listening: every swap between the
    TTS and the Whisper model costs minutes off the HDD, so thirteen lines
    pay two swaps here instead of twenty-six.  `among` is the whole episode's
    records, which an alternate-reference render is judged against."""
    among = among if among is not None else {r["index"]: r for r in records}
    listen = voice_qc.with_lexicon(listen, voice_qc.ear_lexicon(book))
    failed = []
    for record in records:
        clip = book / record["rel_path"]
        verdict = voice_qc.check(clip, record["text"], transcribe=listen)
        heard = voice_verdict(book, record, clip, verdict.seconds)
        room = episode_voice(book, among, record)
        passed = (verdict.passed and not heard["voice_why"] and lift_ok(book, record, clip)
                  and alternate_ok(room, verdict.seconds, record.get("delivery", "calm")))
        record.update(heard=verdict.heard, error_rate=verdict.error_rate, why=verdict.why, words_ok=verdict.passed,
                      episode_voice=room, passed=passed, **heard)
        if not passed:
            failed.append(record["index"])
    return failed


CAST_MARGIN = 0.06
"""How far a line's own cast design must lead EVERY other cast design of the book
(ECAPA cosine, voice_ear.RULER).  The voice gate's discriminator; the floor is its backstop.

SET 2026-10-21 (voice bench VERDICT step 3, fix/): across 411 trusted owner-watched lines
of three books and today's 18 bench takes, the line's own design is nearest every time,
and the smallest lead is Scarlet 0.145, WotW 0.231, Jekyll ep01 0.162, bench 0.100 (0.094
on a second resampler).  A wrong voice's lead is the negative of the genuine one, so every
one of 9,953 wrong-voice trials fails at any margin over 0.  0.06 leaves the lowest
genuine take one paired seed-noise interval (0.034) of room; the bench's 0.08 left 0.014.
Lines under SIM_MEASURABLE_S are not held to it: 1.5 s slices of genuine lines lead by
as little as 0.04, 2.0 s slices by 0.099 at the least (n = 280)."""

SAME_CLIP = 0.99
"""Two cast ids whose designs score this alike are ONE clip (Scarlet's lucy_ferrier and
lucy_ferrier_child read 1.000): one voice, not a rival."""


def rivals_of(book: Path, speaker: str) -> dict[str, Path]:
    """Every OTHER cast voice of the book on disk, the speaker's own clip filed twice excluded."""
    mine = cast_home.clip(book, speaker)
    others = {who: cast_home.clip(book, who) for who in cast_home.cast_of(book)
              if who != speaker and cast_home.clip(book, who).exists()}
    if not mine.exists():
        return others
    return {who: clip for who, clip in others.items() if voice_ear.similarity(mine, clip) < SAME_CLIP}


def cast_margin(book: Path, speaker: str, clip: Path, own: float) -> tuple[str, float] | None:
    """(nearest rival, own score minus the rival's): how far the line leads the rest of the
    cast.  None when the book has no other voice to compare it with."""
    rivals = rivals_of(book, speaker)
    if not rivals:
        return None
    scored = {who: float(voice_ear.similarity(design, clip)) for who, design in rivals.items()}
    rival = max(scored, key=scored.get)
    return rival, round(float(own) - scored[rival], 3)


def margin_ok(near: tuple[str, float] | None, seconds: float) -> bool:
    """The line leads its cast by CAST_MARGIN, or it cannot be measured (too short, no cast)."""
    return near is None or seconds < SIM_MEASURABLE_S or near[1] >= CAST_MARGIN


def voice_why(speaker: str, similarity: float, floor: float, near, seconds: float) -> str:
    """The voice gate's words for a refusal, "" when the voice passes."""
    if similarity < floor:
        return f"voice {similarity:.2f} is under its floor {floor:.2f}"
    if not margin_ok(near, seconds):
        return (f"sounds like {near[0]}: {speaker} leads by {near[1]:+.2f}, "
                f"the cast margin is {CAST_MARGIN:.2f}")
    return ""


def voice_verdict(book: Path, record: dict, clip: Path, seconds: float) -> dict:
    """The voice gate on one line: its own design's score, the floor, the cast margin, the ruler."""
    similarity = float(voice_ear.similarity(reference_for(book, record["speaker"]), clip))
    floor = line_floor(seconds, record.get("delivery", "calm"))
    near = cast_margin(book, record["speaker"], clip, similarity)
    return {"similarity": round(similarity, 3), "floor": floor, "ruler": voice_ear.RULER,
            "rival": near[0] if near else None, "margin": near[1] if near else None,
            "voice_why": voice_why(record["speaker"], similarity, floor, near, seconds)}


def lift_ok(book: Path, record: dict, clip: Path) -> bool:
    """A shouted or exultant line rises LIFT_ST over the speaker's calm design
    read; any other delivery is not asked.  The measured lift is kept."""
    register = record.get("delivery", "calm")
    if register not in episode_emotion.LIFTED:
        return True
    calm = episode_emotion.f0_median(reference_for(book, record["speaker"]))
    record["lift_st"] = round(episode_emotion.lift_st(clip, calm), 2)
    return record["lift_st"] >= episode_emotion.LIFT_ST


def redo_rank(row: dict) -> tuple:
    """A redo's order of two tries: the one the gate passed first, then `try_rank`."""
    return (bool(row.get("passed")), *try_rank(row))


def keep_best(new: dict, previous: dict | None, wav: Path,
              fit: tuple[float | None, float | None] | None = None, clarity: bool = False) -> dict:
    """A redo never makes a line worse: a passing try beats a failing one, then the
    higher `try_rank` (ruler, leads its cast, similarity) stays on disk as l{NN}.wav,
    the other is deleted.  An alternate-reference
    render that is not the man in the room never wins, whatever it scored
    against the design clip.  With `fit` (each try's mean similarity to the
    speaker's other lines in this episode) the closer try wins -- the measure a
    split voice fails on (ep27 l01: two rounds kept the original by the clip)."""
    prev_wav = wav.with_suffix(".prev.wav")
    if previous is None or not prev_wav.exists():
        return new
    if clarity and new.get("passed", True) and new.get("error_rate") is not None:
        # a line QC heard wrong (ep27 l15): the try the ear hears most clearly wins
        better = float(new["error_rate"]) < float(previous.get("error_rate", 1.0))
    elif fit and None not in fit and new.get("passed", True):
        better = fit[0] > fit[1]
    else:
        better = alternate_ok(new.get("episode_voice"), float(new.get("seconds") or SIM_MEASURABLE_S),
                              new.get("delivery", "calm")) and redo_rank(new) >= redo_rank(previous)
    if better:
        prev_wav.unlink()
        return new
    wav.unlink(missing_ok=True)
    prev_wav.rename(wav)
    return dict(previous, tries=new.get("tries", previous.get("tries", 0)))


def rekeyed(records: dict, lines: list, out_dir: Path, book: Path) -> dict:
    """Every recording whose TEXT (and speaker) a plan line still has, moved to
    that line's index and file -- a joined or inserted line renumbers the lines
    after it, and matching by index alone would say them all again (ep27).
    Moves go through temporary copies so no file overwrites one still needed."""
    import shutil
    by_text = {(r.get("text"), r.get("speaker")): r for r in records.values()}
    staged, out = {}, {}
    for line in lines:
        old = by_text.get((line.text, line.speaker))
        src = book / old["rel_path"] if old else None
        if old and src.exists():
            tmp = out_dir / f"rekey_{line.index:02d}.tmp.wav"
            shutil.copyfile(src, tmp)
            staged[line.index] = (old, tmp)
    for index, (old, tmp) in staged.items():
        wav = out_dir / f"l{index:02d}.wav"
        tmp.replace(wav)
        out[index] = dict(old, index=index, rel_path=episode_home.relative(book, wav))
    return out


def prune_stale(records: dict, count: int) -> dict:
    """Records for line indices the plan no longer has are dropped (their wavs
    stay on disk).  ep11 went from 29 lines to 25 and the take builder died on
    a record for line 25 that placed.json could not place."""
    return {k: v for k, v in records.items() if 0 <= int(k) < count}


def keep_terminal(records: dict, index: int, out_dir: Path, force: bool = False) -> bool:
    """Remember a failing line's best try; at the terminal (or, forced, at the wall) put it
    back on disk, flagged."""
    import shutil
    record, wav = records[index], Path(out_dir) / f"l{index:02d}.wav"
    record["best_try"] = remember_best(record, wav, record.get("best_try"), out_dir)
    if (kept := terminal(record, record["best_try"], force)) is None:
        return False
    shutil.copyfile(wav.with_suffix(".best.wav"), wav)
    records[index] = kept
    print(f"  keep_best l{index:02d} sim {kept['similarity']:.2f}/{kept['floor']:.2f} after "
          f"{kept['tries']} tries -- flagged", flush=True)
    return True


def at_wall(records: dict, todo: list, out_dir: Path, home: Path, rounds: int) -> list:
    """The lines wall is spent: every failing line takes its terminal now (best rightly heard
    try kept, flagged) and a CAP line says so; the lines left are those with no rightly heard try."""
    left = [line for line in todo if not keep_terminal(records, line.index, out_dir, force=True)]
    print(step_caps.cap_line("lines", step_attempts.count(home, "lines"), rounds,
                             step_attempts.seconds(home, "lines"), len(todo) - len(left)), flush=True)
    return left


def main(book_id: str, number: int, redo: list[int] | None = None, clarity: bool = False) -> None:
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    out_dir = episode_home.lines_dir(book, number)
    sheet = out_dir / "lines.json"
    records = {r["index"]: r for r in episode_home.read_json(sheet)} if sheet.exists() else {}
    records = rekeyed(records, episode.lines, out_dir, book)   # a recording follows its text (ep27)
    records = prune_stale(records, len(episode.lines))
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
    start = {line.index: records.get(line.index, {}).get("tries", 0) for line in todo}
    rounds = rounds_for(start)
    home = episode_home.home(book, number)
    for attempt in range(rounds):
        if wall_spent(home):
            todo = at_wall(records, todo, out_dir, home, rounds)
            episode_home.write_json(sheet, [records[k] for k in sorted(records)])
            break
        began, bucket = time.time(), round_bucket(attempt, redo or [], records, [line.index for line in todo])
        for line in todo:
            have = records.get(line.index)
            if attempt == 0 and have and "passed" not in have and (out_dir / f"l{line.index:02d}.wav").exists():
                have["rel_path"] = episode_home.relative(book, out_dir / f"l{line.index:02d}.wav")
                continue  # rendered but never listened to: reuse the file
            records[line.index] = carried(records.get(line.index, {}), render(     # a redo, a resume: new seeds
                book, episode, line, out_dir, attempts_from(start[line.index], rounds)[attempt], records))
            print(f"  said l{line.index:02d} {line.speaker:16} {records[line.index]['seconds']:.2f}s",
                  flush=True)
            episode_home.write_json(sheet, [records[k] for k in sorted(records)])
        ear = voice_qc.any_transcriber()
        failed = listen_all([records[line.index] for line in todo], book, ear, among=records)
        failed = [i for i in failed if not ear_cure(book, records[i], records, ear)]
        for line in todo:  # a redo keeps whichever try scored higher, across every attempt
            if line.index in previous:
                wav = out_dir / f"l{line.index:02d}.wav"
                fit = (voice_fit(book, records, line.index, wav),
                       voice_fit(book, records, line.index, wav.with_suffix(".prev.wav")))
                records[line.index] = keep_best(records[line.index], previous.pop(line.index), wav, fit=fit, clarity=clarity)
                if line.index in failed and attempt < rounds - 1:
                    previous[line.index] = dict(records[line.index])
                    wav.replace(wav.with_suffix(".prev.wav"))
        episode_home.write_json(sheet, [records[k] for k in sorted(records)])
        for line in todo:
            r = records[line.index]
            room = f" room {r['episode_voice']:.2f}" if r.get("episode_voice") is not None else ""
            print(f"  {'ok ' if r['passed'] else 'BAD'} l{line.index:02d} wer {r['error_rate']:.2f} "
                  f"sim {r['similarity']:.2f}/{r['floor']:.2f}{room}  {r['why']} {r.get('voice_why', '')}  "
                  f"heard: {r['heard'][:50]}",
                  flush=True)
        failed = [i for i in failed if not keep_terminal(records, i, out_dir)]
        episode_home.write_json(sheet, [records[k] for k in sorted(records)])
        todo = [line for line in todo if line.index in failed]
        step_attempts.spend(home, bucket, time.time() - began)
        if not todo:
            break
    print(f"{len(records) - len(todo)}/{len(records)} lines said their line -> {sheet}", flush=True)
    if todo:
        raise SystemExit(f"{len(todo)} line(s) failed the listen gate {rounds} times")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    redo = [int(v) for a in sys.argv if a.startswith("--redo=") for v in a.split("=", 1)[1].split(",") if v]
    main(args[0], episode_arg(sys.argv), redo, clarity="--clear" in sys.argv)
