"""Cast every character in a book: register, instruction, clip, gate.

Book level, once per title, after the screenplay and before any production.
See `.claude/skills/cast-voices/SKILL.md` for why each step is here.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import cast_home, voice_ear, voice_persona, voice_register  # noqa: E402
from studio import voice  # noqa: E402

PASSAGE = ("I have looked at this a long while, and I know now what it is. "
           "You may think what you like of me, but you will hear me out first.")
"""One passage for the whole cast, so the VOICE is the only variable."""

APART = voice_ear.SAME_SPEAKER
"""ECAPA cosine at or above which two clips are the same person."""

CANDIDATES = 2
"""How many voices are auditioned per character before one is cast.

VoiceDesign has no seed: the same instruction rendered twice gives two
different voices, and nothing in the writing loop knows what is already cast.
So describing a voice more distinctly does not make it land more distinctly --
MEASURED, a cast written with assigned registers, assigned textures and nine
differing attributes still came back with a MEDIAN pair similarity of 0.73.

Auditioning does not need the description to steer anything.  It renders
`CANDIDATES` draws, scores each against everyone already cast, and keeps the
one whose WORST resemblance is lowest -- because one collision is one
collision.  ECAPA scores some pairs at 0.10, so the voice space is wide; the
problem was only ever that we accepted the first draw out of it.

Two, not more, until the gain is measured: each candidate is a ~45 s render,
so this multiplies the cast's wall clock directly."""

SELF_FLOOR = 0.65
"""Half-vs-half ECAPA cosine a design clip must reach against ITSELF.

MEASURED on the cast of A Study in Scarlet after episode 10: Watson 0.762,
Drebber 0.770, Lucy 0.721, Young 0.706, Holmes 0.704, Hope 0.695, Stangerson
0.559, Ferrier 0.498.  Ferrier's clip is two voices; every line cloned from it
is cloned from an average, and his median line similarity across the book is
0.726 against Watson's 0.855.  0.65 sits under every voice that works and over
the two that do not."""

NEAREST_CEIL = 0.80
"""ECAPA cosine above which a design is its nearest neighbour's twin.

MEASURED: Ferrier vs Young 0.847, the highest pair in the cast -- and three of
Ferrier's five lines score HIGHER against Young's design than against his own.
These two men share every dialogue scene of episode 10.  Next pairs: Drebber-
Watson 0.841, Hope-Watson 0.831; both under this line by the ear, and the
line is set above the working cast's median (0.73) with room."""

REROLLS = 3
"""How many rolls a character gets before the least bad design is kept and
named.  Each roll is `CANDIDATES` renders of ~45 s; three rolls is under five
minutes, and a design that fails three times with its register moved twice is
a cast collision to solve by hand, not by rolling all night."""

NUDGE_HZ = 8
"""How far the register moves per failed roll -- AWAY from the rival.  Under
`voice_register.APART`, so a nudged voice cannot land on a third character's
slot; two nudges (16 Hz) is what separated Ferrier from Young on paper."""

SHE = ("lucy", "madame", "mrs", "miss", "sawyer", "servant", "anna",
       # ADDED 2026-09-20: WotW's neighbour's wife was cast at 125 Hz as a man.
       # The list above is Scarlet's women -- Lucy, Madame, Mrs, Miss, a servant
       # -- and it had never met a character whose id says "wife". A word list
       # is right for the book it was written against and silent about the next
       # one, which is the same fault as a threshold calibrated on one episode.
       "wife", "widow", "mother", "sister", "aunt", "niece", "lady",
       "landlady", "barmaid", "nurse", "governess", "washerwoman",
       "schoolmistress", "maid", "housekeeper", "queen", "duchess")

SHAPE = "both"
"""Which official instruction shape is sent.

MEASURED, and it decides whether the register survives.  The hand-written
12-attribute sheets landed 95/110/82/241 Hz against 95/115/85/230 asked --
near-exact.  The same registers asked for through BACKGROUND INFORMATION prose
alone came back 136/122/109/209 against 76/102/131/222: Brigham Young was asked
for the deepest voice in the book and rendered 60 Hz high.

The number is identical in both; what differs is that the sheet gives `pitch:`
its own line and the persona buries it mid-paragraph.  So both are sent -- the
persona for the life the voice comes from, the sheet for the register it has
to hit."""

