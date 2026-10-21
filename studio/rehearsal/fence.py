"""The fence: refuse a rehearsal's reach outside its sandbox BEFORE it happens (2026-10-21_ep02_proof
2.5, 2.6; R7, R8, R19).

ONE `sys.addaudithook` per process.  Armed, it raises RehearsalTripwire and appends a
`<sandbox>/tripwire.jsonl` row on: a write-capable open, rename, remove, mkdir, rmdir, copy,
move, utime or chmod, and ANY sqlite3.connect, under a real root (the real library, db/ with
its -journal/-wal companions, the ComfyUI root, docs/DECISIONS.md, docs/episode_handbook.html);
a process launch off the allowlist (ffmpeg/ffprobe with no output under a real root, git only
at <sandbox>/git, `uv run --no-sync python` from the repo, sys.executable); a socket connect
anywhere but loopback on a manifest fake port or this process's own listener; building an
openai client; and building a ClaudeSDKClient without the rehearsal transport.

RehearsalTripwire is a BaseException so the `except Exception` / `except OSError` a step uses
to survive a flaky log write cannot swallow a trip.  An audit hook cannot be removed:
`disarm()` leaves it inert (one attribute read per event), which only tests call."""
from __future__ import annotations

import functools
import json
import os
import shlex
import sys
import threading
import time
import weakref
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping

from studio import settings

WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
PATH_EVENTS = {"os.remove": (0,), "os.rmdir": (0,), "os.mkdir": (0,), "shutil.rmtree": (0,), "os.truncate": (0,),
               "os.utime": (0,), "os.chmod": (0,), "os.rename": (0, 1), "shutil.move": (0, 1),
               "shutil.copyfile": (1,), "shutil.copytree": (1,), "shutil.copystat": (1,),
               "_winapi.CopyFile2": (1,), "os.link": (1,), "os.symlink": (1,)}
"""Audit event -> the argument positions that name a path it changes (measured on 3.12: copy2
on Windows raises only `_winapi.CopyFile2`; Path.touch raises os.utime first)."""
LAUNCH_EVENTS = frozenset({"os.system", "os.exec", "os.spawn", "os.posix_spawn", "os.startfile", "os.fork",
                           "os.forkpty"})
SOCKET_EVENTS = frozenset({"socket.connect", "socket.sendto", "socket.sendmsg"})
WATCHED = frozenset({"open", "sqlite3.connect", "subprocess.Popen", "socket.bind", *PATH_EVENTS,
                     *LAUNCH_EVENTS, *SOCKET_EVENTS})
NAMED_TRIPS = ("gpu_ledger.py", "notify_bench.py")
LOOPBACK = ("127.0.0.1", "::1")

_ARMED: "Fence | None" = None
_HOOKED = False
_PATCHED = False
_BUSY = threading.local()
_BOUND: "weakref.WeakSet" = weakref.WeakSet()


class RehearsalTripwire(BaseException):
    """A rehearsal reached outside its sandbox; the reach was refused before it happened."""


def norm(path) -> str | None:
    """normcase(abspath) of a path-like; None for a file descriptor or nothing."""
    if path is None or isinstance(path, int):
        return None
    try:
        return os.path.normcase(os.path.abspath(os.fsdecode(os.fspath(path))))
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class Fence:
    roots: tuple[str, ...]
    sandbox: Path
    repo: str
    ports: frozenset[int]
    executable: str

    @classmethod
    def of(cls, roots: Iterable, sandbox: Path, repo: Path, ports: Iterable[int] = ()) -> "Fence":
        forms = [f for r in roots for f in (norm(r), norm(Path(r).resolve()))]
        return cls(tuple(dict.fromkeys(f.rstrip("\\/") for f in forms if f)), Path(sandbox), norm(repo),
                   frozenset(int(p) for p in ports), norm(sys.executable))

    @classmethod
    def from_settings(cls, env: Mapping[str, str] = os.environ) -> "Fence":
        return cls.of(settings.real_roots(env), settings.sandbox(env), settings.REPO, settings.fake_ports(env))


def armed() -> Fence | None:
    return _ARMED


def under(fence: Fence, path) -> str | None:
    """The real root `path` lies in, or None."""
    p = norm(path)
    if p is None:
        return None
    return next((r for r in fence.roots if p == r or p.startswith(r + os.sep)), None)


def write_refusal(fence: Fence, path, what: str) -> str | None:
    root = under(fence, path)
    return f"{what} under the real root {root}: {os.fsdecode(os.fspath(path))}" if root else None


