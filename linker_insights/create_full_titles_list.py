#!/usr/bin/env python3
"""
Dump all valid standalone titles for every Index in the library as derived from
the term data that powers the linker TermMatcher.  The script builds the same
NonUniqueTerm catalog, walks every index's match templates, enumerates every
possible combination of term titles, and writes the results to disk as JSON.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence, Set

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sefaria.settings")

import django  # noqa

django.setup()

from sefaria.model import library  # noqa  E402
from sefaria.model.schema import NonUniqueTermSet  # noqa  E402
from sefaria.model.linker.ref_resolver import TermMatcher  # noqa  E402


LANG_CHOICES = ("en", "he")
DEFAULT_OUTPUT = Path(__file__).with_name("full_titles_by_index.json")


def build_slug_title_map(term_matcher: TermMatcher) -> Dict[str, Set[str]]:
    """
    Reconstruct {term slug -> {titles}} for the provided TermMatcher.  The
    matcher internally maps the strings that it can recognize back to the
    NonUniqueTerm objects, so we invert that mapping to stay perfectly in sync
    with the resolver.
    """
    slug_map: Dict[str, Set[str]] = defaultdict(set)
    for title, term_list in term_matcher._str2term_map.items():  # pylint: disable=protected-access
        for term in term_list:
            slug_map[term.slug].add(title)
    return slug_map


def expand_template_titles(
    slugs: Sequence[str],
    slug_maps_by_lang: Mapping[str, Mapping[str, Set[str]]],
) -> Dict[str, Set[str]]:
    """
    Given a sequence of term slugs for a match template, enumerate all possible
    textual titles per language by taking the Cartesian product of the titles
    available for each slug.
    """
    expanded: Dict[str, Set[str]] = defaultdict(set)
    for lang, slug_map in slug_maps_by_lang.items():
        term_title_options: List[Sequence[str]] = []
        missing_term = False
        for slug in slugs:
            titles = sorted(slug_map.get(slug, ()))
            if not titles:
                missing_term = True
                break
            term_title_options.append(titles)
        if missing_term or not term_title_options:
            continue
        for combo in itertools.product(*term_title_options):
            joined = " ".join(part.strip() for part in combo if part.strip()).strip()
            if joined:
                expanded[lang].add(joined)
    return expanded


def extract_index_titles(
    slug_maps_by_lang: Mapping[str, Mapping[str, Set[str]]],
) -> Dict[str, Dict[str, List[str]]]:
    """
    Iterate through every Index in the library and harvest all of the titles
    that can be formed from its match templates.
    """
    results: Dict[str, Dict[str, List[str]]] = {}
    indexes = library.all_index_records()
    for index in indexes:
        root_node = index.nodes
        templates = list(root_node.get_match_templates())
        lang_titles: MutableMapping[str, Set[str]] = {lang: set() for lang in slug_maps_by_lang}
        for lang in lang_titles:
            primary_candidates: List[str] = []
            try:
                primary_candidates.append(index.get_title(lang) or "")
            except Exception:
                primary_candidates.append("")
            try:
                root_primary = index.nodes.get_primary_title(lang) if getattr(index, "nodes", None) else ""
                primary_candidates.append(root_primary or "")
            except Exception:
                primary_candidates.append("")
            for primary in primary_candidates:
                primary = primary.strip()
                if primary:
                    lang_titles[lang].add(primary)
        for template in templates:
            terms = [term for term in template.terms if term is not None]
            if len(terms) == 0:
                continue
            slugs = [term.slug for term in terms]
            expanded = expand_template_titles(slugs, slug_maps_by_lang)
            for lang, titles in expanded.items():
                lang_titles[lang].update(titles)
        results[index.title] = {lang: sorted(values) for lang, values in lang_titles.items()}
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a JSON map of every Index title to all valid standalone titles "
        "the TermMatcher can recognize."
    )
    parser.add_argument(
        "--langs",
        nargs="+",
        default=list(LANG_CHOICES),
        metavar="LANG",
        help=f"Languages to include (default: {', '.join(LANG_CHOICES)})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Where to write the JSON output (default: {DEFAULT_OUTPUT})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    langs = [lang.strip() for lang in args.langs if lang.strip()]
    invalid_langs = set(langs) - set(LANG_CHOICES)
    if invalid_langs:
        raise ValueError(f"Unsupported languages requested: {sorted(invalid_langs)}")

    non_unique_terms = NonUniqueTermSet()
    slug_maps_by_lang = {
        lang: build_slug_title_map(TermMatcher(lang, non_unique_terms))
        for lang in langs
    }
    titles_by_index = extract_index_titles(slug_maps_by_lang)

    output_path = args.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fout:
        json.dump(titles_by_index, fout, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"Wrote {len(titles_by_index)} indexes to {output_path}")


if __name__ == "__main__":
    main()
