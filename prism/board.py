"""The Prism board: one dark HTML page, per style a 5 x 3 grid (subjects down, models across).

    uv run python -m prism.board        # writes docs/audit/prism/board.html from what is rendered
"""
from __future__ import annotations

import base64
import io
import json
import statistics
import sys
from html import escape
from pathlib import Path

from prism.catalog import ModelGuide, Style, SubjectSet

CSS = """:root{--bg:#0f1012;--panel:#17181b;--line:#2a2c31;--ink:#e6e6e6;--dim:#9a9ca3;--hot:#7fb4ff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,sans-serif}
header{position:sticky;top:0;z-index:2;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 16px;
display:flex;gap:12px;flex-wrap:wrap;align-items:center}h1{font-size:18px;margin:0 12px 0 0}
input,select,button{background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:6px;padding:6px 10px}
section{border-bottom:1px solid var(--line);padding:20px 16px;max-width:1400px;margin:0 auto}
h2{margin:0 0 4px;font-size:17px}.meta{color:var(--dim);margin:0 0 10px}
.grid{display:grid;grid-template-columns:110px repeat(var(--n),minmax(0,1fr));gap:8px;align-items:start}
.head{color:var(--dim);font-size:12px}.head label{display:block;color:var(--ink);cursor:pointer}
figure{margin:0}figure img,.missing{width:100%;aspect-ratio:1;border-radius:6px;background:var(--panel);display:block;object-fit:cover}
.missing{display:grid;place-items:center;color:var(--dim);font-size:12px}figcaption{color:var(--dim);font-size:12px}
details{color:var(--dim);font-size:12px;margin-top:2px}details p{margin:4px 0;color:var(--ink)}
.subj{font-size:12px;color:var(--dim)}.subj b{color:var(--ink);display:block}
@media(max-width:700px){.grid{grid-template-columns:repeat(var(--n),minmax(0,1fr))}.subj{grid-column:1/-1}}"""

SCRIPT = """const KEY='prism-picks';let picks={};try{picks=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
document.querySelectorAll('input[type=radio]').forEach(r=>{const s=r.name.slice(5);if(picks[s]===r.value)r.checked=true;
r.addEventListener('change',()=>{picks[s]=r.value;try{localStorage.setItem(KEY,JSON.stringify(picks))}catch(e){}})});
function show(){const q=document.getElementById('q').value.toLowerCase(),f=document.getElementById('f').value;
document.querySelectorAll('section').forEach(s=>{s.hidden=!((!f||s.dataset.family===f)&&s.textContent.toLowerCase().includes(q))})}
document.getElementById('q').addEventListener('input',show);document.getElementById('f').addEventListener('change',show);
document.getElementById('copy').addEventListener('click',()=>navigator.clipboard.writeText(JSON.stringify(picks,null,1)));"""


def took(row: dict) -> float:
    """The engine's own time when backfilled (prism.timing); the client's poll-quantised clock else."""
    return row.get("exec_seconds", row["seconds"])


def warm_median(rows: list[dict], style_id: str, model_id: str) -> float | None:
    seconds = [took(r) for r in rows if r["style"] == style_id and r["model"] == model_id and not r["cold"]]
    return round(statistics.median(seconds), 1) if seconds else None


def timing(rows: list[dict]) -> dict[tuple, float]:
    return {(r["style"], r["subject"], r["model"]): took(r) for r in rows}


def same(out: str) -> str:
    return out


def thumbnail(path: Path, size: int = 256) -> str:
    """A small JPEG data URI: the portable board travels as one file (a phone, a share)."""
    from PIL import Image
    image = Image.open(path).convert("RGB")
    image.thumbnail((size, size))
    held = io.BytesIO()
    image.save(held, "JPEG", quality=72)
    return "data:image/jpeg;base64," + base64.b64encode(held.getvalue()).decode("ascii")


def cell(job, root: Path, seconds: float | None, src=same) -> str:
    shown = (f'<a href="{job.out}"><img loading="lazy" src="{src(job.out)}" alt=""></a>'
             if (Path(root) / job.out).exists() else '<div class="missing">not rendered</div>')
    took = f"{seconds} s" if seconds is not None else "-"
    return (f"<figure>{shown}<figcaption>{took}</figcaption>"
            f"<details><summary>prompt</summary><p>{escape(job.prompt)}</p></details></figure>")


def model_head(style: Style, guide: ModelGuide, rows: list[dict]) -> str:
    median = warm_median(rows, style.id, guide.id)
    picked = " checked" if style.verdict.best_model == guide.id else ""
    return (f'<div class="head"><label><input type="radio" name="pick-{style.id}" value="{guide.id}"{picked}> '
            f'{escape(guide.label)}</label>warm median {median if median is not None else "-"} s</div>')


def style_section(style: Style, subjects: SubjectSet, guides: dict[str, ModelGuide], by_key: dict,
                  rows: list[dict], root: Path, src=same) -> str:
    guides = {g: guide for g, guide in guides.items()
              if any((style.id, s.id, g) in by_key for s in subjects.subjects)}
    heads = "".join(model_head(style, g, rows) for g in guides.values())
    took = timing(rows)
    body = "".join(
        f'<div class="subj"><b>{escape(s.title)}</b>{escape(s.camera)}</div>'
        + "".join(cell(by_key[(style.id, s.id, g)], root, took.get((style.id, s.id, g)), src) for g in guides)
        for s in subjects.subjects)
    titles = ", ".join(style.lineage.titles[:3])
    return (f'<section id="{style.id}" data-family="{style.family}"><h2>{escape(style.name)}</h2>'
            f'<p class="meta">{escape(style.family)} · {escape(titles)} · {escape(style.verdict.status)}<br>'
            f'{escape(style.summary)}</p><details><summary>style words</summary><p>{escape(style.style_words)}</p>'
            f'</details><div class="grid" style="--n:{len(guides)}"><div></div>{heads}{body}</div></section>')


def page(styles: list[Style], subjects: SubjectSet, guides: dict[str, ModelGuide], planned: list,
         rows: list[dict], root: Path, src=same) -> str:
    by_key = {(j.style, j.subject, j.model): j for j in planned}
    rows = [r for r in rows if "seconds" in r]
    sections = "".join(style_section(s, subjects, guides, by_key, rows, root, src) for s in styles)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width,initial-scale=1"><title>Prism Style Board</title><style>{CSS}</style></head>'
            f'<body><header><h1>Prism · {len(styles)} styles · {escape(subjects.story)}</h1>'
            f'<input id="q" placeholder="filter"><select id="f"><option value="">all</option>'
            f'<option>anime</option><option>live_action</option></select><button id="copy">Copy picks</button>'
            f'</header>{sections}<script>{SCRIPT}</script></body></html>')


def read_rows(root: Path) -> list[dict]:
    log = Path(root) / "timings.jsonl"
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []


def main(argv: list[str]) -> int:
    from prism.catalog import load_guides, load_styles, load_subjects
    from prism.render import ROOT, SUBJECTS, library_plan
    styles, guides = load_styles(Path("prism/styles")), load_guides(Path("prism/models"))
    parts = (styles, load_subjects(SUBJECTS), guides, library_plan(), read_rows(ROOT), ROOT)
    (ROOT / "board.html").write_text(page(*parts), encoding="utf-8")
    print((ROOT / "board.html").resolve())
    if "--portable" in argv:
        (ROOT / "board_portable.html").write_text(page(*parts, src=lambda out: thumbnail(ROOT / out)), encoding="utf-8")
        print((ROOT / "board_portable.html").resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
