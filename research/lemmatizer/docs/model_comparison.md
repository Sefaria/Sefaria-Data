# Dicta, Shoshan and Stanza comparison groundwork

Checked 2026-10-05 against official documentation and inference code. This work prepares inputs and alignment helpers. All three models are now
installed and have passed a one-sentence offline Apple MPS smoke test; no dataset
evaluation or ranking has been performed. See [installation](model_installation.md). Revisions and intended settings are in
`configs/comparison.json`. Libraries are installed in the separate `research/lemmatizer/.venv` environment;
the Sefaria Python environment is unchanged.

## Preprocessing decision

Use **unpointed-v1** as the first shared input condition, with **raw-v1** available
as a separate experiment. This is our comparison policy, not a claim that all
three publishers require identical preprocessing.

- Remove Hebrew combining marks: niqqud, cantillation, dagesh, shin/sin dots,
  meteg and rafe. Do not use a broad Hebrew Unicode-range deletion: it also
  removes punctuation.
- Map maqaf to a hyphen, sof pasuq to a colon, paseq to a vertical bar, and Hebrew
  and curly quotation marks to ASCII quotes. Keep word boundaries and acronym
  punctuation. Fold Hebrew presentation forms and remove bidi display controls.
- Keep consonants, final letters, spelling, prefixes, suffixes and context.
  Do not add full spelling, infer roots, remove stopwords or strip affixes.
- Preserve editorial brackets and both ketiv/qere readings as recorded. Do not
  silently choose one. The manifest counts passages containing brackets; this is
  a diagnostic flag, not a precise ketiv/qere classifier.
- Keep the original frozen text and a boundary map into the model text. Map the
  recorded occurrence using offsets, never by searching for its first spelling.
  Removing pointing can make formerly different forms look identical.

### DictaBERT-lex

The shipped fast tokenizer explicitly applies NFD, lowercase and StripAccents.
Therefore it already removes pointing internally; external removal primarily
makes the comparison input and offset bookkeeping explicit. Its documented
`predict` returns token/lemma pairs, not character offsets. Obtain offsets from
the same fast tokenizer, merge `##` continuation pieces in the same order as the
model code, and validate correspondence to the returned token sequence. Unknown
or unalignable targets must be recorded as abstentions, not guessed positions.

Use `use_lexicon=False` for the initial baseline. The inspected current code has
an optional lexicon path with Modern-genre filtering that excludes Aramaic and
some historical forms. That is a separate experimental condition, not a neutral
cleanup step. Also, the current default output includes a top-three letter-overlap
selection function; it is not simply unconstrained argmax. Pin the revision.
`[BLANK]` is an abstention, not a cluster label.

