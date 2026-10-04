# Dictionary-linked lemmatizer dataset research

Conservative, deterministic extraction of dictionary-attested word occurrences
from Sefaria dictionary–text links. The current pipeline uses BDB, BDB Aramaic,
Jastrow and Klein; WordForms and LLM predictions do not supply its labels.

**Status:** two 1,000-link samples and a targeted lemma-density probe have run.
The full linked corpus has not been extracted. No confidence model has been
trained and no lemmatizers have been evaluated. Accepted examples are provisional
rule-based associations, not expert-adjudicated gold.

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
inputs. Seeds alone cannot reproduce results after database changes. A full run
still needs operational planning (resumption, bounded memory, progress reporting);
the existing sampler is a research script, not a production batch service.
