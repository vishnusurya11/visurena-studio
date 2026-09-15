#!/usr/bin/env python
"""Cut the takes to the plan, lay the lines and the bed, burn the captions.

    uv run python scripts/episode/assemble.py <codex_id> <episode>

The plan's shot times ARE the cut: every take is trimmed to its shot, the
segments are joined, the lines are placed at their `at` and levelled through
the trailer's mixer (`mix_with_lines`: -16 LUFS lines, bed ducked to -24
under them, master at -14 / -2 dBTP), the captions are burned in the safe
box, and a two-second end chip follows the cut to black.  Nothing here is new
sound engineering; it is the trailer's assemble stage under an episode's plan.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import canvas, edit_gate, episode_bed, episode_gutter, episode_home
from studio.comfy import run
from studio.episode_spec import Episode
from studio import trailer_assemble
from studio.trailer_assemble import clip_seconds, concat, extract, integrated, mix_with_lines, true_peak

W, H, FPS = canvas.size("9:16") + (24,)
"""W and H are rebound from the plan in `main`; the plan declares the aspect."""


class TakePath(type(Path())):
    """A take file that knows which shots it covers (take-based engines)."""

    def __new__(cls, path, shots=None):
        self = super().__new__(cls, path)
        self.shots = shots
        return self

    def __init__(self, path, shots=None):
        super().__init__(path)
        self.shots = shots
BED_WORKFLOW = "audio_acestep15_music"
BED_TAGS = ("sparse dark ambient underscore, low sustained cello and double bass drone, "
            "distant piano notes, Victorian London, tension, cinematic, no drums, no vocals, "
            "slow, quiet, minimal")
BED_STYLE = ("Solo violin in D minor at 60 BPM, unaccompanied, played slow and low on the G and D "
             "strings, long bowed notes with a little rosin and bow noise near the bridge, the "
             "phrases falling far apart with air between them, never hurried and never rising to a "
             "finish. A cello holds one long drone far underneath. Recorded at night in a large "
             "panelled room, gaslit Victorian London, grave, patient, unresolved, an underscore "
             "that sits far beneath everything else and stays there.")
"""OWNER 2026-09-13: a violin, because HOLMES PLAYS ONE -- the instrument is the
character, and the episodes have already drawn him with it.

YuE2 takes descriptive STYLE PROSE, not ACE-Step's comma-separated tag list, and
the owner chose it for that control.  IT NAMES NO VOICE, NOT EVEN TO FORBID ONE:
the vendor's own guidance is that a style carrying vocal descriptors makes the
model add a voice, and MiniMax cannot read a negation at all.  A fence built out
of the word you are avoiding is a summons."""

BED_SECONDS = 100.0
END_CHIP_SECONDS = edit_gate.END_CHIP_FRAMES / FPS
"""Title-ends review 2026-09-11: 2 s of silent black before a loop is dead time.
DERIVED, never restated -- `edit_gate` owns the frame count and checks the cut
against it, and holding the number in both places is what left every episode
failing its own tail check by exactly 42 frames."""
BED_TRIM_DB = -11.0  # audio reviewer, iteration 3: the bed sat only 6-9 LU under the voice in the gaps
"""MEASURED 2026-09-11 (reviewer 4): the raw bed was -14.6 LUFS, louder than
the -16 LUFS lines, and the 1.7 s beat before the button was the loudest
stretch of the episode.  Nine dB down puts it under the voice everywhere."""
ROOM_TONE_LUFS = -40.0
BED_FADE_S = 2.76  # a long half-sine fade over bed AND room tone; the bed's last hit at 135.0 s fell inside the old 1.5 s
TITLE_LUFS = -20.0
ENCODE_LAG_S = 0.030
"""The volume+limiter re-encode of the master lands the voice ~30 ms late
against the wavs (measured +0.04 s vs +0.01 s before trim); compensated."""


def quiet_bed(bed: Path, seconds: float, out: Path, normalise: bool = True) -> Path:
    """The bed for an episode: BED_TRIM_DB down, a room-tone floor under it,
    faded out over BED_FADE_S at the placed end, cut to `seconds`."""
    from studio import sfx

    tone = sfx.room_tone(out.with_name("room_tone.wav"), seconds + 1.0, ROOM_TONE_LUFS)
    fade_at = max(seconds - BED_FADE_S, 0.0)
    # MEASURED per bed, not a constant: the -11 dB trim was right for ACE-Step's
    # -14.6 LUFS output alone, and the bed model is now the owner's to choose.
    if not normalise:
        # A COMPOSITE IS ALREADY AT LEVEL, span by span.  Measuring the whole
        # thing and lifting it to one target would average five deliberate
        # levels back into one -- the sameness the tones exist to break.
        gain, loudness, short = 0.0, None, 0.0
        print(f"  bed {Path(bed).name}: composed per span, already at level", flush=True)
    else:
        try:
            loudness = integrated(bed)
            gain, short = bed_gain_db(loudness), bed_shortfall_db(loudness)
        except Exception:                               # no loudnorm pass available
            gain, loudness, short = BED_TRIM_DB, None, 0.0
    if short:
        # The clamp has to speak. Saying "+6.0 dB to reach -25.6" when the bed
        # lands at -27.8 is the sentence that let a failed generation ship.
        print(f"  bed {Path(bed).name}: WARNING {loudness:.1f} LUFS needs "
              f"{BED_TARGET_LUFS - loudness:+.1f} dB and the lift caps at "
              f"{BED_MAX_LIFT_DB:+.1f}; it will sit at {loudness + gain:.1f} LUFS, "
              f"{short:.1f} dB under target", flush=True)
    elif normalise:
        print(f"  bed {Path(bed).name}: {gain:+.1f} dB to reach {BED_TARGET_LUFS} LUFS", flush=True)
    import soundfile as sf
    have = sf.info(str(bed)).frames / sf.info(str(bed)).samplerate
    passes = loops_for(have, seconds)
    if passes > 1:
        print(f"  bed is {have:.1f}s for a {seconds:.1f}s cut: looping x{passes}", flush=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error",
                    "-stream_loop", str(passes - 1), "-i", str(bed), "-i", str(tone),
                    "-filter_complex",
                    f"[0:a]volume={gain}dB,atrim=0:{seconds:.3f}[b];"
                    f"[1:a]atrim=0:{seconds:.3f}[r];[b][r]amix=inputs=2:normalize=0,"
                    f"afade=t=out:st={fade_at:.3f}:d={BED_FADE_S}:curve=ihsin[a]",
                    "-map", "[a]", "-ar", "48000", str(out)], check=True)
    return out
"""Black tail after the last frame.  No text anywhere on the picture: the
owner removed captions, chip and end card (2026-09-10)."""


BED_TIMEOUT = 2400
"""Seconds to wait for a bed, set from the SLOWEST engine and not the fastest.

