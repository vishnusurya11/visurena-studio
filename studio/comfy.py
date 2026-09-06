"""A thin, honest client for the local ComfyUI.

Workflows and their manifests are owned by comfy_studio; this module only knows
how to fill one in and run it.  The manifest's `inject` map is the whole
interface: a name -> {node, field} pair.  Injecting a name the manifest does
not declare raises, because a silently-ignored input is how a reference image
gets "passed" to a workflow that never reads it.
"""
from __future__ import annotations

import json
import shutil
import time
import urllib.request
from pathlib import Path
from typing import Any

WORKFLOWS = Path("D:/Projects/KingdomOfViSuReNa/alpha/comfy_studio/workflows")
COMFY_ROOT = Path("D:/Projects/KingdomOfViSuReNa/alpha/ComfyUI_windows_portable/ComfyUI")
HOST = "http://127.0.0.1:8188"


def load_workflow(name: str) -> tuple[dict, dict]:
    """Return (api-format template, inject map) for a workflow by id."""
    hits = list(WORKFLOWS.glob(f"*/{name}.json"))
    if not hits:
        raise FileNotFoundError(f"no workflow {name!r} under {WORKFLOWS}")
    manifest = hits[0].with_name(f"{name}.manifest.json")
    template = json.loads(hits[0].read_text(encoding="utf-8"))
    inject = json.loads(manifest.read_text(encoding="utf-8"))["inject"]
    return template, inject


def apply_inject(template: dict, inject: dict, values: dict[str, Any]) -> dict:
    """Set each value on the node/field the manifest names.

    Raises on an undeclared name.  This is the guard that matters: the first
    trailer failed because ref images were 'passed' to a text-to-image
    workflow that had nowhere to put them.
    """
    out = json.loads(json.dumps(template))
    for key, value in values.items():
        if key not in inject:
            raise KeyError(f"workflow has no inject point {key!r}; has {sorted(inject)}")
        spec = inject[key]
        node = out[str(spec["node"])]
        node["inputs"][spec["field"]] = value
    return out


def stage_image(path: Path) -> str:
    """Copy an image into ComfyUI's input dir and return the bare filename."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"cannot stage missing image: {path}")
    dest = COMFY_ROOT / "input" / path.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or dest.stat().st_mtime < path.stat().st_mtime:
        shutil.copy2(path, dest)
    return path.name


UNREACHABLE = (urllib.error.URLError, TimeoutError, ConnectionError)
"""What a call raises while the engine is down or restarting."""

RESTART_SECONDS = 600.0
"""How long a call waits for an engine that cannot be reached.  The GPU is
shared: another session restarts ComfyUI under a run (run 11 died twice to
it), and a model-laden engine is back within minutes.  One that is not is
a failure the caller should see."""

RESTART_POLL = 5.0


def down(failure: BaseException) -> bool:
    """Whether the failure is the engine's absence, not its answer: HTTPError
    is a URLError by inheritance and a 400 retried for ten minutes is a 400."""
    return isinstance(failure, UNREACHABLE) and not isinstance(failure, urllib.error.HTTPError)


def _open(request, timeout: float = 60.0):
    """The one door to the engine: urlopen, retried while the engine is
    restarting, for RESTART_SECONDS at most."""
    give_up = time.time() + RESTART_SECONDS
    while True:
        try:
            return urllib.request.urlopen(request, timeout=timeout)
        except UNREACHABLE as failure:
            if not down(failure) or time.time() >= give_up:
                raise
            time.sleep(RESTART_POLL)


def submit(workflow: dict) -> str:
    """Queue a filled-in workflow and return its prompt id."""
    body = json.dumps({"prompt": workflow}).encode("utf-8")
    request = urllib.request.Request(
        f"{HOST}/prompt", data=body, headers={"Content-Type": "application/json"})
    try:
        with _open(request) as response:
            return json.loads(response.read())["prompt_id"]
    except urllib.error.HTTPError as failure:
        # The rejection body names the node and field; without it a 400 is
        # unactionable noise.
        raise RuntimeError(
            f"ComfyUI rejected the workflow: {failure.read().decode()[:900]}") from None


def _post(path: str, body: dict | None = None) -> None:
    """One fire-and-forget POST to the engine."""
    data = json.dumps(body or {}).encode("utf-8")
    request = urllib.request.Request(
        f"{HOST}{path}", data=data, headers={"Content-Type": "application/json"})
    with _open(request):
        return None


def free_models() -> None:
    """Unload every staged model.  A VLM asked to load beside H3's DiT and
    text encoder lands half on the CPU and answers in ten minutes, not one."""
    _post("/free", {"unload_models": True, "free_memory": True})


def interrupt() -> None:
    """Stop the running job; a call that outlived its timeout must not hold
    the queue against the next render."""
    _post("/interrupt")


def history(prompt_id: str) -> dict:
    """The engine's record of one job, or {} while it is still queued."""
    with _open(f"{HOST}/history/{prompt_id}") as response:
        return json.loads(response.read()).get(prompt_id, {})


