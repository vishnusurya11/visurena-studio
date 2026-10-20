"""A cache's judging code is the import closure of its judges, never a typed list.

Skeptic on package H (retro 2026-10-20): take_content's JUDGES named three files, while its
verdict also came from studio/look_table.py (hair families), studio/panel_dq.py (back_view,
at_night) and studio/people_count.py, all reached by imports inside functions.  A change to the
hair-family table moved neither the key nor the pin test.  code_closure follows every studio
import, lazy ones too, so a judge that gains a helper module brings it into the hash.
"""
from __future__ import annotations

from pathlib import Path

from studio import code_closure


def tree(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, body in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8", newline="\n")
    return tmp_path


def test_every_studio_import_form_is_followed(tmp_path):
    root = tree(tmp_path, {
        "studio/judge.py": "from studio import table as t\nfrom studio.night import at\nimport studio.count\n",
        "studio/table.py": "import re\n", "studio/night.py": "", "studio/count.py": ""})
    assert code_closure.imports(root, "studio/judge.py") == {"studio/table.py", "studio/night.py", "studio/count.py"}


def test_a_lazy_import_inside_a_function_is_followed(tmp_path):
    root = tree(tmp_path, {"studio/judge.py": "def f():\n    from studio import hair\n    return hair\n",
                           "studio/hair.py": ""})
    assert code_closure.imports(root, "studio/judge.py") == {"studio/hair.py"}


def test_the_closure_is_transitive_sorted_and_names_a_package_by_its_init(tmp_path):
    root = tree(tmp_path, {"studio/a.py": "from studio import b\n", "studio/b.py": "from studio import judges\n",
                           "studio/judges/__init__.py": "from studio import a\n"})
    assert code_closure.closure(root, ("studio/a.py",)) == ("studio/a.py", "studio/b.py", "studio/judges/__init__.py")


def test_a_name_that_is_no_module_is_left_out(tmp_path):
    root = tree(tmp_path, {"studio/a.py": "from studio.b import Seen\nfrom pathlib import Path\n",
                           "studio/b.py": ""})
    assert code_closure.closure(root, ("studio/a.py",)) == ("studio/a.py", "studio/b.py")
