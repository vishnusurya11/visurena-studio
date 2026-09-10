"""Cast every character in a book: register, instruction, clip, gate.

Book level, once per title, after the screenplay and before any production.
See `.claude/skills/cast-voices/SKILL.md` for why each step is here.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
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

SHE = ("lucy", "madame", "mrs", "miss", "sawyer", "servant", "anna")

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


def audition(book: Path, who: str, instruct: str, cast: dict[str, Path]) -> Path:
    """Render `CANDIDATES` voices and keep the one least like anyone cast."""
    dest = cast_home.clip(book, who)
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tried = []
    for take in range(CANDIDATES):
        spare = dest.with_name(f".take{take}.wav")
        made = voice.comfy.run(voice.DESIGN_WORKFLOW,
                               {"text": PASSAGE, "instruct": instruct,
                                "filename_prefix": f"cast_{who}_{take}"},
                               timeout=voice.DESIGN_TIMEOUT)
        voice._render(made[0], spare)
        rival, score = voice_ear.nearest(spare, cast)
        tried.append((score, take, spare, rival))
        print(f"      take {take + 1}/{CANDIDATES}: nearest {rival or 'nobody'} "
              f"{score:.2f}", flush=True)
    tried.sort(key=lambda row: row[0])
    best = tried[0]
    best[2].replace(dest)
    for _, _, spare, _ in tried[1:]:
        spare.unlink(missing_ok=True)
    return dest


def cast_one(book: Path, card: dict, setting: str, era: str, hertz: int,
             taken: dict[str, int], texture: str = "",
             cast: dict[str, Path] | None = None) -> voice_persona.VoiceInstruction:
    """Write one instruction, render it, and record both beside the audio."""
    who = card["id"]
    cast = cast if cast is not None else {}
    got = voice_persona.write(card, setting, era, hertz, taken, texture=texture)
    started = time.time()
    clip = audition(book, who, got.instruct(SHAPE), cast)
    cast_home.write_sheet(book, who, {
        "character": who, "register_hz": got.hertz(),
        "instruction": got.model_dump(),
        "persona": got.persona(), "sheet": got.sheet(),
        "passage": PASSAGE, "clip": clip.name,
    })
    print(f"  {who:32} {got.hertz():4} Hz  {time.time() - started:4.0f}s", flush=True)
    return got


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("codex_id")
    ap.add_argument("--only", default="", help="comma-separated character ids")
    ap.add_argument("--recast", action="store_true",
                    help="only re-cast characters whose voices collide")
    args = ap.parse_args()

    book = book_dir(args.codex_id)
    setting, era = world(book)
    only = {w.strip() for w in args.only.split(",") if w.strip()} or None
    cards = cards_of(book, only)
    if not cards:
        raise SystemExit("nobody to cast; run cast_home.gather first")

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
