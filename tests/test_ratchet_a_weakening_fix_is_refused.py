"""The ratchet is run by the supervisor on the fixer's commit and never trusted from
the brain (decision 2026-10-06, §The ratchet): (1) the commit adds a test that fails
on the old code and passes on the new; (2) every path stays inside the allow set;
(3) the battery over the last delivered plans may not go quieter unless each removed
fault is asserted a false positive; (4) no cap, wall, share, terminal or ceiling
moves.  `feedback_a_fix_that_changes_nothing` and
`feedback_constants_outlive_their_world` as code.  A clean fix passes all four."""
from __future__ import annotations

from studio import ratchet


def _runner(fails_on_old: bool = True, passes_on_new: bool = True):
    """An injected test runner: (ref, files) -> exit code.  Nothing is checked out."""
    def run(ref: str, files: list[str]) -> int:
        if ref == "old":
            return 1 if fails_on_old else 0
        return 0 if passes_on_new else 1
    return run


WEAKENING = "--- a/studio/plan_gates.py\n+++ b/studio/plan_gates.py\n-NARRATION_WALL = 75\n+NARRATION_WALL = 95\n"
CLEAN = ("--- a/studio/plan_cures.py\n+++ b/studio/plan_cures.py\n"
         "-    return text\n+    return text.replace('shot', 'take')\n")


# --- (4) forbidden edits ----------------------------------------------------------

def test_a_moved_wall_is_a_forbidden_edit():
    assert ratchet.forbidden_edits(WEAKENING) == ["-NARRATION_WALL = 75", "+NARRATION_WALL = 95"]


def test_every_named_constant_and_the_terminal_key_are_forbidden():
    for line in ("+PLAN_LADDERS_MAX = 2", "+MAX_IMPROVE = 3", "+ROUNDS_CAP = 4", "+MAX_RUNS = 9",
                 "-  terminal: flag", "+    episode_ceiling_usd: 5.00",
                 "+def guard_spend(ctx):", "+QUIET_SHARE = 0.5", "+MAX_TAKES = 3"):
        assert ratchet.forbidden_edits(f"--- a/x\n+++ b/x\n{line}\n") == [line], line


def test_an_unchanged_context_line_and_a_file_header_are_not_edits():
    diff = "--- a/studio/take_ladder.py\n+++ b/studio/take_ladder.py\n ROUNDS_CAP = 2\n+    x = 1\n"
    assert ratchet.forbidden_edits(diff) == []


def test_a_clean_diff_has_no_forbidden_edit():
    assert ratchet.forbidden_edits(CLEAN) == []


# --- (1) red before green ---------------------------------------------------------

def test_the_test_files_are_the_tests_in_the_diff():
    names = ["studio/x.py", "tests/test_x_is_cured.py", "tests/fixtures/x.json", "tests/conftest.py"]
    assert ratchet.new_test_files(names) == ["tests/test_x_is_cured.py"]


def test_a_fix_without_a_test_is_refused():
    assert "test" in ratchet.red_before_green(_runner(), "old", "new", [])


def test_a_test_that_passes_on_the_old_code_is_refused():
    why = ratchet.red_before_green(_runner(fails_on_old=False), "old", "new", ["tests/test_x.py"])
    assert why and "old" in why


def test_a_test_that_fails_on_the_new_code_is_refused():
    why = ratchet.red_before_green(_runner(passes_on_new=False), "old", "new", ["tests/test_x.py"])
    assert why and "new" in why


def test_red_then_green_passes():
    assert ratchet.red_before_green(_runner(), "old", "new", ["tests/test_x.py"]) is None


# --- (2) the allow set ------------------------------------------------------------

def test_a_path_under_library_is_outside_the_allow_set():
    assert ratchet.outside_allow_set(["library/book/episodes/ep20/plan.json"]) == [
        "library/book/episodes/ep20/plan.json"]


def test_every_denied_shape_is_refused_even_under_an_allowed_folder():
    bad = ["tests/fixtures/ep05/plan.verdict.json", "studio/eye_takes.json",
           "scripts/learnings.jsonl", "x/drive.jsonl", "gates.yaml", "models.yaml", "stages.yaml",
           "pyproject.toml", "uv.lock", ".claude/settings.json", "docs/DECISIONS.md",
           "architecture/decisions/2026-10-06_x.md"]
    assert ratchet.outside_allow_set(bad) == bad


def test_code_tests_and_the_plan_tracker_are_inside():
    good = ["studio/brain.py", "studio/judges/eye.py", "scripts/episode/drive.py",
            "agents/episode_writer.py", "tests/test_x.py", "architecture/plan/2026-10-06_x.md"]
    assert ratchet.outside_allow_set(good) == []


def test_a_backslash_path_is_read_as_the_same_path():
    assert ratchet.outside_allow_set(["library\\book\\x.json", "studio\\x.py"]) == ["library\\book\\x.json"]


def test_a_file_neither_allowed_nor_denied_is_outside():
    assert ratchet.outside_allow_set(["README.md", "docs/audit/x.md"]) == ["README.md", "docs/audit/x.md"]


# --- (3) a quieter battery --------------------------------------------------------

def test_fewer_faults_without_an_assertion_is_refused():
    before, after = {"ep16": 3, "ep17": 2, "ep18": 0}, {"ep16": 3, "ep17": 0, "ep18": 0}
    assert ratchet.quieter_battery(before, after, set()) == ["ep17: 2 -> 0 faults, none asserted a false positive"]


def test_fewer_faults_asserted_as_false_positives_pass():
    before, after = {"ep16": 3, "ep17": 2}, {"ep16": 3, "ep17": 0}
    assert ratchet.quieter_battery(before, after, {"ep17"}) == []


def test_the_same_or_more_faults_pass():
    assert ratchet.quieter_battery({"ep16": 3}, {"ep16": 4}, set()) == []
    assert ratchet.quieter_battery({"ep16": 3}, {"ep16": 3}, set()) == []


# --- check(): the four together ---------------------------------------------------

def test_a_weakening_fix_is_refused_on_two_counts():
    why = ratchet.check(["studio/plan_gates.py"], WEAKENING, _runner(), "old", "new",
                        {"ep17": 2}, {"ep17": 0}, set())
    assert any("test" in w for w in why) and any("NARRATION_WALL" in w for w in why)
    assert any("ep17" in w for w in why)


def test_a_fix_that_touches_library_is_refused():
    why = ratchet.check(["studio/x.py", "library/book/plan.json", "tests/test_x.py"], CLEAN,
                        _runner(), "old", "new", {}, {}, set())
    assert why == ["outside the allow set: library/book/plan.json"]


def test_a_clean_fix_with_a_red_then_green_test_passes():
    why = ratchet.check(["studio/plan_cures.py", "tests/test_shot_is_cured.py"], CLEAN, _runner(),
                        "old", "new", {"ep17": 2}, {"ep17": 2}, set())
    assert why == []