It was 900.  YuE2's olmpack graph runs three seeded stages and takes longer than
that here: measured on episode 4, the waiter raised `StillRunning` at 900 s, the
assemble died with no master, and ComfyUI's history reported the same prompt id
as `status: success` with the audio on disk.  The bed was made and thrown away
by the clock.  Waiting too long costs minutes; not waiting long enough costs the
whole job."""

YUE2_TOKENS_PER_S, YUE2_MAX_TOKENS = 25, 9000
"""YuE2's semantic stage emits 25 codec tokens a second, capped at 9000 (360 s).

`bed_request` takes `seconds` and the yue2 branch DISCARDED it, so the bed's
length had no relation to the runtime asked for.  `semantic_max_tokens` is the
duration control, it is injectable, and nobody was setting it."""

BED_ENGINE_DEFAULT = "acestep"
"""ACE-STEP, BECAUSE IT IS THE ONE THAT CAN BE TOLD NOT TO SING.

The owner asked for YuE2 -- "ace step is shit .. use yue2 .. more expressive and
great prompt control on style" (2026-09-13) -- and he is right about the style
control.  YuE2 simply has no instrumental control of any kind, and this is a
mechanism, not a bad run.  Read out of the node source 2026-09-14 after YuE2
sang on three separate beds:

  * its token vocabulary has NO vocal/instrumental token at all
    (`_vendor/yue2/tokenization_yue2.py:16-18`), and `encode_ordinary` means an
    `[inst]`-style string is encoded as literal TEXT, never as a control;
  * `SongRequest.text()` interpolates lyrics unconditionally, so an empty field
    yields a `[Lyrics]` header over a blank line -- an UNFILLED SLOT, not an
    instruction;
  * with `cot="full"` the plan stage writes a chord-annotated ABC score whose
    melody line IS the vocal line, and the semantic stage improvises syllables
    over it.  That is why both refused beds were phoneme scat, one
    pseudo-English and one pseudo-Japanese, rather than actual verse;
  * `guidance` returns exactly 1.0 for `cot="full"`, so the negative branch is
    never built and CFG has been OFF on every bed ever generated.

The word "instrumental" occurs ONCE in the whole node pack: a tooltip on the
lyrics input.  This module chose that pipeline because of that tooltip.  A
tooltip is not a mechanism.

ACE-Step has both halves -- `[inst]` is a trained control string in its lyric
encoder, its tags field says instrumental too, and it runs real CFG at 2.0
against a zeroed negative.  So `[inst]` is a lever and `""` is the absence of
one.  Episodes 1, 2 and 4 shipped silent beds on ACE-Step.

