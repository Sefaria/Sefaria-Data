"""Evaluate arbitrary cluster labels, independently of their spelling.

Gold JSONL: {"occurrence_id": "...", "gold_cluster": "..."}
Predictions JSONL: {"occurrence_id": "...", "pred_cluster": "..."}
Missing rows and null/empty predictions are abstentions. Scores are explicitly
conditional on coverage; compare models on a common set and report coverage.
"""
import argparse
from collections import Counter
import json
from pathlib import Path


def ratio(n, d):
    return n / d if d else None


def f1(p, r):
    if p is None or r is None:
        return None
    return 2 * p * r / (p + r) if p + r else 0.0


def choose2(n):
    return n * (n - 1) // 2


def cluster_scores(gold, predicted):
    if len(gold) != len(predicted) or not gold:
        raise ValueError("Expected equal, nonempty label sequences")
    cells = Counter(zip(gold, predicted))
    gs, ps = Counter(gold), Counter(predicted)
    tp = sum(choose2(n) for n in cells.values())
    gold_pairs = sum(choose2(n) for n in gs.values())
    predicted_pairs = sum(choose2(n) for n in ps.values())
    pp, pr = ratio(tp, predicted_pairs), ratio(tp, gold_pairs)
    bp = sum(n * n / ps[p] for (g, p), n in cells.items()) / len(gold)
    br = sum(n * n / gs[g] for (g, p), n in cells.items()) / len(gold)
    return {
        "n": len(gold), "gold_clusters": len(gs), "predicted_clusters": len(ps),
        "pairwise": {"precision": pp, "recall": pr, "f1": f1(pp, pr),
                     "true_positive_pairs": tp, "false_merge_pairs": predicted_pairs - tp,
                     "false_split_pairs": gold_pairs - tp},
        "bcubed": {"precision": bp, "recall": br, "f1": f1(bp, br)},
    }


def read_rows(path, label, allow_null=False):
    result = {}
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        oid, value = row["occurrence_id"], row[label]
        if not isinstance(oid, str) or not oid or oid in result:
            raise ValueError(f"{path}:{line_number}: invalid or duplicate occurrence_id")
        if not (isinstance(value, str) and value) and not (allow_null and value in (None, "")):
            raise ValueError(f"{path}:{line_number}: expected nonempty string label")
        result[oid] = value
    return result


def evaluate(gold, predictions):
    if not gold:
        raise ValueError("Empty gold dataset")
    unknown = set(predictions) - set(gold)
    if unknown:
        raise ValueError(f"Predictions contain {len(unknown)} unknown occurrence IDs")
    covered = [oid for oid in gold if predictions.get(oid) not in (None, "")]
    return {
        "gold_occurrences": len(gold), "covered_occurrences": len(covered),
        "abstentions": len(gold) - len(covered), "coverage": len(covered) / len(gold),
        "scores_conditional_on_coverage": cluster_scores(
            [gold[i] for i in covered], [predictions[i] for i in covered]) if covered else None,
        "note": "Undefined pairwise denominators are null. Partial-coverage scores are not directly comparable across models. Use identical IDs for common-support comparisons, alongside each model's coverage.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gold")
    parser.add_argument("predictions")
    args = parser.parse_args()
    result = evaluate(read_rows(args.gold, "gold_cluster"), read_rows(args.predictions, "pred_cluster", True))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
