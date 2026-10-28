"""G-VARIETY's close cap is cured for free: the excess close shots of a face are widened to medium.

Jekyll ep05 (2026-10-28): 13 close/medium_close shots on Utterson against the grammar's 12. The plan's
climbs oscillated between it and G-SHOTS, PLAN kept best, and step 06 refused the same authoring
gate -- a fail-closed refusal on a spent ladder (brick 8).  A two-person medium close is widened
first (G-TWO: a two-person reaction is a medium), never an over-the-shoulder before a plain one.
"""
from studio import plan_cures as pc


def shot(i, size, faces, frame):
    return {"index": i, "size": size, "faces": faces, "frame": frame}


def plan(n_extra: int) -> dict:
    shots = [shot(0, "medium_close", ["u", "p"], "Medium close of the lawyer and Poole at the door."),
             shot(1, "medium_close", ["u", "g"], "Medium close over the clerk's shoulder toward the lawyer.")]
    shots += [shot(2 + k, "close", ["u"], "Close of the lawyer.") for k in range(n_extra)]
    return {"grammar": "anime_tv", "shots": shots}


def test_the_lint_row_routes_to_the_free_cure():
    assert pc.cure_for("G-VARIETY plan: close/medium_close shots on 'u', measured 13 against 12") == \
        "widen_face_closes"


def test_one_over_widens_the_plain_two_shot_and_its_words():
    doc = pc.widen_face_closes(plan(11))                       # 13 on 'u'
    first = doc["shots"][0]
    assert first["size"] == "medium" and first["frame"].startswith("Medium shot of the lawyer and Poole")
    assert doc["shots"][1]["size"] == "medium_close"
    assert sum(s["size"] in ("close", "medium_close") for s in doc["shots"]) == 12


def test_at_the_cap_nothing_moves():
    doc = pc.widen_face_closes(plan(10))                       # 12 on 'u'
    assert [s["size"] for s in doc["shots"]][:2] == ["medium_close", "medium_close"]
