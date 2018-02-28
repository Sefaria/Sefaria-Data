# -*- coding: utf-8 -*-

import requests, codecs, json
from bs4 import BeautifulSoup
from sefaria.model import *
import regex as re
from sources.functions import post_link
from data_utilities.util import getGematria, numToHeb,isGematria

def scrape_wiki():
    url = u"https://he.wikipedia.org/wiki/%D7%9E%D7%A0%D7%99%D7%99%D7%9F_%D7%94%D7%9E%D7%A6%D7%95%D7%95%D7%AA_%D7%A2%D7%9C_%D7%A4%D7%99_%D7%A1%D7%A4%D7%A8_%D7%94%D7%97%D7%99%D7%A0%D7%95%D7%9A"

    page = requests.get(url)
    soup_body = BeautifulSoup(page.text, "lxml")
    tables = soup_body.select(".mw-parser-output > table")

    pairs = []
    links = []

    for table in tables:
        table_tr = table.select("tr")
        for col in table_tr:
            pairs.append((col.contents[1].text.strip(), re.sub(u'</?td>', u'', col.contents[-1].text).strip()))

    for pair in pairs:
        if re.search(u'ספר|מספר', pair[0]):
            continue
        neg_pos = u"Negative Mitzvot" if re.search(u"לאו", pair[1]) else u'Positive Mitzvot'
        rambam = getGematria(re.sub(u'עשה|לאו', u'', pair[1]).strip())
        chinukh = getGematria(pair[0])
        print chinukh, rambam
        chinukh_simanlen = len(Ref(u'Sefer HaChinukh.{}'.format(chinukh)).all_segment_refs())
        print neg_pos
        link = ({"refs": [
            u'Sefer HaChinukh.{}.{}-{}'.format(chinukh, 1, chinukh_simanlen),
            u'Mishneh Torah, {}.{}'.format(neg_pos, rambam)
        ],
            "type": "Sifrei Mitzvot",
            "auto": True,
            "generated_by": "chinukh_rambam_sfm_linker"  # _sfm_linker what is this parametor intended to be?
        })
        print link['refs']
        links.append(link)
    return links

def scrape_daat():

    url = u"http://www.daat.ac.il/daat/mitsvot/tavla.asp"

    r = requests.get(url)
    soup_body = BeautifulSoup(r.content, "lxml")

    tables = soup_body.select("table")#("div > p")#("tr td > h2")

    rows = tables[1].find_all(border="1")[0].select("tr") # 616 first is the headers and two last aren't in Chinukh

    chinukh_smk = []
    for i, row in enumerate(rows):
        if not i:
            continue
        citation_column = rows[i].select("td")
        if re.search(u"\u05e8\u05d1\u05d9 \u05d9\u05e6\u05d7\u05e7 \u05de\u05e7\u05d5\u05e8\u05d1\u05d9\u05dc",citation_column[-1].text):
            smk_lst = re.findall(u'''\u05e8\u05d1\u05d9 \u05d9\u05e6\u05d7\u05e7 \u05de\u05e7\u05d5\u05e8\u05d1\u05d9\u05dc, \u05e1\u05e4\u05e8 \u05de\u05e6\u05d5\u05d5\u05ea \u05e7\u05d8\u05df(.*)''',citation_column[-1].text)
            # if len(smk_lst)<2:
            #     smk_lst = smk_lst[0]
            chinukh_smk.append((i, smk_lst[-1]))

    links = []
    for pair in chinukh_smk:
        siman_chinukh = pair[0]
        siman_smk = pair[1]
        siman_smk_exctractor(siman_smk)
        print siman_chinukh, siman_smk
        # chinukh_simanlen = len(Ref(u'Sefer HaChinukh.{}'.format(siman_chinukh)).all_segment_refs())
        # link = ({"refs": [
        #     u'Sefer HaChinukh.{}.{}-{}'.format(siman_chinukh, 1, chinukh_simanlen),
        #     u'Sefer Mitzvot Katan.{}'.format(siman_smk)
        # ],
        #     "type": "Sifrei Mitzvot",
        #     "auto": True,
        #     "generated_by": "chinukh_rambam_sfm_linker"  # _sfm_linker what is this parametor intended to be?
        # })
        # print link['refs']
        # links.append(link)
def siman_smk_exctractor(smk_text):
    # smk_text = re.sub(u'סימן', u'', smk_text)
    split = re.split(u'\s', smk_text)
    for word in split:
        if word == u'סימן':
            continue
        word = re.sub(u"[;.,]", u"", word)
        # if isGematria(word):
        smk_siman = getGematria(word)
        print smk_text, smk_siman



    pass

if __name__ == "__main__":
    # rambam_chinukh_lnks = scrape_wiki()
    # post_link(rambam_chinukh_lnks, VERBOSE=True)
    scrape_daat()


