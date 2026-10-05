"""Reading a board page as answers, not markup (plan F1): which route a region
polls and how often, the shell's sidebar and the text of a `data-testid`."""
from __future__ import annotations

import re


def polls(page: str, route: str) -> str | None:
    """The hx-trigger of the element that polls `route` (its hx-get), or None
    when nothing on the page polls it."""
    for tag in re.findall(r"<[a-z]+\b[^>]*>", page):
        if f'hx-get="{route}"' in tag:
            found = re.search(r'hx-trigger="([^"]*)"', tag)
            return found.group(1) if found else ""
    return None


def main(page: str) -> str:
    """The page's own content: its <main>, without the shell around it."""
    start = page.index("<main")
    return page[start:page.index("</main>", start)]


def sidebar(page: str) -> str:
    """The desktop sidebar's markup (the phone sheet repeats it; this is the first)."""
    start = page.index('data-testid="sidebar"')
    return page[start:page.index("</aside>", start)]


def text_of(page: str, testid: str) -> str:
    """The text inside the first element carrying `data-testid=testid` (tags stripped,
    up to that element's own closing tag)."""
    m = re.search(rf'<([a-z]+)\b[^>]*data-testid="{re.escape(testid)}"[^>]*>(.*?)</\1>', page, re.S)
    return re.sub(r"<[^>]+>", "", m.group(2)).strip() if m else ""
