# encoding=utf-8

"""
Run pull_files.py to get the webpages locally.

Parsing strategy:
Start by extracting each siman so that we have a list of Siman instances. Each Siman instance will be should be able
to tell us where it belongs.

We need to be able to extract only the Malbim text from a Siman. We'll also need to configure footnotes.

Let's say that each Siman is composed of:
1) h2 Siman header
2) Base verse
3) Sifra Quote
4) Malbim text
5) footnotes

Find the h2 header with סימן written in it
The Base verse should be the next sibling. An <a> tag should be inside with a base ref.
The next element should contain a link to Sifra
The Sifra text will be the next sibling. It should be a <div style="font-weight:bold">

We should then hit a series of p, dl, ul elements which contain the main text.
An h3 indicates we've hit footnotes. At the footnotes, each p is a new footnote.

Anything else should mean stop. We'll want to keep track of all our "stop" conditions.

Footnotes: contain links which map markers to text. We can use that mapping.

Let's implement a builder class. We can feed it a Siman element and let it go from there. We'll have a second method
with the responsibility of identifying Simanim within a document.

We'll defer the text formatting to the Siman class
"""

import re
import codecs
import random
from bs4 import BeautifulSoup


def extract_simanim(filename):
    with codecs.open(filename, 'r', 'utf-8') as fp:
        soup = BeautifulSoup(fp, 'lxml')
    return [siman for siman in soup.find_all('h2') if re.match(u'^\u05e1\u05d9\u05de\u05df', siman.text)]


class SimanBuilder(object):

    def __init__(self, siman_header):
        pass

    def get_siman_num(self):
        pass

    def get_base_ref(self):
        pass

    def get_sifra_ref(self):
        pass

    def get_main_text(self):
        pass

    def get_footnotes(self):
        pass


class Siman(object):
    def __init__(self, siman_num, base_ref, sifra_ref, main_text, footnotes):
        self.siman_num = siman_num
        self.base_ref = base_ref
        self.sifra_ref = sifra_ref
        self.main_text_raw = main_text
        self.footnotes = footnotes
        self.formated_text = self._format_text()

    def _format_text(self):
        return self.main_text_raw
