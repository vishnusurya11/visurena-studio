"""The board's web process (decision 2026-09-25, "the board"): FastAPI +
Jinja2 + htmx.  `make_app(conn_factory, library, write_factory=None)` builds
it; every read route opens its connection per request from the read-only
factory (`readonly_factory` opens `mode=ro` with a 250 ms busy timeout, so a
poll never blocks a runner), the pages render the views, the partials are the
same fragments the pages include, the JSON twins answer with the models.  The
POST routes under /act/ (C11) are the owner's hand: each opens the SEPARATE
write factory and makes one call through `actions` into studio/work_orders --
an orders row (and a holds row for a hold), nothing else.  Without a write
factory they answer 405; from a foreign page, 403.  No route runs a step,
spawns a process or writes a file.  `/api/pulse.json` (panel ruling C1) is the
one heartbeat every page polls; every partial answers 204 to `?v=<its
fingerprint>` when nothing changed (C2)."""
from __future__ import annotations

import html
import mimetypes
import sqlite3
import time
from collections.abc import Callable, Iterator
from pathlib import Path, PurePosixPath

import anyio

from fastapi import APIRouter, Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from studio import db, registry
from studio.command_center import actions, library_paths, models, procs, progress_view, pulse, shell, thumbs, unit_view, views
from studio.command_center import viewer_routes, viz

mimetypes.add_type("font/woff2", ".woff2")   # Windows' registry does not know it: the fonts went out as octet-stream
HERE = Path(__file__).resolve().parent
INBOX_TEMPLATE = "inbox.html"
ORG_PAGE = registry.ROOT / "architecture" / "index.html"
templates = Jinja2Templates(directory=str(HERE / "templates"))
templates.env.filters.update(clock=progress_view.clock, span=unit_view.span, mmss=progress_view.mmss)
templates.env.globals.update(trace_points=progress_view.trace_points, static_url=shell.static_url, viz=viz,
                             HOLD_EFFECT=actions.HOLD_EFFECT)
router = APIRouter()
READ_ONLY = ("the board was started read-only (command_center.py --read-only): it can show"
             " the studio but not give an order")


def readonly_factory(db_path: str | Path) -> Callable[[], sqlite3.Connection]:
    """A factory of read-only connections to one database file (`mode=ro`,
    busy_timeout 250 ms, rows by name).  A write through it is an
    OperationalError -- the web process cannot write even by mistake."""
    uri = f"file:{Path(db_path).resolve().as_posix()}?mode=ro"

    def open_connection() -> sqlite3.Connection:
        # one connection per request, but FastAPI may open it (the dependency) and
        # use it (the route) on two pool threads: it is never shared, so the check is off
        conn = sqlite3.connect(uri, uri=True, timeout=0.25, check_same_thread=False)
        conn.execute("PRAGMA busy_timeout = 250")
        conn.row_factory = sqlite3.Row
        return conn
    return open_connection


def writable_factory(db_path: str | Path) -> Callable[[], sqlite3.Connection]:
    """A factory of writable connections to the same file, for the /act/ routes
    only (5 s busy timeout, foreign keys on, rows by name)."""
    path = Path(db_path).resolve()

    def open_connection() -> sqlite3.Connection:
        conn = sqlite3.connect(path, timeout=5)
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    return open_connection


def _conn(request: Request) -> Iterator[sqlite3.Connection]:
    """One short-lived connection per request, closed when the response is built."""
    conn = request.app.state.conn_factory()
    try:
        yield conn
    finally:
        conn.close()


def _shared(request: Request) -> dict:
    """What every template shares: the legend and its icons, the nav's stages, the write mode."""
    return {"legend": views.LEGEND, "state_icons": views.ICONS, "stages": registry.stage_names(),
            "writable": request.app.state.write_factory is not None, "read_only": READ_ONLY}


def _render(request: Request, name: str, **context) -> HTMLResponse:
    """A template with what every page shares."""
    return templates.TemplateResponse(request, name, {**_shared(request), **context})


def _unchanged(request: Request, conn: sqlite3.Connection, key: str) -> Response | None:
    """204 when the client's `?v=` is the section's fingerprint now (C2), else None."""
    v = request.query_params.get("v")
    if v and v == pulse.fingerprint(conn, key, time.time()):
        return Response(status_code=204)
    return None


