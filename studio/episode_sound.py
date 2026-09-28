"""The episode's sound layer: the plan's effects and ambiences, laid and checked.

ROOT CAUSE 2026-09-26 (D10).  `scripts/episode/assemble.py` mixed every episode
with an EMPTY cue list -- twelve episodes of voice and a solo violin, the guns,
the shell burst, the river and the crowds all silent.  The plan now names its
sounds (`Shot.sounds`, `Setup.ambience`); this module turns them into the
`(master seconds, file)` cues `trailer_assemble.mix` already knew how to lay,
rendered locally by Stable Audio 3 (`studio/sfx_cues.py`), and QC asks each
one whether the master lets you hear it.
"""
from __future__ import annotations

import re
from pathlib import Path

from studio import sfx_cues

SEED = 7300
EVENT_DB = 6.0
"""dB a cue's loudest 50 ms must rise over the second before it to count as
heard (sfx_cues.event_db).  The generator's builder named 6 as its guess; the
first real master re-fits it."""
LOUD = re.compile(r"\b(fires?|fired|firing|guns?|shells?|burst(s|ing)?|explo\w*|crash\w*|thunder\w*|"
                  r"splash\w*|gallop\w*|hooves|howl\w*|roar\w*|collaps\w*|"
                  r"falls? with|topples?|smash\w*|bells?|whistles?)\b", re.I)
"""Prose words that name an event a viewer expects to HEAR.  A person shouting or
screaming is not here: a voice is carried by its line and its delivery, and ep13's
two shouted lines were refused for want of a cue they did not need."""


def cues_of(episode) -> list[sfx_cues.Cue]:
    """Every sound the plan names, as a cue on its shot."""
    return [sfx_cues.Cue(shot=s.index, sound=x.sound, at=x.at, seconds=x.seconds, gain_db=x.gain_db)
            for s in episode.cut_shots() for x in (getattr(s, "sounds", None) or [])]


def setup_rows(episode, placed: dict) -> dict[str, list[dict]]:
    """Each setup's placed.json shot rows, in cut order."""
    setup_of = {s.index: s.setup for s in episode.shots}
    out: dict[str, list[dict]] = {}
    for row in placed["shots"]:
        out.setdefault(setup_of.get(row["index"], ""), []).append(row)
    return out


def layer(home: Path, episode, placed: dict, run=None) -> list[tuple[float, Path]]:
    """The effects on their shots, then every setup's ambience under its shots."""
    folder, seed = Path(home) / "audio" / "sfx", SEED + 1000 * episode.number
    out = sfx_cues.placed(sfx_cues.render_all(cues_of(episode), folder, seed, run, where=episode.where),
                          placed["shots"])
    for n, (name, rows) in enumerate(setup_rows(episode, placed).items()):
        sound = (getattr(episode.setups.get(name), "ambience", "") or "").strip()
        if sound:
            out += sfx_cues.ambience(sound, rows, folder, seed + 500 + n, run, where=episode.where)
    return out


EFFECT_DUCK_DB = 6.0
AMBIENCE_DUCK_DB = 3.0
"""Owner 2026-09-27 on ep13: "the sound effects are good but too loud".  The
mix ducked only the bed; 5 of 8 effects and every ambience played at full level
under narration (speech 9.8 LU over the gaps; WotW ep10-12 and Sherlock
11.3-16.5).  Effects and ambience now duck under every line, at mix time."""


CUE_TRIM_DB = 3.0
"""Every cue, in the pauses too: master_iter9 (ducked) still had its loudest
between-line moment only 3.1 dB under the voice; Sherlock's median was 6."""


AMBIENCE_TAME = "acompressor=threshold=0.03:ratio=8:attack=5:release=250"
"""An ambience loop's own spikes (a cow, a horse: ~10 LU over its average)
pressed down to the bed they belong to; -30 dBFS sits above the loops' -34."""


def db_gain(db: float) -> float:
    return 10 ** (db / 20.0)


def duck_depth(cue: Path) -> float:
    """An ambience bed ducks less than an event: it is already low."""
    return AMBIENCE_DUCK_DB if Path(cue).name.startswith("amb_") else EFFECT_DUCK_DB


def cue_windows(lines: list[tuple[float, float]], when: float, depth: float) -> list[tuple[float, float, float]]:
    """The master's line windows on the cue's own clock (it starts at `when`)."""
    return [(start - when, end - when, depth) for start, end in lines]


def ducked(cues: list[tuple[float, Path]], lines: list[tuple[float, float]], out_dir: Path,
           run=None) -> list[tuple[float, Path]]:
    """Every cue trimmed by CUE_TRIM_DB and ducked under the lines it overlaps, beside the mix."""
    import subprocess
    from studio.trailer_assemble import duck_expr
    run = run or (lambda args: subprocess.run(args, check=True))
    out = []
    for when, path in cues:
        windows = [w for w in cue_windows(lines, when, duck_depth(path)) if w[1] > 0]
        target = Path(out_dir) / f"{Path(path).stem}.ducked.wav"
        expr = f"{db_gain(-CUE_TRIM_DB):.6f}*{duck_expr(windows)}"
        tame = f"{AMBIENCE_TAME}," if Path(path).name.startswith("amb_") else ""
        run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-af", f"{tame}volume='{expr}':eval=frame", str(target)])
        out.append((when, target))
    return out


def presence(master: Path, episode, placed: dict) -> list[dict]:
    """Per planned cue: where it sits in the master and how far it rises there."""
    rows = {int(s["index"]): s for s in placed["shots"]}
    out = []
    for cue in cues_of(episode):
        at = sfx_cues.start_of(cue, rows)
        got = round(float(sfx_cues.event_db(master, at, cue.seconds)), 1)
        out.append({"shot": cue.shot, "sound": cue.sound, "at": at, "db": got, "ok": got >= EVENT_DB})
    return out


def sound_faults(episode) -> list[str]:
    """G-SOUND: every setup has an ambience, and a shot whose prose names a loud
    event carries a sound."""
    out = [f"G-SOUND setup {name}: no ambience, measured 0 against 1"
           for name, setup in episode.setups.items() if not (getattr(setup, "ambience", "") or "").strip()]
    for s in episode.shots:
        hit = LOUD.search(f"{s.frame} {s.motion}")
        if hit and not getattr(s, "sounds", None):
            out.append(f"G-SOUND shot {s.index}: the prose names '{hit.group(0)}' and the shot has no sound, "
                       f"measured 0 against 1")
    return out
