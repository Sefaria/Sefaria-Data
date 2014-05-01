Sefaria-Data
============

Structured Jewish texts with free public licenses.

This repo contains texts, bibliographical information and lists of intertextual connections created by the [Sefaria Project](http://www.sefaria.org).

A MongoDB dump of Sefaria's database is available for download [via Dropbox](https://www.dropbox.com/sh/z5xdi4b7725ems5/AI4Jyg0xcY). Download this folder and use [`mongorestore`] (http://docs.mongodb.org/v2.2/reference/mongorestore/) to load into your local DB.

From the parent of the downloaded `dump` folder, run:

    mongorestore --drop

This will create (or overwrite) a mongo database called `sefaria`.

For Sefaria source code see [Sefaria-Project](https://github.com/blockspeiser/Sefaria-Project).

### Contents

* `json/` - simple json output (coming soon)
*  `xml/` - simple xml output (coming soon)
*  `misc/` - misc small data files about texts
*  `sources/` - original digital files that were manipulated to producde our data, along with scripts used in parsing.

