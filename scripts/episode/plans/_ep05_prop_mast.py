"""Chapter 5's one drawn picture: the mast, the mirror and the humped dome.

WHY THIS PROP AND NOT `heat_ray_generator`.  In chapter 5 Wells shows the
narrator exactly three things of the Martians' making: "a thin rod rose up,
joint by joint, bearing at its apex a circular disk that spun with a wobbling
motion"; "slowly a humped shape rose out of the pit, and the ghost of a beam of
light seemed to flicker out from it"; and, after the killing, "that thin mast
upon which their restless mirror wobbled".  The camera-like case on a jointed
arm -- `heat_ray_generator` -- is not described until chapter 11 and is carried
by a fighting-machine that has not been assembled yet.  A sheet of it staged in
this episode would put a chapter-11 machine in the chapter-5 pit.

WHAT CHANGED IN THE DOSSIER, and why each edit:
- `physical` is cut from 3 sentences (86 words) to 2 (62).  `pack_refs.prop_row`
  pastes it verbatim into every take block of every setup that declares the
  prop -- five of this episode's six -- against a 150-240 word budget.  The
  dropped sentence is the whip-arms, which are the Martians' own tentacles and
  not part of the machine; shot 2 carries them in its own words.
- `sheet_prompt` drops "clean labels" (ep02 T21: a legible gibberish masthead is
  what a drawer does with an instruction to letter something) and "shown
  spinning with a wobble" (a still cannot draw a rotation, and asking for one
  spends the prompt's attention on a thing that cannot arrive).  The story
  object goes first (refs-only: "a busy prompt drops its key object"), the three
  views are named flat, and the scale figure is a silhouette.

v1 of both is kept under `design.sheet_prompt_v1` / `design.physical_v1`.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CARD = (ROOT / "library" / "20260827135508_the-war-of-the-worlds"
        / "analysis" / "props" / "pit_mast_mirror.json")

PHYSICAL = (
    "A thin jointed metal rod rising joint by joint out of the sand-pit, bearing at its apex a "
    "circular disk the size of a cartwheel that turns with a wobbling motion and catches the light "
    "like a mirror.")
"""v3, and the edit is a SPOILER FIX found by looking at the first four takes.

v2's second sentence -- "Below it the humped black back of a Martian appliance
lifts over the rim of the pit, a smooth dark dome with a shallow funnel mouth
set in its front" -- is pasted by `pack_refs.prop_row` into every take block of
every setup that declares the prop, which is five of this episode's six. So the
dome was in the words at SUNSET: T00 and T01 both drew it sitting at the foot of
the mast beyond the heather, twenty shots before it rises. In chapter 5 the dome
comes up once, at the killing, and afterwards Wells is explicit that "the
Martians and their appliances were altogether invisible, save for that thin mast
upon which their restless mirror wobbled".

The dome is still on the SHEET, which is what binds its look; it is now named
only in the `ray` shots' own frame and at_rest prose, where it belongs."""

SHEET = (
    "Prop reference sheet for the Martian mast, mirror and humped appliance at the Horsell "
    "sand-pit from The War of the Worlds, 1898, on a plain neutral grey backdrop in even soft "
    "light. The mirror is a solid round polished disk of tarnished silver, smooth and unbroken "
    "like a round tray, four feet across, tilted over on a short yoke at the apex of a thin "
    "jointed rod of dark bronze in telescoping segments. The appliance below is a vast smooth "
    "humped dome of black metal as big as a haystack, three times the height of a man, with a "
    "shallow flared funnel mouth set in its front. Three views side by side: the whole mast "
    "standing tall from the side, the solid mirror disk and its yoke seen from below, and the "
    "great dome in three-quarter view. A standing Victorian gentleman in a frock coat and top "
    "hat, drawn small and dark in flat silhouette, stands beside the dome for scale and reaches a "
    "third of its height. Matte metal surfaces, a muted palette of dark bronze, tarnished silver "
    "and black.")
"""v2, after looking at v1 (`sheet_v1.png`).  v1 drew the mirror as a SPOKED
CARTWHEEL -- "the size of a cartwheel" was a scale phrase and the drawer took it
as a shape -- and Wells's word is `mirror`: "that thin mast upon which their
restless mirror wobbled".  It also drew the dome at a man's height against its
own scale silhouette, where the dossier says a haystack.  So the scale phrase is
now a measure ("four feet across") and the shape is stated positively as solid
and unbroken, and the man is told what fraction of the dome he reaches."""


SCALE = ("The mast stands about three times a man's height above the pit rim; the mirror disk is "
         "about four feet across; the humped dome is about the size of a haystack.")
"""v2 of the scale line, and it is a RETREAT from the dossier's "about as tall as
a church spire above the pit rim".  `pack_refs.prop_row` sends the first clause
of this to every take block, and the SHEET draws the rod about two men above the
dome's crown.  ep02 measured which of the two wins: "the hull towers many times
his height" changed nothing while the pit picture drew a coin two men tall -- the
picture outranks the words on size.  So the words are moved to the picture rather
than left to contradict it, and every shot's own `at_rest` fraction is sized
against the sheet: a 135 mm frame at a hundred yards is about 16 m tall, so a
6 m mast really is a third of it (shot 3) and a tenth of a 35 mm frame (shot 25).
A spire would need a redrawn sheet, and the chapter does not need one: Wells's
mast is "thin", and what matters is that the mirror is up there wobbling."""


def main() -> int:
    card = json.loads(CARD.read_text(encoding="utf-8"))
    design = card["profile"]["design"]
    if "scale_v1" not in design:
        design["scale_v1"] = card["profile"]["scale"]
    card["profile"]["scale"] = SCALE
    if "physical_v1" not in design:
        design["physical_v1"] = card["profile"]["physical"]
    if "sheet_prompt_v1" not in design:
        design["sheet_prompt_v1"] = design["sheet_prompt"]
    card["profile"]["physical"] = PHYSICAL
    design["sheet_prompt"] = SHEET
    CARD.write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")
    print(CARD)
    print(f"physical {len(PHYSICAL.split())} words; sheet_prompt {len(SHEET.split())} words")
    return 0


if __name__ == "__main__":
    sys.exit(main())
