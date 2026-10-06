import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from evaluate_inference import cohorts, score


def label(t, g, d='dictionary'):
    return dict(target_id=t, gold_cluster=g, dictionary=d)


class EvaluationTests(unittest.TestCase):
    def test_conflicts_and_duplicates_removed_before_selection(self):
        rows = [label('a','x'), label('a','x'), label('b','x'), label('b','y'),
                label('c','z'), label('d','z'), label('e','z','other')]
        targets = {t: {'form': t} for t in 'abcde'}
        selected, conflicts = cohorts(rows, targets)
        self.assertEqual(conflicts, [('dictionary','b')])
        self.assertEqual({r['target_id'] for r in selected['dictionary','repeated']}, {'c','d'})
        self.assertNotIn(('other','repeated'), selected)

    def test_multiple_forms_uses_entire_eligible_groups(self):
        rows = [label('a','x'), label('b','x'), label('c','y'), label('d','y')]
        targets = {t: {'form': f} for t,f in zip('abcd',['same','same','one','two'])}
        selected, _ = cohorts(rows, targets)
        self.assertEqual(len(selected['dictionary','repeated']), 4)
        self.assertEqual(len(selected['dictionary','multiple_forms']), 2)

    def test_all_abstentions_are_distinct_singletons(self):
        rows = [label('a','x'),label('b','x'),label('c','y'),label('d','y')]
        preds = {t: {'status':'abstained','reason':'empty_prediction','pred_cluster':None} for t in 'abcd'}
        result = score(rows, preds)
        self.assertEqual(result['coverage'], 0)
        self.assertEqual(result['bcubed']['precision'], 1)
        self.assertEqual(result['bcubed']['recall'], .5)
        self.assertEqual(result['predicted_clusters'], 4)

    def test_merges_across_reference_groups_are_penalized(self):
        rows = [label('a','x'),label('b','x'),label('c','y'),label('d','y')]
        preds = {t: {'status':'ok','pred_cluster':'one'} for t in 'abcd'}
        result = score(rows, preds)
        self.assertEqual(result['bcubed']['precision'], .5)
        self.assertEqual(result['bcubed']['recall'], 1)
