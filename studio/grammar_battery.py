"""The anime-TV grammar's battery: every framing, screenplay and capacity gate in
one call, so `plan_check`, the replay and the brief read one list (2026-10-17).

`faults` are the rows that refuse a plan declaring `grammar: anime_tv` before
anything is drawn; `advisories` print and refuse nothing.  Lengths read the voice
(`plan_gates.projected_place`).  $0.
"""
from __future__ import annotations

from studio import episode_capacity, framing_grammar as fg, plan_gates, screenplay_grammar as sg


def seconds(placed: dict) -> dict[int, float]:
    """{shot: projected seconds} from a placement."""
    return {s["index"]: float(s["seconds"]) for s in placed["shots"]}


def framing_faults(episode, secs: dict[int, float]) -> list[str]:
    """The rows a writer can move.  The voice-measured ones are `voice_advisories`."""
    return (fg.face_faults(episode) + fg.push_faults(episode) + fg.amount_faults(episode)
            + fg.ots_faults(episode) + fg.two_shot_faults(episode)
            + fg.payoff_faults(episode) + fg.unsupported_faults(episode))


def voice_advisories(episode, secs: dict[int, float]) -> list[str]:
    """Seconds and shares the RECORDED VOICE sets (G-WIDE, G-MEDIUM, G-INSERT, G-LOCKED):
    advice, never a refusal -- no writer rewrite moves them, and as walls they kept the
    Jekyll Kawajiri ep01 plan climb refusing for 30+ min (2026-10-18, cap every loop)."""
    return (fg.wide_faults(episode, secs) + fg.medium_faults(episode, secs)
            + fg.insert_faults(episode, secs) + fg.locked_faults(episode))


def screenplay_faults(episode, placed: dict) -> list[str]:
    return (sg.cold_open_faults(episode) + sg.act_out_faults(episode, placed) + sg.caption_faults(episode)
            + sg.reaction_faults(episode) + sg.ma_faults(episode) + sg.inner_faults(episode))


def faults(episode, rate: float) -> list[str]:
    """Every grammar refusal of this plan at the series rate and the recorded voice."""
    placed = plan_gates.projected_place(episode, rate)
    return (framing_faults(episode, seconds(placed)) + screenplay_faults(episode, placed)
            + episode_capacity.shot_faults(episode))


def advisories(episode, rate: float) -> list[str]:
    """What the grammar prints and never counts."""
    placed = plan_gates.projected_place(episode, rate)
    shots = len(fg.cut(episode))
    return (voice_advisories(episode, seconds(placed))
            + fg.full_advisories(episode, seconds(placed)) + sg.inner_advisories(episode)
            + sg.tease_advisories(episode) + motif_advisories(episode)
            + [f"G-SHOTS plan: {shots} shots, {episode_capacity.projected_hours(shots):.1f} h projected "
               f"(cap {episode_capacity.MAX_SHOTS})"])


def motif_advisories(episode) -> list[str]:
    """A grammar plan names the book's motif (its first episode's ritual image)."""
    if getattr(episode, "grammar", "") and not getattr(episode, "motif", ""):
        return ["G-MOTIF plan: the plan names no motif -- the hook and the tease return to the book's "
                "recurring image (advisory)"]
    return []


def band() -> dict:
    """Every grammar number, for the writer's brief."""
    from studio.episode_spec import STUDIO_GRAMMAR
    return {"grammar": STUDIO_GRAMMAR, **fg.band(), **sg.band(), "max_shots": episode_capacity.MAX_SHOTS}
