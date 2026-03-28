"""Weekly grid management.

The grid is the master schedule: which genre airs on which day/time.
Each cell in the grid is a ScheduleSlot linked to a ShowConfig.

┌─────────┬───────────┬───────────┬───────────┬───────────┬───────────┬───────────┬───────────┐
│  Time   │    Sun    │    Mon    │    Tue    │    Wed    │    Thu    │    Fri    │    Sat    │
├─────────┼───────────┼───────────┼───────────┼───────────┼───────────┼───────────┼───────────┤
│  09:00  │           │  Horror   │           │  Mystery  │  Thriller │           │           │
│  20:00  │           │           │           │           │           │  Fairy    │           │
└─────────┴───────────┴───────────┴───────────┴───────────┴───────────┴───────────┴───────────┘
"""

from __future__ import annotations

from studio_orchestrator import db
from studio_orchestrator.models import ScheduleSlot


DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
DAY_ABBREVS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

# Mapping from day name/abbreviation to day_of_week integer
DAY_LOOKUP: dict[str, int] = {}
for i, (full, abbr) in enumerate(zip(DAY_NAMES, DAY_ABBREVS)):
    DAY_LOOKUP[full.lower()] = i
    DAY_LOOKUP[abbr.lower()] = i


def parse_day(day_str: str) -> int:
    """Parse a day string into a day_of_week integer (0=Sun, 6=Sat).

    Accepts: 'monday', 'mon', 'Monday', '1', etc.
    """
    day_str = day_str.strip().lower()
    if day_str in DAY_LOOKUP:
        return DAY_LOOKUP[day_str]
    if day_str.isdigit():
        val = int(day_str)
        if 0 <= val <= 6:
            return val
    raise ValueError(f"Invalid day: {day_str!r}. Use a day name (monday, mon) or number (0-6).")


def get_grid(db_path: str) -> list[ScheduleSlot]:
    """Get all active slots in the weekly grid, ordered by day and time."""
    return db.get_slots(db_path, active_only=True)


def add_slot(
    db_path: str,
    day: str,
    time_slot: str,
    genre: str,
    show_config_id: int | None = None,
) -> ScheduleSlot:
    """Add a new slot to the weekly grid.

    Args:
        db_path: Database path
        day: Day of week (name or number)
        time_slot: Time in HH:MM format
        genre: Genre for this slot
        show_config_id: Optional linked show config

    Returns:
        The created ScheduleSlot
    """
    day_of_week = parse_day(day)

    # Validate time format
    parts = time_slot.split(":")
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        raise ValueError(f"Invalid time format: {time_slot!r}. Use HH:MM.")
    hour, minute = int(parts[0]), int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Invalid time: {time_slot!r}.")
    time_normalized = f"{hour:02d}:{minute:02d}"

    slot = ScheduleSlot(
        day_of_week=day_of_week,
        time_slot=time_normalized,
        genre=genre,
        show_config_id=show_config_id,
    )
    slot_id = db.create_slot(db_path, slot)
    slot.id = slot_id
    return slot


def remove_slot(db_path: str, slot_id: int) -> bool:
    """Remove (deactivate) a slot from the grid."""
    return db.remove_slot(db_path, slot_id)


def format_grid(slots: list[ScheduleSlot]) -> str:
    """Format the weekly grid as a readable ASCII table."""
    # Collect unique time slots
    times = sorted({s.time_slot for s in slots})
    if not times:
        return "  (empty grid — no slots configured)"

    # Build grid data: grid[time][day] = genre
    grid: dict[str, dict[int, str]] = {t: {} for t in times}
    for slot in slots:
        label = slot.genre
        if slot.show_config_id:
            label += f" [#{slot.show_config_id}]"
        grid[slot.time_slot][slot.day_of_week] = label

    # Format table
    col_width = 12
    header = f"{'Time':>7} | " + " | ".join(f"{a:^{col_width}}" for a in DAY_ABBREVS) + " |"
    separator = "-" * len(header)

    lines = [separator, header, separator]
    for t in times:
        cells = []
        for day in range(7):
            cell = grid[t].get(day, "")
            cells.append(f"{cell:^{col_width}}")
        lines.append(f"{t:>7} | " + " | ".join(cells) + " |")
    lines.append(separator)

    return "\n".join(lines)