def _page(request: Request, conn: sqlite3.Connection, name: str, **context) -> HTMLResponse:
    """A whole page: the template inside the shell (sidebar, header, palette) drawn for its path."""
    return _render(request, name, shell=shell.shell(conn, request.app.state.library, request.url.path), **context)


class CachedStatic(StaticFiles):
    """The static files; a versioned request (`?v=`, see shell.static_url) and a font
    are cached for a year, immutable -- anything else is revalidated."""

    async def get_response(self, path: str, scope) -> Response:
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            versioned = b"v=" in scope.get("query_string", b"") or path.replace("\\", "/").startswith("fonts/")
            response.headers["Cache-Control"] = "public,max-age=31536000,immutable" if versioned else "no-cache"
        return response


def _department(conn: sqlite3.Connection, stage: str, book: str | None, state: str | None) -> dict:
    """The department view, or a 404 for a stage the registry does not know."""
    try:
        return views.department(conn, stage, book=book, state=state)
    except ValueError:
        raise HTTPException(404, f"{stage!r} is not a department") from None


def _unit(request: Request, conn: sqlite3.Connection, stage: str, codex: str, unit: str) -> dict:
    """The unit view with every band of the page, or a 404 when it has no row."""
    state = request.app.state
    found = unit_view.unit(conn, state.library, codex, stage, unit, logs=state.logs)
    if found is None:
        raise HTTPException(404, f"no unit {stage}/{codex}/{unit}")
    return found


# --- pages ---


@router.get("/", response_class=HTMLResponse)
def home(request: Request, conn: sqlite3.Connection = Depends(_conn)):
    return _page(request, conn, "home.html", floor=views.floor(conn), attention=views.attention(conn),
                   lanes=views.lanes(conn), today=views.today(conn), orders=views.recent_orders(conn),
                   books=views.book_names(conn), queue_eta=views.queue_eta(conn))


@router.get("/inbox", response_class=HTMLResponse)
def inbox_page(request: Request, conn: sqlite3.Connection = Depends(_conn)):
    """Needs you as a page: the attention list, `views.inbox_count()` rows."""
    if same := _unchanged(request, conn, "attention"):
        return same
    rows = views.attention(conn)
    if not (HERE / "templates" / INBOX_TEMPLATE).is_file():
        return _plain_inbox(rows)
    return _page(request, conn, INBOX_TEMPLATE, attention=rows, count=len(rows), books=views.book_names(conn))


def _plain_inbox(rows: list[dict]) -> HTMLResponse:
    """The inbox before its template exists: a bare list of links, never a 404."""
    items = "".join(f'<li><a href="/d/{html.escape(r["stage"])}/{html.escape(r["codex_id"])}/{html.escape(r["unit"])}">'
                    f'{html.escape(r["glyph"])} {html.escape(r["unit"])} · {html.escape(r["stage"])}</a></li>'
                    for r in rows)
    return HTMLResponse(f'<!doctype html><title>Needs you · Visurena Studio</title><main id="main">'
                        f'<h1>Needs you</h1><p>{len(rows)} waiting</p><ul>{items}</ul><p><a href="/">Home</a></p></main>')


@router.get("/queue", response_class=HTMLResponse)
@router.get("/floor", response_class=HTMLResponse)
def floor_page(request: Request, conn: sqlite3.Connection = Depends(_conn)):
    """The queue (/queue; /floor is the old name and keeps answering)."""
    if same := _unchanged(request, conn, "floor"):
        return same
    return _page(request, conn, "floor.html", floor=views.floor(conn), queue=views.queue(conn),
                   holds=views.holds(conn), today=views.today(conn), books=views.book_names(conn),
                   queue_eta=views.queue_eta(conn))


@router.get("/d/{stage}", response_class=HTMLResponse)
def department_page(request: Request, stage: str, book: str | None = None, state: str | None = None,
                    conn: sqlite3.Connection = Depends(_conn)):
    dept = _department(conn, stage, book, state)
    if same := _unchanged(request, conn, f"dept:{stage}"):
        return same
    return _page(request, conn, "department.html", dept=dept,
                   book=book, state=state, books=views.book_names(conn))