def writes(mode, flags) -> bool:
    """An open that can change the file: a w/a/x/+ mode, or a write/create/truncate flag."""
    by_mode = isinstance(mode, str) and any(c in mode for c in "wax+")
    return by_mode or (isinstance(flags, int) and bool(flags & WRITE_FLAGS))


def sqlite_path(database) -> str | None:
    """The file a sqlite3.connect names (a `file:` URI's path); None for memory."""
    text = os.fsdecode(os.fspath(database)) if not isinstance(database, str) else database
    if text.startswith("file:"):
        text = text[len("file:"):].partition("?")[0]
        text = text.lstrip("/") if len(text) > 2 and text.lstrip("/")[1:2] == ":" else text
    return None if text in ("", ":memory:") else text


def event_refusal(fence: Fence, event: str, args: tuple) -> str | None:
    """Why this audit event is refused in a rehearsal, or None."""
    if event == "open":
        return write_refusal(fence, args[0], "open for writing") if writes(args[1], args[2]) else None
    if event in PATH_EVENTS:
        return next((r for i in PATH_EVENTS[event] if (r := write_refusal(fence, args[i], event))), None)
    if event == "sqlite3.connect":
        path = sqlite_path(args[0])
        return write_refusal(fence, path, "sqlite3.connect") if path else None
    if event == "subprocess.Popen":
        return launch_refusal(fence, args[0], args[1], args[2])
    return other_refusal(fence, event, args)


def other_refusal(fence: Fence, event: str, args: tuple) -> str | None:
    if event in LAUNCH_EVENTS:
        return f"{event} is not on the launch allowlist"
    if event == "socket.bind":
        _BOUND.add(args[0])
        return None
    if event in SOCKET_EVENTS:
        return connect_refusal(fence, args[1])
    return None


# ---- launches ----------------------------------------------------------------

def argv_words(args) -> list[str]:
    """A launch's words; a Windows command-line string (what Popen audits there) is split."""
    if isinstance(args, (str, bytes)):
        text = os.fsdecode(args)
        return [w.strip('"') for w in shlex.split(text, posix=False)]
    return [os.fsdecode(os.fspath(a)) for a in args]


def program(executable, words: list[str]) -> tuple[str, str]:
    """(normalized path, bare lower-case name without .exe) of what is launched."""
    exe = os.fsdecode(os.fspath(executable)) if executable else (words[0] if words else "")
    name = os.path.basename(exe).lower()
    return norm(exe) or "", name[:-4] if name.endswith(".exe") else name


def _at(cwd, word: str) -> str:
    return os.path.join(os.fsdecode(os.fspath(cwd)) if cwd else os.getcwd(), word)


def ffmpeg_refusal(fence: Fence, words: list[str], cwd) -> str | None:
    """Every non-option word not after -i is a possible output; none may be under a real root."""
    outs = [w for prev, w in zip(words, words[1:]) if prev != "-i" and not w.startswith("-")]
    root = next(((w, r) for w in outs if (r := under(fence, _at(cwd, w)))), None)
    return f"ffmpeg output under the real root {root[1]}: {root[0]}" if root else None


def ffprobe_refusal(fence: Fence, words: list[str], cwd) -> str | None:
    outs = [w for prev, w in zip(words, words[1:]) if prev == "-o"]
    root = next(((w, r) for w in outs if (r := under(fence, _at(cwd, w)))), None)
    return f"ffprobe output under the real root {root[1]}: {root[0]}" if root else None


def git_refusal(fence: Fence, words: list[str], cwd) -> str | None:
    """git answers only from <sandbox>/git (by cwd or -C): the real tree holds other builders' edits."""
    target = next((w for prev, w in zip(words, words[1:]) if prev == "-C"), None) or cwd or os.getcwd()
    if norm(target) == norm(fence.sandbox / "git"):
        return None
    return f"git outside <sandbox>/git: {os.fsdecode(os.fspath(target))}"


def uv_refusal(fence: Fence, words: list[str], cwd) -> str | None:
    if words[1:4] == ["run", "--no-sync", "python"] and norm(cwd or os.getcwd()) == fence.repo:
        return None
    return f"uv launch other than 'uv run --no-sync python' from the repo: {' '.join(words)[:200]} (cwd {cwd})"


