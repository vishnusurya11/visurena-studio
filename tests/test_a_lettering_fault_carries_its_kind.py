"""ep14 step 08 (2026-09-28): the first panel that showed lettering crashed the
judge -- ocr.lettering rows carry a 'kind' key and `fault(kind, ...)` took it
twice ("got multiple values for argument 'kind'").  The run died, not the panel."""
from pathlib import Path

from studio.judges import panel_eye


def test_a_lettering_row_becomes_a_lettering_fault(monkeypatch):
    rows = [{"text": "WOKING", "kind": "sign", "conf": 0.91}]
    monkeypatch.setattr(panel_eye.ocr, "read", lambda path, reader: [])
    monkeypatch.setattr(panel_eye.ocr, "lettering", lambda *a, **k: rows)
    got = panel_eye.lettering_faults(Path("p.png"), None, [], "", False, 1024, "shot 05")
    assert [f.kind for f in got] == ["lettering"]
    assert got[0].evidence["found"] == "sign" and got[0].evidence["text"] == "WOKING"
