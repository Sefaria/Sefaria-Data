# Solomon Tikkunei Zohar Parser

Author: [Nissa Mai-Rose](https://github.com/nissamai)

Documentation last updated: Jan 18, 2023

## Usage

Running `python tz_post.py` should run `post_tz()` and `post_version()` which should the parsers and post the parsed
text.

## Environment Variables
`PYTHONUNBUFFERED=1;DJANGO_SETTINGS_MODULE=sefaria.settings;PYTHONPATH=Path/To/Your/Sefaria-Project`

## Local Settings
`Sefaria-Project/sources/local_settings.py` should contain the following local settings:

```
API_KEY = """
UID = ""
SEFARIA_SERVER = ""
SEFARIA_PROJECT_PATH = ""
```


## Code Structure

### tz_base

`tz_base.py` contains the model classes that represent the text of Tikkunei HaZohar
along with various helper functions. Each word is associated with a parent Phrase,
a parent Paragraph, a parent Daf, and a parent Tikkun. Words can have 1+ Footnotes, which
encompass all the kinds of comments, including inline comments with particular symbols,
footnotes, and endnotes (see: `FootnoteType` enum).


### tz_parse

`tz_parse.py` contains the parser classes. The base class, `TzParser`, from which `DocsTzParser`,
`DocsTzParser2`, and `HtmlTzParser` are derived.

#### note on `correct_misalignment` function
There is an issue with the vol2 HTML file where on most of the pages, the first verse of English on the page is before the daf change (For example, in the structured HTML document version of the volume, the first verse on page 18b chapter is technically on page 18a), while the Hebrew 1st verse is in the correct location (on page 18b). Where the verses were then mis-aligned, I had a bug in appending hebrew text that did not correspond with English text.

The `correct_misalignment` function pops the last paragraph of each daf and places it into the next daf.

If it is desired to remove this function from other files later, it can be modified.

#### Parsing .docx files 

`DocsTzParser` parses `.docx` files using the `docx` python package, but has the limitation of
being unable to parse footnotes.

`DocsTzParser2` parses `.docx` files using the `docx2python` package but is not fully implemented.

It is likely that all the Tikkunei Zohar files will be delivered as InDesign/`.html` files, and it
will no longer be necessary to use the `.docx` parsers.


#### Parsing .html files

`HtmlTzParser` parses Tikkunei Zohar `.html` files. It has been used to successfully parse Volume 2
files delivered; however, changes may need to be made to parse future delivered files if the format
changes or if all cases are not covered by the original parser.


#### Example of running parsers
See `run_parse` function in `tz_parse.py`


### tz_post

The `post_tz` function adds the term "Tikkunei Zohar" to the database and posts the index.

The `post_version` function runs `get_mappings` function which parses the specified TZ files.
This function can be modified to run whichever parsers which will be run.

If the parsers are run with the `language="bilingual"` option, both Hebrew and English
Solomon Tikkunei Zohar Hebrew & English versions will be posted.