"""Owner 2026-10-15: fix the constable's sheet so later episodes are safe (SHEET-ROW refused it:
hollow eyes on both reads, a peaked cap where the row and tags say a custodian helmet).
Strengthen the drawer's helmet and eye tags; the old sheet goes to superseded/ and build_pack redraws."""
import json
from pathlib import Path
p = Path(__file__).resolve().parents[4] / "library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/refs/look.json"
d = json.loads(p.read_text(encoding="utf-8"))
e = d["refs"]["entities"]["carew_policeman"]
e["tags"] = e["tags"].replace("(tall dark-blue bell-shaped police helmet:1.4)",
                              "(custodian helmet:1.5), (british police helmet:1.4), (tall dark-blue bell-shaped police helmet:1.4)")
if "(pupils:1.2)" not in e["tags"]:
    e["tags"] += ", (detailed eyes:1.2), (pupils:1.2), grey eyes"
if "(hollow eyes:1.5)" not in e["negative"]:
    e["negative"] += ", (hollow eyes:1.5), (empty eyes:1.5), (no pupils:1.4), (solid black eyes:1.4), red collar, star on cap"
p.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
print(e["tags"])

# try 3 (try 2 drew a blue short-sleeved modern shirt and a hard hat): the original helmet tag back,
# the eye fix kept, the Victorian tunic said harder
d = json.loads(p.read_text(encoding="utf-8"))
e = d["refs"]["entities"]["carew_policeman"]
e["tags"] = e["tags"].replace("(custodian helmet:1.5), (british police helmet:1.4), ", "")
e["tags"] = e["tags"].replace("(long dark-blue tunic buttoned to the throat:1.3)",
                              "(long dark-blue victorian police tunic buttoned to the throat:1.4), long sleeves")
if "short sleeves" not in e["negative"].split(", ")[-1]:
    e["negative"] += ", (short sleeves:1.4), shirt pocket, bell, chibi, cartoon, hard hat"
p.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
print(e["tags"])
