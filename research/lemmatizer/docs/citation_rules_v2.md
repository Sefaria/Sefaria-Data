# Conservative citation rules v2

The extraction script now supports three bounded extensions:

1. BDB explicit inflections immediately before the exact citation can carry
   perfect, imperfect, imperative, infinitive, participle or plural labels, with
   a closed set of person/gender/number qualifiers. A nearby correction warning
   after that citation blocks this new rule. It does not choose arbitrary nearby
   Hebrew words or infer a form from the headword.
2. When ordinary matching fails, an attached conjunction waw may be included in
   the target host word. The supplied stem's consonants and pointing must still
   match; require a pointed source form with at least two letters. No general
   prefix stripping, suffix generation, vowel stripping or fuzzy matching.
3. For Jastrow, a complete two-to-eight-word quotation immediately after the exact
   citation can identify a target if exactly one word contains vowel marks.
   Require the whole quotation's consonants to align contiguously and the target's
   supplied vowels, dagesh and shin/sin dots to agree with the text. Return only
   that word, including its written affixes. Reject ambiguous positions,
   abbreviations, ellipses, multiple pointed words and conflicting pointing.

The partial pointing of Jastrow's target is matched as a subset of the passage's
pointing; this is explicitly tagged `quote_consonants_target_pointing`. Waw
matching is tagged `conjunction_waw_pointing_preserved`. Every example retains
its exact evidence, rule version, original span, frozen text, and source version.

## Results

| Sample | v1 | v2 | Additional |
|---|---:|---:|---:|
| Original 1,000 development links | 27 | 60 | 33 |
| 1,000 fresh links | 46 | 77 | 31 |

Fresh links were selected before extraction using a new seed and excluding all
1,032 earlier sampled links. Dictionary entries and works may overlap. On the
fresh sample, no v1 acceptances were lost. New cases comprise 16 ordinary pointed
matches enabled by grammatical labels, 12 conjunction matches (some also require
new grammar labels), and 3 Jastrow quote alignments.

All 31 incremental fresh cases were reviewed contextually by the assistant with
no incorrect associations identified. This is not expert gold or proof of equal
corpus-wide precision. All 77 accepted cases passed native version retrieval,
hash and span validation. All 32 unit tests pass, including contradictory vowels,
unsupported prefixes, multiple pointed quote words, and correction warnings.

The preliminary development output `citation_rules_v2_development` contains 61
examples from before the correction-warning guard was added. It is superseded
by `citation_rules_v2_development_checked` (60). The warning case concerned
I Samuel 18:11, where BDB directs the reader to a proposed different reading.
That example is excluded by the finalized rule.

The fresh sample still strongly favors Tanakh (74/77), with two Mishnah and one
Talmud examples. Repeated occurrences remain scarce: 77 examples cover 76
dictionary-specific lemmas. Acceptance yield is not measured recall: we do not
have complete gold labels for rejected links. The next larger run can use these
rules, but the dataset remains a selected dictionary-attested benchmark subset.

Results: `datasets/citation_rules_v2_validation/REPORT.md`.
Review: `reviews/citation_rules_v2_validation/annotations.jsonl`.