`--bed=yue2` stays reachable.  The one experiment worth its twenty minutes if
the owner wants YuE2 back is `cot="off"`: it plans no ABC score at all, drops
the word "transcription" from the instruction, and turns CFG on for the first
time.  If that sings too, the levers are exhausted."""

BED_TARGET_LUFS = -25.6
"""Where the bed SITS, replacing a fixed -11 dB trim.

The trim was right for one model only: ACE-Step's raw bed measured -14.6 LUFS
-- louder than the -16 LUFS lines -- and -11 dB put it at -25.6, which is the
level two shipped episodes were judged at.  Carrying that -11 across to a model
with a different output loudness would move the bed, not keep it.  So the LEVEL
is the constant and the gain is measured per bed."""

BED_MAX_LIFT_DB = 6.0
"""A bed far under target is a failed generation, not something to crank:
lifting 30 dB would raise its noise floor with it."""


def loops_for(have: float | None, need: float) -> int:
    """How many passes of a `have`-second bed cover `need` seconds.

    `max_duration` IS A CAP, NOT A TARGET.  Asked YuE2 for 172 s against a 162 s
    cut and it stopped at 157.8 s -- 4.2 s of episode with no bed (measured
    2026-09-13); `trailer_music` saw the same on seven cues that ended by
    themselves between 101.9 s and 146.8 s under a 150 s cap.  So the bed is
    covered by looping, which is free, rather than by asking again, which costs
    four minutes and can come back short a second time."""
    import math

    if not have or have <= 0:
        return 1
    return max(1, math.ceil(need / have))


def bed_is_usable(have: float | None, need: float) -> bool:
    """A SHORT bed is usable -- it loops.  Only a missing or empty one is not.

    `bed()` used to delete anything shorter than the runtime and regenerate.
    The file is the expensive part of this stage; covering the cut is free."""
    return bool(have and have > 0)


def bed_gain_db(loudness: float | None) -> float:
    """The gain that puts THIS bed at `BED_TARGET_LUFS`.

    Falls back to the old fixed trim when the bed cannot be measured, so a
    missing ffmpeg loudnorm pass degrades to the previous behaviour instead of
    asking for infinite gain on a silent file."""
    if loudness is None or loudness == float("-inf") or loudness != loudness:
        return BED_TRIM_DB
    return min(round(BED_TARGET_LUFS - loudness, 2), BED_MAX_LIFT_DB)


def bed_shortfall_db(loudness: float | None) -> float:
    """How far under `BED_TARGET_LUFS` this bed will still sit after the lift.

    `bed_gain_db` clamps at `BED_MAX_LIFT_DB` and the caller prints the clamped
    number as though it had reached the target -- which is false exactly when it
    matters.  MEASURED on episode 3: `bed.wav` is -33.63 LUFS, wants +8.03 dB,
    gets +6.00, and lands at -27.83.  In four of the episode's speech gaps the
    bed then sits at or under the -40 LUFS room-tone floor, including the whole
    3.26 s run-out at -45.6, so the listener hears room tone and not a violin.

    The skill's own rule is that a bed far under target is a failed generation.
    This one shipped because the only sentence a human reads said otherwise."""
    if loudness is None or loudness == float("-inf") or loudness != loudness:
        return 0.0
    return round(max(0.0, round(BED_TARGET_LUFS - loudness, 2) - BED_MAX_LIFT_DB), 2)

BED_INSTRUMENTAL = {"acestep": "[inst]", "yue2": ""}
"""HOW EACH MODEL IS TOLD "NO SINGING", AND THEY DO NOT AGREE.

ACE-Step has a token, `[inst]`, and it works: episodes 1 and 2 came back silent.

YUE2 HAS NO TOKEN AT ALL.  Its lyrics field must be EMPTY -- not `[Instrumental]`,
not `(instrumental)`, not a section tag without words.  Given any lyric-shaped
string it writes a song to fit.

