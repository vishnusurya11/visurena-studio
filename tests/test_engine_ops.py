"""The engine operations the autopilot runs (decision 2026-10-06, ops §2's
survival matrix): is the engine alive, is the same prompt still running, kill
the run TREE (never uv.exe alone: 2026-09-05, run 12c's python children kept
rendering 50 min after their uv died), kill ComfyUI's main.py, relaunch the
portable engine from its folder and wait for /system_stats (2026-09-06: a
VRAM-full engine ignores /interrupt).  Every I/O is an injected callable: no
test touches a process, a port or the GPU."""
from __future__ import annotations

from pathlib import Path

from studio import engine_ops as eo
from studio.command_center.procs import ProcInfo

CODEX = "20260827135508"
STATS = {"system": {"os": "nt"}, "devices": [{"vram_total": 1}]}


def test_alive_is_a_dict_off_system_stats_and_false_when_nothing_answers():
    asked = []
    assert eo.alive("http://e:1", get=lambda url: asked.append(url) or STATS)
    assert asked == ["http://e:1/system_stats"]

    def dead(url):
        raise ConnectionError("refused")
    assert not eo.alive("http://e:1", get=dead)


def test_queue_reads_the_running_prompt_ids_and_the_pending_count():
    doc = {"queue_running": [[0, "p-aaa", {}], [1, "p-bbb", {}]], "queue_pending": [[2, "p-ccc"]]}
    assert eo.queue("http://e:1", get=lambda url: doc) == {"running_ids": ["p-aaa", "p-bbb"], "pending": 1}


def test_an_unreachable_engine_holds_no_queue():
    def dead(url):
        raise ConnectionError("refused")
    assert eo.queue("http://e:1", get=dead) == {"running_ids": [], "pending": 0}


def test_the_same_prompt_across_the_window_is_stuck_and_a_moved_or_empty_one_is_not():
    assert eo.same_prompt_stuck({"running_ids": ["p-1"], "pending": 0}, {"running_ids": ["p-1"], "pending": 3})
    assert not eo.same_prompt_stuck({"running_ids": ["p-1"], "pending": 0}, {"running_ids": ["p-2"], "pending": 0})
    assert not eo.same_prompt_stuck({"running_ids": [], "pending": 0}, {"running_ids": [], "pending": 0})
    assert not eo.same_prompt_stuck({"running_ids": ["p-1"], "pending": 0}, {"running_ids": [], "pending": 0})


def rows() -> list[ProcInfo]:
    return [
        ProcInfo(10, 1.0, f'uv.exe run --no-sync python scripts/episode/drive.py {CODEX} 19'),
        ProcInfo(11, 2.0, f'"C:\\x\\.venv\\Scripts\\python.exe" scripts\\episode\\drive.py {CODEX} 19'),
        ProcInfo(12, 3.0, f'python.exe episode.py {CODEX} 19'),
        ProcInfo(13, 4.0, f'python.exe scripts/episode/step_09_shoot.py {CODEX} 19'),
        ProcInfo(14, 5.0, f'python.exe scripts/episode/plan_check.py {CODEX} 19'),
        ProcInfo(20, 6.0, f'python.exe scripts/episode/drive.py {CODEX} 18'),          # another episode
        ProcInfo(21, 7.0, f'python.exe scripts/episode/titles_batch.py {CODEX}'),      # book-wide, no episode
        ProcInfo(30, 8.0, 'python.exe -s ComfyUI/main.py --windows-standalone-build --reserve-vram 2'),
        ProcInfo(31, 9.0, 'explorer.exe'),
    ]


def test_the_run_tree_is_every_process_whose_command_line_runs_this_episode():
    assert [p.pid for p in eo.run_tree(rows(), CODEX, 19)] == [10, 11, 12, 13, 14]


def test_kill_run_tree_kills_each_process_of_the_tree_and_never_the_caller():
    killed = []
    assert eo.kill_run_tree(rows(), CODEX, 19, kill=killed.append) == [10, 11, 12, 13, 14]
    assert killed == [10, 11, 12, 13, 14]
    killed.clear()
    assert eo.kill_run_tree(rows(), CODEX, 19, kill=killed.append, keep={12}) == [10, 11, 13, 14]


def test_kill_engine_finds_comfyui_main_py_by_command_line():
    killed = []
    assert eo.kill_engine(rows(), kill=killed.append) == [30] and killed == [30]
    assert eo.kill_engine([ProcInfo(5, 0.0, r'python.exe -s ComfyUI\main.py')], kill=killed.append) == [5]
    assert eo.kill_engine([ProcInfo(6, 0.0, 'python.exe main.py')], kill=killed.append) == []


def test_the_engine_command_is_the_memory_recipe_under_the_portable_root():
    cmd, cwd = eo.engine_command(Path("E:/portable"))
    assert cwd == Path("E:/portable")
    assert cmd[0].replace("\\", "/") == "E:/portable/python_embeded/python.exe"
    assert cmd[1:] == ["-s", "ComfyUI/main.py", "--windows-standalone-build", "--reserve-vram", "2"]


def test_the_portable_root_is_one_env_var_with_one_default():
    assert eo.portable_root({"COMFY_PORTABLE": "E:/elsewhere"}) == Path("E:/elsewhere")
    assert eo.portable_root({}) == Path(eo.DEFAULT_PORTABLE)
    assert eo.portable_root({}).name == "ComfyUI_windows_portable"


def test_restart_launches_from_the_portable_folder_then_waits_for_the_engine():
    launched = []
    waited = []

    def wait():
        waited.append(True)
        return True
    assert eo.restart(launch=lambda cmd, cwd: launched.append((cmd, cwd)), wait=wait, root=Path("E:/p"))
    assert len(launched) == 1 and launched[0][1] == Path("E:/p") and launched[0][0][1:3] == ["-s", "ComfyUI/main.py"]
    assert waited == [True]
    assert not eo.restart(launch=lambda cmd, cwd: None, wait=lambda: False, root=Path("E:/p"))


def test_wait_alive_polls_until_system_stats_answers_or_time_runs_out():
    clock = iter([0.0, 5.0, 10.0, 15.0, 700.0, 700.0])
    answers = iter([False, False, True])
    slept = []
    ok = eo.wait_alive("http://e:1", seconds=600, poll=5, now=lambda: next(clock), sleep=slept.append,
                       probe=lambda url: next(answers))
    assert ok and slept == [5, 5]
    assert not eo.wait_alive("http://e:1", seconds=1, poll=5, now=iter([0.0, 2.0, 2.0]).__next__,
                             sleep=lambda s: None, probe=lambda url: False)


def test_the_module_stores_no_absolute_path_but_its_one_default():
    """Every other path is built from the one constant at call time."""
    source = Path(eo.__file__).read_text(encoding="utf-8")
    assert source.count("D:/") == 1 and "C:/" not in source and "C:\\" not in source
