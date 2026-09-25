"""One step, run on its own from the command line.

    uv run python scripts/<stage>/step_NN_<name>.py <codex_id> [<number>] [extra...]

Every step module ends with `raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))`
so the same module the runner imports is also a command: the context is built the
same way, the events are written the same way, and an owner gate parks the same way.
"""
from __future__ import annotations

import sys

from studio import db, registry, step_runner


def context_for(stage: str, conn, codex_id: str, number: int | None):
    """The stage's own context builder, by convention `studio/<stage>_run.context`."""
    import importlib
    module = importlib.import_module(f"studio.{stage}_run")
    return module.context(conn, codex_id, number)


def parse(argv: list[str]) -> tuple[str, int | None]:
    args = [a for a in argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(f"usage: {argv[0]} <codex_id> [<number>]")
    number = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    return args[0], number


def main(module, argv: list[str], conn=None) -> int:
    if "--help" in argv or "-h" in argv:
        print(module.__doc__ or module.NAME)
        return 0
    codex_id, number = parse(argv)
    stage = module.__name__.split(".")[-2] if "." in module.__name__ else registry_stage_of(module)
    conn = conn or db.get_connection()
    db.init_db(conn)
    ctx = context_for(stage, conn, codex_id, number)
    ctx.extra = [a for a in argv[1:] if a.startswith("--")]
    outcome = step_runner.run_steps(ctx, [module])
    print(f"{stage}/{module.STEP_ID} {module.NAME}: {outcome}")
    return 0 if outcome == "completed" else 2


def registry_stage_of(module) -> str:
    """A module run as __main__ has no package name; find its stage by its script name."""
    parts = module.__file__.replace("\\", "/").rsplit("/", 2)
    script, folder = parts[-1].removesuffix(".py"), parts[-2] if len(parts) > 1 else ""
    # A SCRIPT NAME IS NOT UNIQUE ACROSS STAGES: screenplay and episode both
    # have step_02_plan, and the first match sent ep12's plan to screenplay.
    # The folder names the stage; fall back to the first match only without one.
    if folder in registry.stage_names() and any(s["script"] == script for s in registry.steps(folder)):
        return folder
    for stage in registry.stage_names():
        if any(step["script"] == script for step in registry.steps(stage)):
            return stage
    raise SystemExit(f"{script} is not a registered step of any stage")


if __name__ == "__main__":  # pragma: no cover
    sys.exit(0)
