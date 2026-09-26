"""The Command Center's board from a shell (decision 2026-09-25, C10 + C11).
A sibling of episode.py that runs no step:

    uv run python command_center.py [--port 8700] [--db db/visurena_studio.db] [--library library]
    uv run python command_center.py --read-only  # show the studio, refuse every order (405)
    uv run python command_center.py --check      # build the app, print its routes, serve nothing

Serves on 127.0.0.1 only.  Every page reads the database read-only per
request; the /act/ buttons (hold, lift, bump, retry, requeue, redo) write one
orders row each through a second, writable connection on the same file.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import uvicorn

from studio import db
from studio.command_center import app as cc_app


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="command_center.py", description=__doc__.split("\n\n")[0])
    top.add_argument("--port", type=int, default=8700)
    top.add_argument("--db", default=str(db.DB_PATH), help="the studio database (pages read it read-only)")
    top.add_argument("--library", default="library", help="the library root")
    top.add_argument("--read-only", action="store_true", help="no write connection: every order answers 405")
    top.add_argument("--check", action="store_true", help="print the routes and exit without serving")
    return top


def flat_routes(routes) -> list:
    """Every route, with an included router's own routes in its place
    (FastAPI 0.141 wraps an included router as one object)."""
    out = []
    for route in routes:
        inner = getattr(route, "original_router", None)
        out += flat_routes(inner.routes) if inner is not None else [route]
    return out


def routes(app) -> list[str]:
    """`METHOD path` per route, in the order the app answers them."""
    lines = []
    for route in flat_routes(app.routes):
        methods = sorted(getattr(route, "methods", None) or ["MOUNT"])
        lines.append(f"{'/'.join(m for m in methods if m != 'HEAD')} {getattr(route, 'path', '')}")
    return lines


def main(argv: list[str], serve=uvicorn.run) -> int:
    args = parser().parse_args(argv)
    writer = None if args.read_only else cc_app.writable_factory(args.db)
    app = cc_app.make_app(cc_app.readonly_factory(args.db), Path(args.library), write_factory=writer)
    if args.check:
        print("\n".join(routes(app)))
        return 0
    serve(app, host="127.0.0.1", port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
