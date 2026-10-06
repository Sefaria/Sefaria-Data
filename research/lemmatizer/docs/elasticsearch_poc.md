# Elasticsearch lemma POC: feasibility and proposed design

Inspected 2026-10-05. This is a code/configuration audit, not a live cluster audit.
Sefaria-Project checkout: afdb84429b607f7b4b3c02ea49f0148884fd85e0
Infrastructure checkout: 8d1f0d9211cfff90380312c7c976bea5c25e2517
Analyzer source: Sefaria/Sefaria-ElasticSearch release v1.1.6.
No deployments, index writes, alias changes or production requests were made.

## Existing behavior

- `sefaria/search.py:put_text_mapping` maps `naive_lemmatizer` to
  `sefaria-naive-lemmatizer` at index time and
  `sefaria-naive-lemmatizer-less-prefixes` at search time. `exact` is separate.
- The configured plugin is rule-based: strips Hebrew marks, handles plural
  suffixes ים/ות with a small exception list, simplifies internal ו/י under
  length constraints, handles final letters and alternate spelling. Its
  index-time prefix list is broad; the query-time prefix list contains only ה/ו.
  It produces alternative normalized tokens, not a single contextual dictionary lemma.
- `sefaria/helper/search.py:get_query_obj` uses `match_phrase`, preserving the
  supplied slop, then category filters and the existing relevance factor
  (`pagesheetrank` in the frontend). Phrase semantics are part of the baseline.
- `TextIndexer.modify_text_in_doc` removes footnotes, HTML, parentheses and
  cantillation (not vowels at this stage). Reuse the indexed text, rather than
  rebuilding from a different preferred-version policy.
- `static/js/sefaria/search.js:isDictaQuery` enables external Dicta for non-exact
  Hebrew searches; merging can replace Elasticsearch Tanakh hits. A direct ES
  experiment must bypass this in BOTH arms. A later public-UX test must preserve
  or explicitly account for federation. ES-only results are not a replication
  of the full public-site experience.

## Recommended first experiment

Create one new isolated text index holding a frozen subset of actual ES documents.
Preserve document IDs, refs, versions, cleaned text, metadata and ranking factors.
Reproduce existing mappings/settings for the baseline fields, and add an ordinary
`shoshan_lemma` text field with a tokenizer that preserves our serialized lemma
terms. The old Hebrew plugin must not stem those lemma terms a second time.
Run two query modes over this same index: existing query; existing query OR a
boosted lemma phrase query. Set minimum_should_match=1 explicitly inside the
combined core query; retain existing filters and function_score outside it.
Keep exact-search mode unchanged. Tune weights on development queries, then
compare on separate judged queries. A subset has different term statistics
from the full production index, so report this as a subset experiment.

Compute document lemmas offline on the existing Mac and bulk-load artifacts.
The current inference runner predicts selected attested targets only; a full-text
exporter must tokenize every passage, handle long contexts, batch Shoshan targets,
preserve one output position per chosen source token and save source offsets.
Abstentions must not collapse positions; use a defined surface fallback, never a
shared BLANK token. Validate punctuation, prefixes, quotes and multiword output
before claiming equivalent phrase behavior. Lemma offsets do not directly point
into original text: preserve a mapping for highlights, or show original snippets
without claiming native ES lemma highlights are correct.

For a fixed query evaluation, precompute query lemmas too: no model-serving
infrastructure is required. For an interactive cauldron, add one persistent
Python inference service with pinned model files and a query cache. Benchmark
CPU latency and peak RAM first; there is no measured CPU serving capacity yet.
Use timeouts and baseline-only fallback on service failure. Do not load a model
per request or into every Django worker. A GPU is optional pending measurements.

## Deployment constraints

Checked-in dev and prod manifests specify ES 8.8.0, ICU and both v1.1.6 Sefaria
plugins. Dev specifies three nodes, each requesting 4 GiB RAM / 750m CPU, limited
to 4 GiB / 1 CPU, with 2 GiB JVM heap and 30 GiB disk per node. These are configured
allocations, not current availability. A small POC may share dev ES if DevOps
confirms free disk/heap and write permissions; a single-node local ES with the
same existing plugins is an alternative for offline evaluation.

The proposed new field requires no new ES plugin, ES upgrade or ES model runtime.
One isolated index suffices for both modes. Use a unique name such as
`lemma-poc-20261005`; never run a generic full reindex against shared aliases.
The inspected Helm chart supports `localSettings.ISOLATE_SEARCH_INDEXES: true`
and environment-specific names for text/sheet/entity aliases; verify the deployed
chart includes this before using it. Cauldron code alone does not isolate data.
A text-only POC loader should write only the explicit new index, without alias
swaps or unrelated sheet/entity reindexing.

Before implementation/deployment: confirm live ES version/plugin list/mappings,
read access to a frozen source index or export, free dev capacity, destination
permissions, deployment chart revision and corpus scope. Start with a bounded
Hebrew corpus including non-Tanakh texts; freeze versions actually in search.
The prior 9,044-target timing is not a full-corpus indexing estimate: every-token
inference is substantially more work. Benchmark a small batch for tokens/sec,
index size and query latency before estimating the full run.

## References

- [Pinned analyzer source](https://github.com/Sefaria/Sefaria-ElasticSearch/tree/v1.1.6)
- [ES 8.8 bool query and minimum_should_match](https://www.elastic.co/guide/en/elasticsearch/reference/8.8/query-dsl-bool-query.html)
- Local code: Sefaria-Project/sefaria/search.py, sefaria/helper/search.py,
  static/js/sefaria/search.js, static/js/sefaria/searchState.js,
  helm-chart/sefaria/templates/configmap/local-settings.yaml.
- Infrastructure manifests: dev/cluster-1/spec/elastic/resources/elastic.yml,
  prod/cluster-1/spec/elastic/resources/elastic-1b.yml.
