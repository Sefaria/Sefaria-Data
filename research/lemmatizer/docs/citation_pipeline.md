# Citation extraction and record schema

1. Select seeded dictionary–corpus links, with a separate quota per dictionary.
   Dictionary–dictionary links are excluded. This is link sampling, not uniform
   lemma sampling; dictionary-balanced rates are not corpus-weighted rates.
2. Retrieve the dictionary entry and its citation evidence. Require a supported
   explicit form or bounded quotation rule; see [rules](citation_rules_v2.md).
3. Resolve target segments (default cap: 100). Automatically rank Hebrew versions
   by `isPrimary`, then priority and ID. Hebrew identification uses
   `languageFamilyName`, falling back to `actualLanguage`. Fall back to another
   ranked version only for a missing/empty segment, never to rescue a failed match.
4. Convert HTML to frozen plain text, retain normalization-to-original offsets,
   and require a unique position with the rule's pointing/boundary constraints.
   Skip missing text, conflicting pointing, ambiguity and unsupported evidence.
5. Save every attempt and reason plus accepted examples, version selections,
   source snapshots and a manifest. Validate native text, hashes and spans
   separately. Structural validation is not semantic adjudication.

## Accepted example

| Fields | Meaning |
|---|---|
| `example_id`, `entry_key` | Stable derived identifiers; entry key is dictionary plus exact headword, not a universal lexeme ID |
| `entry_identity_policy`, `entry_snapshot`, `headword`, `dictionary` | Exact identity policy and dictionary provenance; snapshot does not retain entry Mongo ID |
| `dictionary_ref`, `link_id`, `link_snapshot`, `source_ref` | Dictionary citation and original linked target, potentially a range |
| `segment_ref`, `passage_id` | Actual matched segment and frozen passage identifier |
| `version_id`, `version_title`, `is_fallback` | Chosen source version and fallback status; further selection metadata is saved separately |
| `text`, `text_sha256` | Frozen plain text and its hash |
| `start_char`, `end_char`, `surface` | Python Unicode code-point offsets, end exclusive; `text[start_char:end_char] == surface` |
| `evidence`, `supporting_evidence` | Rule, printed form, definition path, original HTML and citation evidence |
| `match_method`, `rule_version`, `acceptance` | Normalization/matching method and acceptance provenance |
| `expert_verified` | False for current automatic outputs |

Offsets are valid against the frozen text, not arbitrary current text or raw HTML.
On retrieval, verify the text hash before using them. Re-extract changed passages;
do not silently shift offsets. The committed reference index omits full text,
entry/link snapshots and full evidence; local `examples.jsonl` retains them.

Dictionary-specific labels remain separate across dictionaries. Homographs,
senses and duplicated dictionary entries need further identity work before a
clustering benchmark. Unsupported or rejected links are not negative labels.
