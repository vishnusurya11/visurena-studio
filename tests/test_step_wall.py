"""The step wall is kill-proof: a heartbeat row (wall.<id>.live) is charged when the run dies."""
from studio import step_attempts, step_wall


def test_a_beat_writes_this_runs_absolute_seconds(tmp_path):
    step_wall.beat(tmp_path, "10", 41.26)
    assert step_attempts.seconds(tmp_path, "wall.10.live") == 41.3


def test_a_killed_step_is_charged_from_its_last_heartbeat(tmp_path):
    step_attempts.spend(tmp_path, "wall.10", 11.0)            # an earlier run's booked seconds
    step_wall.beat(tmp_path, "10", 600.0)                     # the run is killed after this beat
    assert step_attempts.elapsed(tmp_path, "wall.10") == 611.0


def test_the_next_open_folds_the_live_row_and_clears_it(tmp_path):
    step_wall.beat(tmp_path, "10", 600.0)
    assert step_wall.fold(tmp_path, "10") == 600.0
    assert step_attempts.seconds(tmp_path, "wall.10") == 600.0
    assert step_attempts.seconds(tmp_path, "wall.10.live") == 0.0
    assert step_attempts.elapsed(tmp_path, "wall.10") == 600.0


def test_a_clean_exit_never_double_counts(tmp_path):
    step_wall.beat(tmp_path, "10", 590.0)
    wall = step_wall.StepWall("10", 0, 0.0, clock=lambda: 600.0)
    step_wall.book(tmp_path, wall, order=False)
    assert step_attempts.elapsed(tmp_path, "wall.10") == 600.0


def test_the_heartbeat_thread_writes_then_stops(tmp_path):
    import time
    wall = step_wall.StepWall("10", 0, 0.0, clock=lambda: 5.0)
    heart = step_wall.Heartbeat(tmp_path, wall, every=0.01)
    heart.start()
    time.sleep(0.2)
    heart.stop()
    assert step_attempts.seconds(tmp_path, "wall.10.live") == 5.0
    assert not heart.is_alive()


FIX = __import__("pathlib").Path(__file__).parent / "fixtures" / "ep01_replay" / "P12"


def test_ep01_replay_charges_step_10s_killed_run_and_reads_charged_over_wall(tmp_path):
    """R8: attempts.json had wall.10 = 11.0 s while the killed av3 run spent ~48 min."""
    import shutil
    shutil.copy(FIX / "attempts.json", tmp_path / "attempts.json")
    step_attempts.set_seconds(tmp_path, "wall.10", 11.0)         # what the finally-written wall held
    step_wall.beat(tmp_path, "10", 2880.0)                         # the heartbeat the kill left
    ledger = step_wall.ledger(tmp_path)
    assert ledger["10"]["charged"] == 2891.0 and ledger["10"]["wall"] == 30 * 60
    assert ledger["08"]["charged"] == 3961.8 and "13" in ledger
    assert all(row["charged"] >= 0 for row in ledger.values())