RULES: dict[str, Callable] = {"ffmpeg": ffmpeg_refusal, "ffprobe": ffprobe_refusal, "git": git_refusal,
                              "uv": uv_refusal}


def launch_refusal(fence: Fence, executable, args, cwd) -> str | None:
    """Why this launch is refused in a rehearsal, or None (the allowlist of 2.6)."""
    words = argv_words(args)
    named = next((n for n in NAMED_TRIPS if any(n in w for w in words)), None)
    if named:
        return f"launch naming {named}: {' '.join(words)[:300]}"
    path, name = program(executable, words)
    if path and path == fence.executable:
        return None
    rule = RULES.get(name)
    return rule(fence, words, cwd) if rule else f"launch of {name} is not on the allowlist: {path}"


# ---- sockets -----------------------------------------------------------------

def own_listener(port: int) -> bool:
    """A socket this process bound while armed holds the port (asyncio's socketpair self-pipe)."""
    for sock in list(_BOUND):
        try:
            if sock.getsockname()[1] == port:
                return True
        except (OSError, IndexError, TypeError):
            continue
    return False


def connect_refusal(fence: Fence, address) -> str | None:
    if not isinstance(address, tuple) or len(address) < 2:
        return f"connect to {address!r} (only loopback on the manifest's fake ports)"
    host, port = address[0], address[1]
    if host in LOOPBACK and (port in fence.ports or own_listener(port)):
        return None
    return f"connect to {host}:{port} (only 127.0.0.1 on the manifest's fake ports)"


# ---- the hook, the trip, the client guards ------------------------------------

def trip(fence: Fence, event: str, reason: str) -> None:
    """Write the tripwire row, then raise; the row's own write is never re-checked."""
    _BUSY.on = True
    try:
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "pid": os.getpid(), "event": event, "reason": reason}
        with open(fence.sandbox / "tripwire.jsonl", "a", encoding="utf-8") as out:
            out.write(json.dumps(row) + "\n")
    except OSError:
        pass
    finally:
        _BUSY.on = False
    raise RehearsalTripwire(f"{event}: {reason}")


def hook(event: str, args: tuple) -> None:
    fence = _ARMED
    if fence is None or event not in WATCHED or getattr(_BUSY, "on", False):
        return
    reason = event_refusal(fence, event, args)
    if reason:
        trip(fence, event, reason)


def guarded(original: Callable, event: str, refuses: Callable[..., str | None]) -> Callable:
    """`original` that trips first while armed and `refuses(*args, **kwargs)` gives a reason."""
    @functools.wraps(original)
    def call(self, *args, **kwargs):
        fence = _ARMED
        if fence is not None and (reason := refuses(*args, **kwargs)):
            trip(fence, event, reason)
        return original(self, *args, **kwargs)
    return call


def _without_transport(*args, **kwargs) -> str | None:
    transport = kwargs.get("transport", args[1] if len(args) > 1 else None)
    return None if getattr(transport, "rehearsal", False) else "constructed without the rehearsal transport"


def _query_without_transport(prompt=None, options=None, transport=None, **_) -> str | None:
    return _without_transport(options, transport=transport)


def _openai_refused(name: str) -> Callable[..., str]:
    return lambda *a, **k: f"openai.{name} built in a rehearsal"


def guard_clients() -> None:
    """openai's clients refuse; the SDK client and query() need the rehearsal transport."""
    try:
        import openai
        for cls in (openai.OpenAI, openai.AsyncOpenAI):
            cls.__init__ = guarded(cls.__init__, "openai", _openai_refused(cls.__name__))
    except ImportError:
        pass
    try:
        from claude_agent_sdk import ClaudeSDKClient
        from claude_agent_sdk._internal.client import InternalClient
        ClaudeSDKClient.__init__ = guarded(ClaudeSDKClient.__init__, "ClaudeSDKClient", _without_transport)
        InternalClient.process_query = guarded(InternalClient.process_query, "claude_agent_sdk.query",
                                               _query_without_transport)
    except ImportError:
        pass


def install(fence: Fence) -> None:
    """Arm this process; the hook and the client guards are added once."""
    global _ARMED, _HOOKED, _PATCHED
    _ARMED = fence
    if not _PATCHED:
        _PATCHED = True
        guard_clients()
    if not _HOOKED:
        _HOOKED = True
        sys.addaudithook(hook)


def disarm() -> None:
    """Leave the hook inert (tests only: a rehearsal process stays armed to its exit)."""
    global _ARMED
    _ARMED = None
