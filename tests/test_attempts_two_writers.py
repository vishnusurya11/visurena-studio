"""step_attempts.spend is a locked read-modify-write: two processes keep the counters exact
(P12; ep01 attempts.json had an unlocked spend)."""
import subprocess
import sys
import time

from studio import step_attempts

CHILD = ("import sys; from studio import step_attempts as a; "
         "[a.spend(sys.argv[1], 'k', 1.0) for _ in range(200)]")


def test_two_processes_x_200_spends_keep_the_counters_exact(tmp_path):
    procs = [subprocess.Popen([sys.executable, "-c", CHILD, str(tmp_path)]) for _ in range(2)]
    assert [p.wait(timeout=120) for p in procs] == [0, 0]
    assert step_attempts.count(tmp_path, "k") == 400
    assert step_attempts.seconds(tmp_path, "k") == 400.0


def test_a_stale_lock_is_broken(tmp_path):
    lock = tmp_path / (step_attempts.FILE + ".lock")
    lock.write_text("x")
    old = time.time() - 600
    import os
    os.utime(lock, (old, old))
    assert step_attempts.spend(tmp_path, "k", 2.0) == 1
    assert not lock.exists()
