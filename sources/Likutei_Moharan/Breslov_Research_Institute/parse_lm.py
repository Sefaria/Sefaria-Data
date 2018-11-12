# encoding=utf-8

"""
The data files for this project contain data which is under copyright and could not be shared to github.
For more details, please contact the developers.
The data from this project which has been uploaded to Sefaria  is released under CC-BY-NC


Parsing tips:
Run this regex to simplify the classes:
u'\s?(Para|Char)Override-\d{1,2}'

LME = Likutei Moharan English
LMH = Likutei Moharan Hebrew
LMN = Likutei Moharan Note

LME-FootRef -> These are the references to the footnotes. We want to decompose these.

LMH-styles_LMH-title -> This identifies a new chapter in Hebrew

Each <p> tag will be it's own segment. Use the `LMH-section--` classes to identify the section.

We are going to have to make this a depth 2 text. The split into Seifim is not consistent between the English and the
Hebrew (for example, in Siman 2, there are 6 Seifim in Hebrew but 9 in English). We are going to leave in the references
that mark a new Seif, but these will not be reflected in the structure
"""

import re
from bs4 import BeautifulSoup

