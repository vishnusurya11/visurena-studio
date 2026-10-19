"""The episode desk's generated views of the registry: the command table and the step
algorithm (SKILL.md), the Step caps table and the clock table (GATES.md).

    uv run python scripts/episode/commands.py            # print the command table
    uv run python scripts/episode/commands.py --write    # rewrite every view inside SKILL.md and GATES.md

The skill is the owner's desk over the runner; its list of commands, its caps and its
clocks are therefore VIEWS of stages.yaml and studio/run_budget, never typed.  A test
asserts each copy equals this output, so a registry change that forgets the desk fails
(the caps table was typed by hand until the Jekyll Kawajiri ep01 retro, P16).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import registry, repair_clock, run_budget, step_caps  # noqa: E402

SKILL = ROOT / ".claude" / "skills" / "episode" / "SKILL.md"
GATES = ROOT / ".claude" / "skills" / "episode" / "GATES.md"
OPEN, CLOSE = "<!-- registry:{stage} -->", "<!-- /registry:{stage} -->"


def first_sentence(text: str) -> str:
    text = " ".join(text.split())
    for mark in (". ", "; "):
        if mark in text:
            return text.split(mark, 1)[0] + "."
    return text


def row(stage: str, step: dict, args: str) -> str:
    cmd = f"`uv run python scripts/{stage}/{step['script']}.py {args}`"
    return f"| {step['id']} | {step['name']} | {cmd} | {first_sentence(step['desc'])} |"


def table(stage: str = "episode", args: str = "<book> <n>") -> str:
    lines = [f"| step | name | alone | what it does |", "|---|---|---|---|"]
    lines += [row(stage, step, args) for step in registry.steps(stage)]
    return "\n".join(lines)


def minutes(seconds: float) -> str:
    m = seconds / 60
    return str(int(m)) if m == int(m) else f"{m:g}"


def per_of(cap: step_caps.Cap) -> str:
    return f"climb ({cap.climbs} climbs per episode)" if cap.per == "climb" else cap.per


def cap_row(cap: step_caps.Cap) -> str:
    return f"| {cap.step} | {cap.name} | {cap.rounds} | {per_of(cap)} | {minutes(cap.wall_s)} | {cap.gate} |"


def caps_table(stage: str = "episode") -> str:
    """GATES.md "Step caps": one row per stages.yaml `caps:` row, in file order."""
    lines = ["| step | phase | rounds | per | wall min | gate |", "|---|---|---|---|---|---|"]
    return "\n".join(lines + [cap_row(c) for c in step_caps.table(stage).values()])


def cap_words(cap: step_caps.Cap) -> str:
    climbs = f" x{cap.climbs}" if cap.per == "climb" else ""
    gate = f", gate {cap.gate}" if cap.gate else ""
    return f"{cap.name} {cap.rounds}/{cap.per}{climbs}, {minutes(cap.wall_s)} min{gate}"


def algorithm_line(stage: str, step: dict) -> str:
    caps = [cap_words(c) for c in step_caps.table(stage).values() if c.step == step["id"]]
    return f"{step['id']} {step['name']:<9} caps: " + "; ".join(caps) if caps else f"{step['id']} {step['name']}"


ALGORITHM_HEAD = [
    "RUN(book, n): the autopilot launches drive.py; you read the disk, never call a step",
    "  clock    = the union of the episode's run spans, never reset (GATES clock table)",
    "  counters = attempts.json, per episode: a relaunch, a resume or a retry never resets one",
    "  FOR each step in order, skipping a step whose outputs are current:",
    "    log 'STEP <id> start'; run its ladder; a round is a change of bytes",
    "    pass -> next | cap -> 'CAP <phase>: ...', keep best, sign flagged, next",
    "    ruler fault -> park; fix the gate test-first; retry N | SAFETY -> park by its name",
]


def algorithm(stage: str = "episode") -> str:
    """SKILL.md's step algorithm: the loop, then one line per registry step with its cap rows."""
    body = [algorithm_line(stage, step) for step in registry.steps(stage)]
    return "\n".join(["```"] + ALGORITHM_HEAD + body + ["```"])


def clock_rows() -> list[tuple[str, str, str, str]]:
    return [
        ("rung ceiling", f"{run_budget.EPISODE_CEILING_SECONDS // 60} min",
         "run_budget.EPISODE_CEILING_SECONDS", "past it every rung is terminal, signed flagged; firsts still render"),
        ("owner limit", f"{run_budget.OWNER_LIMIT_SECONDS // 60} min", "run_budget.OWNER_LIMIT_SECONDS",
         "a rescue rung runs only while spent + its price + the firsts owed fit (`Budget.leaves_reserve`)"),
        ("first-render wall", f"{minutes(step_caps.wall_s('takes'))} min", "stages.yaml caps.takes",
         "no new first render starts past it (between renders); attempts.json `takes.first` keeps it across launches"),
        ("repair cap", f"{minutes(repair_clock.cap_for(['09']))} min for a redo of 09", "repair_clock.cap_for",
         "an owner redo of a delivered episode: its own clock from its start; rungs and costly checks priced on it"),
        ("cheap check", f"{int(run_budget.CHEAP_CHECK_SECONDS)} s", "run_budget.CHEAP_CHECK_SECONDS",
         "a check this cheap always runs, whatever the clock"),
        ("dark budget", f"{run_budget.DARK_EPISODES_REQUIRED} episodes", "run_budget.DARK_EPISODES_REQUIRED",
         "a share-based cut is allowed only after this many dark (logged, never cutting) episodes"),
    ]


def clock_table() -> str:
    """GATES.md's one clock table, from studio/run_budget and stages.yaml."""
    lines = ["| clock | value | home | what it stops |", "|---|---|---|---|"]
    return "\n".join(lines + [f"| {a} | {b} | `{c}` | {d} |" for a, b, c, d in clock_rows()])


VIEWS = {SKILL: {"episode": lambda: table("episode"), "algorithm": algorithm},
         GATES: {"caps": caps_table, "clock": clock_table}}


def write_views() -> None:
    for path, views in VIEWS.items():
        text = path.read_text(encoding="utf-8")
        for name, render in views.items():
            text = render_into(text, name, render())
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {path}")


def render_into(text: str, stage: str, body: str) -> str:
    open_, close = OPEN.format(stage=stage), CLOSE.format(stage=stage)
    if open_ not in text or close not in text:
        raise ValueError(f"no {open_} ... {close} markers")
    head, rest = text.split(open_, 1)
    _, tail = rest.split(close, 1)
    return f"{head}{open_}\n{body}\n{close}{tail}"


def between(text: str, stage: str) -> str:
    open_, close = OPEN.format(stage=stage), CLOSE.format(stage=stage)
    return text.split(open_, 1)[1].split(close, 1)[0].strip()


def main(argv: list[str]) -> int:
    if "--write" in argv:
        write_views()
        return 0
    print(table("episode"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
