"""The Viewer's escaping rule, checked without a browser: prompts carry
`<Subject 1>`, `<Picture 1>`, `<image1>`, which innerHTML would eat, so every
value reaches the page through textContent.  The only HTML sinks the scripts
may hold are the static dialog template and the static icon strings; prov.js
and docview.js hold none.  The 20 rendering self-tests stay runnable in a
browser at /static/viewer/docview_test.html."""
from __future__ import annotations

import re
from pathlib import Path

VIEWER = Path(__file__).resolve().parents[1] / "studio" / "command_center" / "static" / "viewer"
SINK = re.compile(r"\b(innerHTML|outerHTML)\s*[+]?=\s*([^;]+);|insertAdjacentHTML|document\.write")
STATIC_RHS = re.compile(r"^(TEMPLATE|icoHTML\([^()]*(\([^()]*\))?[^()]*\))$")


def code(name: str) -> str:
    """The script without its comments (a comment may name innerHTML to forbid it)."""
    text = (VIEWER / name).read_text(encoding="utf-8")
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def sinks(name: str) -> list[str]:
    return [m.group(0) for m in SINK.finditer(code(name))]


def test_the_four_viewer_files_are_on_the_board():
    assert {p.name for p in VIEWER.iterdir()} >= {"viewer.js", "docview.js", "prov.js", "viewer.css", "docview_test.html"}


def test_prov_and_docview_write_no_html():
    assert sinks("prov.js") == [] and sinks("docview.js") == []


def test_viewer_writes_html_only_from_static_strings():
    rhs = [m.group(2).strip() for m in SINK.finditer(code("viewer.js"))]
    assert rhs and all(STATIC_RHS.match(r) for r in rhs), rhs


def test_the_dialog_template_interpolates_only_icons():
    template = re.search(r"const TEMPLATE = `(.*?)`;", code("viewer.js"), flags=re.S).group(1)
    assert all(re.fullmatch(r"icoHTML\('[a-z]+'\)", x) for x in re.findall(r"\$\{(.*?)\}", template))


def test_icons_are_a_static_map():
    icons = re.search(r"const IC = \{(.*?)\n\};", code("viewer.js"), flags=re.S).group(1)
    assert "${" not in icons and "+" not in icons.replace("'", "").split(":")[0]


def test_the_element_helpers_set_text_not_markup():
    for name in ("viewer.js", "prov.js"):
        assert re.search(r"function el\(tag, cls, text\) \{[^}]*n\.textContent = String\(text\)", code(name))


def test_the_self_test_page_loads_the_board_copies_and_runs_twenty_checks():
    page = (VIEWER / "docview_test.html").read_text(encoding="utf-8")
    assert 'src="docview.js"' in page and 'href="viewer.css"' in page
    loop_checks = page.count("check(`") * len(re.search(r"\[('read'.*?)\]\.forEach", page).group(1).split(","))
    assert loop_checks + page.count("check('") == 20


def test_the_board_port_reads_the_board_not_the_mockup():
    for name in ("viewer.js", "prov.js"):
        text = code(name)
        assert "8700" not in text and "data/${" not in text and "20260827135508" not in text