PREFER = {
    # men, low to high, placed by who the character IS
    "brigham_young": 76,          # the deepest voice in the book, ceremonial
    "jefferson_hope": 84,         # very low, gravelled by weather and years
    "john_ferrier": 93,           # old, rough, stubborn
    "sherlock_holmes": 102,       # deep and calm -- NOT Doyle's "high and strident"
    "enoch_j_drebber": 112,       # thick, unsteady with drink
    "tobias_gregson": 121,        # full, brisk, official
    "john_watson": 131,           # warm mid baritone, the reasonable man
    "joseph_stangerson": 142,     # dry, flat, doctrinal
    "stamford": 152,              # light, young, chatty
    "g_lestrade": 162,            # thin, nasal, pushing
    "arthur_charpentier": 171,    # young and hot, highest male
    # women
    "lucy_ferrier": 222,          # young, bright, open
    "unnamed_servant": 243,       # small, timid
    "madame_sawyer": 262,         # old, quavering -- and performed
}
"""Registers that are already DECISIONS, not the allocator's to make.

Anyone who SPEAKS has a register that belongs to the character, not to a
spacing algorithm: Holmes is deep and calm because the owner said so, and
Doyle's own "high and somewhat strident" makes a bad trailer voice.  Sorting
by weight and taking the extremes first gave Watson the bottom of the band and
Jefferson Hope the top, which is backwards for both.

These are spread ~9-11 Hz apart on purpose, which is under `voice_register.APART`
-- eleven men do not fit a nine-voice band, so TEXTURE carries what pitch
cannot, and the measured similarity gate is what actually decides.  The
allocator places only the extras, around these."""


def gender_of(card: dict) -> str:
    """Male or female, from the dossier if it says and the name if it does not."""
    text = f"{card.get('name', '')} {(card.get('profile') or {}).get('physical', '')}".lower()
    if any(word in text for word in (" she ", " her ", "woman", "girl", "daughter")):
        return "female"
    return "female" if any(word in text for word in SHE) else "male"


def book_dir(codex_id: str) -> Path:
    """The library folder for a codex id."""
    found = sorted(Path("library").glob(f"{codex_id}_*"))
    if not found:
        raise SystemExit(f"no book in library/ for codex id {codex_id}")
    return found[0]


def world(book: Path) -> tuple[str, str]:
    """Where and when the book is set, for the Background field."""
    path = book / "trailer/main/story.json"
    if path.exists():
        story = json.loads(path.read_text(encoding="utf-8"))
        return story.get("setting", ""), story.get("era", story.get("setting", ""))
    return "", ""


def cards_of(book: Path, only: set[str] | None) -> list[dict]:
    """Every character with a home, or just the ones asked for."""
    cards = []
    for who in cast_home.cast_of(book):
        if only and who not in only:
            continue
        card = json.loads(cast_home.card(book, who).read_text(encoding="utf-8"))
        card["id"] = who
        cards.append(card)
    return cards


def design(book: Path, who: str, instruct: str) -> Path:
    """Render this character's identity clip, once, cached."""
    dest = cast_home.clip(book, who)
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    made = voice.comfy.run(voice.DESIGN_WORKFLOW,
                           {"text": PASSAGE, "instruct": instruct,
                            "filename_prefix": f"cast_{who}"},
                           timeout=voice.DESIGN_TIMEOUT)
    voice._render(made[0], dest)
    return dest


def collisions(book: Path, cast: list[str]) -> list[tuple[str, str, float]]:
    """Every pair of rendered voices that measures as one person."""
    clips = {who: cast_home.clip(book, who) for who in cast
             if cast_home.clip(book, who).exists()}
    return sorted(((one, other, score)
                   for (one, other), score in voice_ear.apart(clips).items()
                   if score >= APART), key=lambda row: -row[2])


@dataclass(frozen=True)
class Pick:
    """One rendered candidate and what the ear made of it."""
    clip: Path
    self_similarity: float
    rival: str
    nearest: float
    fault: str
    hertz: int


def design_fault(self_sim: float, nearest: float) -> str:
    """Why a design fails at cast time, or "" when it passes both gates."""
    why = []
    if self_sim < SELF_FLOOR:
        why.append(f"does not agree with itself ({self_sim:.3f} < {SELF_FLOOR})")
    if nearest > NEAREST_CEIL:
        why.append(f"is its nearest neighbour's twin ({nearest:.3f} > {NEAREST_CEIL})")
    return "; ".join(why)


def nudge_step(who: str, rival: str) -> int:
    """Which way the register moves: AWAY from the rival, up when there is none.

    Young holds 76 and Ferrier 93 -- Ferrier goes up.  A rival placed higher
    pushes the voice down.  Direction comes from the assigned registers, not
    the rendered ones, because the rendered ones are what went wrong."""
    mine, theirs = PREFER.get(who, 0), PREFER.get(rival, 0)
    return -NUDGE_HZ if theirs > mine else NUDGE_HZ


