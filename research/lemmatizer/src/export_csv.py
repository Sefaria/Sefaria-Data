"""Export a readable UTF-8 BOM CSV, one row per lemma–occurrence association."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import re

COLUMNS = ['dictionary', 'lemma', 'lemma_id', 'group_size', 'matched_word',
           'text_ref', 'ref_category', 'ref_category_path', 'passage_highlighted', 'version_title', 'dictionary_ref',
           'extraction_rule', 'example_id']


def natural_key(text):
    return tuple((1, int(part)) if part.isdigit() else (0, part)
                 for part in re.split(r'(\d+)', text))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='examples.jsonl')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cases', type=Path, help='Frozen cases.jsonl; defaults to beside input')
    args = parser.parse_args()
    categories = {}
    cases_path = args.cases or args.input.with_name('cases.jsonl')
    with cases_path.open(encoding='utf-8') as source:
        for line in source:
            case = json.loads(line)
            path = case.get('categories', [])
            if not path:
                continue
            for passage in case.get('passages', []):
                ref = passage['ref']
                if ref in categories and categories[ref] != path:
                    raise ValueError('Conflicting source categories: ' + ref)
                categories[ref] = path
    rows = []
    ids = set()
    with args.input.open(encoding='utf-8') as source:
        for line in source:
            e = json.loads(line)
            a, b = e['start_char'], e['end_char']
            if not 0 <= a < b <= len(e['text']) or e['text'][a:b] != e['surface']:
                raise ValueError('Invalid source span: ' + e['example_id'])
            if e['example_id'] in ids:
                raise ValueError('Duplicate example ID: ' + e['example_id'])
            ids.add(e['example_id'])
            category_path = categories.get(e['segment_ref'])
            if not category_path:
                raise ValueError('Missing source categories: ' + e['segment_ref'])
            rows.append({'dictionary': e['dictionary'], 'lemma': e['headword'],
                'lemma_id': e['entry_key'], 'matched_word': e['surface'],
                'text_ref': e['segment_ref'],
                'ref_category': category_path[0],
                'ref_category_path': ' > '.join(category_path),
                'passage_highlighted': e['text'][:a] + '⟦' + e['surface'] + '⟧' + e['text'][b:],
                'version_title': e['version_title'], 'dictionary_ref': e['dictionary_ref'],
                'extraction_rule': e['evidence']['rule'], 'example_id': e['example_id']})
    counts = Counter(r['lemma_id'] for r in rows)
    rows.sort(key=lambda r: (r['dictionary'], r['lemma'], r['lemma_id'],
                             natural_key(r['text_ref']), r['example_id']))
    for row in rows:
        row['group_size'] = counts[row['lemma_id']]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    # Round-trip checks catch quoting, embedded newlines, and Hebrew encoding loss.
    with args.output.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != COLUMNS:
            raise ValueError('CSV headers do not match')
        saved = list(reader)
    expected = [{k: str(row[k]) for k in COLUMNS} for row in rows]
    if saved != expected:
        raise ValueError('CSV round-trip verification failed')
    print(json.dumps({'rows': len(rows), 'lemma_groups': len(counts),
                      'bytes': args.output.stat().st_size, 'output': str(args.output.resolve())}))


if __name__ == '__main__':
    main()
