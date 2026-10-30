"""An owner's reopen of the panel ladder gives back a rung's seconds, not only its round (Jekyll ep06, 2026-10-29).

Order 69 reopened the ladder for G-WHO's panels 0/24/25.  `reopen` refunded the round, but the regrid row held
1310 s against a 1200 s wall, so `episode_spent` stayed True, `curable` said no, and the terminal sent all three
shots refs-only without a single redraw.  A fresh round now leaves exactly one rung's price under the wall."""
from studio import panel_ladder as pl
from studio import step_attempts, step_caps


def test_a_reopen_over_the_wall_leaves_one_rung(tmp_path):
    step_attempts.spend(tmp_path, pl.REGRID, 1310.3)
    assert pl.episode_spent(tmp_path)
    pl.reopen(tmp_path, 69)
    assert not pl.episode_spent(tmp_path)
    assert step_attempts.seconds(tmp_path, pl.REGRID) == step_caps.wall_s(pl.REGRID) - pl.RUNG_SECONDS


def test_a_reopen_under_the_wall_keeps_its_seconds(tmp_path):
    step_attempts.spend(tmp_path, pl.REGRID, 100.0)
    pl.reopen(tmp_path, 70)
    assert step_attempts.seconds(tmp_path, pl.REGRID) == 100.0


def test_the_refund_is_recorded_and_given_once_per_order(tmp_path):
    import json
    step_attempts.spend(tmp_path, pl.REGRID, 1310.3)
    pl.reopen(tmp_path, 69)
    step_attempts.add_seconds(tmp_path, pl.REGRID, 900.0)
    pl.reopen(tmp_path, 69)
    assert pl.episode_spent(tmp_path)
    row = json.loads((tmp_path / "storyboard" / "ladder.json").read_text())["reopened"][0]
    assert row["seconds_before"] == 1310.3
