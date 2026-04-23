#!/usr/bin/env python3
"""Convert papers.bib to data/publications.json for Hugo."""

import json
import re
import sys
from pathlib import Path

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

VENUE_TYPE_MAP = {
    "article": "journal",
    "inproceedings": "conference",
    "proceedings": "conference",
    "incollection": "book-chapter",
    "book": "book",
    "phdthesis": "thesis",
    "mastersthesis": "thesis",
    "techreport": "report",
    "misc": "other",
}

WORKSHOP_KEYWORDS = {"workshop", "ws", "@ chi", "@ cscw", "@ ecir"}


def classify(entry):
    etype = entry.get("ENTRYTYPE", "misc").lower()
    base = VENUE_TYPE_MAP.get(etype, "other")
    if base == "conference":
        venue = (entry.get("booktitle", "") + entry.get("title", "")).lower()
        if any(k in venue for k in WORKSHOP_KEYWORDS):
            return "workshop"
    return base


def clean(text):
    text = re.sub(r"[{}]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_authors(author_str):
    parts = [a.strip() for a in author_str.split(" and ")]
    result = []
    for p in parts:
        if "," in p:
            last, first = p.split(",", 1)
            result.append(f"{first.strip()} {last.strip()}")
        else:
            result.append(p)
    return result


def main():
    bib_path = Path(__file__).parent.parent / "_bibliography" / "papers.bib"
    out_path = Path(__file__).parent.parent / "data" / "publications.json"
    out_path.parent.mkdir(exist_ok=True)

    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode

    with open(bib_path) as f:
        db = bibtexparser.load(f, parser=parser)

    pubs = []
    for entry in db.entries:
        year = int(entry.get("year", 0) or 0)
        pub = {
            "key": entry.get("ID", ""),
            "type": classify(entry),
            "title": clean(entry.get("title", "")),
            "authors": parse_authors(clean(entry.get("author", ""))),
            "year": year,
            "venue": clean(entry.get("journal") or entry.get("booktitle") or entry.get("school") or ""),
            "pages": clean(entry.get("pages", "")),
            "abbr": clean(entry.get("abbr", "")),
            "url": entry.get("url", ""),
            "doi": entry.get("doi", ""),
            "pdf": entry.get("pdf", ""),
        }
        pubs.append(pub)

    pubs.sort(key=lambda p: (-p["year"], p["title"]))

    with open(out_path, "w") as f:
        json.dump(pubs, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(pubs)} publications to {out_path}")


if __name__ == "__main__":
    main()
