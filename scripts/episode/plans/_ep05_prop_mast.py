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
    "like a mirror. Below it the humped black back of a Martian appliance lifts over the rim of "
    "the pit, a smooth dark dome with a shallow funnel mouth set in its front.")

SHEET = (
    "Prop reference sheet for the Martian mast, mirror and humped appliance at the Horsell "
    "sand-pit from The War of the Worlds, 1898, on a plain neutral grey backdrop in even soft "
    "light. The mast is a thin jointed rod of dark bronze in telescoping segments standing "
    "upright, crowned at its apex by a polished silver disk the size of a cartwheel tilted over on "
    "a short yoke. The appliance is a smooth humped dome of black metal the size of a haystack, "
    "with a shallow funnel mouth set in its front and a faint shimmer of heat standing over the "
    "mouth. Three views side by side: the whole mast from the side, the disk and its yoke from "
    "below, and the dome in three-quarter view with the mast rising behind it. A standing "
    "Victorian gentleman in a frock coat, drawn small and dark in flat silhouette, stands beside "
    "the dome for scale. Matte metal surfaces, a muted palette of dark bronze, tarnished silver "
    "and black.")


def main() -> int:
    card = json.loads(CARD.read_text(encoding="utf-8"))
    design = card["profile"]["design"]
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