This was got wrong once, expensively, and the error was a MIS-ATTRIBUTION rather
than a guess: `(instrumental)` is MiniMax Music 3's exception, measured on the
TRAILER (`music_tone`, `audio_minimax_music_3`), and it was written into this
module as though it had been measured on YuE2.  It had not.  Episode 3's bed then
sang invented English verse for 101 of its 157.8 seconds -- 64 % -- and shipped,
because nothing between the generator and the mix ever listened to it.  Hence
`bed_sings()` below: the marker is now VERIFIED per bed, not asserted here."""


def bed_request(engine: str, seconds: float, seed: int,
                tone: str = "") -> tuple[str, dict]:
    """The workflow and the values for one bed, by engine.

    Pure: no network, no GPU, so the ask is testable without spending a minute
    of either.  YuE2 runs three seeded stages on one graph (ABC score, semantic,
    sampler) and all three move together -- a retry that re-rolled only the
    sampler would keep the tune and change the mix, which is not what a retry
    means when the tune is what was wrong."""
    if engine not in BED_INSTRUMENTAL:
        raise ValueError(f"unknown bed engine {engine!r}; one of {sorted(BED_INSTRUMENTAL)}")
    if engine == "yue2":
        # THE OLMPACK PIPELINE, because it is the one that DOCUMENTS an
        # instrumental: `OlmYuE2Request.lyrics` reads "Leave empty for
        # instrumental music."  `audio_yue2_song` drives `YuE2GenerateMusic`,
        # whose lyrics field promises nothing -- given `(instrumental)` it sang
        # invented verse, and given "" it sang again.
        return "audio_yue2_song_olmpack", {
            "style": episode_bed.tone_style(tone) if tone else BED_STYLE,
            "lyrics": BED_INSTRUMENTAL[engine], "cot": "full",
            "seed": seed, "abc": "", "filename_prefix": "ep_bed",
            # the duration control, at 25 tokens a second; it was never set
            "semantic_max_tokens": min(int(seconds * YUE2_TOKENS_PER_S), YUE2_MAX_TOKENS)}
    # THE TONE DECIDES THE TAGS, THE TEMPO AND THE KEY.  bpm and keyscale are
    # separate values on this request, so a tone that changed only its tags
    # would arrive at 60 BPM in D minor like every other -- which is the
    # sameness the owner heard.
    voice = episode_bed.TONES.get(tone)
    return BED_WORKFLOW, {
        "tags": voice.tags if voice else BED_TAGS,
        "lyrics": BED_INSTRUMENTAL[engine], "seconds": seconds,
        "duration": seconds,
        "bpm": voice.bpm if voice else 60,
        "keyscale": voice.key if voice else "D minor",
        "seed": seed, "lm_seed": seed, "filename_prefix": "ep_bed"}


def toned_bed(home: Path, number: int, beds: list[dict], placed: dict,
              engine: str = BED_ENGINE_DEFAULT) -> Path:
    """One bed per distinct tone, each at its own level, laid into `audio/bed.wav`.

    OWNER 2026-09-14: "make sure audio is not too loud the BG ... different types
    based on the context of background thrilling .. normal".

    MEASURED on the shipped episode 5 master before any of this: speech -13.2
    LUFS, the bed in an un-ducked gap -28.0, the bed inside the voice band -34.9.
    It was never objectively loud.  What made it READ as loud is that one solo
    violin in D minor played for 160 seconds under a breakfast, a joke, a
    flashback and a murder, and a constant is a thing the ear gives up filtering.

    An episode with no `beds` block gets one `plain` span end to end, so episodes
    1 to 5 would rebuild exactly as they shipped, only quieter."""
    at = {s["index"]: s["t_start"] for s in placed["shots"]}
    plan = episode_bed.bed_plan(beds, at, placed["duration_s"])
    room = home / "audio"
    room.mkdir(parents=True, exist_ok=True)
    print(f"  bed: {len(plan.spans)} span(s), {len(plan.needed)} tone(s) to make", flush=True)

    made: dict[str, Path] = {}
    for tone in plan.needed:
        made[tone] = one_tone(room, number, tone, plan.seconds[tone], engine)
    return episode_bed.compose(plan.spans, made, room / "bed.wav")


BED_ROLLS = 3
"""How many times a tone may come back empty before the assemble stops.

