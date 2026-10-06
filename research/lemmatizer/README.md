# Dictionary-linked lemmatizer dataset research

Conservative, deterministic extraction of dictionary-attested word occurrences
from Sefaria dictionary–text links. The current pipeline uses BDB, BDB Aramaic,
Jastrow and Klein; WordForms and LLM predictions do not supply its labels.

**Status:** the full run processed 246,757 candidate links and recovered 9,062
occurrences across 3,901 dictionary-specific entries. Of those entries, 1,599
have at least two occurrences and 929 have at least three. No confidence model
has been trained and the three installed lemmatizers have now been evaluated on repeated dictionary-specific groups (see below). Accepted examples are
provisional rule-based associations, not expert-adjudicated gold.

## What is saved

- `src/`, `tests/`: current pipeline and earlier research utilities. The current
  entry points are `measure_citation_yield.py`, `build_citation_dataset.py`,
  `verify_citation_examples.py` and `probe_lemma_density.py`.
- [Extraction rules](docs/citation_rules_v2.md), [schema and method](docs/citation_pipeline.md),
  and [research findings](docs/findings.md).
- [Occurrence reference index](results/occurrence_refs.jsonl): 314 associations
  from the density probe, with dictionary/segment refs, exact matched surface,
  version identifiers, offsets, text hash and rule. Full passages and dictionary
  definitions are omitted. This index alone is not a complete evaluation dataset.
- [Density summary](results/density_summary.json): aggregate counts and per-entry
  reference lists. These lemmas were selected for prior extraction success.
- `configs/`: small historical WordForm sampling configs and the local DictaLM
  import recipe/checksum, retained for research provenance.

Generated `datasets/`, `reviews/`, sampling plans and `local_archive/` are ignored
by Git. Existing local files are preserved. Superseded notes are in
`local_archive/docs/`; their former results should not be read as current rules.
Earlier WordForm/review/LLM scripts remain for reproducibility and shared helper
imports; they are not stages of the current extractor. `evaluate_clusters.py` is
an unevaluated scoring prototype.

## Run

Use a Python environment with the sibling `Sefaria-Project` dependencies installed
and its Django settings connected to a local Sefaria database. Extraction reads
that database and writes only local output. A database dump is not included here.
Run from the Sefaria-Data root; every output directory must be new.

```sh
python -B -m unittest discover -s research/lemmatizer/tests -p 'test_*.py'

python -B research/lemmatizer/src/measure_citation_yield.py \
  --per-dictionary 250 --seed my-citation-sample \
  --output research/lemmatizer/datasets/new_sample

python -B research/lemmatizer/src/verify_citation_examples.py \
  research/lemmatizer/datasets/new_sample

python -B research/lemmatizer/src/probe_lemma_density.py \
  --examples research/lemmatizer/datasets/new_sample/examples.jsonl \
  --output research/lemmatizer/datasets/new_density
```

Each command that accesses Sefaria accepts `--project /path/to/Sefaria-Project`.
Sampling accepts optional `--exclude previous/cases.jsonl` to exclude earlier
link IDs; without it, nothing is excluded. Exclusion does not ensure distinct
lemmas or works. The density command accepts multiple `--examples` paths and
expands all links for that success-conditioned cohort. The native verifier needs
`cases.jsonl`, so it applies to sampling outputs, not density-probe outputs.

Exact historical samples require the original database snapshot and saved local
inputs. Seeds alone cannot reproduce results after database changes. Use the full-run wrapper below for checkpointing and progress. The sampler
remains a separate research tool for small diagnostic runs.

## Full corpus extraction with progress and resumption

The full-run wrapper uses the same v2 rules and scans all relevant links for the
four supported dictionaries (no sample quotas). Install `tqdm` in your Sefaria
Python environment if absent. From the repository root:

```sh
python -B research/lemmatizer/src/extract_all_citations.py \
  --output research/lemmatizer/datasets/full_citations_v2
```

Two tqdm bars show link inventory and extraction, including rate, ETA, accepted
unique examples and skipped links. Django startup precedes the bars. The default
100-segment cap and conservative matching rejections still apply: scanning every
link does not mean accepting every link. Source database access is read-only.

The local SQLite checkpoint commits every 100 links; Ctrl-C rolls back the
unfinished batch. Resume with the same command plus `--resume`. Keep the
`staging.sqlite` file. Only one process may use an output directory. Resume refuses
changed script hashes, project path or segment cap. Link records are frozen in
the initial inventory, but text/entry retrieval uses the live database; avoid
changing the database during a run or between resumptions. If inventory was
interrupted it is rebuilt before extraction starts.

