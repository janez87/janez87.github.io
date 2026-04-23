#!/usr/bin/env python3
"""Look up DOIs via CrossRef for BibTeX entries that lack one, then patch papers.bib."""

import re
import time
import unicodedata

import bibtexparser
import requests
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

CROSSREF_URL = "https://api.crossref.org/works"
HEADERS = {"User-Agent": "academic-site-doi-lookup/1.0 (mailto:andrea.mauri@univ-lyon1.fr)"}
SCORE_THRESHOLD = 0.85  # title similarity required to accept a match


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def title_similarity(a: str, b: str) -> float:
    a_words = set(normalise(a).split())
    b_words = set(normalise(b).split())
    if not a_words or not b_words:
        return 0.0
    return len(a_words & b_words) / max(len(a_words), len(b_words))


def lookup_doi(title: str, first_author_family: str) -> str | None:
    params = {
        "query.title": title,
        "query.author": first_author_family,
        "rows": 3,
        "select": "DOI,title,score",
    }
    try:
        r = requests.get(CROSSREF_URL, params=params, headers=HEADERS, timeout=10)
        r.raise_for_status()
        items = r.json().get("message", {}).get("items", [])
        for item in items:
            cr_title = " ".join(item.get("title", []))
            sim = title_similarity(title, cr_title)
            if sim >= SCORE_THRESHOLD:
                return item.get("DOI")
    except Exception as e:
        print(f"    WARNING: CrossRef error: {e}")
    return None


def first_family_name(author_str: str) -> str:
    first = author_str.split(" and ")[0].strip()
    return first.split(",")[0].strip()


def main():
    bib_path = "/_bibliography/papers.bib"
    import os
    bib_path = os.path.join(os.path.dirname(__file__), "..", "_bibliography", "papers.bib")

    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode

    with open(bib_path) as f:
        raw = f.read()

    db = bibtexparser.loads(raw, parser=parser)

    found = 0
    not_found = []

    for entry in db.entries:
        if entry.get("doi"):
            continue  # already has one

        title = re.sub(r"[{}]", "", entry.get("title", "")).strip()
        author = entry.get("author", "")
        family = first_family_name(author)

        if not title:
            continue

        print(f"Looking up: {entry['ID']}")
        doi = lookup_doi(title, family)
        time.sleep(0.35)  # be polite to CrossRef

        if doi:
            print(f"  ✓ {doi}")
            # Patch the raw BibTeX: insert doi field after the key line
            pattern = rf"(@\w+\{{{re.escape(entry['ID'])},)"
            replacement = rf"\1\n  doi       = {{{doi}}},"
            raw = re.sub(pattern, replacement, raw, count=1)
            found += 1
        else:
            print(f"  ✗ not found")
            not_found.append(entry["ID"])

    with open(bib_path, "w") as f:
        f.write(raw)

    print(f"\nDone. Found {found} DOIs. Missing: {len(not_found)}")
    if not_found:
        print("No match:", ", ".join(not_found))


if __name__ == "__main__":
    main()
