"""Slot management — CRUD operations and slot-show linking.

Handles linking shows to slots, checking for conflicts, and managing
the relationship between the schedule grid and show configs.
"""

from __future__ import annotations

from typing import Optional

from studio_orchestrator import db
from studio_orchestrator.models import ScheduleSlot, ShowConfig


def link_show_to_slot(db_path: str, slot_id: int, show_config_id: int) -> None:
    """Link a show config to a schedule slot.

    Updates both the slot (adds show_config_id) and the show (adds slot_id).
    """
    conn = db.get_connection(db_path)
    try:
        conn.execute(
            "UPDATE schedule_slots SET show_config_id = ? WHERE id = ?",
            (show_config_id, slot_id),
        )
        conn.execute(
            "UPDATE show_configs SET slot_id = ?, updated_at = datetime('now') WHERE id = ?",
            (slot_id, show_config_id),
        )
        conn.commit()
    finally:
        conn.close()


def unlink_show_from_slot(db_path: str, slot_id: int) -> None:
    """Remove a show config from a schedule slot."""
    conn = db.get_connection(db_path)
    try:
        # Get current show_config_id before clearing
        row = conn.execute(
            "SELECT show_config_id FROM schedule_slots WHERE id = ?", (slot_id,)
        ).fetchone()
        if row and row["show_config_id"]:
            conn.execute(
                "UPDATE show_configs SET slot_id = NULL, updated_at = datetime('now') WHERE id = ?",
                (row["show_config_id"],),
            )
        conn.execute(
            "UPDATE schedule_slots SET show_config_id = NULL WHERE id = ?", (slot_id,)
        )
        conn.commit()
    finally:
        conn.close()


def get_slot_with_show(db_path: str, slot_id: int) -> tuple[Optional[ScheduleSlot], Optional[ShowConfig]]:
    """Get a slot and its linked show config."""
    slot = db.get_slot(db_path, slot_id)
    show = None
    if slot and slot.show_config_id:
        show = db.get_show_config(db_path, slot.show_config_id)
    return slot, show


def get_unlinked_slots(db_path: str) -> list[ScheduleSlot]:
    """Get active slots that don't have a show config linked."""
    all_slots = db.get_slots(db_path, active_only=True)
    return [s for s in all_slots if s.show_config_id is None]


def create_show_and_link(
    db_path: str,
    slot_id: int,
    name: str,
    book_id: str,
    genre: str,
    art_style: str = "classical_illustration",
    voice_profile: str = "default",
) -> ShowConfig:
    """Create a new show config and link it to a slot in one operation."""
    show = ShowConfig(
        name=name,
        book_id=book_id,
        genre=genre,
        art_style=art_style,
        voice_profile=voice_profile,
        slot_id=slot_id,
    )
    show_id = db.create_show_config(db_path, show)
    show.id = show_id

    # Link slot to show
    link_show_to_slot(db_path, slot_id, show_id)

    # Count total episodes for this book
    stories = db.get_stories(db_path, book_id=book_id)
    show.total_episodes = len(stories)
    conn = db.get_connection(db_path)
    try:
        conn.execute(
            "UPDATE show_configs SET total_episodes = ? WHERE id = ?",
            (show.total_episodes, show_id),
        )
        conn.commit()
    finally:
        conn.close()

    return show
