from __future__ import annotations

import urllib.request
from pathlib import Path

from studio_parser.config import ParserConfig

PG_BASE = "https://www.gutenberg.org/cache/epub"


def get_format_urls(numeric_id: str) -> dict[str, str]:
    """Return dict of {format_label: download_url} for a PG book."""
    return {
        "html": f"{PG_BASE}/{numeric_id}/pg{numeric_id}-images.html",
        "epub2": f"{PG_BASE}/{numeric_id}/pg{numeric_id}.epub",
        "epub2_images": f"{PG_BASE}/{numeric_id}/pg{numeric_id}-images.epub",
        "epub3_images": f"{PG_BASE}/{numeric_id}/pg{numeric_id}-images-3.epub",
    }


def get_format_filenames(numeric_id: str) -> dict[str, str]:
    """Return dict of {format_label: filename} for a PG book."""
    return {
        "html": f"pg{numeric_id}-images.html",
        "epub2": f"pg{numeric_id}.epub",
        "epub2_images": f"pg{numeric_id}-images.epub",
        "epub3_images": f"pg{numeric_id}-images-3.epub",
    }


def extract_numeric_id(book_id: str) -> str:
    """Extract numeric part from book_id like 'pg160' -> '160'."""
    return book_id.replace("pg", "").strip()


def download_book(book_id: str, config: ParserConfig) -> dict[str, Path]:
    """Download all 4 format variants from Project Gutenberg.

    Returns dict of {format_label: Path} for files that exist after download.
    Files are stored in {download_dir}/{book_id}/.
    """
    numeric_id = extract_numeric_id(book_id)
    urls = get_format_urls(numeric_id)
    filenames = get_format_filenames(numeric_id)

    download_dir = config.paths.download_dir / book_id
    download_dir.mkdir(parents=True, exist_ok=True)

    downloaded: dict[str, Path] = {}

    for label, url in urls.items():
        dest = download_dir / filenames[label]
        if dest.exists():
            print(f"  EXISTS: {filenames[label]} ({dest.stat().st_size:,} bytes)")
            downloaded[label] = dest
            continue

        print(f"  Downloading {filenames[label]} ...", end=" ", flush=True)
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 (Visurena Studio Parser)"}
            )
            resp = urllib.request.urlopen(req)
            data = resp.read()
            with open(dest, "wb") as f:
                f.write(data)
            print(f"OK ({len(data):,} bytes)")
            downloaded[label] = dest
        except Exception as e:
            print(f"FAILED ({e})")

    return downloaded