Sources: [model card](https://huggingface.co/dicta-il/dictabert-lex),
[tokenizer](https://huggingface.co/dicta-il/dictabert-lex/blob/384e79fc97afc9070c34be5b334716873ff54795/tokenizer.json),
[inference](https://huggingface.co/dicta-il/dictabert-lex/blob/384e79fc97afc9070c34be5b334716873ff54795/BertForLexPrediction.py),
[output decoding](https://huggingface.co/dicta-il/dictabert-lex/blob/384e79fc97afc9070c34be5b334716873ff54795/BertForJointParsing.py).

### Shoshan

The source normalizes Unicode/presentation forms and quotes, preserving pointing
in surface text. Its shipped encoder tokenizer strips accents, like Dicta's.
Thus pointed input is supported in its text path; stripping it first is not a
mandatory installation requirement. Input and lemma-bank normalization differ.

Use `lemmatize` with explicit `form`, `sentence` and `start`, or validate offsets
from `annotate`. Do not use `lemma(form, sentence)` for repeated forms: without a
start offset it can locate the first occurrence. Do not pass dictionary-derived
POS. Keep default routing, leave `blank_function_words=False`, and retain the
reported prediction source and score. The retrieval score is not a calibrated
probability of correctness. Pin code AND weights: fixes to normalization and
routing change behavior without necessarily changing weights.

Sources: [README](https://github.com/ivrit/shoshan),
[normalization](https://github.com/ivrit/shoshan/blob/046a031ee5ff0b5585b9185c41e37f9e1e6e784f/src/shoshan/normalize.py),
[inference](https://github.com/ivrit/shoshan/blob/046a031ee5ff0b5585b9185c41e37f9e1e6e784f/src/shoshan/infer.py),
[shipped tokenizer](https://huggingface.co/HebArabNlpProject/shoshan/blob/c5f520f61a0de2eefa22aeff227e7daa4e979f45/model/encoder/tokenizer.json).

### Stanza

Use `tokenize,mwt,pos,lemma` for Hebrew. Its lemma processor needs the predicted
word form and POS; do not skip Hebrew multiword-token expansion or provide gold
POS. The official documentation inspected does not prescribe Hebrew niqqud
removal. Our unpointed baseline is a domain/preprocessing choice to test, not a
verified universal Stanza requirement.

Align our target to the original Stanza Token's `start_char/end_char`, then
inspect `token.words`. A written form such as בספרו can expand into multiple
words. For a single Word, take its lemma. For a split token, select its single
open-class component (NOUN/PROPN/VERB/ADJ/ADV/NUM). If zero or multiple such words
exist, abstain. Preserve all components and report projection/abstention counts.
This projection is an explicit evaluation policy and can disadvantage function
words; audit it rather than hiding it. Never choose the component closest to the
reference headword. The pure helper is `benchmark_core.stanza_lemma`.

Sources: [lemma processor](https://stanfordnlp.github.io/stanza/lemma.html),
[MWT expansion](https://stanfordnlp.github.io/stanza/mwt.html),
[token/word objects](https://stanfordnlp.github.io/stanza/data_objects.html),
[Hebrew resource packages](https://raw.githubusercontent.com/stanfordnlp/stanza-resources/main/resources_1.11.0.json).

## Context limits: check before inference

Dicta's `predict` silently truncates to its tokenizer limit (512 including special
tokens). Shoshan's inspected `encode_sentences` defaults to **160**, and pooling
can fall back to position zero when a target was truncated out. This could create
a plausible-looking prediction for the wrong context.

`benchmark_core.require_token_budget` checks the actual tokenizer without
truncation. Initially record `context_too_long` rather than run overlong passages.
Before the main comparison, implement and test common target-centered windows:
whole-word boundaries, same window for all three systems, and a fit under BOTH
BERT tokenizers after model-specific normalization. Preserve window offsets and
ensure the entire target remains. Do not truncate each model differently or use
character length as a token count. This windowing/inference step remains to be
implemented and smoke-tested with the installed models.

[Shoshan encoder source](https://github.com/ivrit/shoshan/blob/046a031ee5ff0b5585b9185c41e37f9e1e6e784f/src/shoshan/model_joint.py).

## Prepared files and evaluation contract

```sh
python -B research/lemmatizer/src/prepare_benchmark.py \
  --input research/lemmatizer/datasets/full_citations_v2/examples.jsonl \
  --output research/lemmatizer/datasets/comparison_unpointed_v2
```

Use a new output directory for each preparation. Add `--policy raw-v1` for an
unaltered comparison condition. This command needs neither models nor Mongo.

- `passages.jsonl`: unique original/model texts and original-to-model boundaries.
- `targets.jsonl`: physical target positions, with model and original offsets.
- `labels.jsonl`: reference labels, dictionaries, refs, categories and rules;
  keep this out of model inputs.
- `manifest.json`: input checksum, preprocessing policy, counts and diagnostics.
- `label_conflicts.jsonl`: 11 physical targets with competing headwords within a
  dictionary. Exclude these dictionary/target pairs from single-label clustering
  scores until adjudicated; retain the original associations for inspection.

The actual prepared dataset contains 9,062 associations, 9,044 physical targets
and 7,361 passages. There are 7,752 Tanakh, 893 Talmud, 272 Mishnah and 145 Midrash
associations. The longest normalized passage has 18,782 characters; 519 passages
contain editorial brackets. All source hashes and target spans were checked.

For each model, save one prediction row per target with `target_id`, raw lemma,
normalized `pred_cluster`, status/reason, model revision, preprocessing policy,
context window and alignment details. Retain Stanza components and Shoshan sources.
Use `label_key` only for pointing/quote normalization, never root/synonym folding.

Join predictions to labels by target ID. The implemented evaluation now uses
`evaluate_inference.py`: deduplicate physical targets within each dictionary,
exclude conflicting dictionary/target labels, then retain reference clusters
with at least two occurrences. Each abstention becomes a unique singleton;
all models are scored on identical reference-selected cohorts. Report B³ and
pairwise scores with coverage. A second subset requires multiple unpointed
surface spellings. Do not merge entries across dictionaries. Groups are scored
together within each dictionary, so false merges count.

Categories alone do not reliably identify Hebrew versus Aramaic. These scores
reflect the conservatively extracted data rather than the library population.

## Current status

Full inference and repeated-cluster evaluation have completed. See the
[inference and evaluation guide](inference.md) for commands and outputs.
Bootstrap uncertainty estimates and CPU/MPS parity checks remain outstanding.
