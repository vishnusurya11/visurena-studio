"""The board's stylesheets as the tests read them (plan F2/F4): the three files
under studio/command_center/static/css, the two themes' tokens with every
`var(--x)` resolved, and the WCAG contrast of two colours.  Studio black is
`:root{...}` in the tokens layer; Graphite is that block overlaid with
`:root[data-theme="light"]{...}`."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "studio" / "command_center" / "static" / "css"
TEMPLATES = ROOT / "studio" / "command_center" / "templates"
STATIC = ROOT / "studio" / "command_center" / "static"


def css(name: str) -> str:
    """One of tokens / components / pages, as text."""
    return (CSS / f"{name}.css").read_text(encoding="utf-8")


def block(text: str, head: str) -> str:
    """The body of the first block that opens with `head` (brace-matched)."""
    i = text.index(head) + len(head) - 1
    depth = 0
    for j in range(i, len(text)):
        depth += {"{": 1, "}": -1}.get(text[j], 0)
        if depth == 0:
            return text[i + 1:j]
    raise ValueError(f"unclosed block {head!r}")


def declarations(body: str) -> dict[str, str]:
    """{name: value} for every `--name:value` in a block body."""
    return {m.group(1): m.group(2).strip() for m in re.finditer(r"--([\w-]+)\s*:\s*([^;}]+)", body)}


def resolve(tokens: dict[str, str]) -> dict[str, str]:
    """Each token with its `var(--x)` chain followed to a literal."""
    out = {}
    for name, value in tokens.items():
        seen = set()
        while (m := re.fullmatch(r"var\(--([\w-]+)\)", value)) and m.group(1) not in seen:
            seen.add(m.group(1))
            value = tokens.get(m.group(1), value)
        out[name] = value
    return out


def themes() -> dict[str, dict[str, str]]:
    """{"dark": Studio black, "light": Graphite}, resolved."""
    layer = block(css("tokens"), "@layer tokens {")
    dark = declarations(block(layer, ":root{"))
    light = {**dark, **declarations(block(layer, ':root[data-theme="light"]{'))}
    return {"dark": resolve(dark), "light": resolve(light)}


def _lum(hex_: str) -> float:
    def ch(c):
        c = int(c, 16) / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(hex_[i:i + 2]) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """WCAG 2 contrast ratio of two #rrggbb colours."""
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)