@router.get("/d/{stage}/{codex}/{unit}", response_class=HTMLResponse)
def unit_page(request: Request, stage: str, codex: str, unit: str,
              conn: sqlite3.Connection = Depends(_conn)):
    found = _unit(request, conn, stage, codex, unit)
    return _page(request, conn, "unit.html", unit=found, stage=stage, codex=codex, books=views.book_names(conn),
                   **_live(request, conn, stage, codex, unit, found["row"]["shown"] in ("done", "flagged")))


def _live(request: Request, conn: sqlite3.Connection, stage: str, codex: str, unit: str, finished: bool) -> dict:
    """The live card's context for an episode unit with a run worth showing, else none."""
    if stage != "episode":
        return {"live": None}
    state = request.app.state
    p = progress_view.progress(state.library, conn, codex, unit, logs=state.logs, proc_rows=state.procs())
    if not progress_view.show(p, finished):
        return {"live": None}
    return {"live": p, "live_shape": progress_view.shape(p), "live_valuetext": progress_view.valuetext(p)}


@router.get("/b/{codex}", response_class=HTMLResponse)
def book_page(request: Request, codex: str, conn: sqlite3.Connection = Depends(_conn)):
    found = views.book(conn, request.app.state.library, codex)
    if found is None:
        raise HTTPException(404, f"no book {codex}")
    if same := _unchanged(request, conn, f"book:{codex}"):
        return same
    return _page(request, conn, "book.html", book=found, books=views.book_names(conn))


@router.get("/books", response_class=HTMLResponse)
def books_page(request: Request, conn: sqlite3.Connection = Depends(_conn)):
    """The shelf: every book with its units."""
    if same := _unchanged(request, conn, "lanes"):
        return same
    return _page(request, conn, "books.html", shelf=views.shelf(conn))


@router.get("/architecture", response_class=HTMLResponse)
def architecture_page(request: Request, conn: sqlite3.Connection = Depends(_conn)):
    """The org chart inside the shell (an iframe of /org)."""
    return _page(request, conn, "architecture.html")


@router.get("/org")
def org_chart(request: Request):
    page = Path(request.app.state.org_page)
    if not page.is_file():
        raise HTTPException(404, "the org chart is not on disk")
    return FileResponse(page, media_type="text/html", headers={"Cache-Control": "no-store"})


# --- partials (the same fragments the pages include) ---


@router.get("/partials/floor", response_class=HTMLResponse)
def floor_partial(request: Request, conn: sqlite3.Connection = Depends(_conn)):
    if same := _unchanged(request, conn, "floor"):
        return same
    return _render(request, "_floor.html", floor=views.floor(conn), books=views.book_names(conn))


@router.get("/partials/attention", response_class=HTMLResponse)
def attention_partial(request: Request, conn: sqlite3.Connection = Depends(_conn)):
    if same := _unchanged(request, conn, "attention"):
        return same
    return _render(request, "_attention.html", attention=views.attention(conn), books=views.book_names(conn))


@router.get("/partials/needs-you-count", response_class=HTMLResponse)
def needs_you_count(request: Request, conn: sqlite3.Connection = Depends(_conn)):
    """The nav's badge: how many rows Needs you holds, as bare text."""
    if same := _unchanged(request, conn, "attention"):
        return same
    return HTMLResponse(str(views.inbox_count(conn)))


@router.get("/partials/orders", response_class=HTMLResponse)
def orders_partial(request: Request, conn: sqlite3.Connection = Depends(_conn)):
    if same := _unchanged(request, conn, "orders"):
        return same
    return _render(request, "_orders.html", orders=views.recent_orders(conn), books=views.book_names(conn))


@router.get("/partials/lanes", response_class=HTMLResponse)
def lanes_partial(request: Request, conn: sqlite3.Connection = Depends(_conn)):
    if same := _unchanged(request, conn, "lanes"):
        return same
    return _render(request, "_lanes.html", lanes=views.lanes(conn), books=views.book_names(conn))


@router.get("/partials/d/{stage}", response_class=HTMLResponse)
def department_partial(request: Request, stage: str, book: str | None = None, state: str | None = None,
                       conn: sqlite3.Connection = Depends(_conn)):
    if same := _unchanged(request, conn, f"dept:{stage}"):
        return same
    return _render(request, "_rows.html", dept=_department(conn, stage, book, state),
                   books=views.book_names(conn))


