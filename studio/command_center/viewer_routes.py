"""The Viewer's read routes (SPEC_v3 "for the board"; V09 the server additions):

- GET /json/{codex}/{path}       a JSON / JSONL file of the book; `?ptr=` a JSON pointer
                                 slice, `?rows=a-b` a JSONL row range; over 2 MB -> 413
                                 with the /lib link to open it raw; gzip when asked.
- GET /log/{codex}/{name}        a run log under logs/<codex>/<stage>/ (or a .log in the
                                 book), the last 500 lines, `?before=` pages back, every
                                 line cut at 2,000 chars.
- GET /files/{codex}/{unit_rel}  a unit folder's viewable files grouped by kind.
- GET /viewer/{codex}/{stage}/{unit}.json   the unit's sequences (viewer_model).

The same guard as /lib: a 14-digit codex, the resolved path under the book folder
(or the log root), a suffix on the allow-list; every refusal is a 404, never a 403.
Reads only -- no route writes, runs or decodes anything."""
from __future__ import annotations

import gzip
import json
import re
import sqlite3
from pathlib import Path, PurePosixPath

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from studio import registry
from studio.command_center import library_paths
from studio.command_center import viewer_model as vm

router = APIRouter()
JSON_CAP = 2 * 1024 * 1024
SLICE_READ_CAP = 32 * 1024 * 1024
LOG_LINES, LOG_LINES_MAX, LINE_CAP = 500, 5000, 2000
LOG_READ_CAP = 32 * 1024 * 1024
ROWS_MAX = 5000
GZIP_MIN = 1024
JSON_SUFFIXES = frozenset({".json", ".jsonl"})
RUN_LOG = re.compile(r"^(\d{14})__([a-z_]+)__\d{14}\.log$")
UNIT_NAME = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
NO_CACHE = {"Cache-Control": "no-cache"}


# --- guards ---


def resolve_in_book(library: Path, codex: str, rel: str, suffixes: frozenset) -> Path | None:
    """A file of this book with an allowed suffix, or None (the /lib guard, own allow-list)."""
    folder = library_paths.book_folder(library, codex)
    if folder is None or PurePosixPath(rel).suffix.lower() not in suffixes:
        return None
    root, target = folder.resolve(), (folder / rel).resolve()
    if target == root or not target.is_relative_to(root) or not target.is_file():
        return None
    return target


def resolve_dir(library: Path, codex: str, rel: str) -> Path | None:
    """A folder of this book (never the book root itself), or None."""
    folder = library_paths.book_folder(library, codex)
    if folder is None or not rel:
        return None
    root, target = folder.resolve(), (folder / rel).resolve()
    if target == root or not target.is_relative_to(root) or not target.is_dir():
        return None
    return target


def resolve_log(logs: Path, library: Path, codex: str, name: str) -> Path | None:
    """A run log named `<codex>__<stage>__<ts>.log` under logs/<codex>/<stage>/, or a .log in the book."""
    m = RUN_LOG.match(name)
    if m is None:
        return resolve_in_book(library, codex, name, frozenset({".log"}))
    if m.group(1) != codex or not library_paths.CODEX.match(codex):
        return None
    root = (Path(logs) / codex).resolve()
    target = (root / m.group(2) / name).resolve()
    return target if target.is_relative_to(root) and target.is_file() else None


# --- slices ---


