"""Candidates for Jekyll's series card art on the book's own drawer (book_look.t2i, kind title)."""
import shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from studio import book_look
from studio.comfy import run

BOOK = Path("library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde")
motif = (BOOK / "title" / "motif.txt").read_text(encoding="utf-8")
out = Path(__file__).parent
for seed in [int(s) for s in sys.argv[1:]]:
    wf, values = book_look.t2i(BOOK, motif, width=1024, height=1024, seed=seed,
                               prefix="series_title/cand", kind="title", entity="title")
    made = run(wf, values)[0]
    shutil.copyfile(made, out / f"cand_{seed}.png")
    print(seed, flush=True)
