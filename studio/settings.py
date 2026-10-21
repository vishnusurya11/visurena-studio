"""The one place a library root is chosen, failing closed both ways (2026-10-21_ep02_proof 1.1).

`VISURENA_LIBRARY=<path>` names the library root.  Rehearsal mode is on when the sandbox
manifest `<VISURENA_LIBRARY>/../rehearsal.json` exists.  With the variable unset every
function returns today's path, byte for byte.  At import (every module below reads this
one) the variable WITHOUT a manifest raises RehearsalEnvLeak: there is no legitimate use of
it outside a rehearsal, so this one rule stops autopilot, drive, step 13 and every other
entry point.  A manifest whose sandbox touches a real root, or that names :8188, raises.
Standard library only: `studio/__init__.py` reaches this module before anything else."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parents[1]
ENV = "VISURENA_LIBRARY"
MANIFEST = "rehearsal.json"
LIBRARY_DIR = "library"
"""The library folder's name, in the repo and in a sandbox: the one spelling of it."""
REAL_LIBRARY = REPO / LIBRARY_DIR
TODAY_HOST = "http://127.0.0.1:8188"
TODAY_COMFY_ROOT = Path("D:/Projects/KingdomOfViSuReNa/alpha/ComfyUI_windows_portable/ComfyUI")
TODAY_PORTABLE = "D:/Projects/KingdomOfViSuReNa/alpha/ComfyUI_windows_portable"
REAL_ENGINE_PORT = 8188


class RehearsalEnvLeak(RuntimeError):
    """VISURENA_LIBRARY is set but no rehearsal manifest sits beside it."""


class RehearsalManifestUnsafe(RuntimeError):
    """A manifest whose sandbox touches a real root, or that names the real engine's port."""


def _library_env(env: Mapping[str, str]) -> Path | None:
    value = (env.get(ENV) or "").strip()
    return Path(value) if value else None


def rehearsal(env: Mapping[str, str] = os.environ) -> dict | None:
    """The parsed, checked manifest; None when the variable is unset."""
    library = _library_env(env)
    if library is None:
        return None
    path = library.parent / MANIFEST
    if not path.is_file():
        raise RehearsalEnvLeak(f"{ENV}={library} but no {path}: a library override outside a rehearsal")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    check_manifest(library.parent, manifest)
    return manifest


def sandbox(env: Mapping[str, str] = os.environ) -> Path | None:
    """The sandbox folder (the manifest's), None outside a rehearsal."""
    return _library_env(env).parent if rehearsal(env) is not None else None


def overlaps(a: Path, b: Path) -> bool:
    """True when one path is the other or holds it."""
    a, b = Path(os.path.normcase(os.path.abspath(a))), Path(os.path.normcase(os.path.abspath(b)))
    return a == b or a in b.parents or b in a.parents


def todays_real_roots(manifest: Mapping | None = None) -> tuple[Path, ...]:
    """What a rehearsal may never write: the real library, db/, ComfyUI and two docs."""
    m = manifest or {}
    named = [REAL_LIBRARY, REPO / "db", TODAY_COMFY_ROOT, REPO / "docs" / "DECISIONS.md",
             REPO / "docs" / "episode_handbook.html"]
    named += [Path(p) for p in (m.get("real_library"), m.get("real_comfy_root")) if p]
    named += [Path(p) for p in m.get("real_roots") or ()]
    return tuple(dict.fromkeys(p.resolve() for p in named))


def _ports(manifest: Mapping) -> set[int]:
    host = urlsplit(manifest.get("comfy_host") or "")
    port = host.port or (80 if host.scheme == "http" and host.hostname else None)
    return {int(p) for p in manifest.get("fake_ports") or ()} | ({port} if port else set())


def check_manifest(box: Path, manifest: Mapping) -> None:
    """Raise unless the sandbox is clear of every real root and no port is the real engine's."""
    for root in todays_real_roots(manifest):
        if overlaps(box, root):
            raise RehearsalManifestUnsafe(f"sandbox {box} overlaps the real root {root}")
    if REAL_ENGINE_PORT in _ports(manifest):
        raise RehearsalManifestUnsafe(f"the manifest names port {REAL_ENGINE_PORT}, the real ComfyUI")


def fake_ports(env: Mapping[str, str] = os.environ) -> tuple[int, ...]:
    """The loopback ports the fence lets a rehearsal connect to."""
    manifest = rehearsal(env)
    return tuple(sorted(_ports(manifest))) if manifest else ()


def library_root(relative: bool = False, env: Mapping[str, str] = os.environ) -> Path:
    """The library: VISURENA_LIBRARY in a rehearsal, else <repo>/library (or today's
    cwd-relative `library` for the callers that spelled it so)."""
    if rehearsal(env) is not None:
        return _library_env(env)
    return Path(LIBRARY_DIR) if relative else REAL_LIBRARY


def db_path(env: Mapping[str, str] = os.environ) -> Path:
    """The studio DB: <sandbox>/db in a rehearsal, else today's cwd-relative db/."""
    box = sandbox(env)
    return (box / "db" if box else Path("db")) / "visurena_studio.db"


def comfy_host(today: str | None = None, env: Mapping[str, str] = os.environ) -> str:
    """The engine's URL: the manifest's in a rehearsal, else `today` (a caller's COMFY_URL)
    or the real engine."""
    manifest = rehearsal(env)
    return manifest["comfy_host"] if manifest else (today or TODAY_HOST)


def comfy_root(env: Mapping[str, str] = os.environ) -> Path:
    """The ComfyUI folder staged inputs and outputs live in."""
    box = sandbox(env)
    return box / "comfy" if box else TODAY_COMFY_ROOT


def comfy_portable(today: str = TODAY_PORTABLE, env: Mapping[str, str] = os.environ) -> str:
    """The portable engine folder (`today`, the caller's one default): a sandbox path that holds
    no engine in a rehearsal."""
    box = sandbox(env)
    return str(box / "comfy_portable") if box else today


def git_root(env: Mapping[str, str] = os.environ) -> Path:
    """Where `git` answers HEAD and porcelain: the sandbox's 1-commit repo in a rehearsal."""
    box = sandbox(env)
    return box / "git" if box else REPO


def tmp_root(env: Mapping[str, str] = os.environ) -> Path | None:
    box = sandbox(env)
    return box / "tmp" if box else None


def real_libraries(env: Mapping[str, str] = os.environ) -> tuple[Path, ...]:
    """The repo's real library, plus the one the manifest names when it differs."""
    named = (rehearsal(env) or {}).get("real_library")
    return tuple(dict.fromkeys([REAL_LIBRARY, *([Path(named)] if named else [])]))


def real_roots(env: Mapping[str, str] = os.environ) -> tuple[Path, ...]:
    """Every root the fence refuses writes under; () outside a rehearsal."""
    manifest = rehearsal(env)
    return todays_real_roots(manifest) if manifest is not None else ()


rehearsal()
