# Record model predictions

Run from the Sefaria-Data root using the installed research environment:

```sh
research/lemmatizer/.venv/bin/python -B research/lemmatizer/src/run_inference.py \
  --input research/lemmatizer/datasets/comparison_unpointed_v2 \
  --output research/lemmatizer/datasets/inference_unpointed_v1
```

This runs Dicta, Shoshan and Stanza sequentially on Apple MPS, entirely offline.
There is a context-preparation progress bar and one inference bar per model.
The input has 9,044 distinct target occurrences; the 9,062 dictionary associations
remain separate. No dictionary labels are supplied to the models. No evaluation
scores or bootstrap samples are computed at this stage.

The output directory must be new. To resume after interruption, repeat the same
command with `--resume`. Each prediction is committed immediately to SQLite;
completed targets, including abstentions, are not rerun. Resume verifies input,
source, package version, device, configuration and installed-model checksums.
Only one process may use an output directory. Unexpected errors stop the run
instead of being silently counted as alignment failures. Hard termination may
leave stale JSONL exports; resuming regenerates them from the checkpoint.

For a small test use another output directory and add `--limit 20`. This selects
the same 20 targets for every model by sorted target ID, not a stratified sample.
Resume without the limit to extend that run to the full dataset. Optional
`--model dicta|shoshan|stanza` runs one model; `--device cpu` changes the device
and requires a separate output directory from any MPS run.

## Saved output

- `dicta.jsonl`, `shoshan.jsonl`, `stanza.jsonl`: one row per processed target,
  including abstentions. Exported after each model and on orderly exit.
- `predictions.sqlite`: durable predictions and shared context windows; retain
  this for resumption.
- `manifest.json`: model/configuration, input and source hashes, package versions,
  device and preprocessing/context policies.
- `summary.json`: counts of usable outputs and reasons for abstaining per model.
- `run_status.json`: whether the requested selection finished or stopped.

Prediction fields:

| Field | Meaning |
|---|---|
| `target_id`, `passage_id` | Join keys into prepared targets/passages; join `labels.jsonl` by target ID later |
| `form` | Target spelling after shared preprocessing |
| `original_start`, `original_end` | Half-open character offsets in the original frozen passage |
| `model_start`, `model_end` | Half-open offsets in the full preprocessed passage |
| `window` | Exact supplied context, its full-passage offsets, target-relative offsets and tokenizer lengths |
| `raw_lemma` | Model lemma before output normalization |
| `pred_cluster` | Normalized predicted lemma for later grouping; null when unavailable |
| `status`, `reason` | `ok` or `abstained`, with an explicit reason; `ok` does not mean correct |
| `projection`, `details` | Alignment/projection method and model-specific output, including Stanza components |
| `elapsed_seconds` | Time for this target, possibly benefiting from cached passage predictions |

Shoshan's saved `score` is a retrieval similarity, not a calibrated probability.
Multiple dictionary associations reuse a single target prediction. Later scoring
must remain separate by dictionary and handle `label_conflicts.jsonl` explicitly.

## Context and alignment policy

The current runner accepts `unpointed-v1` prepared inputs only. It supplies the
same context to all models. Full passages are used when they fit both tokenizers;
otherwise a deterministic window grows around the target on whitespace
boundaries. Both actual tokenizers must fit, including special tokens: at most
512 for Dicta and 160 for Shoshan. Attached punctuation and prefixes are not cut
to squeeze a target into the window. This avoids silent truncation, but limits
all models to the shared shorter context and can cut a sentence at its edges.

Dicta wordpieces are reconstructed with tokenizer offsets and checked against
its output sequence. Stanza must match the target's complete surface-token span;
a segmented token is projected to its unique lexical component or abstained.
Shoshan receives an explicit target offset, checked against its own normalization
and encoded span. No adapter picks a word using agreement with a dictionary label.
Ambiguous alignment is recorded as an abstention. Full context/token predictions
are cached for nearby targets where possible.

