"""What a spent clock ships flagged (C3_verdict #5 (v), D3): the report marked
passed-and-flagged and the one audit row the owner reads after the fact.  A
studio module, so no step names the audit rows (they are never a gate)."""
from __future__ import annotations

from pathlib import Path

from studio import audit_rows, episode_home


def flag_qc(book_dir: Path, unit: str, path: Path, report: dict, failed: list[str]) -> dict:
    """The QC report shipped flagged on `failed` rows: written back, one audit row."""
    report = {**report, "passed": True, "ceiling_flagged": failed}
    episode_home.write_json(path, report)
    audit_rows.append(book_dir, {"unit": unit, "gate": "QC", "judge": "qc", "sha8": report.get("sha8", ""),
                                 "artefact": Path(path).name, "faults": [{"kind": name} for name in failed],
                                 "terminal": "ceiling"})
    return report
