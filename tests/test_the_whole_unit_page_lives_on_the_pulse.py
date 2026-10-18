"""Every band of the unit page follows the unit's pulse (page experts 2026-10-18, D3): only
#head, #orders and #tails polled; Gates, Runs and the properties panel ('Moved 23m ago', the
lease, the state) froze at load.  Each now re-reads its own band from the page on the unit's
pulse key and morphs in place, as the inbox and the department pages do."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

UNIT = (Path(__file__).resolve().parents[1] / "studio" / "command_center" / "templates" / "unit.html").read_text(encoding="utf-8")


@pytest.mark.parametrize("band", ["gates", "runs", "props"])
def test_a_band_morphs_on_the_units_pulse(band):
    tag = re.search(rf'<(?:section|aside)[^\n]*id="{band}"[^\n]*', UNIT).group(0)
    # ruling 5.3: never outerHTML on the unit page -- the band's children morph into it
    assert 'hx-trigger="{{ pk }} from:body"' in tag and f'hx-select="#{band} > *"' in tag
    assert 'hx-swap="morph:innerHTML"' in tag and 'data-v="{{ vfp }}"' in tag and "hx-get=" in tag
