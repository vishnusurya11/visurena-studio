r"""Burned-in captions for a 9:16 episode: phrases, timed, inside the safe box.

Most viewers read the episode (69 % watch with sound off in public, rule 17),
so every line is captioned, phrase by phrase (Kruger 2013: short segments beat
sentences), in the lower-middle third where no platform's UI sits, with the
speaker's name on a line whose face is not on screen (DCMP, rule 18) -- the
one caption rule that is specific to voice-over-over-cutaways.

Every ASS override below is a RAW string: \N, \fs and \an collide with Python
escapes and libass drops what it cannot parse in silence (see `ass_title`).
"""
from __future__ import annotations

MAX_WORDS = 3
MAX_CHARS = 24
"""One to three words on screen at a time, never more than 24 characters."""
LEAD_MS = 80
TAIL_MS = 150
MIN_ON_MS = 300
"""A phrase shows from just before its first word to just after its last."""
FONT = "Arial"
SAFE_BOTTOM = 1436 / 1920
"""Below this the TikTok/Reels/Shorts UI can cover the caption (rule 17)."""
BASELINE = 0.69
"""Where the caption's bottom edge sits: lower-middle third, above the safe line."""
COLOUR, OUTLINE = "&H00FFFFFF", "&H00000000"


def phrases(text: str, max_words: int = MAX_WORDS, max_chars: int = MAX_CHARS) -> list[str]:
    """Split a line into caption phrases, breaking at punctuation first."""
    out, current = [], []
    for word in text.split():
        candidate = " ".join(current + [word])
        if current and (len(current) >= max_words or len(candidate) > max_chars):
            out.append(" ".join(current))
            current = []
        current.append(word)
        if word[-1] in ".!?;:,":
            out.append(" ".join(current))
            current = []
    if current:
        out.append(" ".join(current))
    return out


def timed(parts: list[str], at: float, seconds: float) -> list[tuple[float, float, str]]:
    """Each phrase's window, shared out by word count across the measured line.

    Windows never overlap: a phrase ends exactly where the next begins, and
    only the last one keeps a tail.  The first master (2026-09-10) showed two
    phrases stacked on screen because every phrase led by 80 ms and trailed
    by 150 ms -- the next line's start sat inside the previous line's tail."""
    words = [len(p.split()) for p in parts]
    total = sum(words) or 1
    starts, t = [], at
    for count in words:
        starts.append(t)
        t += seconds * count / total
    out = []
    for i, part in enumerate(parts):
        start = max(0.0, starts[i] - (LEAD_MS / 1000 if i == 0 else 0))
        end = starts[i + 1] if i + 1 < len(parts) else starts[i] + seconds * words[i] / total + TAIL_MS / 1000
        out.append((start, max(end, start + MIN_ON_MS / 1000), part))
    return out


def stamp(t: float) -> str:
    return f"{int(t // 3600)}:{int(t // 60) % 60:02d}:{t % 60:05.2f}"


def header(width: int, height: int) -> str:
    size = round(height * 0.042)
    margin_v = round(height * (1 - BASELINE))
    chip = round(height * 0.024)
    return (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {width}\nPlayResY: {height}\nWrapStyle: 2\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour,"
        " Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle,"
        " BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Cap,{FONT},{size},{COLOUR},{OUTLINE},&H80000000,-1,0,0,0,100,100,0,0,1,4,0,2,"
        f"{round(width * 0.06)},{round(width * 0.06)},{margin_v},1\n"
        f"Style: Chip,{FONT},{chip},&H00DAE6ED,{OUTLINE},&H00000000,-1,0,0,0,100,100,2,0,1,3,0,8,"
        f"60,60,{round(height * 0.08)},1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")


def caption_event(start: float, end: float, text: str, speaker: str | None) -> str:
    """One phrase; the speaker's name above it when their face is not on screen."""
    name = (r"{\fs" + "28" + r"}" + speaker.upper() + r"{\r}\N") if speaker else ""
    return f"Dialogue: 0,{stamp(start)},{stamp(end)},Cap,,0,0,0,,{name}{text}\n"


def chip_event(text: str, seconds: float) -> str:
    """The series chip, top-safe, for the first seconds (rule 19)."""
    return f"Dialogue: 0,{stamp(0)},{stamp(seconds)},Chip,,0,0,0,,{text}\n"


def script(width: int, height: int, lines: list[dict], chip: str = "",
           chip_seconds: float = 3.0) -> str:
    """The whole ASS file: `lines` carry text, at, seconds, speaker, on_screen."""
    events = [chip_event(chip, chip_seconds)] if chip else []
    for line in lines:
        label = None if line.get("on_screen") else line["speaker"].replace("_", " ")
        for i, (start, end, text) in enumerate(timed(phrases(line["text"]), line["at"],
                                                     line["seconds"])):
            events.append(caption_event(start, end, text, label if i == 0 else None))
    return header(width, height) + "".join(events)