@router.get("/partials/unit/{stage}/{codex}/{unit}/tails", response_class=HTMLResponse)
def tails_partial(request: Request, stage: str, codex: str, unit: str,
                  conn: sqlite3.Connection = Depends(_conn)):
    if same := _unchanged(request, conn, f"unit:{stage}/{codex}/{unit}"):
        return same
    return _render(request, "_tails.html", unit=_unit(request, conn, stage, codex, unit),
                   stage=stage, codex=codex)


@router.get("/partials/unit/{stage}/{codex}/{unit}/head", response_class=HTMLResponse)
def unit_head_partial(request: Request, stage: str, codex: str, unit: str,
                      conn: sqlite3.Connection = Depends(_conn)):
    if same := _unchanged(request, conn, f"unit:{stage}/{codex}/{unit}"):
        return same
    return _render(request, "_unit_head.html", unit=_unit(request, conn, stage, codex, unit),
                   stage=stage, codex=codex)


@router.get("/partials/unit/episode/{codex}/{unit}/live", response_class=HTMLResponse)
def unit_live_partial(request: Request, codex: str, unit: str, conn: sqlite3.Connection = Depends(_conn)):
    """The live card alone, for the client to swap in when the run's shape changes."""
    if same := _unchanged(request, conn, f"unit:episode/{codex}/{unit}"):
        return same
    found = _unit(request, conn, "episode", codex, unit)
    context = _live(request, conn, "episode", codex, unit, found["row"]["shown"] in ("done", "flagged"))
    if context["live"] is None:
        return HTMLResponse("")
    return _render(request, "_unit_live.html", unit=found, stage="episode", codex=codex, **context)


@router.get("/partials/unit/{stage}/{codex}/{unit}/orders", response_class=HTMLResponse)
def unit_orders_partial(request: Request, stage: str, codex: str, unit: str,
                        conn: sqlite3.Connection = Depends(_conn)):
    if same := _unchanged(request, conn, f"unit:{stage}/{codex}/{unit}"):
        return same
    return _render(request, "_unit_orders.html", unit=_unit(request, conn, stage, codex, unit),
                   stage=stage, codex=codex)


# --- the JSON twins ---


@router.get("/api/pulse.json", response_model=models.Pulse)
def pulse_json(request: Request, response: Response, since: int | None = None,
               conn: sqlite3.Connection = Depends(_conn)):
    """The heartbeat (C1): the fingerprints, the shell's numbers, the events since the cursor."""
    response.headers["Cache-Control"] = "no-store"
    state = request.app.state
    return pulse.pulse(conn, time.time(), state.boot, since, state.progress)


def gpu_progress(app: FastAPI) -> Callable[[str, str], dict | None]:
    """The GPU card's progress for the pulse: the live card's own read, at most
    once per pulse.GPU_TTL_S per unit, None when it cannot be read."""
    cache = pulse.Ttl(pulse.GPU_TTL_S)

    def read(codex: str, unit: str) -> dict | None:
        return cache.get((codex, unit), time.time(), lambda: _read_progress(app, codex, unit))
    return read


def _read_progress(app: FastAPI, codex: str, unit: str) -> dict | None:
    """progress_view.progress on its own connection; a failure is no progress, never a 500."""
    try:
        conn = app.state.conn_factory()
        try:
            return progress_view.progress(app.state.library, conn, codex, unit, logs=app.state.logs,
                                          proc_rows=app.state.procs())
        finally:
            conn.close()
    except Exception:
        return None


@router.get("/api/floor.json", response_model=models.Floor)
def floor_json(conn: sqlite3.Connection = Depends(_conn)):
    return views.floor(conn)


@router.get("/api/palette.json")
def palette_json(request: Request, conn: sqlite3.Connection = Depends(_conn)):
    """⌘K's index on its own: the palette refetches it on open when older than 10 s."""
    return shell.palette_index(conn, request.app.state.library)


@router.get("/api/d/{stage}.json", response_model=models.Department)
def department_json(stage: str, book: str | None = None, state: str | None = None,
                    conn: sqlite3.Connection = Depends(_conn)):
    return _department(conn, stage, book, state)


@router.get("/api/unit/{stage}/{codex}/{unit}.json", response_model=models.Unit)
def unit_json(request: Request, stage: str, codex: str, unit: str,
              conn: sqlite3.Connection = Depends(_conn)):
    return _unit(request, conn, stage, codex, unit)


