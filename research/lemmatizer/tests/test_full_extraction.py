"""Durability and duplicate-link behavior of the full-run wrapper."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from extract_all_citations import RunStore, record_result, export_run


class FullExtractionTests(unittest.TestCase):
    def test_atomic_checkpoint_resume_and_shared_occurrence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = RunStore(root)
            for key in ('one', 'two'):
                store.db.execute('INSERT INTO queue(id,data) VALUES (?,?)', (key, '{}'))
            store.db.commit()
            case = {'audit_id': 'a', 'dictionary': 'BDB Dictionary',
                    'dictionary_ref': 'BDB, foo 1', 'target_ref': 'Genesis 1:1'}
            example = {'example_id': 'e', 'entry_key': 'k', 'dictionary': 'BDB Dictionary',
                       'headword': 'foo', 'surface': 'foo', 'dictionary_ref': 'BDB, foo 1'}
            record_result(store, {'_id': 'one'}, case, example, None)
            store.db.commit()
            record_result(store, {'_id': 'two'}, case, example, None)
            store.db.rollback()  # Simulate interruption before the next checkpoint.
            store.db.close()
            store = RunStore(root)
            self.assertEqual(store.db.execute('SELECT id FROM queue WHERE done=0').fetchall(), [('two',)])
            self.assertEqual(store.db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0], 1)
            record_result(store, {'_id': 'two'}, case, example, None)
            store.db.commit()
            export_run(store, root, 'complete')
            report = json.loads((root / 'report.json').read_text())
            self.assertEqual(report['outcomes']['accepted_links'], 2)
            self.assertEqual(report['unique_examples'], 1)
            self.assertEqual(len((root / 'cases.jsonl').read_text().splitlines()), 2)
            lemma = json.loads((root / 'lemmas.jsonl').read_text())
            self.assertEqual(lemma['occurrence_count'], 1)
            self.assertEqual(lemma['example_ids'], ['e'])
            store.db.close()


if __name__ == '__main__':
    unittest.main()