Bounded on purpose: an unbounded retry on a model that has started returning
silence spends the GPU all night and delivers nothing."""


def one_tone(room: Path, number: int, tone: str, want: float, engine: str) -> Path:
    """One tone, generated, levelled, and RE-ROLLED if it comes back empty.

    MEASURED on episode 6's first assemble: five tones in one pass, four within
    0.2 dB of target and `grave` at -58.0 against -29.0.  `level` printed the
    clamp warning and the assemble used the file anyway, which put 29 seconds of
    nothing under the Camberwell flashback.

    A warning is not a fix.  `BED_MAX_LIFT_DB`'s own docstring already said what
    this means -- "a bed far under target is a failed generation, not something
    to crank" -- and nothing acted on it.

    RE-ROLL RATHER THAN RE-ASK: four good beds came from the same prose in the
    same minute, so there is nothing in the request to repair."""
    out = room / f"bed_{tone}.wav"
    target = episode_bed.tone_lufs(tone)
    for roll in range(BED_ROLLS):
        if not out.exists():
            seed = bed_seed(out, number) + 977 * roll
            workflow, values = bed_request(engine, want, seed, tone)
            got = run(workflow, values, timeout=BED_TIMEOUT)
            out.write_bytes(got[0].read_bytes())
        try:
            loudness = integrated(out)
        except Exception:
            loudness = None
        if not episode_bed.is_dead(loudness, target):
            level(out, target)
            print(f"    {tone:10s} {want:6.1f}s at {target:6.1f} LUFS -> {out.name}", flush=True)
            return out
        dead = out.with_name(f"{out.stem}.empty{roll + 1}{out.suffix}")
        out.rename(dead)
        print(f"    {tone}: came back at {loudness:.1f} LUFS against {target:.1f} -- empty. "
              f"Kept as {dead.name}; re-rolling ({roll + 1}/{BED_ROLLS}).", flush=True)
    raise SystemExit(f"the {tone} bed came back empty {BED_ROLLS} times. The same prose "
                     f"made the other tones in the same pass, so this is the model and not "
                     f"the ask: check ComfyUI, then re-run assemble.")


def level(path: Path, target: float) -> Path:
    """Put one file AT `target` LUFS, in place.

    Each tone is levelled BEFORE composing, never after: normalising the
    composite would average five deliberate levels back into one, which is the
    thing the tones exist to stop."""
    try:
        loudness = integrated(path)
    except Exception:
        print(f"    WARNING: {path.name} could not be measured; left as generated", flush=True)
        return path
    gain = min(round(target - loudness, 2), BED_MAX_LIFT_DB)
    if round(target - loudness, 2) > BED_MAX_LIFT_DB:
        print(f"    WARNING {path.name}: {loudness:.1f} LUFS needs {target - loudness:+.1f} dB "
              f"and the lift caps at {BED_MAX_LIFT_DB:+.1f}; it will sit "
              f"{round(target - loudness, 2) - BED_MAX_LIFT_DB:.1f} dB under target", flush=True)
    tmp = path.with_suffix(".lev.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(path),
                    "-af", f"volume={gain}dB", str(tmp)], check=True)
    tmp.replace(path)
    return path


def bed_seed(out: Path, number: int, base: int = 90000) -> int:
    """The seed for the NEXT bed, moved along by every refused one on disk.

    A gate that can refuse must leave a way forward.  `bed_gate` refuses a bed
    that sings -- rightly; episode 3's sang invented verse under the narration
    for 64 % of its length and reached YouTube's queue -- and renames it
    `bed.sings.wav`.  The seed was `base + number`, fixed, so re-running
    regenerated the SAME bed, which sang again, and there was no flag to change
    it.  Episode 4's assemble died after four minutes of GPU with no master and
    every retry would have died identically.

    `refused_name` in this same subsystem already wrote the rule: "a model that
    sings once tends to sing again ... read the name off what is there, never
    off a counter".  So does this -- a plain re-run re-rolls, and the seed stays
    reproducible from the tree rather than remembered."""
    out = Path(out)
    refused = len(list(out.parent.glob(f"{out.stem}.sings*{out.suffix}")))
    return base + number + 101 * refused


def bed(out: Path, seed: int, runtime: float = BED_SECONDS,
        engine: str = BED_ENGINE_DEFAULT) -> Path:
    """A quiet instrumental bed, made once, long enough for the placed runtime."""
    seconds = float(max(BED_SECONDS, int(runtime) + 10))
    if out.exists():
        import soundfile as sf
        info = sf.info(str(out))
        if bed_is_usable(info.frames / info.samplerate, runtime):
            return out
        out.unlink()  # empty or unreadable: the only reason to spend again
    workflow, values = bed_request(engine, seconds, seed)
    made = run(workflow, values, timeout=BED_TIMEOUT)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(made[0].read_bytes())
    # SOMETHING LISTENS BEFORE IT SHIPS. Episode 3's bed sang invented verse under
    # the narration for 64 % of its length and reached YouTube's queue, because the
    # prompt said "no vocals" and nothing checked. A prompt is an intention.
    from studio import bed_gate

    why = bed_gate.refuse(out)
    if why == bed_gate.UNVERIFIED:
        # NOT silence. A gate that cannot measure must say so out loud, or it is
        # indistinguishable from one that measured and approved -- which is how
        # the first version of this gate passed a bed that was singing.
        print(f"  WARNING: the {engine} bed is UNVERIFIED -- no transcriber was "
              f"reachable. Listen to {out} before publishing.", flush=True)
    elif why:
        kept = bed_gate.refused_name(out)
        out.rename(kept)
        raise SystemExit(f"the {engine} bed was refused and kept as {kept.name}: {why}")
    else:
        print(f"  bed checked: no singing heard in {out.name}", flush=True)
    return out


def guard(take: Path, seconds: float, work: Path) -> str:
    """The gutter guard's crop for one take, from its first, middle and last frame."""
    import numpy as np
    from PIL import Image

    greys = []
    for k, at in enumerate((0.0, seconds / 2, max(seconds - 0.1, 0.0))):
        png = work / f"guard_{take.stem}_{k}.png"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{at:.3f}", "-i", str(take),
                        "-frames:v", "1", str(png)], check=True)
        greys.append(np.asarray(Image.open(png).convert("L"), dtype=float))
    return episode_gutter.crop_filter(episode_gutter.box(greys), W, H)