## Validation

The automated suite passes 43 tests, including repeated-spelling alignment,
wordpiece reconstruction, target preservation and refusing oversized words.
A real 20-target MPS smoke test produced 18 usable Dicta outputs (two empty),
20 Shoshan outputs and 20 Stanza outputs. All shared contexts and target spans
were checked; a second invocation resumed without recomputing predictions.
The longest passage (18,782 characters) was also tested: all three models
completed with the same shortened context, retaining the exact target span.
These checks establish execution/alignment behavior, not lemma accuracy or
representative coverage. The full dataset inference has not been started.

## Evaluate saved predictions

```sh
research/lemmatizer/.venv/bin/python -B research/lemmatizer/src/evaluate_inference.py \
  --input research/lemmatizer/datasets/comparison_unpointed_v2 \
  --predictions research/lemmatizer/datasets/inference_unpointed_v1 \
  --output research/lemmatizer/datasets/evaluation_unpointed_v1
```

Use a new output directory. This requires complete predictions for all three
models and checks the prepared-input hashes against the inference manifest.
It deduplicates dictionary/target associations and excludes conflicting labels
before selecting reference clusters with at least two distinct occurrences.
All eligible groups within a dictionary are scored together, so false merges
between groups count. Every abstention becomes a distinct singleton, without
removing it from the comparison. A second subset keeps only groups with multiple
unpointed input spellings. Neither subset depends on model predictions.

`report.md` contains coverage and B³ precision/recall/F1. `report.json` also
contains pairwise scores, exclusion details and provenance hashes.
`membership.jsonl` records the exact evaluation sets for later analysis.
No cross-dictionary grouping or bootstrap intervals are computed.

The full run produced repeated-cluster cohorts of 6,023 occurrences / 1,302 groups
for BDB, 218 / 73 for BDB Aramaic, 444 / 192 for Jastrow and 59 / 29 for Klein.
These are per-dictionary counts; an occurrence may appear in multiple dictionaries.

## Bootstrap score stability

```sh
research/lemmatizer/.venv/bin/python -B research/lemmatizer/src/bootstrap_evaluation.py \
  --evaluation research/lemmatizer/datasets/evaluation_unpointed_v1 \
  --predictions research/lemmatizer/datasets/inference_unpointed_v1 \
  --output research/lemmatizer/datasets/bootstrap_unpointed_v1 \
  --replicates 2000 --seed 20261005
```

Each dictionary/subset independently resamples its reference groups with
replacement, retaining all occurrences in each selected group. Multiplicity
weights the original rows; duplicated groups retain their original lexical
identity, and abstentions retain their target-specific singleton identity.
The same draw is used for every model. B³ is recomputed from the weighted
contingency table each time; per-item scores are not simply resampled.

`report.md` and `report.json` contain percentile 95% intervals for scores and
paired F1 differences. JSON also includes coverage intervals and provenance.
`replicates.npz` preserves every replicate, with axis/key mappings in JSON.
The implementation checks that unweighted scores reproduce the original report.
Unit tests compare weighted results against explicit duplicated-row scoring.

These are approximate, conditional intervals, not estimates of library-wide
performance. Groups sharing works/passages may be dependent. Resampling can
remove competing groups and change false-merge opportunities, so bootstrap
scores can shift upward (visible for BDB); percentile intervals need not be
centered on the original estimate. Treat absolute score intervals cautiously.
Pairwise intervals are not adjusted for multiple comparisons. Klein's four-group
multiple-form subset is too small for useful general conclusions; its constant
100% Stanza interval only reflects the absence of observed errors there.

In the main repeated-cluster cohort, Shoshan minus Dicta is +2.50 percentage
points on BDB (95% interval +1.19 to +3.29), +2.27 on Jastrow (-0.75 to +5.05),
and -2.65 on BDB Aramaic (-6.77 to +1.32). Thus the BDB ordering is more stable
under this resampling scheme than the other two orderings.
