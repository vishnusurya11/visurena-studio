"""An owner-ordered redo has its own allowance (wall.<id>.order); a forged flag is refused (K12)."""
from types import SimpleNamespace

from studio import step_attempts, step_wall, work_orders


def _ctx(home, now):
    return SimpleNamespace(stage="episode", number=1, home=home, clock=lambda: now[0],
                           log=lambda *a, **k: None, book_dir=home)


def _step():
    return SimpleNamespace(STEP_ID="08", NAME="panels")


def test_recorded_is_true_only_with_a_taken_row(tmp_path):
    assert not work_orders.recorded(tmp_path, "08")
    work_orders.note_redos_taken(tmp_path, [{"kind": "redo", "step_id": "08", "id": 7}])
    assert work_orders.recorded(tmp_path, "08")
    work_orders.clear_taken(tmp_path, "08")
    assert not work_orders.recorded(tmp_path, "08")


def test_a_bump_row_is_no_order(tmp_path):
    work_orders.note_redos_taken(tmp_path, [{"kind": "bump", "step_id": "08", "id": 1}])
    assert not work_orders.recorded(tmp_path, "08")


def test_an_ordered_redo_books_to_order_not_the_cure_wall(tmp_path):
    work_orders.note_redos_taken(tmp_path, [{"kind": "redo", "step_id": "08", "id": 7}])
    now = [1000.0]
    ctx = _ctx(tmp_path, now)
    ctx.step_wall = step_wall.open_wall(ctx, _step())
    now[0] += 900
    assert ctx.step_wall.elapsed() == 0.0                     # the cure cap reads first-pass only
    step_wall.record_spent(ctx, ctx.step_wall)
    assert step_attempts.seconds(tmp_path, "wall.08") == 0.0
    assert step_attempts.seconds(tmp_path, "wall.08.order") == 900.0
    assert step_wall.charged(tmp_path, "08") == 900.0          # the 6 h clock counts both


def test_a_forged_flag_without_a_row_books_to_the_cure_wall(tmp_path):
    now = [1000.0]
    ctx = _ctx(tmp_path, now)
    ctx.order = True                                           # a flag nobody recorded
    ctx.step_wall = step_wall.open_wall(ctx, _step())
    now[0] += 120
    step_wall.record_spent(ctx, ctx.step_wall)
    assert step_attempts.seconds(tmp_path, "wall.08") == 120.0
    assert step_attempts.seconds(tmp_path, "wall.08.order") == 0.0