For a smoke test, add `--limit 100` and use a separate output directory. This
limits extraction, not inventory. A subsequent `--resume` without `--limit`
processes all remaining links. The user subsequently completed the full run;
the totals above come from its saved report.

At completion (or after a limited run), streaming exports produce:

- `examples.jsonl`: deduplicated lemma–occurrence associations with exact spans,
  frozen text, evidence and version provenance.
- `lemmas.jsonl`: dictionary-specific entry groups, occurrence counts, surfaces
  and example IDs. These are not reconciled cross-dictionary lexemes.
- `attempts.jsonl`: every processed link, outcome, rejection reason and example ID;
  duplicate supporting links remain visible here.
- `cases.jsonl`: accepted cases only, for native-text validation; unlike the
  sampler, rejected full-text cases are not exported. Frozen queue links and
  attempt diagnostics remain in SQLite.
- `version_selections.jsonl`, `source/`, `report.json`: selection provenance,
  exact scripts, coverage counts and cluster-size distribution.

JSONL exports are produced at the end, not after every checkpoint. The database
is the authoritative resumable state; an interrupted export can be regenerated
with `--resume`. Keep the full output directory locally; it is ignored by Git.
To validate accepted spans against native version text after extraction:

```sh
python -B research/lemmatizer/src/verify_citation_examples.py \
  research/lemmatizer/datasets/full_citations_v2
```

The verifier currently loads accepted examples/cases in memory. Its checks do not
establish semantic precision. Earlier timing estimates remain provisional;
watch the full run's measured throughput and ETA.


## Readable CSV export

```sh
python -B research/lemmatizer/src/export_csv.py \
  --input research/lemmatizer/datasets/full_citations_v2/examples.jsonl \
  --output research/lemmatizer/datasets/full_citations_v2/lemma_occurrences.csv
```

The exporter reads categories from `cases.jsonl` beside the input (override with
`--cases`). It validates spans, IDs and category availability, then checks the
CSV round trip. Output is UTF-8 with BOM, sorted by dictionary, headword and
reference, with one row per association. Generated CSV files stay local under
`datasets/`.

| Column | Meaning |
|---|---|
| `dictionary` | Dictionary supplying the association |
| `lemma` | Exact dictionary headword |
| `lemma_id` | Dictionary-specific grouping key; no cross-dictionary merging |
| `group_size` | Number of exported occurrences in this group |
| `matched_word` | Exact matched surface, including pointing |
| `text_ref` | Matched passage reference |
| `ref_category` | Top-level Sefaria category of the target text |
| `ref_category_path` | Full source category hierarchy, separated by ` > ` |
| `passage_highlighted` | Frozen passage with the occurrence enclosed in `⟦…⟧` |
| `version_title` | Source text version |
| `dictionary_ref` | Source dictionary reference |
| `extraction_rule` | Rule supporting acceptance |
| `example_id` | Identifier linking to the full JSONL record |

## Comparing off-the-shelf lemmatizers

See [model comparison groundwork](docs/model_comparison.md) for the inspected
Dicta/Shoshan/Stanza preprocessing behavior, pinned model references, context
limits, Stanza segmentation policy, and preparation command. Shared model inputs
and dictionary labels are separated by `prepare_benchmark.py`; normalization and
alignment helpers are in `benchmark_core.py`. The models are now [installed and smoke-tested](docs/model_installation.md).
The [resumable inference runner](docs/inference.md) records predictions from all
three models with shared context windows and progress bars. Full inference and the repeated-cluster evaluation have completed locally.
See the inference guide for the evaluation command and saved-report schema.

## Offline Elasticsearch comparison

The [offline search guide](docs/offline_search.md) documents the runnable local
Tanakh + Rashi + Mishnah experiment: corpus export, resumable full-text Shoshan inference,
Docker Elasticsearch, paired baseline/enhanced queries, and relevance scoring.
The full 55,589-passage corpus has been exported, lemmatized, and indexed locally.
The Sefaria-Project experiment page supports paired search, per-word lemma inspection,
and optional י/ו expansion. Retrieval-quality evaluation with judged queries remains
pending. See the [Cauldron deployment assessment](docs/cauldron_deployment.md) for
the proposed shared dev deployment.
