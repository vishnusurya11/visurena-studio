"""The take prompt for MiniMax H3: the official Start Frame skeleton, with the
shortest body that measured as holding the frame.

Skeleton (MiniMax's keyframe format): the alignment line, a blank line, then
`integrated_multimodal_description: [Shot 1] ...`, `overall_soundscape:`,
`non_diegetic_music: N/A`.  The storyboard panel is <Picture 1>, fully
referenced at 0.00 s.

Body, measured on one panel and seed four times (2026-09-10): every element
the prompt names, the model shows.  A paragraph describing the room pulled
the camera back to show the room; a paragraph describing a bystander's face
pulled that face into a hand close-up.  So the body is: the panel's own
frame text, the motion as ordered beats (prose positions -- the format keeps
timestamps for cuts), a framing LOCK, and the rules.  Nothing else.
"""
from __future__ import annotations

from studio import house_style
from studio.episode_spec import Episode, Shot

def style_line() -> str:
    """The style line for this run, from `studio.house_style`.

    This was a constant reading "1881 London". Episode 8 was drawn and
    rendered under it over an 1847 Utah desert, because `Episode.palette`
    was wired into the location plate alone and the fix was called done --
    13 of 13 sheet prompts and 28 of 28 take prompts carried the wrong
    place. The place is declared once per run now, in one module.
    """
    return house_style.live()
LOCK = ("The camera keeps the distance, height and lens of <Picture 1> for the whole shot: "
        "nothing outside the panel's frame is revealed, no pull-back, no widening, no "
        "re-framing. Everyone and everything stays exactly as drawn in <Picture 1>.")
RULES = ("Nobody speaks and no lips move; any listener keeps the mouth closed. One continuous "
         "shot, one camera idea, no cut, no morph. Realistic anatomy and hands. No captions, "
         "overlays or text.")
ALIGNMENT = ("For the target video, at 0.00 seconds into the target video, <Picture 1> "
             "(from [Shot 1]) is fully referenced.")


def beats(shot: Shot) -> list[str]:
    """`motion` split at semicolons, in playback order."""
    return [c.strip().rstrip(".") for c in shot.motion.split(";") if c.strip()]


def position(index: int, count: int) -> str:
    """Where a beat sits, in words: the format reserves timestamps for cuts."""
    if count == 1:
        return "Through the whole shot"
    if index == 0:
        return "At the start of the shot"
    if index == count - 1:
        return "In the final part of the shot"
    return "Halfway through the shot" if count == 3 else (
        "A third of the way through the shot" if index / (count - 1) < 0.45 else
        "Two thirds of the way through the shot")


def timeline(shot: Shot) -> str:
    rows = beats(shot)
    return " ".join(f"{position(i, len(rows))}, {clause}." for i, clause in enumerate(rows))


def description(shot: Shot) -> str:
    return (f"[Shot 1] {style_line()} Begin exactly from <Picture 1>: {shot.frame} {timeline(shot)} "
            f"In the final second every moving element comes to rest and the frame holds to "
            f"the cut. {LOCK} {RULES}")


SPEAK_RULES = ("One continuous shot, one camera idea, no cut, no morph. Realistic anatomy and "
               "hands. No captions, overlays or text.")


def speaking(shot: Shot, speaker: str, text: str) -> str:
    """The Start Frame body for a shot whose person speaks the line's own wav
    (measured: docs/analysis/research/episode-06-lipsync-h3.md §4)."""
    name = speaker.replace("_", " ").title()
    return (f"[Shot 1] {style_line()} Begin exactly from <Picture 1>: {shot.frame} At the start of the "
            f"shot {name} is silent for a quarter of a second, mouth closed. Then {name} (S1) "
            f"speaks to the person just off-screen, physically speaking with natural lip movement "
            f"on every syllable: <d>[English] {text}</d> {timeline(shot)} After the line "
            f"{name} falls silent, mouth closed, and the frame holds to the cut. {LOCK} "
            f"{SPEAK_RULES}")


def build(episode: Episode, shot: Shot) -> str:
    spoken = [l for l in (episode.lines_of(shot.index) if episode else []) if l.kind == "dialogue"]
    if spoken:
        line = spoken[0]
        name = line.speaker.replace("_", " ").title()
        return (f"{ALIGNMENT}\n\n"
                f"integrated_multimodal_description: {speaking(shot, line.speaker, line.text)}\n\n"
                f"overall_soundscape: {name}'s voice, close and dry, and the room's own tone; "
                f"no other voice.\n\n"
                f"non_diegetic_music: N/A")
    return (f"{ALIGNMENT}\n\n"
            f"integrated_multimodal_description: {description(shot)}\n\n"
            f"overall_soundscape: Room tone only; no spoken dialogue, no voice.\n\n"
            f"non_diegetic_music: N/A")
