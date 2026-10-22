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
import os
import shutil
import time
import urllib.request
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from studio import settings

WORKFLOWS = Path("D:/Projects/KingdomOfViSuReNa/alpha/comfy_studio/workflows")
COMFY_ROOT = settings.comfy_root()
HOST = settings.comfy_host()
"""The portable ComfyUI on :8188, or the sandbox's comfy/ and fake engine in a rehearsal
(2026-10-21_ep02_proof 1.2)."""


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


def staged_name(path: Path) -> str:
    """The content-addressed name `stage_image` gives a file, without copying
    it -- so currency can ask what a build WOULD stage."""
    path = Path(path)
    digest = hashlib.md5(path.read_bytes()).hexdigest()[:8]
    return f"{path.stem}_{digest}{path.suffix}"


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
    dest = COMFY_ROOT / "input" / staged_name(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    # The Qwen3-VL reader writes its frame into ComfyUI/temp; a second instance
    # deleted that folder on exit and every read failed (2026-10-11).
    (COMFY_ROOT / "temp").mkdir(parents=True, exist_ok=True)
    # the name IS the content, so an existing file is already the right bytes
    if not dest.exists():
        shutil.copy2(path, dest)
    return dest.name


UNREACHABLE = (urllib.error.URLError, TimeoutError, ConnectionError)
"""What a call raises while the engine is down or restarting."""

TRANSIENT = ("HostBuffer", "read_file_slice")
"""Substrings of execution errors that are the machine's moment, not the
graph's fault -- worth exactly ONE resubmission of the same filled graph.
Deliberately narrow; extend only from observed drive logs (a renamed node
error silently disables the retry, which fails safe: behaves as today)."""


def transient(said: str) -> bool:
    """Whether an execution failure belongs to the retriable class."""
    return any(mark in (said or "") for mark in TRANSIENT)

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


def already_queued(queue: dict, prompt_id: str) -> str | None:
    """`prompt_id` when a running or pending job carries it, else None.  The job's identity is the
    client id `submit` posted, never its `filename_prefix`: `trailer_say`, `ep_bed` and `ep_title`
    are constants and `ep_take_05` names no episode, so a prefix adopted another job (fleet E A4)."""
    for key in ("queue_running", "queue_pending"):
        if any(len(item) > 1 and item[1] == prompt_id for item in queue.get(key, [])):
            return prompt_id
    return None


def took(prompt_id: str) -> bool:
    """The engine holds the job: queued, running, or already in its history."""
    if already_queued(reachable(_get, "/queue") or {}, prompt_id):
        return True
    return bool((reachable(_get, f"/history/{prompt_id}") or {}).get(prompt_id))


CLAIM_WAIT_S = 30.0
"""The longest a submission waits for another process's GPU claim (av3 master, whisper)."""
CLAIM_POLL_S = 2.0


def foreign_claims(own_pid: int) -> list[dict]:
    """The live GPU claims held by processes other than this one."""
    from studio import compute_device
    return compute_device.live_claims(own_pid=own_pid)


def wait_foreign_claims(cap_s: float = CLAIM_WAIT_S, claims=foreign_claims, sleep=time.sleep,
                        now=time.time) -> bool:
    """Wait up to `cap_s` for foreign live claims to clear; True when one still holds
    the card at the cap.  Never waits for this pid's own claim.  A probe failure waits for nothing."""
    give_up = now() + cap_s
    while True:
        try:
            held = claims(os.getpid())
        except Exception:
            return False
        if not held:
            return False
        if now() >= give_up:
            return True
        sleep(CLAIM_POLL_S)


def submit(workflow: dict, timeout: float = 180.0) -> str:
    """Queue a filled-in workflow and return its prompt id.

    POSTING A TAKE IS NOT IDEMPOTENT.  `_open` retries anything that looks like
    an unreachable engine, and a socket timeout looks exactly like one -- but a
    busy ComfyUI answers slowly while having ALREADY queued the job.  MEASURED
    on WotW ep04 (2026-09-19): take 11 was queued SEVEN times and take 01 twice
    behind a 694 s take, ~45 min of GPU spent rendering the same seed.  So a
    timeout here asks the engine whether the job landed instead of re-POSTing, by the client
    prompt id this POST carries (one id, so the second POST, if any, cannot run twice either)."""
    wait_foreign_claims()
    own = str(uuid.uuid4())
    body = json.dumps({"prompt": workflow, "prompt_id": own}).encode("utf-8")
    request = urllib.request.Request(
        f"{HOST}/prompt", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return accepted(json.loads(response.read()))
    except UNREACHABLE as failure:
        if isinstance(failure, urllib.error.HTTPError):
            raise RuntimeError(
                f"ComfyUI rejected the workflow: {failure.read().decode()[:900]}") from None
        if took(own):
            return own
        with _open(request) as response:                 # engine really was down
            return accepted(json.loads(response.read()))


def accepted(reply: dict) -> str:
    """The prompt id of a WHOLE accept.  An HTTP 200 carrying `node_errors` is the engine's partial
    accept (GPU transcript 2026-10-21, error_invalid_graph.json): it queued only the outputs that
    still validate, and the job ends "success" with no picture, so a caller's `run(...)[0]` dies on
    an IndexError.  The remnant is taken off the queue and the answer raised as the rejection it is."""
    if not reply.get("node_errors"):
        return reply["prompt_id"]
    try:
        _post("/queue", {"delete": [reply["prompt_id"]]})
    except (OSError, ValueError):                       # best effort: the remnant renders no picture
        pass
    raise RuntimeError(f"ComfyUI accepted only part of the workflow: {json.dumps(reply['node_errors'])[:900]}")


def node_order(node_id) -> tuple[int, ...]:
    """A node id's place in node order; a subgraph's "30:20" sorts as (30, 20), after "30"."""
    return tuple(int(part) if part.isdigit() else 0 for part in str(node_id).split(":"))


def _post(path: str, body: dict | None = None) -> None:
    """One fire-and-forget POST to the engine."""
    data = json.dumps(body or {}).encode("utf-8")
    request = urllib.request.Request(
        f"{HOST}{path}", data=data, headers={"Content-Type": "application/json"})
    with _open(request):
        return None


def free_models() -> None:
    """Unload every staged model.  A VLM asked to load beside H3's DiT and
    text encoder lands half on the CPU and answers in ten minutes, not one.
    BEST-EFFORT AND NEVER RETRIED: with no engine up there is nothing staged
    to free, and a judge batch of fake readers (every eye test) must not sit
    in _open's restart loop (five-hour plan fix 5 wrapped the eyes in
    model_kept)."""
    try:
        data = json.dumps({"unload_models": True, "free_memory": True}).encode("utf-8")
        request = urllib.request.Request(f"{HOST}/free", data=data,
                                         headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=10.0):
            return None
    except OSError:
        pass


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


def outputs_by_node(record: dict) -> dict[str, list[Path]]:
    """node id -> the files that node reported.  On v0.41.2 a LoadVideo echoes its
    INPUT here (type "input") ahead of the SaveVideo's output, so a caller that
    wants the render names its save node (Jekyll Kawajiri POC, 2026-10-18)."""
    out: dict[str, list[Path]] = {}
    for node, rec in record.get("outputs", {}).items():
        out[str(node)] = outputs_of({"outputs": {node: rec}})
    return out


def texts_of(record: dict) -> list[str]:
    """Every text a finished job reported (PreviewAny-style `{"text": [...]}`
    entries, e.g. a VLM caption), in node order.  These are not files, so
    `outputs_of` never sees them."""
    found: list[str] = []
    for node_id in sorted(record.get("outputs", {}), key=node_order):
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


def queue_counts_strict(fetch=None) -> tuple[int, int]:
    """(running, pending) off /queue; an engine that cannot be reached RAISES, so the
    device router reads a down engine as down, not as an idle one."""
    queue = (fetch or _get_once)("/queue")
    return len(queue.get("queue_running", [])), len(queue.get("queue_pending", []))


def queue_counts(fetch=None) -> tuple[int, int]:
    """(running, pending) off /queue.  An engine that cannot be reached holds
    no queue -- a restart empties it -- and the stage itself will meet the
    restart; an engine that ANSWERS with an error is not absent, and raises."""
    try:
        return queue_counts_strict(fetch)
    except UNREACHABLE as failure:
        if not down(failure):
            raise
        return 0, 0


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


def wait_record(prompt_id: str, timeout: float = 3600.0, poll: float = 0.5) -> dict:
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
                changed_over(record)                     # A27: the first job after a free closes its load row
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


def retried(graph: dict, timeout: float) -> list[Path]:
    """Submit and wait once; on a TRANSIENT execution error or a lost engine,
    the SAME filled graph goes in exactly once more -- then the failure is
    real and propagates.  One retry, never a loop (G-TRANSIENT-RETRY: a
    HostBuffer.read_file_slice moment used to become a fatal SystemExit)."""
    try:
        return wait(submit(graph), timeout=timeout)
    except EngineLost:
        return wait(submit(graph), timeout=timeout)
    except RuntimeError as err:
        if not transient(str(err)):
            raise
        return wait(submit(graph), timeout=timeout)


def run(name: str, values: dict[str, Any], timeout: float = 3600.0) -> list[Path]:
    """Fill in a workflow by name, run it, and return what it wrote; a
    transient engine failure is resubmitted once (`retried`)."""
    template, inject = load_workflow(name)
    return retried(apply_inject(template, inject, values), timeout)


KEEP_LOADED = False
"""Set inside `model_kept()`: text jobs keep their model between reads."""


def keep_loaded(prompt: dict) -> dict:
    """Every node that can keep its model, told to keep it."""
    for node in prompt.values():
        if "keep_model_loaded" in node.get("inputs", {}):
            node["inputs"]["keep_model_loaded"] = True
    return prompt


KEEP_DEPTH = 0
"""How many `model_kept()` batches are open: only the outermost frees."""


@contextmanager
def model_kept():
    """A batch of reads that loads its model once; the OUTERMOST batch begins AND
    ends with /free, so the VL model never sits beside H3 (speed plan #6).  ep14
    (2026-09-29): the first read after a render round hung 600 s twice with H3
    still staged -- 5.5 GB of 24 free, the VL model loading half on the CPU.
    Nested batches free nothing: the inner exit must not unload the outer's model."""
    global KEEP_LOADED, KEEP_DEPTH
    if KEEP_DEPTH == 0:
        free_models()
    KEEP_DEPTH += 1
    KEEP_LOADED = True
    try:
        yield
    finally:
        KEEP_DEPTH -= 1
        if KEEP_DEPTH == 0:
            KEEP_LOADED = False
            free_models()


LAST_FAMILY: str | None = None
"""The model family the engine last ran for this process (K10)."""


def free_on_family(family: str) -> bool:
    """Free the engine's models when the GPU family changes (krea -> vl -> h3);
    True when it freed.  Best effort, never raises; a blank family changes nothing."""
    global LAST_FAMILY
    if not family or family == LAST_FAMILY:
        return False
    open_changeover({"model": family, "why": f"{LAST_FAMILY or 'nothing'} -> {family}", "began": time.time()})
    LAST_FAMILY = family                 # the first call frees too: another process may have staged models
    try:
        free_models()
    except Exception:
        return False
    return True


CHANGEOVERS: Path | None = settings.library_root() / "changeovers.jsonl"
"""One row per model load (craft ruling A27): the family the engine changed to, why, and the seconds from the
free to the first job done on it (load and that job; `node_s` is the engine's own window).  None logs nothing."""


def open_path() -> Path | None:
    """The open changeover, on disk beside the ledger: the drive frees (step_runner) and the step's own child
    process waits on the job (stage_run.launch), so memory in one process closed nothing (wave-3 review)."""
    return None if CHANGEOVERS is None else Path(CHANGEOVERS).with_name(Path(CHANGEOVERS).stem + ".open.json")


def open_changeover(said: dict) -> None:
    """Open a changeover; a later free replaces one no job closed.  Never raises."""
    if (path := open_path()) is not None:
        try:
            path.write_text(json.dumps(said), encoding="utf-8")
        except OSError:
            pass


def claim_changeover() -> dict | None:
    """The open changeover, taken by exactly one process: only one rename of the file can win."""
    path = open_path()
    if path is None or not path.exists():
        return None
    mine = path.with_name(f"{path.name}.{os.getpid()}")
    try:
        os.rename(path, mine)
        said = json.loads(mine.read_text(encoding="utf-8"))
        mine.unlink()
    except (OSError, ValueError):
        return None
    return said if isinstance(said, dict) else None


def changed_over(record: dict) -> None:
    """Close the open changeover with its row on the first job done after the free, in any process; a later
    job is no load.  A ledger that cannot be written, or a record it cannot read, never fails the job."""
    if (said := claim_changeover()) is None:
        return
    try:
        from studio import take_phases
        t0, t1 = take_phases.window(record)
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "model": said["model"], "why": said["why"],
               "seconds": round(time.time() - float(said["began"]), 2),
               "node_s": round(t1 - t0, 2) if t0 and t1 else None}
        with open(CHANGEOVERS, "a", encoding="utf-8") as out:
            out.write(json.dumps(row) + "\n")
    except (OSError, KeyError, TypeError, ValueError, IndexError, AttributeError):
        pass


ROW_DEADLINE: float | None = None
"""Epoch seconds when the current step row's cap ends, or None (set by the runner)."""
ROW_GRACE_S = 60.0


@contextmanager
def row_deadline(at: float | None):
    """Text calls inside the block may not outlive the row's cap by more than ROW_GRACE_S."""
    global ROW_DEADLINE
    before, ROW_DEADLINE = ROW_DEADLINE, at
    try:
        yield
    finally:
        ROW_DEADLINE = before


def text_timeout(timeout: float, applies: bool = True) -> float:
    """min(the call's timeout, the row's remaining time + grace); renders pass applies=False."""
    if not applies or ROW_DEADLINE is None:
        return timeout
    return max(1.0, min(timeout, ROW_DEADLINE - time.time() + ROW_GRACE_S))


VLM_CALLS: Path | None = settings.library_root() / "vlm_calls.jsonl"
"""One row per engine text read (five-iterations B15.2): the ~13 s read's setup against its
decode is unmeasured, so ep02's reads fit seconds = a + b * tokens.  None logs nothing (tests)."""


def call_row(name: str, seconds: float, text: str, record: dict) -> dict:
    """The read's row: wall seconds, the engine's execution seconds, the reply's size."""
    from studio import take_phases
    t0, t1 = take_phases.window(record)
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "workflow": name, "seconds": round(seconds, 2),
            "node_s": round(t1 - t0, 2) if t0 and t1 else None,
            "answer_chars": len(text), "answer_tokens": -(-len(text) // 4)}


def log_call(row: dict) -> None:
    """Append the row; a log that cannot be written never fails the read."""
    if VLM_CALLS is None:
        return
    try:
        with open(VLM_CALLS, "a", encoding="utf-8") as out:
            out.write(json.dumps(row) + "\n")
    except OSError:
        pass


def run_text(name: str, values: dict[str, Any], timeout: float = 600.0) -> str:
    """Fill in a text-producing workflow (a VLM caption), run it, and return the text.
    A call that outlives its (row-capped) timeout interrupts the engine, then raises."""
    template, inject = load_workflow(name)
    prompt = apply_inject(template, inject, values)
    began = time.monotonic()
    try:
        record = wait_record(submit(keep_loaded(prompt) if KEEP_LOADED else prompt),
                             timeout=text_timeout(timeout))
    except StillRunning:
        reachable(interrupt)
        raise
    text = "\n".join(texts_of(record))
    log_call(call_row(name, time.monotonic() - began, text, record))
    return text


TEXT_CACHE = settings.library_root() / ".vlm_cache"
TEXT_CACHE_VERSION = "1"
"""Bump when a node's behaviour changes under an unchanged workflow JSON."""


def text_key(name: str, values: dict[str, Any]) -> str:
    """Everything that makes a text answer: the workflow, its inject map and
    the values (a staged image name is content-addressed, so it is the bytes)."""
    template, inject = load_workflow(name)
    body = json.dumps([TEXT_CACHE_VERSION, name, template, inject, values], sort_keys=True, default=str)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def cached_text(name: str, values: dict[str, Any], readable, timeout: float = 600.0,
                root: Path | None = None) -> str:
    """`run_text`, served from the cache when these exact inputs were read
    before; an answer `readable` refuses is returned but never kept (speed plan #5)."""
    key = text_key(name, values)
    path = Path(root or TEXT_CACHE) / key[:2] / f"{key}.txt"
    if path.exists():
        return path.read_text(encoding="utf-8")
    text = run_text(name, values, timeout)
    if readable(text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return text
