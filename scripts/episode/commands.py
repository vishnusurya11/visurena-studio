"""The episode desk's command table, generated from the registry.

    uv run python scripts/episode/commands.py            # print the table
    uv run python scripts/episode/commands.py --write    # rewrite it inside SKILL.md

The skill is the owner's desk over the runner; its list of commands is
therefore a VIEW of stages.yaml, never typed.  A test asserts the skill's
copy equals this output, so a registry change that forgets the desk fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import registry  # noqa: E402

SKILL = ROOT / ".claude" / "skills" / "episode" / "SKILL.md"
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


def render_into(text: str, stage: str, body: str) -> str:
    open_, close = OPEN.format(stage=stage), CLOSE.format(stage=stage)
    if open_ not in text or close not in text:
        raise ValueError(f"{SKILL.name} has no {open_} ... {close} markers")
    head, rest = text.split(open_, 1)
    _, tail = rest.split(close, 1)
    return f"{head}{open_}\n{body}\n{close}{tail}"


def between(text: str, stage: str) -> str:
    open_, close = OPEN.format(stage=stage), CLOSE.format(stage=stage)
    return text.split(open_, 1)[1].split(close, 1)[0].strip()


def main(argv: list[str]) -> int:
    body = table("episode")
    if "--write" in argv:
        SKILL.write_text(render_into(SKILL.read_text(encoding="utf-8"), "episode", body),
                         encoding="utf-8", newline="\n")
        print(f"wrote {SKILL}")
        return 0
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