@router.get("/api/progress/episode/{codex}/{unit}.json", response_model=models.Progress,
            response_model_exclude_none=True)
def progress_json(request: Request, codex: str, unit: str, response: Response,
                  conn: sqlite3.Connection = Depends(_conn)):
    """The live card's poll (progress tracker spec §3): one episode run's progress."""
    body = progress_card(request, conn, codex, unit)
    response.headers["Cache-Control"] = "no-store"
    return body


def progress_card(request: Request, conn: sqlite3.Connection, codex: str, unit: str) -> dict:
    """The card's data, or a 404 for a unit with no row or no folder."""
    state = request.app.state
    found = progress_view.progress(state.library, conn, codex, unit, logs=state.logs, proc_rows=state.procs())         if db.work_order(conn, codex, "episode", unit) is not None else None
    if found is None:
        raise HTTPException(404, f"no episode unit {codex}/{unit}")
    return found


# --- artefacts ---


@router.get("/lib/{codex}/{path:path}")
def artefact(request: Request, codex: str, path: str):
    """A book's file, revalidated by its ETag: a match is a 304, a Range request is always served."""
    target = library_paths.resolve_artefact(request.app.state.library, codex, path)
    if target is None:
        raise HTTPException(404, "no such artefact")
    tag = library_paths.etag(target)
    headers = {"Cache-Control": "no-cache", "ETag": tag}
    if "range" not in request.headers and library_paths.etag_matches(request.headers.get("if-none-match"), tag):
        return Response(status_code=304, headers=headers)
    return FileResponse(target, headers=headers)


def _thumb_limiter(app: FastAPI) -> anyio.CapacityLimiter:
    """The renders' limiter, made inside the server's loop on first use."""
    if getattr(app.state, "thumb_limiter", None) is None:
        app.state.thumb_limiter = anyio.CapacityLimiter(thumbs.CONCURRENT)
    return app.state.thumb_limiter


@router.get("/thumb/{codex}/{width}/{path:path}")
async def thumb(request: Request, codex: str, width: int, path: str):
    """A panel shrunk to 160/320/1024 px WebP from the process LRU, a miss
    rendered off the loop two at a time; the URL carries the mtime, so the
    answer never changes and is cached forever."""
    if width not in thumbs.WIDTHS or PurePosixPath(path).suffix.lower() not in thumbs.IMAGES:
        raise HTTPException(404, "no such thumbnail")
    target = library_paths.resolve_artefact(request.app.state.library, codex, path)
    if target is None:
        raise HTTPException(404, "no such artefact")
    data = await thumbs.thumb_async(target, path, width, request.app.state.thumbs, _thumb_limiter(request.app))
    return Response(data, media_type="image/webp", headers={"Cache-Control": "public,max-age=31536000,immutable"})


# --- the owner's hand: POST /act/*, one work_orders call each ---


def _local(request: Request) -> None:
    """The CSRF guard: a POST from a page on another host is refused."""
    if not actions.local_origin(request.headers):
        raise actions.Refused(403, "refused: this order came from a page that is not the board")


def _write_conn(request: Request) -> Iterator[sqlite3.Connection]:
    """One writable connection per action; 405 when the board was started read-only."""
    factory = request.app.state.write_factory
    if factory is None:
        raise actions.Refused(405, READ_ONLY)
    conn = factory()
    try:
        yield conn
    finally:
        conn.close()


act = APIRouter(prefix="/act", dependencies=[Depends(_local)])


def _receipt(request: Request, done: dict) -> HTMLResponse:
    """The receipt fragment; `orders-changed` (detail: the order) refreshes the Orders strip."""
    response = _render(request, "_receipt.html", done=done)
    response.headers["HX-Trigger"] = actions.trigger(done)
    return response


@act.post("/hold", response_class=HTMLResponse)
def hold_action(request: Request, scope: str = Form(""), reason: str = Form(""), codex: str = Form(""),
                stage: str = Form(""), unit: str = Form(""),
                conn: sqlite3.Connection = Depends(_write_conn)):
    return _receipt(request, actions.hold(conn, scope, reason, codex, stage, unit))


@act.post("/lift/{hold_id}", response_class=HTMLResponse)
def lift_action(request: Request, hold_id: int, conn: sqlite3.Connection = Depends(_write_conn)):
    return _receipt(request, actions.lift(conn, hold_id))