def segments_of(placed: dict, takes: dict[int, Path]) -> list[tuple[int, float]]:
    """(take index, seconds) in cut order.  A per-shot engine has a take per
    shot; a take-based engine (r2v) has a take per RUN of shots, keyed by the
    run's first shot, cut to the run's summed placed seconds."""
    by = {s["index"]: s["seconds"] for s in placed["shots"]}
    out, k = [], 0
    order = sorted(by)
    while k < len(order):
        index = order[k]
        run = getattr(takes[index], "shots", None) or [index]
        out.append((index, round(sum(by[i] for i in run), 6)))
        k += len(run)
    return out


def picture(placed: dict, takes: dict[int, Path], work: Path) -> Path:
    """Every take trimmed from its first frame to its PLACED seconds, guarded
    against the storyboard gutter, joined in order.  `work/gutter.json` says
    what was cropped where."""
    segments, guarded = [], {}
    for index, seconds in segments_of(placed, takes):
        crop = guard(takes[index], seconds, work)
        if crop:
            guarded[index] = crop
        seg = extract(takes[index], 0.0, seconds, work / f"seg{index:02d}.mp4", W, H, FPS, pre=crop)
        segments.append(seg)
    episode_home.write_json(work / "gutter.json", guarded)
    print(f"gutter guard cropped {len(guarded)} takes: {guarded}", flush=True)
    return concat(segments, work / "picture.mp4")


def video_frames(video: Path) -> int:
    """How many frames the PICTURE has, which is not what the container says:
    a card whose sound outlasts its last frame reports the sound's duration."""
    seen = subprocess.run(["ffmpeg", "-v", "quiet", "-stats", "-i", str(video), "-map", "0:v",
                           "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    return int(seen.stderr.rsplit("frame=", 1)[1].split()[0])


CARD_RATIO_TOLERANCE = 0.01
"""A card may be a pixel off its exact ratio (2048/3 = 682.67); it may not be a
different SHAPE."""


def card_fits(size: tuple[int, int] | None, width: int, height: int) -> bool:
    """Is this title card the episode's own shape?

    `conform_card` scales with `force_original_aspect_ratio=increase` and then
    crops, so a card of the wrong shape is blown up and has its edges CUT OFF --
    lettering included.  Episode 3 had no `ep03.mp4`, fell back to the book's
    9:16 `title.mp4`, and shipped with the title cropped top and bottom while QC
    reported `title_card: true` because a card was present."""
    if not size or not all(size):
        return False
    return abs(size[0] / size[1] - width / height) <= CARD_RATIO_TOLERANCE


def check_card(size, width: int, height: int, name: str, number: int) -> None:
    """Refuse a wrong-shaped card, and NAME THE COMMAND that makes a right one."""
    if card_fits(size, width, height):
        return
    raise SystemExit(
        f"title card {name} is {size[0]}x{size[1]} but this episode is {width}x{height}: "
        f"conforming it would crop the lettering off.\n"
        f"  make this episode's own card:  uv run python scripts/episode/title.py "
        f"<codex_id> {number} --approved")


def card_size(card: Path) -> tuple[int, int] | None:
    """The card's pixel size, read off ffmpeg rather than assumed."""
    seen = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(card)],
                          capture_output=True, text=True)
    import re

    found = re.search(r", (\d{2,5})x(\d{2,5})[ ,]", seen.stderr)
    return (int(found.group(1)), int(found.group(2))) if found else None


