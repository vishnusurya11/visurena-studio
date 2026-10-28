"""The plan battery's lines, tagged BUILDER or JUDGED (C3_verdict #5 (iv), D3).

A BUILDER line is a refusal a downstream script repeats: a plan that carries
one cannot be built, so "ship the best plan at the ceiling" would crash at
step 06/07/09 and relaunch-loop.  Every other battery line is JUDGED -- taste
and authoring rules nothing downstream refuses -- and at a spent clock it
ships flagged.  Each BUILDER label cites the script that repeats it; the list
was read from the code (2026-10-11), not from the verdict's draft: G-LIGHT,
PLAN GATES, MOTION hard and ACTOR are repeated downstream, ONE PER TAKE is not
(`episode_takes.groups` packs a run; no builder refuses one).
"""
from __future__ import annotations

BUILDER: dict[str, str] = {
    "CONTRACT": "episode_home.load_plan: every step reads the plan through the contract",
    "G-LIGHT": "takes_r2v.opened: house_style.faults raises 'G-LIGHT refuses the plan' (steps 06, 09)",
    "PLAN GATES": "takes_r2v.opened: plan_gates.chapter_faults raises 'the plan fails the authoring gates'",
    "TAKE LENGTH": "takes_r2v.refuse_long_shots: 'longer than a take' (steps 06, 09)",
    "TAKE BUILDER": "takes_r2v.refuse_long_shots / refuse_still_motions, called by plan_check itself",
    "MOTION hard": "takes_r2v.refuse_still_motions and seq_boards' motion refusal (steps 07, 09)",
    "G-TAKELINT": "takes_r2v.prompts: the step-06 take lint ('take prompts refused')",
    "CAST BOUND": "seq_boards.unbound_cast: 'the cast is not bound' (step 07)",
    "ACTOR": "seq_boards: actor_gate.hard_episode, 'the plan fails the actor gate' (step 07)",
    "G-ALIKE": "takes_r2v.refuse_alike: cast_alike.faults, two cast who read as one person (step 06)",
}
CLEAN = ("clean", "all bound", "every shot", "legacy book", "no shot stages", "0")


def label_of(line: str) -> str | None:
    """The section a column-0 line opens (`LABEL : value`), or None for a
    detail line.  A contract refusal is `CONTRACT ...`; `CONTRACT OK` is not one."""
    if not line or line[0].isspace():
        return None
    if line.startswith("CONTRACT") and not line.startswith("CONTRACT OK"):
        return "CONTRACT"
    return line.split(":", 1)[0].strip() if ":" in line else None


def refusing(line: str) -> bool:
    """A header line whose value is not one of the clean answers."""
    value = line.split(":", 1)[1].strip() if ":" in line else ""
    return bool(value) and not value.startswith(CLEAN)


def builder_lines(lines: list[str]) -> list[str]:
    """The lines a downstream builder would refuse again: a refusing BUILDER
    header, a contract line, and the detail lines under a refusing BUILDER
    header (MOTION hard prints every soft motion under a clean header)."""
    out, open_ = [], False
    for line in lines:
        label = label_of(line)
        if label is not None:
            open_ = label in BUILDER and (label == "CONTRACT" or refusing(line))
            out += [line] if open_ else []
        elif open_ and line.strip():
            out.append(line)
    return out
