"""The process table, read (progress tracker spec §7, liveness): which
process is driving an episode, and when it started.

The board spawns nothing, so the table is read through the Windows API with
ctypes (EnumProcesses, then per process the command line via
NtQueryInformationProcess(ProcessCommandLineInformation) and the creation time
via GetProcessTimes).  `find_drive` is pure over the rows, and the view takes
the lookup as an argument, so no test depends on this machine's processes.
Elsewhere than Windows the table is empty: every run reads as dead."""
from __future__ import annotations

import sys
import time
from typing import NamedTuple

EPOCH_DELTA = 11644473600.0      # 1601-01-01 to 1970-01-01, in seconds
CACHE_S = 3.0
_cache: dict[str, object] = {"at": 0.0, "rows": []}


class ProcInfo(NamedTuple):
    pid: int
    started: float | None          # UTC epoch seconds
    cmdline: str


def find_drive(rows: list[ProcInfo], codex: str, number: int) -> ProcInfo | None:
    """The earliest process whose command line runs drive.py for this codex
    and episode number (uv, its venv shim and the interpreter all match)."""
    wanted = {str(number), f"{number:02d}", f"ep{number:02d}"}
    hits = [p for p in rows if "drive.py" in p.cmdline and codex in p.cmdline
            and wanted & set(p.cmdline.replace('"', " ").split())]
    return min(hits, key=lambda p: p.started or 0.0) if hits else None


def list_processes() -> list[ProcInfo]:
    """Every process this user may query, with its command line; cached for a
    few seconds so a 2 s poll does not walk the table twice.  A process another
    session launched can be invisible here (OpenProcess refused, 2026-10-07):
    liveness falls back to the run's own files (views.carried), never to a
    spawned query -- the web process spawns nothing."""
    if time.time() - float(_cache["at"]) < CACHE_S:
        return list(_cache["rows"])
    rows = _windows_table() if sys.platform == "win32" else []
    _cache.update(at=time.time(), rows=rows)
    return rows


def _windows_table() -> list[ProcInfo]:
    """The Windows process table through ctypes."""
    api = _api()
    rows = []
    for pid in _pids(api):
        handle = api["k32"].OpenProcess(0x1000, False, pid)    # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            continue
        try:
            rows.append(ProcInfo(pid, _started(api, handle), _cmdline(api, handle)))
        finally:
            api["k32"].CloseHandle(handle)
    return rows


def _api() -> dict:
    """kernel32 and ntdll with the signatures this module calls."""
    import ctypes
    from ctypes import wintypes
    k32, nt = ctypes.WinDLL("kernel32", use_last_error=True), ctypes.WinDLL("ntdll")
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    k32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    nt.NtQueryInformationProcess.restype = ctypes.c_long
    nt.NtQueryInformationProcess.argtypes = [wintypes.HANDLE, wintypes.ULONG, ctypes.c_void_p,
                                             wintypes.ULONG, ctypes.POINTER(wintypes.ULONG)]
    return {"ctypes": ctypes, "wt": wintypes, "k32": k32, "nt": nt}


def _pids(api: dict) -> list[int]:
    """Every process id (K32EnumProcesses)."""
    ctypes, wt = api["ctypes"], api["wt"]
    arr, need = (wt.DWORD * 8192)(), wt.DWORD()
    if not api["k32"].K32EnumProcesses(arr, ctypes.sizeof(arr), ctypes.byref(need)):
        return []
    return [p for p in arr[: need.value // ctypes.sizeof(wt.DWORD)] if p]


def _started(api: dict, handle) -> float | None:
    """The process's creation time as UTC epoch seconds."""
    ctypes, wt = api["ctypes"], api["wt"]
    times = [wt.FILETIME() for _ in range(4)]
    if not api["k32"].GetProcessTimes(handle, *[ctypes.byref(t) for t in times]):
        return None
    ticks = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
    return ticks / 1e7 - EPOCH_DELTA


def _cmdline(api: dict, handle) -> str:
    """The process's command line (ProcessCommandLineInformation = 60); empty when refused."""
    ctypes, wt = api["ctypes"], api["wt"]

    class UnicodeString(ctypes.Structure):
        _fields_ = [("Length", wt.USHORT), ("MaximumLength", wt.USHORT), ("Buffer", ctypes.c_void_p)]
    buf, size = ctypes.create_string_buffer(65536), wt.ULONG(0)
    if api["nt"].NtQueryInformationProcess(handle, 60, buf, ctypes.sizeof(buf), ctypes.byref(size)) != 0:
        return ""
    text = UnicodeString.from_buffer(buf)
    return ctypes.wstring_at(text.Buffer, text.Length // 2) if text.Buffer else ""