def conform_card(card: Path, out: Path) -> Path:
    """The title card in the episode's own format, every frame kept and the
    sound ending with the picture.

    MEASURED 2026-09-12: the `fps=` filter dropped the card's last frame (90 in,
    89 out) and loudnorm left 3.80 s of sound over 3.71 s of picture, so the
    concat held that last frame for 0.09 s before the black.  An output frame
    rate conforms the same way and keeps the frame; a `-t` at the picture's own
    length ends the sound where the picture ends."""
    seconds = video_frames(card) / FPS
    fade_at = max(seconds - 0.3, 0.0)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(card),
                    "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},format=yuv420p",
                    "-fps_mode", "cfr", "-r", str(FPS),
                    "-af", f"aresample=48000,loudnorm=I={TITLE_LUFS}:TP=-1.5:LRA=7,volume=-1.7dB,"
                           f"afade=t=in:d=0.4,afade=t=out:st={fade_at:.3f}:d=0.3",
                    "-t", trailer_assemble.frames_arg(seconds, FPS),
                    "-c:v", "libx264", "-preset", "fast", "-crf", "17",
                    "-c:a", "aac", "-ar", "48000", str(out)], check=True)
    return out


def black_chip(out: Path) -> Path:
    """Black and silence, the same length every run.

    `-shortest` across two lavfi inputs is a race: the same code gave 6 frames
    on one master and 48 on the next.  A duration is not a race."""
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
                    "-i", f"color=c=black:s={W}x{H}:r={FPS}",
                    "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "16", "-c:a", "aac", "-ar", "48000",
                    "-t", trailer_assemble.frames_arg(END_CHIP_SECONDS, FPS), str(out)], check=True)
    return out


def tail(master: Path, title: Path | None, out: Path, work: Path, number: int = 0) -> Path:
    """After the last frame: the book's animated title card if it exists (its
    own sound kept), then black with silence.  No text is burned anywhere.

    The card must be the EPISODE'S shape: the book-wide fallback is drawn for
    whatever aspect the book started in, and conforming it across shapes crops
    the lettering (see `card_fits`)."""
    parts = [master]
    if title and title.exists():
        check_card(card_size(title), W, H, title.name, number)
        parts.append(conform_card(title, work / "title_conformed.mp4"))
    parts.append(black_chip(work / "black.mp4"))
    listing = work / "final.txt"
    listing.write_text("".join("file '" + p.as_posix() + "'\n" for p in parts), encoding="utf-8")
    # The concat demuxer carries the first part's own start offset into the join:
    # MEASURED 2026-09-12, the mix's first frame sits at 0.000 and the joined
    # master's at 0.041, so the whole picture arrived one frame late -- which is
    # also why every cut in QC read one frame past the frame the plan named.
    # setpts puts the join back on zero; the output rate keeps every frame the
    # `fps=` filter would have dropped.
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
                    "-vf", "setpts=PTS-STARTPTS", "-af", "asetpts=PTS-STARTPTS",
                    "-fps_mode", "cfr", "-r", str(FPS), "-muxdelay", "0", "-muxpreload", "0",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-c:a", "aac", "-b:a", "256k",
                    "-ar", "48000", str(out)], check=True)
    # The concat demuxer does not refuse a part whose picture does not match the
    # first one: it drops it and reports success.  That is how a master four
    # frames short shipped without anyone seeing it, so the join counts itself.
    want = sum(video_frames(p) for p in parts)
    got = video_frames(out)
    if got != want:
        raise RuntimeError(
            f"the join lost picture: {got} frames out of {want} "
            f"({', '.join(f'{p.name} {video_frames(p)}f' for p in parts)}). "
            f"A part whose size, rate or pixel format differs is dropped silently.")
    return out


TARGET_LUFS, FLOOR_LUFS, TP_CEILING = -14.0, -15.5, -1.0


def final_gain(lufs: float, tp: float) -> float:
    """One last gain toward -14, never past the true-peak ceiling.

    The mixer's gain is bounded by the peak before the end chip's silence is
    appended, so the delivered file measured -15.8 LUFS with 0.7 dB of peak
    headroom left (first master, 2026-09-10).  Spend that headroom, no more."""
    if lufs >= FLOOR_LUFS:
        return 0.0
    return round(max(0.0, min(TARGET_LUFS - lufs, TP_CEILING - 0.1 - tp)), 2)


LIMIT = 0.794
"""A true-peak limiter at -2.0 dBFS after the final gain: the AAC encode
overshoots by ~0.5 dB (the r2v master measured -0.49 dBTP after a gain
computed to land at -1.1), so the delivered peak stays under -1.0 dBTP."""


def trim(master: Path, work: Path) -> Path:
    lufs, tp = integrated(master), true_peak(master)
    gain = final_gain(lufs, tp)
    if gain <= 0 and tp <= TP_CEILING:
        return master
    louder = work / "trimmed.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(master), "-c:v", "copy",
                    "-af", f"atrim=start={ENCODE_LAG_S},asetpts=PTS-STARTPTS,"
                           f"volume={max(gain, 0.0)}dB,alimiter=limit={LIMIT}:level=false",
                    "-c:a", "aac", "-b:a", "256k", str(louder)], check=True)
    master.write_bytes(louder.read_bytes())
    return master


