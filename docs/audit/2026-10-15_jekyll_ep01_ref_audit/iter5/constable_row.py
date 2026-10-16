"""Try 3 of the constable's sheet is kept (HEL look, eyes with irises, a rounded helmet, a long coat);
the SHEET IS TRUTH (owner 2026-10-15), so his row says what it draws."""
import json
from pathlib import Path
BOOK = Path(__file__).resolve().parents[4] / "library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"
looks = BOOK / "refs/looks.json"
d = json.loads(looks.read_text(encoding="utf-8"))
c = d["characters"]["carew_policeman"]
c["body"] = "A tall, spare London police constable of about thirty-five with bushy eyebrows and a lined face."
c["looks"]["base_uniform"]["layers"].update({
    "headwear": "rounded dark-blue police helmet with a gold star badge",
    "hair": "close-cropped black hair",
    "face": "thick white moustache; lined face, bushy eyebrows",
    "top": "long dark-blue police greatcoat with a black leather belt, light-blue shirt, black boots"})
looks.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
heads = BOOK / "analysis/heads.json"
h = json.loads(heads.read_text(encoding="utf-8"))
h["carew_policeman"]["words"] = ("A tall, spare London police constable of about thirty-five with bushy eyebrows and a lined "
                                 "face, in a long dark-blue police greatcoat with a black leather belt. Close-cropped black "
                                 "hair; a thick white moustache; a rounded dark-blue police helmet with a gold star badge.")
heads.write_text(json.dumps(h, indent=1, ensure_ascii=False), encoding="utf-8")
look = BOOK / "refs/look.json"
L = json.loads(look.read_text(encoding="utf-8"))
e = L["refs"]["entities"]["carew_policeman"]
e["tags"] = e["tags"].replace("sandy-red hair", "close-cropped black hair").replace("(thick moustache:1.3)", "(thick white moustache:1.3)")
look.write_text(json.dumps(L, indent=1, ensure_ascii=False), encoding="utf-8")
print("constable row = his sheet")