class EngineLost(RuntimeError):
    """The engine answers again and knows nothing of the job: it restarted
    while the job ran.  A RuntimeError, so every caller that already treats
    a failed render as "the machine produced nothing" needs no new clause;
    one that can afford a second submission catches this first."""


def reachable(ask, *args):
    """`ask`'s answer, or None while the engine cannot be reached."""
    try:
        return ask(*args)
    except UNREACHABLE:
        return None


def outputs_of(record: dict) -> list[Path]:
    """Absolute paths of every file a finished job wrote."""
    found: list[Path] = []
    for node in record.get("outputs", {}).values():
        for key in ("images", "audio", "video", "gifs"):
            for item in node.get(key, []):
                sub = item.get("subfolder", "")
                found.append(COMFY_ROOT / item.get("type", "output") / sub / item["filename"])
    return found


def texts_of(record: dict) -> list[str]:
    """Every text a finished job reported (PreviewAny-style `{"text": [...]}`
    entries, e.g. a VLM caption), in node order.  These are not files, so
    `outputs_of` never sees them."""
    found: list[str] = []
    for node_id in sorted(record.get("outputs", {}), key=int):
        found += [t for t in record["outputs"][node_id].get("text", []) if isinstance(t, str)]
    return found


def _get(path: str) -> dict:
    with _open(f"{HOST}{path}") as response:
        return json.loads(response.read())


def pending(prompt_id: str) -> bool:
    """Whether the job is still waiting its turn behind another."""
    return any(item[1] == prompt_id for item in _get("/queue").get("queue_pending", []))


def running(prompt_id: str) -> bool:
    """Whether the job is the one the engine is executing now."""
    return any(item[1] == prompt_id for item in _get("/queue").get("queue_running", []))


def lost(prompt_id: str) -> bool:
    """The engine knows nothing of the job -- neither queued, nor running,
    nor finished.  Only a restart forgets a job."""
    return not pending(prompt_id) and not running(prompt_id) and not history(prompt_id)


QUEUE_SECONDS = 7200.0


def wait_record(prompt_id: str, timeout: float = 3600.0, poll: float = 5.0) -> dict:
    """Block until a job finishes and return its record; raise on engine error
    or timeout.  The clock starts when the job leaves the queue: a sheet
    queued behind an 11-minute take had timed out before it ran a second."""
    queued_until = time.time() + QUEUE_SECONDS
    while reachable(pending, prompt_id) is not False and time.time() < queued_until:
        time.sleep(poll)
    deadline = time.time() + timeout
    while time.time() < deadline:
        record = reachable(history, prompt_id)
        if record is not None:
            settled(prompt_id, record)
            if record.get("status", {}).get("completed"):
                return record
        time.sleep(poll)
    raise TimeoutError(f"{prompt_id} still running after {timeout}s")


def settled(prompt_id: str, record: dict) -> None:
    """Raise on the two ways a job ends with nothing: the engine reported
    an error, or it restarted and forgot the job.  An engine that is
    unreachable for the check is simply waited for."""
    if record.get("status", {}).get("status_str") == "error":
        raise RuntimeError(f"{prompt_id} failed: {_first_error(record)}")
    if not record and reachable(lost, prompt_id):
        raise EngineLost(f"{prompt_id} vanished: the engine restarted")


def wait(prompt_id: str, timeout: float = 3600.0, poll: float = 5.0) -> list[Path]:
    """Block until a job finishes; the files it wrote."""
    return outputs_of(wait_record(prompt_id, timeout, poll))


def _first_error(record: dict) -> str:
    for kind, payload in record.get("status", {}).get("messages", []):
        if kind == "execution_error":
            return f"{payload.get('node_type')}: {payload.get('exception_message')}"
    return "unknown error"


def run(name: str, values: dict[str, Any], timeout: float = 3600.0) -> list[Path]:
    """Fill in a workflow by name, run it, and return what it wrote."""
    template, inject = load_workflow(name)
    return wait(submit(apply_inject(template, inject, values)), timeout=timeout)


def run_text(name: str, values: dict[str, Any], timeout: float = 600.0) -> str:
    """Fill in a text-producing workflow (a VLM caption), run it, and return the text."""
    template, inject = load_workflow(name)
    record = wait_record(submit(apply_inject(template, inject, values)), timeout=timeout)
    return "\n".join(texts_of(record))
