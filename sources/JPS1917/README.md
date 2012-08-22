This directory contains scripts used to parse a digital copy of the 1917 JPS Tanakh obtained from [OpenSiddur.org](http://opensiddur.org/2010/08/%D7%AA%D7%A0%D7%B4%D7%9A-the-holy-scriptures-a-new-translation-jps-1917/)

This work is released with [CC0 license](http://creativecommons.org/publicdomain/zero/1.0/).

#### Overview of Method

Parsing began with the raw text output from OpenSiddur which was processed using regular expressions in Python to find book, chapter and verse divisions, pagebreaks and footnotes, paragraph breaks and verse laid out poetically.

The text was first transformed into a simple version of (USFM)[http://paratext.ubs-translations.org/about/usfm]. The text was checked for inconsistencies against a copy of [Machon Mamre's digital JPS 1917 text](http://www.mechon-mamre.org/e/et/et0.htm). Machon Mamre's text is not included in this repo, as they claim a copyright on it.  

Using these tests the regular expression were updated and manual changes were made to the source files in `split/` to improve accuracy. When the number of inconsistancies was low, output of `parse.py` was copied and corrected by hand against the PDF.

Finally, the USFM text was converted to JSON for use in Sefaria. This conversion ignored page breaks, paragraphs, footnotes and poetic lines, which are not currenlty supported by Sefaria. 

#### Known Issues

* There are a large number of false positives for paragraph marks for texts that use poetic layout (for example, Psalms). 
* Some page breaks are missing.
* Footnote achors are maked with the letters [abcdef] in the orginal and occur in the text without a space before the marked word (e.g., "aMoses"). These anchors were left as they apear in `usfm-footnote-anchors/` but the majority were automatically removed in `usfm/`. Since the majority of footnotes appeared on proper names beginning with capital letters, 151 of 164 anchors were found by searching for `r' [abcdef][A-Z]'`. This still leaves 13 anchors in `usfm/` and `json/`.

#### Method Details

1. `source/Tanakh1917.txt` was trimmed and split into a separted file for each book with `split.py`, storing resulting files in `split/`.
2. `parse.py` processed files in `split/` into `usfm-raw/`. Along the way several stages of the process were saved in `steps/` for debugging.
3. `count.py` and `compare.py` were used to compare the counts of verses per chapter and the first character of each chapter (respectively) against Machon Mamre's text. A number of inconsistencies were found between Machon Mamre's text and the PDF - in which case the compare values were updated to reflect the PDF.
4. Texts in `split/` were manually updated in a number of places where there were mistakes or inconsistencies in the original text that made it difficut to parse automatically. For example, first verses are generally not numbered but in some occasions they were (Exodus 18).
5. `usfm-raw/` was manually corrected to generate `usfm-footnote-markers/`.
6. 151 footnote markers were removed from `usfm-footnote-markers/` to produce `usfm/`.
7. `usfm2json.py` was used to convert `usfm/` to JSON.
8. `post.py` posted the resulting JSON to www.sefaria.org.

