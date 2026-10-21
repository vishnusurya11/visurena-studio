"""Record the ComfyUI contract: a logging reverse proxy that keeps ONE request/reply pair per
route the studio uses, plus one /history reply that carries an execution_error
(2026-10-21_ep02_proof DESIGN 2.2, R12; staged run SR-5).

    uv run --no-sync python -m scripts.proof.record_comfy_transcript --upstream http://127.0.0.1:8188 \
        --owner-go-sr5 [--listen 18189] [--out tests/fixtures/proof/comfy_transcript]

Built and tested ONLY in front of the fake engine.  Pointing it at the real engine (:8188) is
SR-5 and needs the owner's explicit go, so that port is refused without `--owner-go-sr5`; a
non-loopback upstream is always refused.  A pair already on disk is never rewritten; a failed
upstream answers 502 and records nothing.  The proxy adds no request of its own: it records
what a real job sends through it.

`shape`, `shape_diff` and `contract_diff` are the contract test's comparison: key sets and value
types, with id-keyed dicts (prompt ids, node ids) wildcarded and the fake's one label key
(`rehearsal`) allowed."""
from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from studio.rehearsal.fake_comfy import CONTRACT_ROUTES, REAL_ENGINE_PORT, TRANSCRIPT

ERROR_KEY = "history_execution_error"
LOOPBACK = ("127.0.0.1", "localhost", "::1")
ROUTES = {("POST", "/prompt"): "post_prompt", ("GET", "/queue"): "get_queue", ("POST", "/queue"): "post_queue",
          ("GET", "/system_stats"): "get_system_stats", ("POST", "/free"): "post_free",
          ("POST", "/interrupt"): "post_interrupt", ("GET", "/internal/logs/raw"): "get_internal_logs_raw"}
IDLIKE = re.compile(r"^(\d+|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$")
ALLOWED_EXTRA = frozenset({"rehearsal"})
"""The fake's `rehearsal: {clock, match}` label on a history record: the one key it may add."""
FORWARD_TIMEOUT = 120.0


# ---- routes and what is worth keeping ---------------------------------------------------

def route_key(method: str, path: str) -> str | None:
    """The contract name of a request, or None for a route the studio does not use."""
    route = urlsplit(path).path
    if method == "GET" and (route == "/history" or route.startswith("/history/")):
        return "get_history"
    return ROUTES.get((method, route))


def body_of(raw: bytes) -> Any:
    """JSON when it parses, the text when it does not, None when empty."""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return raw.decode("utf-8", "replace")


def has_execution_error(reply: Any) -> bool:
    """Whether a /history reply holds a record whose messages include an execution_error."""
    records = reply.values() if isinstance(reply, dict) else ()
    return any(m and m[0] == "execution_error" for r in records if isinstance(r, dict)
               for m in (r.get("status") or {}).get("messages", []))


def keys_for(key: str, reply: Any) -> list[str]:
    """Which contract slots this pair can fill: an empty or error history is not the success shape."""
    if key != "get_history":
        return [key]
    if has_execution_error(reply):
        return [ERROR_KEY]
    return [key] if reply else []


class Transcript:
    """The transcript folder: one `<route>.json` per kept pair, each written once."""

    def __init__(self, out: Path):
        self.out = Path(out)
        self._lock = threading.Lock()

    def path(self, key: str) -> Path:
        return self.out / f"{key}.json"

    def saved(self, key: str) -> bool:
        return self.path(key).is_file()

    def missing(self) -> list[str]:
        return [k for k in CONTRACT_ROUTES if not self.saved(k)]

    def offer(self, key: str | None, pair: dict) -> list[str]:
        """Keep the pair in every slot it fills that is still empty; the slots it filled."""
        if key is None or not 200 <= pair["status"] < 300:
            return []
        with self._lock:
            kept = [k for k in keys_for(key, pair["reply"]) if not self.saved(k)]
            for k in kept:
                self.out.mkdir(parents=True, exist_ok=True)
                self.path(k).write_text(json.dumps({"route": k, **pair}, indent=1), encoding="utf-8")
            return kept


# ---- the proxy ----------------------------------------------------------------------------

def forward(upstream: str, method: str, path: str, body: bytes) -> tuple[int, bytes]:
    """The upstream's (status, body); an upstream that cannot be reached raises ConnectionError."""
    request = urllib.request.Request(f"{upstream}{path}", data=body if method == "POST" else None, method=method,
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=FORWARD_TIMEOUT) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as err:
        return err.code, err.read()
    except (urllib.error.URLError, OSError) as err:
        raise ConnectionError(f"upstream {upstream} unreachable: {err}") from None


class Proxy:
    """A ThreadingHTTPServer on 127.0.0.1:<listen> forwarding to `upstream` and recording."""

    def __init__(self, upstream: str, out: Path = TRANSCRIPT, listen: int = 0):
        self.upstream, self.transcript = upstream.rstrip("/"), Transcript(out)
        self._server = ThreadingHTTPServer(("127.0.0.1", int(listen)), _ProxyHandler)
        self._server.daemon_threads = True
        self._server.proxy = self

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def __enter__(self) -> "Proxy":
        threading.Thread(target=self._server.serve_forever, kwargs={"poll_interval": 0.05},
                         name="comfy-transcript-proxy", daemon=True).start()
        return self

    def __exit__(self, *exc) -> None:
        self._server.shutdown()
        self._server.server_close()

    def handle(self, method: str, path: str, body: bytes) -> tuple[int, bytes]:
        """Forward one request, offer the pair to the transcript, return the upstream's answer."""
        try:
            status, raw = forward(self.upstream, method, path, body)
        except ConnectionError as err:
            return 502, json.dumps({"error": str(err)}).encode("utf-8")
        pair = {"method": method, "path": path, "request": body_of(body), "status": status,
                "reply": body_of(raw), "recorded": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        self.transcript.offer(route_key(method, path), pair)
        return status, raw


class _ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args) -> None:
        return None

    def do_GET(self) -> None:
        self._relay("GET")

    def do_POST(self) -> None:
        self._relay("POST")

    def _relay(self, method: str) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        status, raw = self.server.proxy.handle(method, self.path, self.rfile.read(length) if length else b"")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


