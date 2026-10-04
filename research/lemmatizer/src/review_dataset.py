"""Validate exported dataset invariants and generate a compact human review."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from extraction_core import find_spans, sha


def rows(directory, kind, key):
    result = {}
    for line in (directory / (kind + '.jsonl')).read_text().splitlines():
        row = json.loads(line)
        if row[key] in result:
            raise ValueError('Duplicate ID: ' + row[key])
        result[row[key]] = row
    return result


def review(directory):
    manifest = json.loads((directory / 'manifest.json').read_text())
    assert manifest['status'] == 'complete'
    passages = rows(directory, 'passages', 'passage_id')
    entries = rows(directory, 'entries', 'entry_id')
    occurrences = rows(directory, 'occurrences', 'occurrence_id')
    word_forms = rows(directory, 'word_forms', 'word_form_id')
    attempts = [json.loads(l) for l in (directory / 'attempts.jsonl').read_text().splitlines()]
    for p in passages.values():
        assert sha(p['text']) == p['text_sha256']
        assert sha(p['raw_text']) == p['raw_text_sha256']
    for o in occurrences.values():
        p = passages[o['passage_id']]
        a,b = o['start_char'],o['end_char']
        assert 0 <= a < b <= len(p['text'])
        assert p['text'][a:b] == o['surface']
        for link in o['associations']:
            assert link['entry_id'] in entries and link['word_form_id'] in word_forms
            assert (a,b) in find_spans(p['text'], link['word_form'], link['match_method'])
    per_dictionary = defaultdict(Counter)
    for a in attempts:
        for oid in a['candidate_occurrence_ids']:
            assert oid in occurrences
        for pid in a['searched_passage_ids']:
            assert pid in passages
        record = word_forms[a['word_form_id']]
        for lex in {l['lookup'].get('parent_lexicon', l['lookup'].get('lexicon')) for l in record['resolved_lookups']}:
            per_dictionary[lex][a['status']] += 1
    lines = ['# WordForm extraction pilot', '',
        'Engineering sample, not a representative coverage estimate. All associations are unreviewed candidates.', '',
        f"- Selected word forms: {len(word_forms)}; extraction attempts: {len(attempts)}.",
        f"- Frozen passages: {len(passages)}; distinct occurrences: {len(occurrences)}.",
        f"- Dictionary entries retained: {len(entries)}.",
        f"- Native TextChunk cross-checks: {manifest.get('native_texts_verified', 0)} passages.",
        '- Every exported offset, text hash, association target and normalized match passed validation.', '',
        '## Results by dictionary', '',
        '| Dictionary | Unique match | Repeated match | No match | Missing text |',
        '|---|---:|---:|---:|---:|']
    for lex,c in sorted(per_dictionary.items()):
        lines.append(f"| {lex} | {c['matched_unique']} | {c['matched_multiple']} | {c['no_match']} | {c['missing_hebrew_text']} |")
    lines += ['', 'Dictionary rows overlap: one WordForm can point into more than one dictionary.', '',
        '## Example occurrences', '', 'The bold text is the exact extracted substring. Offsets are Unicode code points in the frozen plain passage, with an exclusive end.', '']
    # Include repeated matches, multiple dictionaries, and all three seed dictionaries.
    chosen = []
    for predicate in [lambda o:any(a['matches_in_source_ref']>1 for a in o['associations']),
                      lambda o:len({entries[a['entry_id']]['dictionary'] for a in o['associations']})>1,
                      lambda o:any(entries[a['entry_id']]['dictionary']=='Jastrow Dictionary' for a in o['associations']),
                      lambda o:any(entries[a['entry_id']]['dictionary']=='Klein Dictionary' for a in o['associations'])]:
        subset = [o for o in occurrences.values() if predicate(o) and o not in chosen][:3]
        chosen.extend(subset)
    for o in chosen:
        p = passages[o['passage_id']]
        labels = sorted({entries[a['entry_id']]['dictionary'] + ': ' + entries[a['entry_id']]['headword'] for a in o['associations']})
        methods = sorted({a['match_method'] for a in o['associations']})
        lines += [f"### {p['ref']}", '', f"{o['left_context']}**{o['surface']}**{o['right_context']}", '',
                  f"- Version: {p['version_title']} (fallback: {p['is_fallback']}).",
                  f"- Span: [{o['start_char']}, {o['end_char']}); match: {', '.join(methods)}.",
                  '- Candidate entries: ' + '; '.join(labels) + '.',
                  '- Occurrence ID: `' + o['occurrence_id'] + '`.', '']
    lines += ['## Unmatched and unavailable cases', '', '| Ref | WordForm | Status |', '|---|---|---|']
    for a in sorted(attempts, key=lambda r:(r['status'],r['source_ref'])):
        if a['status'] not in ('matched_unique','matched_multiple'):
            form = word_forms[a['word_form_id']]['source_record']['form']
            lines.append(f"| {a['source_ref']} | {form} | {a['status']} |")
    lines += ['', '## Timing', '', '```json', json.dumps(manifest['timings_seconds'], indent=2), '```', '',
              'Warm local caches and this small, deliberately selected sample do not establish a full-corpus runtime.', '']
    (directory / 'REVIEW.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'validated_occurrences':len(occurrences),'validated_passages':len(passages),'by_dictionary':per_dictionary},ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path)
    review(p.parse_args().directory)
