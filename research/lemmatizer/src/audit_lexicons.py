"""Read-only lexicon inventory. Requires pymongo; no Django or model imports.

Usage: python audit_lexicons.py --output inventory.json
URI is read from LEMMATIZER_MONGO_URI (default localhost); never written to output.
Counts are of documents/pointers, NOT annotated tokens or unique lemmas.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re


def first_segment(chapter):
    if isinstance(chapter, list) and chapter and isinstance(chapter[0], list) and chapter[0]:
        return chapter[0][0]
    return None


def audit(db):
    entries = Counter()
    entry_fields = defaultdict(Counter)
    entry_keys = Counter()
    examples = {}
    for e in db.lexicon_entry.find({}):
        lex = e.get("parent_lexicon", "<missing>")
        entries[lex] += 1
        entry_keys[(lex, e.get("headword"))] += 1
        for key in ("refs", "citations", "quotes", "strong_number", "strong_numbers", "rid", "root", "occurrences"):
            if e.get(key):
                entry_fields[lex][key] += 1
        if 'data-ref=' in json.dumps(e.get("content", {}), ensure_ascii=False):
            entry_fields[lex]["content_with_data_ref"] += 1

    totals = Counter()
    lex_stats = defaultdict(Counter)
    provenance = defaultdict(Counter)
    form_heads = defaultdict(set)
    provenance_with_refs = defaultdict(Counter)
    ref_books = Counter()
    for wf in db.word_form.find({}):
        totals["documents"] += 1
        refs = wf.get("refs") or []
        looks = wf.get("lookups") or []
        if not isinstance(refs, list) or not isinstance(looks, list):
            totals["malformed_list_fields"] += 1
            continue
        totals["with_refs" if refs else "without_refs"] += 1
        totals["ref_list_items"] += len(refs)
        totals["duplicate_ref_items"] += len(refs) - len(set(refs))
        if len(looks) > 1:
            totals["multiple_lookup_pointers"] += 1
        by_lex = defaultdict(set)
        for lookup in looks:
            if not isinstance(lookup, dict):
                totals["non_object_lookup"] += 1
                continue
            lex = lookup.get("parent_lexicon", lookup.get("lexicon", "<missing>"))
            if "lexicon" in lookup:
                totals["legacy_lexicon_key_pointers"] += 1
            by_lex[lex].add(lookup.get("headword"))
            lex_stats[lex]["lookup_pointers"] += 1
            if not entry_keys[(lex, lookup.get("headword"))]:
                lex_stats[lex]["unresolved_headword_pointers"] += 1
        for lex, heads in by_lex.items():
            form_heads[(lex, wf.get("form"))].update(heads)
            if refs:
                provenance_with_refs[lex][wf.get("generated_by", "<missing>")] += 1
            s = lex_stats[lex]
            s["word_form_documents"] += 1
            s["documents_with_refs"] += bool(refs)
            s["documents_with_multiple_headwords"] += len(heads) > 1
            s["ref_bearing_documents_with_multiple_headwords"] += bool(refs) and len(heads) > 1
            s["unique_ref_items_summed_per_document"] += len(set(refs))
            provenance[lex][wf.get("generated_by", "<missing>")] += 1
            if refs and lex not in examples:
                examples[lex] = {k: wf[k] for k in ("_id", "form", "c_form", "language_code", "generated_by") if k in wf}
                examples[lex]["lookups"] = looks
                examples[lex]["refs_first_5"] = refs[:5]
                examples[lex]["ref_count"] = len(refs)
        for ref in set(refs):
            ref_books[re.split(r" \d", ref, maxsplit=1)[0]] += 1
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "database": db.name,
        "scope": "Local Mongo snapshot; word_form/lexicon_entry/lexicon plus Genesis version examples; no token alignment or model evaluation.",
        "totals": dict(totals),
        "lexicons": {lex: {"entries": entries[lex], **dict(lex_stats[lex]),
                    "nonempty_entry_fields": dict(entry_fields[lex]),
                    "word_form_provenance": dict(provenance[lex]),
                    "ref_bearing_provenance": dict(provenance_with_refs[lex]),
                    "surface_forms_with_multiple_headwords_across_records": sum(len(h) > 1 for (l, f), h in form_heads.items() if l == lex),
                    "duplicate_headword_keys": sum(n > 1 for (l, h), n in entry_keys.items() if l == lex)}
                    for lex in sorted(set(entries) | set(lex_stats))},
        "ref_prefix_counts_top100_heuristic": ref_books.most_common(100),
        "examples": examples,
        "genesis_1_1_versions": [{"version_id": str(v["_id"]), "versionTitle": v.get("versionTitle"), "language": v.get("language"), "text": first_segment(v.get("chapter"))} for v in db.texts.find({"title": "Genesis", "language": "he"}, {"chapter": {"$slice": 1}, "versionTitle": 1, "language": 1})],
        "sample_generated_word_forms": [{**{k: w.get(k) for k in ("_id", "form", "lookups", "generated_by")}, "refs_first_5": (w.get("refs") or [])[:5]} for w in db.word_form.find({"generated_by": "prefix_adder_1", "refs.0": {"$exists": True}}).limit(5)],
        "metadata": list(db.lexicon.find({}, {"_id": 0, "name": 1, "language": 1, "index_title": 1, "version_title": 1, "version_lang": 1})),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="sefaria")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from pymongo import MongoClient
    with MongoClient(os.environ.get("LEMMATIZER_MONGO_URI", "mongodb://localhost:27017"), serverSelectionTimeoutMS=5000) as client:
        result = audit(client[args.db])
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"totals": result["totals"], "lexicons": result["lexicons"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