def _unit_order_route(kind: str) -> None:
    """POST /act/<kind> for a bump, retry or requeue on one unit."""
    def unit_order_action(request: Request, codex: str = Form(""), stage: str = Form(""),
                          unit: str = Form(""), conn: sqlite3.Connection = Depends(_write_conn)):
        return _receipt(request, actions.unit_order(conn, kind, codex, stage, unit))
    act.post(f"/{kind}", response_class=HTMLResponse, name=f"{kind}_action")(unit_order_action)


for _kind in actions.UNIT_KINDS:
    _unit_order_route(_kind)


@act.post("/redo", response_class=HTMLResponse)
def redo_action(request: Request, codex: str = Form(""), stage: str = Form(""), unit: str = Form(""),
                step_id: str = Form(""), note: str = Form(""), artefact: str = Form(""),
                conn: sqlite3.Connection = Depends(_write_conn)):
    return _receipt(request, actions.redo(conn, codex, stage, unit, step_id, note, artefact))


@act.post("/acknowledge", response_class=HTMLResponse)
def acknowledge_action(request: Request, codex: str = Form(""), stage: str = Form(""), unit: str = Form(""),
                       note: str = Form(""), conn: sqlite3.Connection = Depends(_write_conn)):
    return _receipt(request, actions.acknowledge(conn, codex, stage, unit, note))


async def _refused(request: Request, exc: actions.Refused):
    """A refused action is a fragment with the reason, swapped where the receipt goes."""
    return templates.TemplateResponse(request, "_refused.html", {"detail": exc.detail},
                                      status_code=exc.status)


async def _not_found(request: Request, exc: StarletteHTTPException):
    """Every refusal is a page in the shell with the reason and the asked path;
    never a stack, never a 403."""
    return _error_page(request, exc.status_code, str(exc.detail))


async def _server_error(request: Request, exc: Exception):
    """A failure is the same page with a 500 -- the shell and a way home, never a stack."""
    return _error_page(request, 500, f"the board failed on this page ({type(exc).__name__})")


def _error_page(request: Request, status: int, detail: str) -> HTMLResponse:
    """The error template inside the shell; a bare page when even that cannot render."""
    context = {**_shared(request), "detail": detail, "status": status, "path": request.url.path,
               "shell": _error_shell(request)}
    try:
        return templates.TemplateResponse(request, "404.html", context, status_code=status)
    except Exception:
        return HTMLResponse(f"<!doctype html><title>{status}</title><h1>{status}</h1><p>{html.escape(detail)}</p>"
                            f'<p><code>{html.escape(request.url.path)}</code></p><p><a href="/">Home</a></p>',
                            status_code=status)


def _error_shell(request: Request) -> dict | None:
    """The shell for the asked path, or None when the studio cannot be read."""
    try:
        conn = request.app.state.conn_factory()
    except Exception:
        return None
    try:
        return shell.shell(conn, request.app.state.library, request.url.path)
    except Exception:
        return None
    finally:
        conn.close()


def make_app(conn_factory: Callable[[], sqlite3.Connection], library: Path,
             logs: Path | None = None, org_page: Path = ORG_PAGE,
             write_factory: Callable[[], sqlite3.Connection] | None = None) -> FastAPI:
    """The board over one read-only connection factory, one library root and
    one logs root (default: the library's sibling `logs/`); with a write
    factory, the /act/ routes can give orders, else they answer 405."""
    app = FastAPI(title="Visurena Studio — Command Center")
    app.state.conn_factory = conn_factory
    app.state.write_factory = write_factory
    app.state.library = Path(library)
    app.state.logs = Path(logs) if logs else Path(library).parent / "logs"
    app.state.org_page = Path(org_page)
    app.state.procs = procs.list_processes
    app.state.thumbs = thumbs.Lru()
    app.state.thumb_limiter = None
    app.state.boot = time.time()
    app.state.progress = gpu_progress(app)
    app.mount("/static", CachedStatic(directory=str(HERE / "static")), name="static")
    app.include_router(router)
    app.include_router(act)
    app.include_router(viewer_routes.router)
    app.add_exception_handler(StarletteHTTPException, _not_found)
    app.add_exception_handler(actions.Refused, _refused)
    app.add_exception_handler(Exception, _server_error)
    return app