def json_pointer(doc, ptr: str):
    """RFC 6901: '' is the whole document, '/a/0/b~1c' walks keys and indexes; KeyError when absent."""
    if ptr == "":
        return doc
    if not ptr.startswith("/"):
        raise KeyError(ptr)
    for raw in ptr[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(doc, list) and token.isdigit() and int(token) < len(doc):
            doc = doc[int(token)]
        elif isinstance(doc, dict) and token in doc:
            doc = doc[token]
        else:
            raise KeyError(ptr)
    return doc


def parse_rows(spec: str) -> tuple[int, int]:
    """'a-b' (0-based, both ends kept) or 'a-' -> (start, stop) as a slice; ValueError when malformed."""
    m = re.fullmatch(r"(\d+)-(\d*)", spec or "")
    if m is None:
        raise ValueError(spec)
    start = int(m.group(1))
    stop = int(m.group(2)) + 1 if m.group(2) else start + ROWS_MAX
    if stop <= start:
        raise ValueError(spec)
    return start, min(stop, start + ROWS_MAX)


def jsonl_rows(text: str, start: int, stop: int) -> str:
    """The non-empty lines start..stop-1 of a JSONL text, as JSONL."""
    rows = [line for line in text.splitlines() if line.strip()]
    return "".join(line + "\n" for line in rows[start:stop])


def log_page(lines: list[str], before: int | None, n: int) -> tuple[list[str], int]:
    """(the n lines ending before `before` -- default the end -- each cut at LINE_CAP, first line number)."""
    end = len(lines) if before is None else max(0, min(before, len(lines)))
    start = max(0, end - n)
    return [clip(line) for line in lines[start:end]], start


def clip(line: str) -> str:
    return line if len(line) <= LINE_CAP else line[:LINE_CAP] + f" … [{len(line) - LINE_CAP} more chars]"


def tail_text(path: Path, cap: int = LOG_READ_CAP) -> tuple[str, bool]:
    """The file's text, or its last cap bytes from the first whole line (truncated=True)."""
    with open(path, "rb") as fh:
        fh.seek(0, 2)
        n = fh.tell()
        fh.seek(max(0, n - cap))
        data = fh.read()
    if n <= cap:
        return data.decode("utf-8", "replace"), False
    return data.split(b"\n", 1)[-1].decode("utf-8", "replace"), True


# --- responses ---


def gzipped(request: Request, body: bytes, media: str, headers: dict | None = None) -> Response:
    """The body, gzip-encoded when the client accepts it and it is worth it."""
    headers = {**NO_CACHE, **(headers or {}), "Vary": "Accept-Encoding"}
    if len(body) >= GZIP_MIN and "gzip" in request.headers.get("accept-encoding", ""):
        body, headers["Content-Encoding"] = gzip.compress(body, compresslevel=5), "gzip"
    return Response(body, media_type=media, headers=headers)


def too_big(codex: str, rel: str, n: int) -> JSONResponse:
    """413 with the hint: open the raw file through /lib."""
    raw = library_paths.artefact_url(codex, rel)
    return JSONResponse({"detail": f"{PurePosixPath(rel).name} is {vm.size(n)}, over the 2 MB the Viewer reads;"
                                   f" open raw at {raw} or ask for a slice (?ptr= / ?rows=)", "raw": raw},
                        status_code=413, headers=NO_CACHE)


def json_slice(request: Request, codex: str, rel: str, target: Path, ptr: str | None, rows: str | None) -> Response:
    """The pointer or row slice of a file under the slice read cap."""
    text = target.read_text(encoding="utf-8", errors="replace")
    if rows is not None:
        try:
            start, stop = parse_rows(rows)
        except ValueError:
            raise HTTPException(404, f"rows {rows!r} is not 'a-b'") from None
        body, media = jsonl_rows(text, start, stop).encode(), "application/x-ndjson"
    else:
        try:
            body, media = json.dumps(json_pointer(json.loads(text), ptr), indent=1).encode(), "application/json"
        except (KeyError, ValueError):
            raise HTTPException(404, f"no {ptr!r} in {PurePosixPath(rel).name}") from None
    return too_big(codex, rel, len(body)) if len(body) > JSON_CAP else gzipped(request, body, media)


# --- routes ---


@router.get("/json/{codex}/{path:path}")
def json_file(request: Request, codex: str, path: str, ptr: str | None = None, rows: str | None = None):
    target = resolve_in_book(request.app.state.library, codex, path, JSON_SUFFIXES)
    if target is None:
        raise HTTPException(404, "no such file")
    n = target.stat().st_size
    if ptr is None and rows is None:
        if n > JSON_CAP:
            return too_big(codex, path, n)
        media = "application/x-ndjson" if path.endswith(".jsonl") else "application/json"
        return gzipped(request, target.read_bytes(), media)
    return too_big(codex, path, n) if n > SLICE_READ_CAP else json_slice(request, codex, path, target, ptr, rows)


@router.get("/log/{codex}/{name:path}")
def log_file(request: Request, codex: str, name: str, before: int | None = None, n: int = LOG_LINES):
    state = request.app.state
    target = resolve_log(state.logs, state.library, codex, name)
    if target is None:
        raise HTTPException(404, "no such log")
    text, truncated = tail_text(target)
    lines, first = log_page(text.splitlines(), before, max(1, min(n, LOG_LINES_MAX)))
    headers = {"X-Log-First": str(first), "X-Log-Total": str(len(text.splitlines())),
               "X-Log-Truncated": "1" if truncated else "0"}
    return gzipped(request, ("\n".join(lines) + ("\n" if lines else "")).encode(), "text/plain; charset=utf-8", headers)


def grouped(files: list[dict], prefix: str) -> dict:
    """Files by kind, each with its book-relative path."""
    out: dict[str, list] = {k: [] for k in ("image", "video", "audio", "doc", "text", "log")}
    for f in files:
        out[f["kind"]].append({**f, "rel": f"{prefix}/{f['rel']}"})
    return out


@router.get("/files/{codex}/{unit_rel:path}")
def unit_files(request: Request, codex: str, unit_rel: str):
    folder = resolve_dir(request.app.state.library, codex, unit_rel)
    if folder is None:
        raise HTTPException(404, "no such folder")
    rel = unit_rel.strip("/")
    files = vm.index_files(folder)
    return JSONResponse({"codex": codex, "unit_rel": rel, "n": len(files), "groups": grouped(files, rel)},
                        headers=NO_CACHE)


def unit_run_ids(conn: sqlite3.Connection, codex: str, stage: str, unit: str) -> list[str]:
    """Every run id the events table holds for this unit (its run logs are `<run_id>.log`)."""
    rows = conn.execute("SELECT DISTINCT run_id FROM events WHERE codex_id = ? AND stage = ? AND unit = ?",
                        (codex, stage, unit))
    return [r[0] for r in rows if r[0]]


def run_ids(request: Request, codex: str, stage: str, unit: str) -> list[str]:
    """The unit's run ids from the read-only DB; none when the DB cannot answer."""
    try:
        conn = request.app.state.conn_factory()
    except sqlite3.Error:
        return []
    try:
        return unit_run_ids(conn, codex, stage, unit)
    except sqlite3.Error:
        return []
    finally:
        conn.close()


@router.get("/viewer/{codex}/{stage}/{unit}.json")
def viewer_unit(request: Request, codex: str, stage: str, unit: str):
    state = request.app.state
    if stage not in registry.stage_names() or not UNIT_NAME.match(unit):
        raise HTTPException(404, f"no unit {stage}/{unit}")
    home = vm.unit_home(stage, unit)
    folder = resolve_dir(state.library, codex, home)
    if folder is None:
        raise HTTPException(404, f"no folder for {stage}/{codex}/{unit}")
    logs = vm.run_logs(state.logs, codex, stage, run_ids(request, codex, stage, unit))
    body = json.dumps(vm.unit_model(folder, codex, stage, unit, home, logs)).encode()
    return gzipped(request, body, "application/json")