# ---- the shape and its diff -----------------------------------------------------------------

def kind(shape_: Any) -> str:
    if isinstance(shape_, dict):
        return "dict"
    return "list" if isinstance(shape_, list) else str(shape_)


def members(shape_: Any) -> dict[str, Any]:
    """kind -> shape: an `anyof` lists its members, any other shape is its own one member."""
    if isinstance(shape_, dict) and set(shape_) == {"anyof"}:
        return dict(shape_["anyof"])
    return {kind(shape_): shape_}


def merge(a: Any, b: Any) -> Any:
    """One shape that covers both: dict keys unioned, list items merged, mixed kinds an anyof."""
    if a == b or b is None:
        return a
    if a is None:
        return b
    out = members(a)
    for k, v in members(b).items():
        if k not in out:
            out[k] = v
        elif k == "dict":
            out[k] = {key: merge(out[k].get(key), v.get(key)) for key in {**out[k], **v}}
        elif k == "list":
            out[k] = ["list", merge(out[k][1], v[1])]
    return next(iter(out.values())) if len(out) == 1 else {"anyof": dict(sorted(out.items()))}


def merge_all(shapes: list) -> Any:
    out = None
    for s in shapes:
        out = merge(out, s)
    return out


def type_name(value: Any) -> str:
    if value is None:
        return "null"
    return {bool: "bool", int: "int", float: "float", str: "str"}.get(type(value), type(value).__name__)


def shape(value: Any) -> Any:
    """Key sets and value types; a dict keyed by ids (prompt or node ids) collapses to `<id>`."""
    if isinstance(value, dict):
        if value and all(IDLIKE.match(str(k)) for k in value):
            return {"<id>": merge_all([shape(v) for v in value.values()])}
        return {k: shape(v) for k, v in value.items()}
    if isinstance(value, list):
        return ["list", merge_all([shape(v) for v in value])]
    return type_name(value)


def dict_diff(real: dict, fake: dict, path: str) -> list[str]:
    out = []
    for key in sorted(set(real) | set(fake)):
        sub = f"{path}.{key}" if path else key
        if key not in fake:
            out.append(f"{sub}: missing in the fake")
        elif key not in real:
            out += [] if key in ALLOWED_EXTRA else [f"{sub}: only in the fake"]
        else:
            out += shape_diff(real[key], fake[key], sub)
    return out


def shape_diff(real: Any, fake: Any, path: str = "") -> list[str]:
    """Every place the fake's shape departs from the real one's; [] when they agree."""
    if real is None or fake is None:
        return []                                   # an empty list on one side says nothing
    rm, fm = members(real), members(fake)
    if set(rm) != set(fm):
        return [f"{path}: real {'|'.join(sorted(rm))}, fake {'|'.join(sorted(fm))}"]
    out = []
    for k in sorted(rm):
        if k == "dict":
            out += dict_diff(rm[k], fm[k], path)
        elif k == "list":
            out += shape_diff(rm[k][1], fm[k][1], f"{path}[]")
    return out


def load_pair(folder: Path, key: str) -> dict | None:
    path = Path(folder) / f"{key}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def contract_diff(real_dir: Path, fake_dir: Path) -> list[str]:
    """Route by route, the fake transcript's reply shapes against the real transcript's."""
    out = []
    for key in CONTRACT_ROUTES:
        real, fake = load_pair(real_dir, key), load_pair(fake_dir, key)
        if real is None or fake is None:
            out.append(f"{key}: no pair in the {'real' if real is None else 'fake'} transcript")
            continue
        out += shape_diff(shape(real["reply"]), shape(fake["reply"]), key)
    return out


# ---- the command --------------------------------------------------------------------------

def refusal(upstream: str, owner_go: bool) -> str | None:
    """Why this upstream may not be recorded now, or None."""
    parts = urlsplit(upstream)
    if parts.hostname not in LOOPBACK:
        return f"upstream {upstream} is not loopback: the proxy records the local engine only"
    if parts.port == REAL_ENGINE_PORT and not owner_go:
        return (f"upstream {upstream} is the real ComfyUI: recording it is staged run SR-5 and needs the "
                f"owner's explicit go (--owner-go-sr5)")
    return None


def parse(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--upstream", required=True, help="the engine to record, e.g. http://127.0.0.1:8188")
    ap.add_argument("--listen", type=int, default=18189, help="the proxy's loopback port (point COMFY at it)")
    ap.add_argument("--out", type=Path, default=TRANSCRIPT, help="the transcript folder")
    ap.add_argument("--owner-go-sr5", action="store_true", help="the owner said go for SR-5")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse(sys.argv[1:] if argv is None else argv)
    why = refusal(args.upstream, args.owner_go_sr5)
    if why:
        print(f"REFUSED: {why}", file=sys.stderr)
        raise SystemExit(2)
    with Proxy(args.upstream, args.out, args.listen) as proxy:
        print(f"recording {args.upstream} through {proxy.url} into {Path(args.out).resolve()}")
        while proxy.transcript.missing():
            time.sleep(5.0)
        print(f"complete: {len(CONTRACT_ROUTES)} pairs in {Path(args.out).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