def nudge(instruct: str, hertz: int, step: int) -> str:
    """The same instruction with every `<hertz> Hz` moved by `step`."""
    return re.sub(rf"\b{hertz}\s*Hz\b", f"{hertz + step} Hz", instruct)


def retire(dest: Path) -> Path | None:
    """The clip being recast becomes design_vN.wav (its sheet voice_vN.json),
    N the first free number, so a recast never destroys what it replaces."""
    dest = Path(dest)
    if not dest.exists():
        return None
    n = 1
    while dest.with_name(f"{dest.stem}_v{n}{dest.suffix}").exists():
        n += 1
    old = dest.with_name(f"{dest.stem}_v{n}{dest.suffix}")
    dest.replace(old)
    sheet = dest.with_name("voice.json")
    if sheet.exists():
        sheet.replace(sheet.with_name(f"voice_v{n}.json"))
    return old


def render_design(instruct: str, dest: Path) -> Path:
    """One VoiceDesign render of PASSAGE under `instruct`, conformed to `dest`."""
    made = voice.comfy.run(voice.DESIGN_WORKFLOW,
                           {"text": PASSAGE, "instruct": instruct,
                            "filename_prefix": f"cast_{dest.parent.parent.name}"},
                           timeout=voice.DESIGN_TIMEOUT)
    return voice._render(made[0], dest)


def judge(clip: Path, cast: dict[str, Path]) -> tuple[float, str, float, str]:
    """(self-similarity, rival, nearest, fault) for one rendered candidate."""
    self_sim = voice_ear.self_similarity(clip)
    rival, near = voice_ear.nearest(clip, cast)
    return self_sim, rival, near, design_fault(self_sim, near)


def one_roll(dest: Path, roll: int, instruct: str, cast: dict[str, Path],
             hertz: int, render) -> list[Pick]:
    """`CANDIDATES` renders of one instruction, each scored by the ear."""
    picks = []
    for take in range(CANDIDATES):
        spare = dest.with_name(f".take{roll}_{take}.wav")
        render(instruct, spare)
        self_sim, rival, near, fault = judge(spare, cast)
        picks.append(Pick(spare, self_sim, rival, near, fault, hertz))
        print(f"      roll {roll + 1} take {take + 1}/{CANDIDATES} at {hertz} Hz: self {self_sim:.2f}, "
              f"nearest {rival or 'nobody'} {near:.2f}{'  ' + fault if fault else ''}", flush=True)
    return picks


def best_of(picks: list[Pick]) -> Pick:
    """Passing first; then the lowest collision; then the most self-agreeing."""
    return min(picks, key=lambda p: (bool(p.fault), p.nearest, -p.self_similarity))


def settle(tried: list[Pick], dest: Path) -> Pick:
    """The winner becomes design.wav; every other take is deleted."""
    best = best_of(tried)
    best.clip.replace(dest)
    for pick in tried:
        pick.clip.unlink(missing_ok=True)
    if best.fault:
        print(f"      WARNING: no roll passed; kept the least bad, which {best.fault}", flush=True)
    return dataclasses.replace(best, clip=dest)


def audition(book: Path, who: str, instruct: str, cast: dict[str, Path],
             hertz: int = 0, render=None) -> Pick:
    """Render, gate, and re-roll with the register nudged until a design passes.

    A roll that fails both gates is not re-asked with the same words: the
    register moves `NUDGE_HZ` away from the rival it collided with, because a
    VoiceDesign has no seed and the only lever the writer holds is the sheet.
    The direction is fixed by the FIRST rival: MEASURED on the Ferrier recast,
    roll 2's rival changed and the register walked back to where roll 1 was."""
    dest = cast_home.clip(book, who)
    dest.parent.mkdir(parents=True, exist_ok=True)
    render = render or render_design
    step, tried = 0, []
    for roll in range(REROLLS):
        if roll:
            instruct, hertz = nudge(instruct, hertz, step), hertz + step
        picks = one_roll(dest, roll, instruct, cast, hertz, render)
        tried += picks
        step = step or nudge_step(who, best_of(picks).rival)
        if any(not pick.fault for pick in picks):
            break
    return settle(tried, dest)


def cast_clips(book: Path, exclude: str) -> dict[str, Path]:
    """Every OTHER character's design clip on disk: what a candidate is scored against."""
    return {who: cast_home.clip(book, who) for who in cast_home.cast_of(book)
            if who != exclude and cast_home.clip(book, who).exists()}


def sheet_of(who: str, got: voice_persona.VoiceInstruction, pick: Pick) -> dict:
    """What is recorded beside the audio: the ask, and what the ear measured."""
    return {"character": who, "register_hz": got.hertz(), "register_rendered_hz": pick.hertz,
            "instruction": got.model_dump(), "persona": got.persona(), "sheet": got.sheet(),
            "passage": PASSAGE, "clip": pick.clip.name,
            "gates": {"self_similarity": round(pick.self_similarity, 3),
                      "nearest": pick.rival, "nearest_similarity": round(pick.nearest, 3),
                      "fault": pick.fault}}


