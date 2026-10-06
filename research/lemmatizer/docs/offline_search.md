# Offline lexical-search experiment

Implemented 2026-10-05. Baseline: Sefaria Elasticsearch phrase search using its
existing naive Hebrew analyzer. Enhanced: baseline OR Shoshan lemma phrase match,
with an adjustable weight. Both use the same index, documents and pagesheetrank
factor. This is an ES-only subset experiment, not the public site's federated
Tanakh/Dicta search. No semantic-search POC is involved.

## Current local artifacts

- `datasets/search_tanakh_rashi_v1`: full frozen corpus, 51,431 documents:
  23,206 Tanakh verses and 28,225 Rashi segments. Includes 39 biblical books
  (Sefaria's split-book convention) and 39 Rashi works identified through corpus
  and base-text metadata. One automatically selected primary Hebrew version per
  work, ordered by native priority then version ID. No segment fallback to other
  versions. Version selections and licenses are recorded in the manifest.
- Corpus comes from local Mongo, not a production Elasticsearch snapshot.
  Native `TextIndexer.modify_text_in_doc` supplies the search text; its source
  and footnote helper are recorded. In particular, the native footnote helper
  moves supported footnote contents to the end; it does not simply discard them.
- `datasets/search_lemmas_smoke_v1`: 64 deterministically selected passages,
  779 tokens, all returned nonempty single-token lemmas. Apple GPU execution took
  about five seconds after model loading. This small sample is not a corpus-wide
  runtime benchmark. Resume was tested without recomputation.
- `datasets/search_comparison_smoke_v1`: five explicitly synthetic queries,
  two ranked runs per query, an unlabelled judgment pool, plugin/analyzer checks
  and a long-context test. The longest exported passage, Rashi on Ezekiel 14:14:1,
  has 3,590 characters and 422 tokens; all tokens/offsets were retained.
- `lemma-poc-smoke-v1`: 64-document smoke index, only on local port 19200.
- Full-corpus lemmatization and local indexing have completed, including the
  Mishnah extension (55,589 passages). Retrieval-quality evaluation has NOT run.
  Synthetic smoke queries are plumbing tests, not evidence of improvement.

## Local Elasticsearch

```sh
docker compose -f research/lemmatizer/offline_search/compose.yaml up -d --build
```

Docker Desktop must be running. This creates project `sefaria-lemma-eval`, an
ES 8.8.0 node, a persistent Docker volume, 1 GiB heap, a 4 GiB container memory
limit, and a loopback-only port `127.0.0.1:19200`. Security is disabled only on
this local experimental instance. The image installs ICU and Sefaria's existing
v1.1.6 index/search analyzer plugins. It has no neural model plugin.
The container restarts automatically unless explicitly stopped. After a
connection-refused error, run the Compose command above and wait for readiness:

```sh
curl 'http://127.0.0.1:19200/_cluster/health?wait_for_status=yellow&timeout=30s'
```

Then retry loading; saved lemmas do not need regenerating. The limit was raised
from 3 GiB after a confirmed out-of-memory kill; further memory failures still
require checking Docker's available memory.

Stop it, retaining the index data, with:

```sh
docker compose -f research/lemmatizer/offline_search/compose.yaml stop
```

The CLI refuses remote servers, other ports, and index names outside the
`lemma-poc-` prefix. Index creation refuses existing names; nothing automatically
deletes an index or swaps an alias. If bulk loading fails, use a fresh name.
There is no deployment to cauldrons or production.

## Full run (from Sefaria-Data root)

The corpus already exists. Run this next, with tqdm progress and per-batch
checkpoints:

```sh
research/lemmatizer/.venv/bin/python -B research/lemmatizer/src/lemmatize_search_corpus.py \
  --input research/lemmatizer/datasets/search_tanakh_rashi_v1 \
  --output research/lemmatizer/datasets/search_lemmas_v1
```

Repeat with `--resume` if interrupted. Use a new output directory for changed
code/models/device/batch size. Default device is Apple MPS. Add `--limit 64` for
a small run, then resume without the limit to extend it. Saved JSONL is exported
on orderly exit; SQLite holds completed batches if a process is killed.

When full lemmatization completes:

```sh
research/lemmatizer/.venv/bin/python -B research/lemmatizer/src/offline_search.py \
  --index lemma-poc-tanakh-rashi-v1 load \
  --corpus research/lemmatizer/datasets/search_tanakh_rashi_v1 \
  --lemmas research/lemmatizer/datasets/search_lemmas_v1
```

Incomplete annotations are refused unless explicitly using `--allow-partial` for
a smoke index. Both baseline and enhanced then use that SAME selected subset.

Provide queries as JSONL, each with a unique `query_id` and nonempty `query`:

```json
{"query_id":"q001","query":"בני ישראל"}
```

```sh
research/lemmatizer/.venv/bin/python -B research/lemmatizer/src/offline_search.py \
  --index lemma-poc-tanakh-rashi-v1 compare \
  --queries research/lemmatizer/configs/search_smoke_queries.jsonl \
  --output research/lemmatizer/datasets/search_comparison_v1 \
  --weight 1 --depth 50
```

Replace the smoke query file with representative real queries before evaluating
quality. Weight 1 is an untuned starting value. Split query sets before tuning;
use held-out queries for the final comparison. Query lemmas are computed once,
then reused for both modes. Saved runs include exact Elasticsearch request bodies,
ranked document IDs, scores, refs, versions, original cleaned text and timings.
JSON files remain under ignored datasets directories.

## Relevance judgments and scoring

`judgments.jsonl` is the deduplicated union of the two result lists, deterministically
scrambled without mode/rank labels. Fill `relevance` with 0 (irrelevant),
1 (marginal), 2 (relevant), or 3 (highly relevant). Keep null when unjudged.
Decide the intended meaning of each query before judging; grade documents without
consulting which model retrieved them. No LLM labels are supplied automatically.

```sh
research/lemmatizer/.venv/bin/python -B research/lemmatizer/src/score_search_runs.py \
  --runs research/lemmatizer/datasets/search_comparison_v1/runs.jsonl \
  --judgments research/lemmatizer/datasets/search_comparison_v1/judgments.jsonl \
  --output research/lemmatizer/datasets/search_comparison_v1/scores.json
```

Reports P@10 (grades >0 count relevant), graded nDCG@10, and recall of known
positives within the retrieved depth. nDCG's ideal and recall's denominator use
the judged pool, not exhaustive library relevance. Queries with unjudged returned
top-ten documents do not get P@10/nDCG scores. No judgments means no quality
scores. Aggregate comparisons use identical eligible queries. Query bootstrap
intervals remain a later step once we have real judgments.

## Token/phrase contract

- Shared normalization uses the existing `unpointed-v1` policy. No additional
  root or synonym folding. Document lemmas are indexed with whitespace analysis;
  the old Hebrew stemmer does not process lemmas again.
- Tokens are Unicode word sequences, retaining internal ASCII quote marks in
  acronyms. Hyphens/punctuation delimit words. This tokenization is a new-field
  policy, not a claim of exact equivalence to Lucene's StandardTokenizer.
- Shoshan receives explicit positions, including repeated spellings. Whole-token
  nonoverlapping context chunks must fit its actual 160-token budget. The full
  model is loaded once and targets sharing context reuse an encoder pass.
- Each source token contributes one indexed term. Empty/multiword predictions,
  non-Hebrew tokens and over-budget tokens retain their normalized surface form;
  status and reason are recorded. No blank tokens or dropped word positions.
- Baseline and lemma clauses both use phrase matching with shared `--slop`
  (default 10, matching ordinary frontend search; use 0 for strict phrases). A short query
  may be disambiguated differently from the same word in passage context.
- Original-to-normalized token offsets are stored. The POC exports original
  snippets without neural highlights: native ES offsets in a lemma string must
  not be presented as original-text offsets.
- Baseline uses the inspected application query, pagesheetrank and plugin release,
  but subset term statistics and a deterministic doc-ID tie break differ from
  production. Document versions are fixed by our agreed one-version policy.

## Re-exporting corpus

Only needed for a new snapshot; this reads local Mongo using the Sefaria runtime:

```sh
/Users/yon/.pyenv/versions/sefaria-3.12.9/bin/python -B research/lemmatizer/src/export_search_corpus.py \
  --output research/lemmatizer/datasets/search_tanakh_rashi_NEW
```

The exporter fails if a work lacks a primary Hebrew version and records all
selected versions. It does not modify Mongo or Elasticsearch.

## Mishnah extension (2026-10-06)

The expanded snapshot `datasets/search_tanakh_rashi_mishnah_v1` contains 55,589
passages: the original 51,431 unchanged Tanakh/Rashi documents plus 4,158 Mishnah
passages across all 63 tractates. Each added tractate uses one automatically
selected primary Hebrew version, without segment fallback. The original snapshot
and index remain available for reproducing prior runs.

Reproduce the extension with `export_search_corpus.py --include-mishnah --extend
<original-corpus> --output <new-corpus>`. The original rows and version selections
are preserved, and the prior manifest is embedded for provenance.
`seed_search_extension.py` verifies every original document is unchanged and its
annotations are complete, then creates a new checkpoint. The source model/runtime
identity is retained; ordinary resume checks enforce it. Existing annotations
are copied, not recomputed. This checkpoint has already been prepared locally.

Process only the added passages:

```sh
research/lemmatizer/.venv/bin/python -B research/lemmatizer/src/lemmatize_search_corpus.py \
  --input research/lemmatizer/datasets/search_tanakh_rashi_mishnah_v1 \
  --output research/lemmatizer/datasets/search_lemmas_mishnah_v1 \
  --resume
```

Then create a new comparison index with all three collections:

```sh
research/lemmatizer/.venv/bin/python -B research/lemmatizer/src/offline_search.py \
  --index lemma-poc-tanakh-rashi-mishnah-v1 load \
  --corpus research/lemmatizer/datasets/search_tanakh_rashi_mishnah_v1 \
  --lemmas research/lemmatizer/datasets/search_lemmas_mishnah_v1
```

Use this new index name for subsequent `compare` commands. Re-run BOTH baseline
and enhanced retrieval: adding Mishnah changes the candidate pool and index term
statistics. Old result rankings and judgment pools are not the new evaluation.

Correction (2026-10-06): prior POC runs used slop 0 and were stricter than ordinary
frontend search, which requests 10. New runs record `slop` in their manifest.
Saved prior results are unchanged. Lemma weight 0 now removes the lemma clause
entirely, preserving both baseline candidates and scores.
