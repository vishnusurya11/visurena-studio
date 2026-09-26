"""The board's web process (decision 2026-09-25, "the board"): FastAPI +
Jinja2 + htmx, read-only.  `make_app(conn_factory, library)` builds it; the
connection is opened per request from the injected factory (`readonly_factory`
opens `mode=ro` with a 250 ms busy timeout, so a poll never blocks a runner),
the pages render the views, the partials are the same fragments the pages
include, the JSON twins answer with the models.  No route runs a step, spawns
a process, writes a file or writes a row."""
from __future__ import annotations

import sqlite3
from collections.abc import Callable, Iterator
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from studio import registry
from studio.command_center import library_paths, models, views

HERE = Path(__file__).resolve().parent
ORG_PAGE = registry.ROOT / "architecture" / "index.html"
templates = Jinja2Templates(directory=str(HERE / "templates"))
router = APIRouter()


def readonly_factory(db_path: str | Path) -> Callable[[], sqlite3.Connection]:
    """A factory of read-only connections to one database file (`mode=ro`,
    busy_timeout 250 ms, rows by name).  A write through it is an
    OperationalError -- the web process cannot write even by mistake."""
    uri = f"file:{Path(db_path).resolve().as_posix()}?mode=ro"

    def open_connection() -> sqlite3.Connection:
        conn = sqlite3.connect(uri, uri=True, timeout=0.25)
        conn.execute("PRAGMA busy_timeout = 250")
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


def _render(request: Request, name: str, **context) -> HTMLResponse:
    """A template with what every page shares: the legend, the nav's stages."""
    return templates.TemplateResponse(request, name, {
        "legend": views.LEGEND, "stages": registry.stage_names(), **context})


def _department(conn: sqlite3.Connection, stage: str, book: str | None, state: str | None) -> dict:
    """The department view, or a 404 for a stage the registry does not know."""
    try:
        return views.department(conn, stage, book=book, state=state)
    except ValueError:
        raise HTTPException(404, f"{stage!r} is not a department") from None


def _unit(request: Request, conn: sqlite3.Connection, stage: str, codex: str, unit: str) -> dict:
    """The unit view, or a 404 when it has no row."""
    state = request.app.state
    found = views.unit(conn, state.library, codex, stage, unit, logs=state.logs)
    if found is None:
        raise HTTPException(404, f"no unit {stage}/{codex}/{unit}")
    return found


# --- pages ---


@router.get("/", response_class=HTMLResponse)
def home(request: Request, conn: sqlite3.Connection = Depends(_conn)):
    return _render(request, "home.html", floor=views.floor(conn), attention=views.attention(conn),
                   lanes=views.lanes(conn), today=views.today(conn), books=views.book_names(conn))


@router.get("/floor", response_class=HTMLResponse)
def floor_page(request: Request, conn: sqlite3.Connection = Depends(_conn)):
    return _render(request, "floor.html", floor=views.floor(conn), queue=views.queue(conn),
                   holds=views.holds(conn), today=views.today(conn), books=views.book_names(conn))


@router.get("/d/{stage}", response_class=HTMLResponse)
def department_page(request: Request, stage: str, book: str | None = None, state: str | None = None,
                    conn: sqlite3.Connection = Depends(_conn)):
    return _render(request, "department.html", dept=_department(conn, stage, book, state),
                   book=book, state=state, books=views.book_names(conn))


@router.get("/d/{stage}/{codex}/{unit}", response_class=HTMLResponse)
def unit_page(request: Request, stage: str, codex: str, unit: str,
              conn: sqlite3.Connection = Depends(_conn)):
    return _render(request, "unit.html", unit=_unit(request, conn, stage, codex, unit),
                   stage=stage, codex=codex, books=views.book_names(conn))


