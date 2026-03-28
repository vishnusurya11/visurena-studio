"""Show runner — manages a show's lifecycle.

Phase 0: config record + simple queries.
Phase 2+: evolves to LangGraph agent with creative autonomy.

A show runner knows:
- Which book it's drawing from
- Which episode it's on
- What art style and voice to use
- When its book runs out (and what to do next)
"""

from __future__ import annotations

from typing import Optional

from studio_orchestrator import db
from studio_orchestrator.models import (
    ApprovalStatus,
    CreativeConfig,
    ShowConfig,
    ShowStatus,
    Story,
)


class ShowRunner:
    """Manages a show's lifecycle.

    Phase 0: config record + simple queries.
    Phase 2+: LangGraph agent with creative autonomy.
    """

    def __init__(self, show: ShowConfig, db_path: str):
        self.show = show
        self.db_path = db_path

    def get_next_episode(self) -> Optional[Story]:
        """Return the next approved story for this show.

        Stories are ordered by their ID (insertion order from parser).
        The show's current_episode tracks how many have been produced.
        """
        stories = db.get_approved_stories(self.db_path, book_id=self.show.book_id)
        if not stories:
            return None

        # Skip already-produced episodes
        episode_idx = self.show.current_episode
        if episode_idx >= len(stories):
            return None

        return stories[episode_idx]

    def advance_episode(self) -> None:
        """Mark the current episode as produced and advance the counter."""
        new_episode = self.show.current_episode + 1
        db.update_show_episode(self.db_path, self.show.id, new_episode)
        self.show.current_episode = new_episode

        # Check if show is complete
        if self.show.total_episodes and new_episode >= self.show.total_episodes:
            db.complete_show(self.db_path, self.show.id)
            self.show.status = ShowStatus.COMPLETED

    def is_complete(self) -> bool:
        """Check if all episodes in this show have been produced."""
        if not self.show.total_episodes:
            return False
        return self.show.current_episode >= self.show.total_episodes

    def remaining_episodes(self) -> int:
        """How many episodes are left to produce."""
        if not self.show.total_episodes:
            return 0
        return max(0, self.show.total_episodes - self.show.current_episode)

    def pick_next_book(self, genre: str) -> Optional[str]:
        """When the current book runs out, find the next book by genre.

        Phase 0: Returns the first book with approved stories in the genre
                 that isn't the current book.
        Phase 2+: Uses LLM to pick based on audience data and story quality.
        """
        conn = db.get_connection(self.db_path)
        try:
            rows = conn.execute(
                """SELECT DISTINCT book_id FROM parsed_stories
                   WHERE human_approved = ? AND genre LIKE ? AND book_id != ?
                   ORDER BY book_id""",
                (ApprovalStatus.APPROVED.value, f"%{genre}%", self.show.book_id),
            ).fetchall()
            return rows[0]["book_id"] if rows else None
        finally:
            conn.close()

    def get_creative_config(self) -> CreativeConfig:
        """Return art style, voice, and narrative approach for this show."""
        return CreativeConfig(
            art_style=self.show.art_style,
            voice_profile=self.show.voice_profile,
            narrator_config=self.show.narrator_config,
        )
