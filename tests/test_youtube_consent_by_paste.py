"""Consent from any device: the owner approves on a phone, the localhost
redirect fails there, and the address it shows carries the one-time code.

2026-09-28: ep13's upload waited on a browser consent the owner could not
reach ("I'm at work I can't access it"); run_local_server only works on the
studio PC.  `--paste` prints the link and takes the failed redirect address.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("youtube_auth_paste", ROOT / "scripts/publish/youtube_auth.py")
auth = importlib.util.module_from_spec(_spec)
sys.modules["youtube_auth_paste"] = auth
_spec.loader.exec_module(auth)


def test_the_code_is_read_from_the_failed_redirect_address():
    url = "http://localhost:8765/?state=abc&code=4/0AbCd-EfG_h&scope=https://www.googleapis.com/auth/youtube.upload"
    assert auth.code_from(url) == "4/0AbCd-EfG_h"


def test_an_address_without_a_code_is_refused():
    import pytest
    with pytest.raises(SystemExit):
        auth.code_from("http://localhost:8765/?error=access_denied")
