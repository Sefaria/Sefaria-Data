Sefaria-Data
============

Structured Jewish texts with free public licenses.

This repo contains texts, bibliographical information and lists of intertextual connections created by the [Sefaria Project](http://www.sefaria.org).

A MongoDB dump of Sefaria's database is available for download [via Dropbox](https://www.dropbox.com/sh/z5xdi4b7725ems5/AI4Jyg0xcY). Download this folder and use [`mongorestore`](http://docs.mongodb.org/v2.2/reference/mongorestore/) to load into your local DB.

From the parent of the downloaded `dump` folder, run:

    mongorestore --drop

This will create (or overwrite) a mongo database called `sefaria`.

For Sefaria source code see [Sefaria-Project](https://github.com/blockspeiser/Sefaria-Project).

### Contents

* `export/` - all files which are generated periodically through an export process from the Sefaria database
* `export/json/` - simple json output of texts
* `export/txt/` - simple plain text output of texts
* `export/xml/` - simple xml output of texts (coming soon)
* `export/links/` - CSV output of all know interconnections in texts
* `export/schemas/` - JSON files corresponding to schema information about each text
* `sources/` - original digital files that were manipulated to produce our data, along with scripts used in parsing.
* `misc/` - misc small data files about texts

Output folders are organized by category and containg seperate directories for each language. Each file is named according the version of the particular text. 

Each terminal directory also includes a file called `merged` (e.g., `merged.json` or `merged.txt`). This file uses the same logic used on the Sefaria web site to include the maximal content available. For example, we have cases in the Mishnah where no single English version is complete by itself, but the merged version will include a complete text that picks and merges from multiple sources as needed.

When we do have complete versions of texts, we will still include a merged file. In that case, the merged file will be a copy of the default complete version. This simplifies many applications - you are always guarenetted that by looking at the merged version you'll see a maximal amount of text available, with preference for the text versions we've set. 

Code for generating these outfiles can be found in our [Sefaria-Project](https://github.com/blockspeiser/Sefaria-Project) repo under [sefaria/export.py](https://github.com/blockspeiser/Sefaria-Project/blob/master/sefaria/export.py).
