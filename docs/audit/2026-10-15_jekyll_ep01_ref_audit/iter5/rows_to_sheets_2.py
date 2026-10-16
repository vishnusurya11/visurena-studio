import json, pathlib
p = pathlib.Path("library/20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde/refs/looks.json")
d = json.loads(p.read_text(encoding="utf-8"))
d["characters"]["edward_hyde"]["looks"]["base"]["layers"]["face"] = "clean-shaven, pale smooth cheeks; thin lips curled in a wide, cold grin"
d["characters"]["gabriel_john_utterson"]["body"] = "A lean, long, bony, dry man of about forty, narrow-chested."
p.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
d = json.loads(p.read_text(encoding="utf-8"))
d["characters"]["edward_hyde"]["body"] = ("A small, slight, sinister young man of about twenty-five, adult in build but a head "
                                          "shorter than other men, narrow-shouldered and pale, with lean, corded, knuckly pale hands.")
p.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
