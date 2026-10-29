# Terminal vowel corrections

This dataset contributes audited missing final holam (U+05B9) and shuruk (U+05BC) marks in specific Hebrew text versions. It accompanies the raw ToratEmet siddur corrections in [Sefaria-Data #192](https://github.com/Sefaria/Sefaria-Data/pull/192), related to [#191](https://github.com/Sefaria/Sefaria-Data/issues/191).

`corrections.json` contains 569 vowel insertions across 289 version-specific references:

| Version | Insertions |
| --- | ---: |
| Daat Siddur Ashkenaz | 489 |
| Torat Emet 357, Edot HaMizrach | 34 |
| Torat Emet 357, Sefard | 42 |
| The Metsudah siddur, 1981, Sefard | 1 |
| Tanach with Ta'amei Hamikra | 3 |

Each record identifies the Hebrew reference and version title, a SHA-256 fingerprint of the original HTML string encoded as UTF-8, and explicit vowel insertions with the affected word before and after. Sources, edition licenses, and attribution are included in the dataset. Prayer records were matched exactly against the named version's Sefaria export downloaded on October 29, 2026. The three Tanakh verses were additionally checked against that version in the live text API on the same date: Zechariah 14:3, Job 11:3, and Ecclesiastes 2:23.

## Applying a record

Load only the named Hebrew version and verify `sourceTextSha256` before making any changes. If the fingerprint differs, review the current segment instead of applying stale offsets. An insertion's `offset` counts Unicode scalar values in the original decoded HTML string, matching Python 3 string indexing. Insert the given `character` at that offset, processing insertions in descending offset order. The preceding character is always the final vav. No existing character, HTML tag, vowel, or cantillation mark is replaced or normalized.

`wordBefore` and `wordAfter` make each change reviewable. These are exact audited occurrences, not a rule to add vowels to every final vav. Consonantal endings such as Esau, Aramaic *milgav*, and *lav* remain unchanged. Wholly unpointed words and unrelated internal vowel omissions are outside this dataset.

The dataset excludes eleven `מִמְּקומו` occurrences already addressed by the earlier correction report; that earlier change supplies both missing holams. Generated cantillation overlays duplicate underlying prayer occurrences and are also excluded.

## Raw ToratEmet inputs

The same bounded vocabulary also matches 92 missing terminal vowels in the raw files under `sources/ToratEmet/Books_363/150_תפילות וסגולות`: 34 in `0001_sidur.txt` and 58 in `0002_sidur2.txt`. Those files are patched directly in this PR. Their Windows-1255 encoding, CRLF line endings, source metadata, markup, and boundary whitespace are preserved. The raw files contain additional repetitions and sections beyond the version segments used in the audit; the 92 raw insertions and 569 dataset insertions overlap and must not be added together as a count of distinct library corrections.

The raw files are repository inputs, while the JSON describes version-specific library segments. Applying either requires Sefaria's normal editorial and ingestion review; this contribution does not upload or modify the live library.
