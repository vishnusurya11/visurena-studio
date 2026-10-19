"""commits_after counts HEAD's lead over a sha and says 0 when git cannot answer."""
from studio import git_ahead


def test_head_is_zero_commits_ahead_of_itself():
    assert git_ahead.commits_after("HEAD") == 0


def test_an_unknown_sha_counts_zero():
    assert git_ahead.commits_after("0" * 40) == 0
