"""Verify frozen accepted spans against native Sefaria version text (read only)."""
import argparse
import json
from pathlib import Path
from build_dataset import Backend
from extraction_core import find_spans, sha
from build_citation_dataset import evidence_matches


class NullStore:
    def put(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[4]/'Sefaria-Project')
    args = parser.parse_args()
    backend = Backend(args.project, NullStore())
    examples = list(map(json.loads, (args.directory/'examples.jsonl').read_text().splitlines()))
    wanted = {e['passage_id'] for e in examples}
    passages = {}
    for line in (args.directory/'cases.jsonl').read_text().splitlines():
        for p in json.loads(line)['passages']:
            if p['passage_id'] in wanted:
                passages[p['passage_id']] = p
    errors = []
    for pid, passage in passages.items():
        native = backend.TextChunk(backend.Ref(passage['ref']), lang=passage['version_language'],
            vtitle=passage['version_title'], fallback_on_default_version=False).text
        if native != passage['raw_text']:
            errors.append({'passage_id': pid, 'issue': 'native_text_mismatch'})
    for e in examples:
        p = passages[e['passage_id']]
        if (e['text'] != p['text'] or sha(e['text']) != e['text_sha256']
            or e['text'][e['start_char']:e['end_char']] != e['surface']
            or (e['start_char'], e['end_char'],e['match_method']) not in
                [(a,b,mode) for _,a,b,mode in evidence_matches({'passages':[p]},e['evidence'])]):
            errors.append({'example_id': e['example_id'], 'issue': 'span_or_hash_mismatch'})
    result = {'native_passages_checked': len(passages), 'examples_checked': len(examples),
        'errors': errors, 'semantic_correctness_assessed': False}
    (args.directory/'validation.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
