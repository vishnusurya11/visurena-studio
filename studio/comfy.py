"""A thin, honest client for the local ComfyUI.

Workflows and their manifests are owned by comfy_studio; this module only knows
how to fill one in and run it.  The manifest's `inject` map is the whole
interface: a name -> {node, field} pair.  Injecting a name the manifest does
not declare raises, because a silently-ignored input is how a reference image
gets "passed" to a workflow that never reads it.
"""
from __future__ import annotations

import hashlib
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
    """Copy a file into ComfyUI's input dir under a CONTENT-ADDRESSED name.

    `ComfyUI/input/` is one flat global directory shared by every book and every
    episode, and this used to copy in under the file's BARE NAME, skipping the
    copy on an mtime comparison.  Two things followed, both measured on episode 3
    (2026-09-13):

      * A REDRAW MASQUERADED AS THE RENDER'S INPUT.  Fifteen ep03 cells on disk
        no longer match the bytes staged when their take rendered.  T13 scores
        100/100 only because its record predates a redraw -- re-run its DQ and it
        hard-fails against a picture it was never shown.  The gate and the render
        were reading different files and nothing said so.
      * EPISODES COLLIDED SILENTLY.  Cell names carry no book and no episode, and
        ep02 and ep03 share more than twenty (`Q00_0.png`, `Q02_1.png`, ...).
        Stage one after the other and the next render quietly uses the wrong
        picture -- no error, no log line.

    The digest makes both impossible, and it makes the staged name itself the
    record of which bytes rendered."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"cannot stage missing image: {path}")
    digest = hashlib.md5(path.read_bytes()).hexdigest()[:8]
    dest = COMFY_ROOT / "input" / f"{path.stem}_{digest}{path.suffix}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    # the name IS the content, so an existing file is already the right bytes
    if not dest.exists():
        shutil.copy2(path, dest)
    return dest.name


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


def save_prefix(graph: dict) -> str | None:
    """The `filename_prefix` a graph writes under: its identity in the queue."""
    for node in graph.values():
        if node.get("class_type", "").startswith("Save"):
            got = node.get("inputs", {}).get("filename_prefix")
            if got:
                return got
    return None


def already_queued(queue: dict, prefix: str) -> str | None:
    """The prompt id of a running or pending job writing `prefix`, if any."""
    for key in ("queue_running", "queue_pending"):
        for item in queue.get(key, []):
            if len(item) > 2 and save_prefix(item[2]) == prefix:
                return item[1]
    return None


def submit(workflow: dict, timeout: float = 180.0) -> str:
    """Queue a filled-in workflow and return its prompt id.

    POSTING A TAKE IS NOT IDEMPOTENT.  `_open` retries anything that looks like
    an unreachable engine, and a socket timeout looks exactly like one -- but a
    busy ComfyUI answers slowly while having ALREADY queued the job.  MEASURED
    on WotW ep04 (2026-09-19): take 11 was queued SEVEN times and take 01 twice
    behind a 694 s take, ~45 min of GPU spent rendering the same seed.  So a
    timeout here asks the queue whether the job landed instead of re-POSTing."""
    body = json.dumps({"prompt": workflow}).encode("utf-8")
    request = urllib.request.Request(
        f"{HOST}/prompt", data=body, headers={"Content-Type": "application/json"})
    prefix = save_prefix(workflow)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())["prompt_id"]
    except UNREACHABLE as failure:
        if isinstance(failure, urllib.error.HTTPError):
            raise RuntimeError(
                f"ComfyUI rejected the workflow: {failure.read().decode()[:900]}") from None
        landed = already_queued(reachable(_get, "/queue") or {}, prefix) if prefix else None
        if landed:
            return landed
        with _open(request) as response:                 # engine really was down
            return json.loads(response.read())["prompt_id"]


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


STUCK_SECONDS = 30.0
"""How long after an interrupt a job may still show as running before the
engine is called stuck.  Run 18: a Qwen3-VL read on a VRAM-full engine
ignored six interrupts over 11 h; a job that does take the interrupt is
off the queue within a poll or two."""


def stuck(prompt_id: str, patience: float = STUCK_SECONDS, poll: float = 5.0) -> bool:
    """Whether the job is still running `patience` after its interrupt.  An
    engine that cannot be reached is restarting, which is not stuck."""
    deadline = time.time() + patience
    while time.time() < deadline:
        if not reachable(running, prompt_id):
            return False
        time.sleep(poll)
    return bool(reachable(running, prompt_id))


def history(prompt_id: str) -> dict:
    """The engine's record of one job, or {} while it is still queued."""
    with _open(f"{HOST}/history/{prompt_id}") as response:
        return json.loads(response.read()).get(prompt_id, {})


class StillRunning(TimeoutError):
    """A job that outlived its timeout, named so the caller can ask whether
    the interrupt it sends takes."""

    def __init__(self, prompt_id: str, timeout: float):
        super().__init__(f"{prompt_id} still running after {timeout}s")
        self.prompt_id = prompt_id


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


def _get_once(path: str, timeout: float = 5.0) -> dict:
    """One GET with no restart wait: a question about the queue is answered
    now or not at all."""
    with urllib.request.urlopen(f"{HOST}{path}", timeout=timeout) as response:
        return json.loads(response.read())


def queue_counts(fetch=None) -> tuple[int, int]:
    """(running, pending) off /queue.  An engine that cannot be reached holds
    no queue -- a restart empties it -- and the stage itself will meet the
    restart; an engine that ANSWERS with an error is not absent, and raises."""
    try:
        queue = (fetch or _get_once)("/queue")
    except UNREACHABLE as failure:
        if not down(failure):
            raise
        return 0, 0
    return len(queue.get("queue_running", [])), len(queue.get("queue_pending", []))


def busy(fetch=None) -> bool:
    """Whether the engine has work: running + pending > 0.

    Episode 10, 20:20: a take_dq's seven Whisper jobs were queued when the r4
    takes were submitted; T02 rendered at 598 s (warm 266) and the DQ ran five
    times its uncontended time and was then re-run.  `run.py` asks this before
    any stage that touches the engine."""
    running, pending = queue_counts(fetch)
    return running + pending > 0


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
    raise StillRunning(prompt_id, timeout)


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
