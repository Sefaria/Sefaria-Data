# Research state (2026-10-04)

## Why dictionary links

WordForms contain surface forms, possible dictionary lookups and refs, rather than
contextually adjudicated occurrence labels. In an independent WordForm review,
262 proposed associations included 132 correct, 93 incorrect and 37 uncertain;
53 additional cases had no proposal. Finding a surface span did not establish
which lookup was correct. Dictionary citation links provide more direct evidence,
but still require explicit form extraction and contextual alignment.

The local inventory contained 353,420 dictionary-prefix links: 106,663 between
dictionaries and 246,757 dictionary–corpus candidates (BDB 135,710; BDB Aramaic
3,651; Jastrow 104,751; Klein 2,645). These are candidates, not verified examples.

## Current results

| Run | Accepted | Interpretation |
|---|---:|---|
| 1,000 development links, v1 → v2 | 27 → 60 | Same links used for rule development |
| 1,000 fresh links, v1 → v2 | 46 → 77 | Earlier 1,032 link IDs excluded; entries/works may overlap |
| All 1,885 links for 132 previously recovered entries | 314 | Success-conditioned density probe |

All 31 incremental fresh cases were reviewed by the assistant with no errors
identified; all 77 fresh accepted cases passed native-text/hash/span validation.
These are provisional reviews, not independent expert gold. The fresh sample
contains 74 Tanakh, two Mishnah and one Talmud examples, showing substantial
selection bias. Acceptance yield is not measured recall.

The density probe has 58 entries with at least two examples (240 examples),
35 with at least three (194 examples), and 16 with at least five. There are 49
entries with multiple unpointed forms. The remaining 74 entries are singletons.
Additional density examples have not all been contextually reviewed. See the
committed [summary](../results/density_summary.json) and
[occurrence index](../results/occurrence_refs.jsonl). These counts are not a
full-corpus projection: the cohort was selected for prior extraction success.

The 1,000-link runs took about 25–44 seconds locally; the density probe about
21 seconds. Those warm, small runs do not establish full-run runtime. The subsequent full run processed all 246,757 candidates and recovered 9,062
occurrences across 3,901 entries (1,599 with at least two occurrences; 929 with
at least three). The user-reported extraction/export time was 210.5 seconds,
plus inventory and initialization. Full-run semantic precision is not yet measured.

## Local model experiment

DictaLM 3.0 24B Thinking Q4_K_M ran through Ollama on an M3 Max with 36 GiB RAM,
using the Apple GPU (full GPU offload at 8,192 context). Five development cases
took about 7.8 minutes and produced 3/5 span agreement, the same as Llama 3.1 on
those five cases. Errors included over-selection and malformed output.

One case had empty citation context due to an input-builder bug, and another
failed literal HTML-evidence validation despite correct token selection. These
confounds and the tiny sample prevent a reliable model ranking or a conclusion
that local LLMs cannot help. Predictions are not accepted labels. The import
recipe/checksum are retained under `configs/`; download the official GGUF beside
the Modelfile before importing. Model weights and generated responses stay local.

## Next decisions

Use a larger deterministic run to measure usable cluster sizes and dictionary/work
coverage before evaluating lemmatizers. Report results by source, match rule and
frequency; retain skipped outcomes. A conservative subset can support a scoped
benchmark but should not be presented as representative of the whole library.

No logistic regression is trained. Alignment features alone may not resolve
semantic dictionary ambiguity. A learned confidence model would need reliable
positive and negative contextual labels, held-out entries/works, and calibration.
Do not label all skipped cases negative or use assistant confidence as ground truth.
Cluster scoring should be label-invariant, penalize erroneous merges as well as
splits, and avoid treating abstentions as a single predicted lemma. Cross-dictionary
lexeme reconciliation remains unresolved.

## Source provenance

Inspected repositories: Sefaria-Data `c3cba315dc4f4ba25c5f10bb1201094f1424ac04`,
Sefaria-Project `afdb84429b607f7b4b3c02ea49f0148884fd85e0`, and sefaria-wiki
`8a9875b84d21132e214cc8f76b267ba5fb7ff9aa`. Relevant implementation includes
Project `sefaria/model/lexicon.py`, `text.py`, `link.py`, and Data
`sources/bdb/index.py` and `sources/bdb/word_forms.py`. BDB citation links are
created from rendered dictionary citation anchors separately from WordForms.

Full source texts, historical manifests, per-case reviews and superseded notes
remain in ignored local directories. Git contains the concise state and references,
not a portable backup of that evidence. Preserve those directories separately if
exact historical reproduction is required.