def main(book_id: str, number: int, engine: str = "i2v",
         bed_engine: str = BED_ENGINE_DEFAULT) -> None:
    """`engine` is the PICTURE engine (i2v/r2v); `bed_engine` is the music model.
    Two different questions that both used to be called 'engine'."""
    book = episode_home.book_dir(book_id)
    episode = episode_home.load_plan(book, number)
    global W, H
    W, H = canvas.size(episode.aspect)   # the plan declares the canvas (studio/canvas.py)
    home = episode_home.home(book, number)
    work = episode_home.work_dir(book, number, engine)
    work.mkdir(parents=True, exist_ok=True)
    takes = {}
    for r in episode_home.read_json(episode_home.takes_dir(book, number, engine) / "shots.json"):
        takes[r["index"]] = TakePath(book / r["rel_path"], r.get("shots"))
    placed = episode_home.read_json(home / "placed.json")
    wavs = {r["index"]: book / r["rel_path"]
            for r in episode_home.read_json(episode_home.lines_dir(book, number) / "lines.json")}
    covered = {i for p in takes.values() for i in (p.shots or [])} | set(takes)
    missing = [s.index for s in episode.shots if s.index not in covered]
    if missing:
        raise SystemExit(f"no take for shots {missing}")

    episode_home.make_rooms(book, number)   # free; the bed and the mix in front of it are not
    write_cut_manifest(work, episode_home.read_json(
        episode_home.takes_dir(book, number, engine) / "shots.json"), book)
    cut = picture(placed, takes, work)
    music = quiet_bed(toned_bed(home, number, episode.beds, placed, bed_engine),
                      placed["duration_s"], work / "bed_quiet.wav", normalise=False)
    # audio reviewer, iteration 3: 10 dB in 20 ms on every line pumped; the bed now sits lower
    # (BED_TRIM_DB) and ducks gently: at least 4 dB, 0.15 s attack, 0.25 s pre-delay, 1.0 s release
    trailer_assemble.DUCK_DEPTH_DB, trailer_assemble.DUCK_ATTACK = 4.0, 0.15
    trailer_assemble.DUCK_PREDELAY, trailer_assemble.DUCK_RELEASE = 0.25, 1.0
    mixed = mix_with_lines(cut, music, [], [(line["at"], wavs[line["index"]])
                                            for line in placed["lines"]],
                           work / "mixed.mp4", seconds=placed["duration_s"])
    card = book / "title" / f"ep{number:02d}.mp4"
    out = tail(mixed, card if card.exists() else book / "title" / "title.mp4",
               episode_home.master_path(book, number, engine), work, number)
    trim(out, work)
    keep = next_iteration(home)
    (home / "cut" / f"master_iter{keep}.mp4").write_bytes(out.read_bytes())
    print(f"master -> {out}  (kept as master_iter{keep}.mp4)")


def write_cut_manifest(work: Path, records: list[dict], book: Path) -> Path:
    """G5.6's input: what each take file WAS, recorded at cut time.

    `edit_gate.provenance` asks whether the takes on disk are still the ones the
    master was cut from, and can only answer it against a manifest written when
    the cut was made -- "a manifest read off the same files it is compared to can
    never be stale".  `edit_gate` says this module writes it.  It did not, on any
    episode: `find library -name cut.json` came back empty for ep01 to ep05.

    So provenance returned `{"measured": False, "stale_takes": []}`, the empty
    list read as clean, and every report has claimed a master provably made of
    the files on disk without the claim ever being checked."""
    rows = {Path(r["rel_path"]).stem: {"rel_path": r["rel_path"],
                                       "bytes": (Path(book) / r["rel_path"]).stat().st_size}
            for r in records if (Path(book) / r["rel_path"]).exists()}
    return episode_home.write_json(Path(work) / "cut.json", rows)


def next_iteration(home: Path) -> int:
    """The number the cut about to be written takes, read off the CUT ROOM.

    Every iteration is kept under a numbered name so none overwrites the one
    before it.  This globbed `home` and masters moved to `home/"cut"/`, so the
    glob matched nothing, `max(default=0) + 1` was always 1, and every assemble
    would have written master_iter1.mp4 over the last -- silently inverting the
    rule the numbering exists to keep.

    Always the NEXT number, never a gap filled: a name is a moment in time."""
    seen = [f.stem.split("master_iter")[1] for f in (Path(home) / "cut").glob("master_iter*.mp4")]
    return max((int(s) for s in seen if s.isdigit()), default=0) + 1


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0], int(args[1]) if len(args) > 1 else 1, episode_home.engine_arg(sys.argv),
         next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--bed=")),
              BED_ENGINE_DEFAULT))
