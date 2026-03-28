from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

NS_NCX = {"ncx": "http://www.daisy.org/z3986/2005/ncx/"}


def parse_ncx_toc(ncx_xml: str) -> list[tuple[str, str, int, int]]:
    """Parse toc.ncx -> list of (label, anchor_id, depth, children_count)."""
    root = ET.fromstring(ncx_xml)
    entries: list[tuple[str, str, int, int]] = []

    def walk(nav_point, depth):
        label_el = nav_point.find("ncx:navLabel/ncx:text", NS_NCX)
        content_el = nav_point.find("ncx:content", NS_NCX)
        label = label_el.text.strip() if label_el is not None and label_el.text else ""
        href = content_el.get("src", "") if content_el is not None else ""
        anchor = href.split("#")[1] if "#" in href else ""
        children = nav_point.findall("ncx:navPoint", NS_NCX)
        entries.append((label, anchor, depth, len(children)))
        for child in children:
            walk(child, depth + 1)

    nav_map = root.find("ncx:navMap", NS_NCX)
    if nav_map is not None:
        for np in nav_map.findall("ncx:navPoint", NS_NCX):
            walk(np, 1)
    return entries


def parse_nav_toc(nav_html: str) -> list[tuple[str, str, int, int]]:
    """Parse EPUB3 toc.xhtml -> list of (label, anchor_id, depth, children_count)."""
    soup = BeautifulSoup(nav_html, "html.parser")
    nav = soup.find("nav")
    if not nav:
        return []

    entries: list[tuple[str, str, int, int]] = []

    def walk_ol(ol, depth):
        for li in ol.find_all("li", recursive=False):
            a = li.find("a", recursive=False)
            if not a:
                continue
            label = a.get_text(strip=True)
            href = a.get("href", "")
            anchor = href.split("#")[1] if "#" in href else ""
            child_ol = li.find("ol", recursive=False)
            children_count = len(child_ol.find_all("li", recursive=False)) if child_ol else 0
            entries.append((label, anchor, depth, children_count))
            if child_ol:
                walk_ol(child_ol, depth + 1)

    top_ol = nav.find("ol", recursive=False)
    if top_ol:
        walk_ol(top_ol, 1)
    return entries


def read_epub(filepath: Path) -> tuple[str, str, list, BeautifulSoup, list[str]]:
    """Read EPUB and return (title, author, toc_entries, combined_soup, warnings)."""
    warnings: list[str] = []

    with zipfile.ZipFile(filepath) as z:
        # Find OPF
        container = z.read("META-INF/container.xml").decode("utf-8")
        container_root = ET.fromstring(container)
        rootfile = container_root.find(
            ".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile"
        )
        opf_path = rootfile.get("full-path", "OEBPS/content.opf")
        opf_dir = "/".join(opf_path.split("/")[:-1])

        # Parse OPF
        opf_xml = z.read(opf_path).decode("utf-8")
        opf_root = ET.fromstring(opf_xml)

        ns_dc = "http://purl.org/dc/elements/1.1/"
        ns_opf = "http://www.idpf.org/2007/opf"

        title_el = opf_root.find(f".//{{{ns_dc}}}title")
        book_title = title_el.text.strip() if title_el is not None and title_el.text else ""

        creator_el = opf_root.find(f".//{{{ns_dc}}}creator")
        author = creator_el.text.strip() if creator_el is not None and creator_el.text else ""

        # Manifest + Spine
        manifest = {}
        for item in opf_root.findall(f".//{{{ns_opf}}}item"):
            manifest[item.get("id")] = item.get("href")

        spine_ids = [
            ref.get("idref") for ref in opf_root.findall(f".//{{{ns_opf}}}itemref")
        ]

        # Parse TOC - try EPUB3 nav first
        toc_entries: list = []

        for item_id, href in manifest.items():
            if href.endswith("toc.xhtml"):
                nav_path = f"{opf_dir}/{href}" if opf_dir else href
                try:
                    toc_entries = parse_nav_toc(z.read(nav_path).decode("utf-8"))
                except Exception as e:
                    warnings.append(f"Failed to parse nav TOC: {e}")
                break

        # Fallback to NCX
        if not toc_entries:
            for item_id, href in manifest.items():
                if href.endswith(".ncx"):
                    ncx_path = f"{opf_dir}/{href}" if opf_dir else href
                    try:
                        toc_entries = parse_ncx_toc(z.read(ncx_path).decode("utf-8"))
                    except Exception as e:
                        warnings.append(f"Failed to parse NCX: {e}")
                    break

        # Concatenate all spine content docs into one soup
        combined_html = "<html><body>"
        for item_id in spine_ids:
            if item_id not in manifest:
                continue
            href = manifest[item_id]
            full_path = f"{opf_dir}/{href}" if opf_dir else href
            try:
                content = z.read(full_path).decode("utf-8")
                doc_soup = BeautifulSoup(content, "html.parser")
                body = doc_soup.find("body")
                if body:
                    combined_html += str(body.decode_contents())
            except (KeyError, UnicodeDecodeError):
                pass
        combined_html += "</body></html>"

        combined_soup = BeautifulSoup(combined_html, "html.parser")

    return book_title, author, toc_entries, combined_soup, warnings
