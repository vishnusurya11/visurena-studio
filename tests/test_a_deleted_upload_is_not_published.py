"""Owner 2026-10-28: deleted Jekyll ep05 from YouTube, then "fix episode 5". The autopilot read the
ep05 upload row (public) and never picked the episode again: a deleted video still counted as
published. Rows are read in order: a `deleted` row cancels the uploads before it; a later public
upload counts again."""
from studio import autopilot

UP = {"episode": 5, "privacy": "public", "video_id": "uwkQRbf5oUg"}
GONE = {"episode": 5, "video_id": "uwkQRbf5oUg", "deleted": True}


def test_a_deleted_episode_is_picked_again():
    assert autopilot.next_unit([4, 5], [{"episode": 4, "privacy": "public"}, UP, GONE], [], 5) == 5


def test_a_reupload_after_the_delete_is_published():
    assert autopilot.next_unit([5], [UP, GONE, {**UP, "video_id": "new"}], [], 5) is None


def test_published_reads_the_delete_too():
    assert not autopilot.published([UP, GONE], 5)
    assert autopilot.published([UP], 5)
