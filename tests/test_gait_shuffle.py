"""G-GAIT: a walker whose feet step fast while the body barely crosses the ground
is shuffling -- the feet must slide.  Jekyll HEL ep01 T03 (owner 2026-10-14: "the
little walk is weird"): 3.9 steps/s for 0.03 body heights per step."""
import cv2
import numpy as np

from studio import gait


def rows_of(freq: float, travel_hps: float, n: int = 60, h: float = 100.0, grow: float = 0.0) -> list[dict]:
    t = np.arange(n) / gait.FPS
    art = 2.0 + 1.5 * np.sin(2 * np.pi * freq * t)
    travel = travel_hps * h / gait.FPS
    return [{"feet": True, "h": h, "art": float(a), "travel": travel, "grow": grow} for a in art]


def test_a_subject_who_walks_is_a_walker():
    assert gait.walks("The camera pans across, travelling two strides at a walking pace, across the whole shot; "
                      "the little man stumps along the far pavement at a good walk at a walking pace")
    assert gait.walks("The camera tracks beside the little man as he walks at a walking pace toward the corner lamp")
    assert gait.walks("the girl runs at a walking pace as hard as she is able toward the corner")


def test_the_camera_travelling_strides_is_not_a_walker():
    assert not gait.walks("The camera tilts up from the near pavement to the flat grey plaster forehead, travelling "
                          "two strides at a walking pace, across the whole shot; Mr. Enfield lifts his cane")
    assert not gait.walks("his bony fingers turn over and grip his wrist; his clasped hands sway with each stride")


def test_cadence_reads_the_step_rate():
    freq, prominence = gait.cadence(rows_of(2.0, 0.8))
    assert abs(freq - 2.0) < 0.25
    assert prominence >= gait.PROMINENCE


def test_a_fast_step_that_crosses_no_ground_is_a_shuffle():
    m = gait.judge(rows_of(3.9, 0.12))
    assert m["state"] == "shuffle"
    assert m["step_h"] < gait.SHUFFLE_STEP


def test_a_real_walk_passes():
    assert gait.judge(rows_of(2.0, 0.8))["state"] == "walk"


def test_the_owner_liked_slow_step_passes():
    # WotW ep03 T07 (owner-liked): 3.1 steps/s for 0.055 heights a step
    assert gait.judge(rows_of(3.1, 0.17))["state"] == "walk"


def test_too_short_a_run_with_feet_is_not_measured():
    m = gait.judge(rows_of(3.9, 0.12, n=gait.MIN_RUN - 1))
    assert m["state"].startswith("unmeasured")


def test_a_walk_toward_the_camera_is_not_measured_by_ground_travel():
    m = gait.judge(rows_of(3.9, 0.12, grow=0.4))
    assert m["state"] == "unmeasured: depth"


def test_the_feet_out_of_frame_break_the_run():
    rows = rows_of(3.9, 0.12, n=80)
    for r in rows[20:60]:
        r["feet"] = False
    assert gait.judge(rows)["state"].startswith("unmeasured")


def test_row_is_na_by_the_plan_without_a_walker():
    g = gait.row({"state": "shuffle", "freq": 3.9, "step_h": 0.03}, "the camera holds; he lifts his hand")
    assert g.ok and g.value is None and "n/a" in g.note


def test_row_is_hard_on_a_shuffle():
    g = gait.row({"state": "shuffle", "freq": 3.9, "step_h": 0.03, "travel_hps": 0.12}, "he walks to the door")
    assert not g.ok and g.hard and g.penalty > 0
    assert "shuffle" in g.note


def test_row_passes_a_walk_and_says_not_measured_when_unread():
    walk = gait.row({"state": "walk", "freq": 2.0, "step_h": 0.4, "travel_hps": 0.8}, "he walks to the door")
    assert walk.ok and walk.value == 0.4
    unread = gait.row(None, "he walks to the door")
    assert unread.ok and unread.value is None and "not measured" in unread.note


def test_per_frame_reads_legs_that_ride_with_the_body_as_no_articulation():
    rng = np.random.default_rng(3)
    ground = (rng.random((384, 384)) * 255).astype(np.uint8)
    ground = cv2.GaussianBlur(ground, (5, 5), 0)
    figure = cv2.GaussianBlur((rng.random((100, 40)) * 120).astype(np.uint8), (5, 5), 0)
    a, b = ground.copy(), ground.copy()
    a[100:200, 150:190] = figure
    b[100:200, 153:193] = figure                # the whole figure slides 3 px, legs and all
    a, b = np.dstack([a] * 3), np.dstack([b] * 3)
    r = gait.per_frame(a, b, (153.0, 100.0, 193.0, 200.0))
    assert r["feet"] and r["travel"] > 1.0
    assert r["art"] < 0.5 * r["travel"]


def test_per_frame_with_the_feet_on_the_frame_edge_reads_no_feet():
    img = np.zeros((384, 384, 3), np.uint8)
    assert gait.per_frame(img, img, (100.0, 200.0, 140.0, 383.0)) == {"feet": False}


def test_measure_without_a_detector_is_not_measured():
    frames = [np.zeros((384, 384, 3), np.uint8)] * 30
    assert gait.measure(frames, detect=None)["state"].startswith("unmeasured")


def test_measure_reads_the_largest_person_each_frame():
    frames = [np.zeros((384, 384, 3), np.uint8)] * 4
    seen = []

    def detect(rgb):
        seen.append(rgb.shape)
        return [((10.0, 10.0, 30.0, 60.0), 0.9), ((100.0, 50.0, 160.0, 300.0), 0.8)]
    m = gait.measure(frames, detect=detect, stride=1)
    assert len(seen) == 3 and m["state"].startswith("unmeasured")
