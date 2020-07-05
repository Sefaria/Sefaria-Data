# -*- coding: utf-8 -*-

"""
Creates a corpus from Wikipedia dump file.
Inspired by:
https://github.com/panyang/Wikipedia_Word2vec/blob/master/v1/process_wiki.py
Source: https://www.kdnuggets.com/2017/11/building-wikipedia-text-corpus-nlp.html

Dump downloaded from https://dumps.wikimedia.org/hewiki/latest/
Dump link https://dumps.wikimedia.org/hewiki/latest/hewiki-latest-pages-articles.xml.bz2
"""

import re
from gensim.corpora import WikiCorpus


def make_corpus(wiki):
    """Convert Wikipedia xml dump file to text corpus"""
    for text in wiki.get_texts():
        text = ' '.join(text)  # unicodify text
        text = re.sub(r"[^\u05d0-\u05ea '\"״׳]", " ", text)
        text = " ".join(text.split())

        # run prefix tagger here
        yield text


if __name__ == "__main__":
    # change input filename
    wiki = WikiCorpus("/Users/nss/Downloads/hewiki-latest-pages-articles.xml.bz2")