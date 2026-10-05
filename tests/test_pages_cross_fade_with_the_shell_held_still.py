"""Cross-document View Transitions (panel ruling 2.11): the root cross-fades at --d2 while the
sidebar, the header and the GPU card are named and held still; the heartbeat chip comes back on a
phone when the board is offline or restarted (2.2).  CSS text checks, $0."""
from pathlib import Path

CSS = (Path(__file__).parent.parent / "studio" / "command_center" / "static" / "css" / "components.css").read_text(encoding="utf-8")


def test_navigation_opts_into_view_transitions():
    assert "@view-transition{navigation:auto}" in CSS.replace(" ", "")


def test_the_shell_parts_are_named_once_each():
    for name in ("vt-side", "vt-head", "vt-gpu"):
        assert CSS.count(f"view-transition-name:{name}") == 1


def test_the_root_fades_at_the_d2_token_and_the_shell_does_not_move():
    flat = CSS.replace(" ", "")
    assert "::view-transition-group(root){animation-duration:var(--d2)}" in flat
    assert "::view-transition-group(vt-side),::view-transition-group(vt-head),::view-transition-group(vt-gpu){animation:none}" in flat


def test_a_phone_shows_the_heartbeat_when_the_board_is_down():
    flat = CSS.replace(" ", "")
    assert '.ph.livechip[data-hb="offline"],.ph.livechip[data-hb="restarted"]{display:inline-flex}' in flat
