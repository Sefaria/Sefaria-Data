import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import unittest
from evaluate_clusters import cluster_scores, evaluate


class EvaluationTests(unittest.TestCase):
    def test_invariant_to_renaming(self):
        result = cluster_scores(['a', 'a', 'b', 'b'], ['x', 'x', 'y', 'y'])
        self.assertEqual(result['pairwise']['f1'], 1)
        self.assertEqual(result['bcubed']['f1'], 1)

    def test_all_merged(self):
        result = cluster_scores(['a', 'a', 'b', 'b'], ['x'] * 4)
        self.assertAlmostEqual(result['pairwise']['precision'], 1/3)
        self.assertEqual(result['pairwise']['recall'], 1)
        self.assertEqual(result['bcubed']['precision'], .5)

    def test_all_split(self):
        result = cluster_scores(['a', 'a', 'b', 'b'], list('wxyz'))
        self.assertIsNone(result['pairwise']['precision'])
        self.assertEqual(result['pairwise']['recall'], 0)
        self.assertEqual(result['bcubed']['recall'], .5)

    def test_crossing_partitions(self):
        result = cluster_scores(list('aabb'), list('xyxy'))
        self.assertEqual(result['pairwise']['f1'], 0)
        self.assertEqual(result['bcubed']['f1'], .5)

    def test_abstention_and_unknown_id(self):
        result = evaluate({'1': 'a', '2': 'a'}, {'1': 'x', '2': None})
        self.assertEqual(result['coverage'], .5)
        self.assertIsNone(evaluate({'1': 'a'}, {})['scores_conditional_on_coverage'])
        with self.assertRaises(ValueError):
            evaluate({'1': 'a'}, {'3': 'x'})

    def test_invalid_lengths(self):
        with self.assertRaises(ValueError):
            cluster_scores(['a'], [])
        with self.assertRaises(ValueError):
            cluster_scores([], [])


if __name__ == '__main__':
    unittest.main()