def recorded_instruction(book: Path, who: str) -> voice_persona.VoiceInstruction | None:
    """The instruction already on file for this character -- the latest retired
    sheet first, then the live one -- or None when nothing was ever written.

    A recast re-renders; it does not re-write.  The words that made Ferrier's
    clip were never the fault (a VoiceDesign has no seed; the RENDER was), and
    writing them again is a paid reasoning call to arrive at the same sheet."""
    room = cast_home.voice_dir(book, who)
    sheets = sorted(room.glob("voice_v*.json"), key=lambda p: int(p.stem.split("_v")[1]))
    live = room / "voice.json"
    for path in [*reversed(sheets), *([live] if live.exists() else [])]:
        body = json.loads(path.read_text(encoding="utf-8")).get("instruction")
        if body:
            return voice_persona.VoiceInstruction.model_validate(body)
    return None


def cast_one(book: Path, card: dict, setting: str, era: str, hertz: int,
             taken: dict[str, int], texture: str = "",
             cast: dict[str, Path] | None = None) -> voice_persona.VoiceInstruction:
    """Write one instruction (or read the one on file), render it, and record
    both beside the audio."""
    who = card["id"]
    cast = cast if cast is not None else cast_clips(book, who)
    dest = cast_home.clip(book, who)
    got = recorded_instruction(book, who) or \
        voice_persona.write(card, setting, era, hertz, taken, texture=texture)
    started = time.time()
    if dest.exists():
        print(f"  {who:32} {got.hertz():4} Hz  already cast; --recast to redesign", flush=True)
        return got
    pick = audition(book, who, got.instruct(SHAPE), cast, hertz=got.hertz())
    cast_home.write_sheet(book, who, sheet_of(who, got, pick))
    print(f"  {who:32} {pick.hertz:4} Hz  self {pick.self_similarity:.2f}  nearest "
          f"{pick.rival or 'nobody'} {pick.nearest:.2f}  {time.time() - started:4.0f}s", flush=True)
    return got


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("codex_id")
    ap.add_argument("--only", default="", help="comma-separated character ids")
    ap.add_argument("--recast", action="store_true",
                    help="redesign the --only characters: the old clip is kept as design_vN.wav")
    args = ap.parse_args()

    book = book_dir(args.codex_id)
    setting, era = world(book)
    only = {w.strip() for w in args.only.split(",") if w.strip()} or None
    cards = cards_of(book, only)
    if not cards:
        raise SystemExit("nobody to cast; run cast_home.gather first")
    if args.recast:
        if not only:
            raise SystemExit("--recast needs --only: a whole-cast redesign is a decision, not a flag")
        for card in cards:
            old = retire(cast_home.clip(book, card["id"]))
            print(f"  {card['id']}: old design kept as {old.name if old else 'nothing (no clip yet)'}")

    print(f"book: {book}")
    print(f"cast: {len(cards)} characters\n")

    print("=== registers, assigned before anything is written ===")
    for gender in ("male", "female"):
        count = sum(1 for c in cards if gender_of(c) == gender)
        room = voice_register.capacity(gender)
        if count > room:
            print(f"  NOTE {count} {gender} voices into a band that holds {room} "
                  f"at {voice_register.APART} Hz apart -- pitch alone cannot "
                  f"separate them, so TEXTURE must carry the rest")
    given = voice_register.assign(cards, gender_of, PREFER)
    for who, hertz in sorted(given.items(), key=lambda kv: kv[1]):
        print(f"  {who:32} {hertz:4} Hz  ({gender_of(next(c for c in cards if c['id'] == who))})")

    print("\n=== writing and rendering ===")
    taken: dict[str, int] = {}
    for card in sorted(cards, key=voice_register.weight, reverse=True):
        cast_one(book, card, setting, era, given[card["id"]], taken)
        taken[card["id"]] = given[card["id"]]

    print("\n=== measured similarity ===")
    near = collisions(book, [c["id"] for c in cards])
    if not near:
        print(f"  every pair below {APART} -- the cast is distinct")
    else:
        for one, other, score in near:
            print(f"  COLLISION {one} vs {other}: {score:.2f}")
        print(f"\n  recast the lighter part of each pair into a free slot, "
              f"delete its design.wav, and run again")

    print(f"\ncast root: {book / 'cast'}")
    print("next: listen to every clip with studio/voice_qc.py")


if __name__ == "__main__":
    main()