@router.get("/b/{codex}", response_class=HTMLResponse)
def book_page(request: Request, codex: str, conn: sqlite3.Connection = Depends(_conn)):
    found = views.book(conn, request.app.state.library, codex)
    if found is None:
        raise HTTPException(404, f"no book {codex}")
    return _render(request, "book.html", book=found, books=views.book_names(conn))


@router.get("/org")
def org_chart(request: Request):
    page = Path(request.app.state.org_page)
    if not page.is_file():
        raise HTTPException(404, "the org chart is not on disk")
    return FileResponse(page, media_type="text/html", headers={"Cache-Control": "no-store"})


# --- partials (the same fragments the pages include) ---


@router.get("/partials/floor", response_class=HTMLResponse)
def floor_partial(request: Request, conn: sqlite3.Connection = Depends(_conn)):
    return _render(request, "_floor.html", floor=views.floor(conn), books=views.book_names(conn))


@router.get("/partials/attention", response_class=HTMLResponse)
def attention_partial(request: Request, conn: sqlite3.Connection = Depends(_conn)):
    return _render(request, "_attention.html", attention=views.attention(conn), books=views.book_names(conn))


@router.get("/partials/lanes", response_class=HTMLResponse)
def lanes_partial(request: Request, conn: sqlite3.Connection = Depends(_conn)):
    return _render(request, "_lanes.html", lanes=views.lanes(conn), books=views.book_names(conn))


@router.get("/partials/d/{stage}", response_class=HTMLResponse)
def department_partial(request: Request, stage: str, book: str | None = None, state: str | None = None,
                       conn: sqlite3.Connection = Depends(_conn)):
    return _render(request, "_rows.html", dept=_department(conn, stage, book, state),
                   books=views.book_names(conn))


@router.get("/partials/unit/{stage}/{codex}/{unit}/tails", response_class=HTMLResponse)
def tails_partial(request: Request, stage: str, codex: str, unit: str,
                  conn: sqlite3.Connection = Depends(_conn)):
    return _render(request, "_tails.html", unit=_unit(request, conn, stage, codex, unit))


# --- the JSON twins ---


@router.get("/api/floor.json", response_model=models.Floor)
def floor_json(conn: sqlite3.Connection = Depends(_conn)):
    return views.floor(conn)


@router.get("/api/d/{stage}.json", response_model=models.Department)
def department_json(stage: str, book: str | None = None, state: str | None = None,
                    conn: sqlite3.Connection = Depends(_conn)):
    return _department(conn, stage, book, state)


@router.get("/api/unit/{stage}/{codex}/{unit}.json", response_model=models.Unit)
def unit_json(request: Request, stage: str, codex: str, unit: str,
              conn: sqlite3.Connection = Depends(_conn)):
    return _unit(request, conn, stage, codex, unit)


# --- artefacts ---


@router.get("/lib/{codex}/{path:path}")
def artefact(request: Request, codex: str, path: str):
    target = library_paths.resolve_artefact(request.app.state.library, codex, path)
    if target is None:
        raise HTTPException(404, "no such artefact")
    return FileResponse(target, headers={"Cache-Control": "no-store"})


async def _not_found(request: Request, exc: StarletteHTTPException):
    """Every refusal is a plain page with the reason; never a stack, never a 403."""
    return templates.TemplateResponse(request, "404.html", {"detail": exc.detail, "status": exc.status_code},
                                      status_code=exc.status_code)


def make_app(conn_factory: Callable[[], sqlite3.Connection], library: Path,
             logs: Path | None = None, org_page: Path = ORG_PAGE) -> FastAPI:
    """The board over one connection factory, one library root and one logs
    root (default: the library's sibling `logs/`)."""
    app = FastAPI(title="Visurena Studio — Command Center")
    app.state.conn_factory = conn_factory
    app.state.library = Path(library)
    app.state.logs = Path(logs) if logs else Path(library).parent / "logs"
    app.state.org_page = Path(org_page)
    app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")
    app.include_router(router)
    app.add_exception_handler(StarletteHTTPException, _not_found)
    return app
