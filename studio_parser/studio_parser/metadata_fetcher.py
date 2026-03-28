from __future__ import annotations

import re
import urllib.request
from xml.etree import ElementTree as ET

from studio_parser.downloader import extract_numeric_id
from studio_parser.models import BookMetadata

RDF_NS = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "dcterms": "http://purl.org/dc/terms/",
    "pgterms": "http://www.gutenberg.org/2009/pgterms/",
    "dcam": "http://purl.org/dc/dcam/",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
}


def clean_author_name(raw_name: str) -> str:
    """Clean PG author name to plain readable form.

    'James, M. R. (Montague Rhodes)' → 'M. R. James'
    'Chopin, Kate, 1850-1904' → 'Kate Chopin'
    'Hawthorne, Nathaniel, 1804-1864' → 'Nathaniel Hawthorne'
    """
    name = raw_name.strip()

    # Strip parentheticals: (Montague Rhodes)
    name = re.sub(r"\s*\([^)]*\)", "", name)

    # Strip trailing year ranges: , 1804-1864 or , 1850-
    name = re.sub(r",\s*\d{4}\s*-\s*\d{0,4}\s*$", "", name)

    # Flip "Last, First" → "First Last"
    if "," in name:
        parts = name.split(",", 1)
        last = parts[0].strip()
        first = parts[1].strip()
        if first and last:
            name = f"{first} {last}"

    return name.strip()


def _extract_year_from_text(text: str) -> str | None:
    """Try to find original publication year from description text."""
    # Look for patterns like "published in 1904" or "written in 1904"
    match = re.search(r"(?:published|written|first published|originally published)\s+(?:in\s+)?(\d{4})", text, re.IGNORECASE)
    if match:
        return match.group(1)
    # Look for "collection of ... stories published in YYYY"
    match = re.search(r"stories\s+published\s+in\s+(\d{4})", text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def fetch_pg_metadata(book_id: str) -> BookMetadata | None:
    """Fetch and parse Project Gutenberg RDF metadata for a book.

    Returns BookMetadata or None if fetch fails.
    """
    numeric_id = extract_numeric_id(book_id)
    url = f"https://www.gutenberg.org/cache/epub/{numeric_id}/pg{numeric_id}.rdf"

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (Visurena Studio Parser)"}
        )
        data = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    except Exception as e:
        print(f"  WARNING: Failed to fetch PG metadata: {e}")
        return None

    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        print(f"  WARNING: Failed to parse PG RDF: {e}")
        return None

    # Title
    title_el = root.find(".//dcterms:title", RDF_NS)
    title = title_el.text.strip() if title_el is not None and title_el.text else ""

    # Author
    raw_author = ""
    author_birth = ""
    author_death = ""
    author_wikipedia = ""
    agent = root.find(".//pgterms:agent", RDF_NS)
    if agent is not None:
        name_el = agent.find("pgterms:name", RDF_NS)
        raw_author = name_el.text.strip() if name_el is not None and name_el.text else ""
        birth_el = agent.find("pgterms:birthdate", RDF_NS)
        author_birth = birth_el.text.strip() if birth_el is not None and birth_el.text else ""
        death_el = agent.find("pgterms:deathdate", RDF_NS)
        author_death = death_el.text.strip() if death_el is not None and death_el.text else ""
        wiki_el = agent.find("pgterms:webpage", RDF_NS)
        if wiki_el is not None:
            author_wikipedia = wiki_el.get(f"{{{RDF_NS['rdf']}}}resource", "")

    author = clean_author_name(raw_author)

    # Subjects (LCSH)
    subjects = []
    for subj in root.findall(".//dcterms:subject", RDF_NS):
        value = subj.find(".//rdf:value", RDF_NS)
        if value is not None and value.text:
            subjects.append(value.text.strip())

    # Bookshelves
    bookshelves = []
    for shelf in root.findall(".//pgterms:bookshelf", RDF_NS):
        value = shelf.find(".//rdf:value", RDF_NS)
        if value is not None and value.text:
            bookshelves.append(value.text.strip())

    # Genre: combine subjects + bookshelves, deduplicated
    genre_parts = []
    seen = set()
    for item in subjects + bookshelves:
        # Skip LC classification codes like "PR"
        if len(item) <= 3 and item.isupper():
            continue
        if item.lower() not in seen:
            seen.add(item.lower())
            genre_parts.append(item)
    genre = ", ".join(genre_parts)

    # Issued date
    issued_el = root.find(".//dcterms:issued", RDF_NS)
    issued_date = issued_el.text.strip() if issued_el is not None and issued_el.text else ""

    # Description / summary
    desc_el = root.find(".//dcterms:description", RDF_NS)
    description_raw = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
    marc520_el = root.find(".//pgterms:marc520", RDF_NS)
    summary = marc520_el.text.strip() if marc520_el is not None and marc520_el.text else ""

    # Wikipedia link from description
    wikipedia_link = ""
    if "wikipedia.org" in description_raw:
        match = re.search(r"(https?://\S*wikipedia\S+)", description_raw)
        if match:
            wikipedia_link = match.group(1)

    # Try to extract original publication year
    publish_year = ""
    if summary:
        year = _extract_year_from_text(summary)
        if year:
            publish_year = year
    if not publish_year and issued_date:
        publish_year = issued_date[:4]

    # Language
    lang_el = root.find(".//dcterms:language//rdf:value", RDF_NS)
    language = lang_el.text.strip() if lang_el is not None and lang_el.text else ""

    # Reading ease
    marc908_el = root.find(".//pgterms:marc908", RDF_NS)
    reading_ease = marc908_el.text.strip() if marc908_el is not None and marc908_el.text else ""

    # Download count
    downloads_el = root.find(".//pgterms:downloads", RDF_NS)
    download_count = int(downloads_el.text.strip()) if downloads_el is not None and downloads_el.text else 0

    # Table of contents
    toc_el = root.find(".//dcterms:tableOfContents", RDF_NS)
    table_of_contents = toc_el.text.strip() if toc_el is not None and toc_el.text else ""

    return BookMetadata(
        title=title,
        author=author,
        author_raw=raw_author,
        author_birth_year=author_birth,
        author_death_year=author_death,
        author_wikipedia=author_wikipedia,
        genre=genre,
        subjects=subjects,
        bookshelves=bookshelves,
        publish_year=publish_year,
        pg_issued_date=issued_date,
        language=language,
        description=summary or description_raw,
        wikipedia_link=wikipedia_link,
        reading_ease=reading_ease,
        download_count=download_count,
        table_of_contents=table_of_contents,
    )
