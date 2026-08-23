"""Story-time dating: turn the book's own words into real calendar dates.

Owner decision 2026-08-23: no artificial "Day N" — use the timeline the book states.
A Study in Scarlet supplies real anchors ("the fourth of May, eighteen hundred and
forty-seven", "August 4th, 1860", "Tuesday, the 4th inst.") and real offsets
("Twenty-nine days", "about five years", "Three weeks"), so dates are computed, not
invented.

Two primitives, both text-only and deterministic:
  parse_date(text)      -> date | None    absolute dates, incl. spelled-out years
  parse_offset(text)    -> timedelta|None durations that ADVANCE the clock

Anything the text does not state stays unstated: callers mark such scenes
`date_confidence: "computed"` (chained from an anchor) or `"unknown"`.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"])}

_UNITS = {"day": 1, "week": 7, "fortnight": 14, "month": 30,
          "twelvemonth": 365, "year": 365, "hour": 0, "minute": 0}

_SMALL = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
          "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
          "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
          "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
          "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
          "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100}

_ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
             "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
             "eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14,
             "fifteenth": 15, "twentieth": 20, "thirtieth": 30}

_YEAR = re.compile(r"\b(1[6-9]\d{2})\b")


def words_to_number(text: str) -> int | None:
    """'eighteen hundred and forty-seven' -> 1847; 'twenty-nine' -> 29."""
    tokens = re.split(r"[\s-]+", text.lower().replace(",", ""))
    tokens = [t for t in tokens if t and t != "and"]
    if not any(t in _SMALL for t in tokens):
        return None
    total = current = 0
    for token in tokens:
        if token not in _SMALL:
            continue
        value = _SMALL[token]
        if value == 100:
            current = max(1, current) * 100
        else:
            current += value
        if current >= 1000:
            total, current = total + current, 0
    result = total + current
    return result or None


def parse_date(text: str, default_year: int | None = None) -> date | None:
    """An absolute date the TEXT states. Handles numeric and spelled-out forms."""
    low = (text or "").lower().strip()
    if not low:
        return None
    year = None
    match = _YEAR.search(low)
    if match:
        year = int(match.group(1))
    else:
        spelled = re.search(r"((?:eighteen|nineteen|seventeen)[\s-]+hundred"
                            r"(?:[\s-]+and)?(?:[\s-]+[a-z-]+)*)", low)
        if spelled:
            candidate = words_to_number(spelled.group(1))
            if candidate and 1600 <= candidate <= 1999:
                year = candidate
    month = next((n for name, n in MONTHS.items() if re.search(rf"\b{name}\b", low)), None)
    day = None
    numeric = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\b(?!\d)", low)
    if numeric:
        value = int(numeric.group(1))
        if not 1 <= value <= 31:
            return None                   # stated day is impossible -> distrust the parse
        day = value
    if day is None:
        for word, value in _ORDINALS.items():
            if re.search(rf"\b{word}\b", low):
                day = value
                break
    year = year or default_year
    if year is None or month is None:
        return None
    try:
        return date(year, month, day or 1)
    except ValueError:
        return None


def parse_offset(text: str) -> timedelta | None:
    """A duration that ADVANCES the clock. Returns None for vague or zero spans."""
    low = (text or "").lower().strip()
    if not low:
        return None
    unit = next((u for u in _UNITS if re.search(rf"\b{u}s?\b", low)), None)
    if unit is None or _UNITS[unit] == 0:
        return None
    count = 1
    numeric = re.search(r"\b(\d+)\b", low)
    if numeric:
        count = int(numeric.group(1))
    else:
        spelled = words_to_number(low)
        if spelled:
            count = spelled
        elif re.search(r"\ba few\b|\bseveral\b", low):
            count = 3
        elif re.search(r"\bsome\b|\ba couple\b", low):
            count = 2
    if count > 400:                       # a misparse, not a real span
        return None
    return timedelta(days=count * _UNITS[unit])


def format_date(value: date) -> str:
    return f"{value.day} {value.strftime('%B')} {value.year}"


# --- time of day -----------------------------------------------------------------
# DAY/NIGHT is the film-breakdown convention, but the book is more precise than that
# ("noon exactly", "after ten at night", "That very evening"). Keep the precision:
# a label for display and an hour for ordering/daylight.

_PARTS = [                                   # longest / most specific first
    ("midnight", "midnight", 0),
    ("daybreak", "dawn", 6), ("break of day", "dawn", 6), ("sunrise", "dawn", 6),
    ("dawn", "dawn", 6),
    ("noon", "noon", 12), ("midday", "noon", 12),
    ("afternoon", "afternoon", 15),
    ("evening", "evening", 19), ("dusk", "dusk", 20), ("sunset", "dusk", 20),
    ("twilight", "dusk", 20), ("nightfall", "dusk", 20),
    ("morning", "morning", 9), ("forenoon", "morning", 9),
    ("night", "night", 22),
]

_CLOCK = re.compile(
    r"\b(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    r"\s*(?:o'clock|o’clock|:\d{2})", re.IGNORECASE)


def _label_for_hour(hour: int) -> str:
    if hour < 5:
        return "early hours"
    if hour < 12:
        return "morning"
    if hour == 12:
        return "noon"
    if hour < 17:
        return "afternoon"
    if hour < 21:
        return "evening"
    return "night"


def parse_time_of_day(text: str) -> tuple[str, int] | None:
    """'after ten at night' -> ('night', 22); 'at noon' -> ('noon', 12)."""
    low = (text or "").lower()
    if not low.strip():
        return None
    part = next(((label, hour) for token, label, hour in _PARTS
                 if re.search(rf"\b{re.escape(token)}\b", low)), None)
    clock = _CLOCK.search(low)
    if clock:
        raw = clock.group(1)
        hour = int(raw) if raw.isdigit() else _SMALL.get(raw, 0)
        if 1 <= hour <= 12:
            if part and part[1] >= 12 and hour < 12:      # "ten at night"
                hour += 12
            elif not part and hour < 8:                    # bare small hour -> evening
                hour += 12
            return _label_for_hour(hour), hour
    return part


def finest_time_of_day(texts: list[str]) -> tuple[str, int] | None:
    """The most precise time-of-day among several phrases (a clock beats a part)."""
    best = None
    for text in texts:
        parsed = parse_time_of_day(text)
        if not parsed:
            continue
        precise = bool(_CLOCK.search((text or "").lower())) or parsed[0] in (
            "noon", "midnight", "dawn", "dusk")
        rank = 2 if precise else 1
        if best is None or rank > best[0]:
            best = (rank, parsed)
    return best[1] if best else None


def daylight(hour: int) -> str:
    """The film-breakdown binary, derived from the hour."""
    return "DAY" if 6 <= hour < 20 else "NIGHT"
