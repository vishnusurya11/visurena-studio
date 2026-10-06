"""The ratchet: what the supervisor checks on the fixer's commit before it stands
(decision 2026-10-06).  Mechanical, run on the diff and the suite, never trusted
from the brain:

    1. red before green -- the commit carries a test that FAILS on the old code and
       PASSES on the new; a fix with no such test changed nothing provable
       (feedback_a_fix_that_changes_nothing);
    2. the allow set -- code, tests and the plan tracker; never library/, a verdict,
       a ledger, the yaml contracts, the lock, .claude or a decision;
    3. a quieter battery -- the gates over the last delivered plans may not report
       FEWER faults unless each removed fault is asserted a false positive;
    4. forbidden edits -- no terminal, ceiling, cap, wall, share or `guard_spend`
       moves (feedback_constants_outlive_their_world).

A refusal is a sentence; the supervisor reverts the commit on any.  The test runner
is injected (`run(ref, files) -> exit code`) so nothing here checks out or spends.
"""
from __future__ import annotations

import re
from collections.abc import Callable

ALLOW = ("studio/**/*.py", "scripts/**/*.py", "agents/**/*.py", "tests/**/*.py",
         "architecture/plan/*.md")
DENY = ("library/**", "**/*.verdict.json", "**/eye_*.json", "**/learnings.jsonl", "**/drive.jsonl",
        "gates.yaml", "models.yaml", "stages.yaml", "pyproject.toml", "uv.lock", ".claude/**",
        "docs/DECISIONS.md", "architecture/decisions/**")
FORBIDDEN = ("terminal:", "episode_ceiling_usd", "PLAN_LADDERS_MAX", "MAX_IMPROVE", "ROUNDS_CAP",
             "MAX_RUNS", "guard_spend")
_CAP = re.compile(r"[A-Z_]*(?:_CAP|_WALL|_SHARE|MAX_)[A-Z_]*\s*=\s*[\d.]+")
TEST_FILES = "tests/**/test_*.py"


def _regex(pattern: str) -> re.Pattern:
    """A path glob as a regex: `**/` spans folders, `*` and `?` stay inside one."""
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] in "*?":
            out, i = out + ("[^/]*" if pattern[i] == "*" else "[^/]"), i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(f"^{out}$")


def matches(path: str, pattern: str) -> bool:
    return bool(_regex(pattern).match(path.replace("\\", "/")))


def new_test_files(diff_names: list[str]) -> list[str]:
    """The test files in the commit: what red-before-green runs."""
    return [name for name in diff_names if matches(name, TEST_FILES)]


def red_before_green(run: Callable[[str, list[str]], int], sha_old: str, sha_new: str,
                     test_files: list[str]) -> str | None:
    """None when the tests fail on the old code and pass on the new; else why not."""
    if not test_files:
        return "no test file in the commit: a fix proves itself with a test that failed before it"
    if run(sha_old, test_files) == 0:
        return f"the tests pass on the old code {sha_old}: they do not catch what the fix changes"
    if run(sha_new, test_files) != 0:
        return f"the tests fail on the new code {sha_new}"
    return None


def outside_allow_set(diff_names: list[str], allow: tuple = ALLOW, deny: tuple = DENY) -> list[str]:
    """Every path that is denied, or allowed by nothing."""
    return [name for name in diff_names
            if any(matches(name, d) for d in deny) or not any(matches(name, a) for a in allow)]


def changed_lines(diff_text: str) -> list[str]:
    """The added and removed lines of a unified diff, headers excluded."""
    return [line for line in diff_text.splitlines()
            if line[:1] in "+-" and not line.startswith(("+++", "---"))]


def forbidden_edits(diff_text: str) -> list[str]:
    """Changed lines that move a terminal, a ceiling, a cap, a wall, a share or the wall's guard."""
    return [line for line in changed_lines(diff_text)
            if any(word in line for word in FORBIDDEN) or _CAP.search(line)]


def quieter_battery(before: dict[str, int], after: dict[str, int],
                    asserted_false_positives: set[str]) -> list[str]:
    """Per delivered plan: fewer faults after the fix, with no assertion, is a gate gone quiet."""
    refusals = []
    for plan, faults in before.items():
        now = after.get(plan, 0)
        if now < faults and plan not in asserted_false_positives:
            refusals.append(f"{plan}: {faults} -> {now} faults, none asserted a false positive")
    return refusals


def check(diff_names: list[str], diff_text: str, run: Callable[[str, list[str]], int],
          sha_old: str, sha_new: str, before: dict[str, int], after: dict[str, int],
          asserted: set[str]) -> list[str]:
    """The four together; an empty list lets the commit stand."""
    refusals = [f"outside the allow set: {name}" for name in outside_allow_set(diff_names)]
    red_green = red_before_green(run, sha_old, sha_new, new_test_files(diff_names))
    if red_green:
        refusals.append(red_green)
    refusals += [f"forbidden edit: {line.strip()}" for line in forbidden_edits(diff_text)]
    refusals += [f"quieter battery: {why}" for why in quieter_battery(before, after, asserted)]
    return refusals
