# -*- coding: utf-8 -*-

import requests, codecs, json
import unicodecsv as csv
from bs4 import BeautifulSoup
from sefaria.model import *
from sefaria.system.exceptions import InputError
from sefaria.helper.link import create_link_cluster
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
        neg_pos = u"Negative Commandments" if re.search(u"לאו", pair[1]) else u'Positive Commandments'
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


def scrape_links(csvfilename, times=1):
    '''

    :param csvfilename:
    :param times: times = 1 csv will present only the resolved refs, times = 2, will present also the orignol as a row before the resolved
    :return:
    '''

    url = u"http://www.daat.ac.il/daat/mitsvot/tavla.asp"

    r = requests.get(url)
    soup_body = BeautifulSoup(r.content, "lxml")

    tables = soup_body.select("table")  # ("div > p")#("tr td > h2")

    rows = tables[1].find_all(border="1")[0].select("tr") # 616 first is the headers and two last aren't in Chinukh

    chinukh_smk = []
    links = []
    cnt_long = 0
    for i, row in enumerate(rows):
        for rnd in range(times)[::-1]:
            row_link = {}
            if not i:
                continue
            citation_column = rows[i].select("td")
            if re.search(u"\u05e8\u05d1\u05d9 \u05d9\u05e6\u05d7\u05e7 \u05de\u05e7\u05d5\u05e8\u05d1\u05d9\u05dc",citation_column[-1].text):
                smk_lst = re.findall(u'''\u05e8\u05d1\u05d9 \u05d9\u05e6\u05d7\u05e7 \u05de\u05e7\u05d5\u05e8\u05d1\u05d9\u05dc, \u05e1\u05e4\u05e8 \u05de\u05e6\u05d5\u05d5\u05ea \u05e7\u05d8\u05df(.*)''',citation_column[-1].text)
            row_link['chinukh'] = i
            row_link['smk'] = re.findall(u'''\u05e8\u05d1\u05d9 \u05d9\u05e6\u05d7\u05e7 \u05de\u05e7\u05d5\u05e8\u05d1\u05d9\u05dc, \u05e1\u05e4\u05e8 \u05de\u05e6\u05d5\u05d5\u05ea \u05e7\u05d8\u05df(.*)''',citation_column[-1].text)
            row_link['rambam'] = re.findall(u'''רמב"ם, ספר המצווו?ת(.*?)[;:.\n]''',citation_column[-1].text)
            row_link['smg'] = re.findall(u'''רבי משה מקוצי, ספר מצוות גדול(.*?)[;,:.\n]''',citation_column[-1].text)
            row_link['mishneh'] = re.findall(u'(רמב"ם הלכות.*?)(?:[;,:.\n]|ע"ש)',citation_column[-1].text)
            row_link['shulchanArukh'] = re.findall(u'שו"ע(.*?)[;:.\n]', citation_column[-1].text)
            for column in ['smk', 'rambam', 'smg', 'mishneh', 'shulchanArukh']:
                if len(row_link[column]) > 1:
                    if rnd == 1:
                        row_link[column] = u" |".join(row_link[column])
                    else:
                        row_link[column] = siman_exctractor(row_link[column], column)
                elif row_link[column]:
                    if rnd == 1:
                        row_link[column] = row_link[column][0]
                    else:
                        row_link[column] = siman_exctractor(row_link[column][0], column)
                    # row_link[column] = row_link[column][0]
            links.append(row_link)

        # chinukh_smk.append((i, smk_lst[-1]))
    print cnt_long
    with open(u'{}.csv'.format(csvfilename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, ['chinukh', 'smk', 'rambam', 'smg', 'mishneh', 'shulchanArukh']) #fieldnames = obj_list[0].keys())
        writer.writeheader()
        writer.writerows(links)

        # for pair in chinukh_smk:
        #     row_dict = {}
        #     siman_chinukh = pair[0]
        #     siman_smk = pair[1]
        #     simanai_smk = siman_smk_exctractor(siman_smk)
        #     print siman_chinukh, simanai_smk
        #     row_dict[u"chinukh"] = siman_chinukh
        #     row_dict[u"smk"] = simanai_smk
        #     writer.writerow(row_dict)


def links_chinukh_smk(filename):
        links = []
        with open(filename, 'r') as csvfile:
            file_reader = csv.DictReader(csvfile)
            for i, row in enumerate(file_reader):
                if not row:
                    continue
                chinukh_simanlen = len(Ref(u'Sefer HaChinukh.{}'.format(row["chinukh"])).all_segment_refs())
                for smki in eval(row["smk"]):
                    smk_siman_len = len(Ref(u'Sefer Mitzvot Katan.{}'.format(smki)).all_segment_refs()) if len(Ref(u'Sefer Mitzvot Katan.{}'.format(smki)).all_segment_refs()) !=0 else 1
                    link = ({"refs": [
                        u'Sefer HaChinukh.{}.{}-{}'.format(row["chinukh"], 1, chinukh_simanlen),
                        u'Sefer Mitzvot Katan.{}.{}-{}'.format(smki, 1, smk_siman_len)
                    ],
                        "type": "Sifrei Mitzvot",
                        "auto": True,
                        "generated_by": "chinukh_rambam_sfm_linker"  # _sfm_linker what is this parametor intended to be?
                    })
                    print link['refs']
                    links.append(link)
        return links


def chinukh_smg():
    cnt = 0
    dictList  = []
    for m in range(613):
        ls = LinkSet(Ref('Sefer Mitzvot Katan')).refs_from(Ref('Sefer HaChinukh {}'.format(m+1)))
        # ls = LinkSet(Ref('Sefer HaChinukh')).refs_from(Ref('Sefer Mitzvot Katan'))
        if ls:
            row = {}
            row['chimukh'] = m+1
            row['smk'] = ls
            for l in ls:
                smg_ls = LinkSet(Ref("Sefer Mitzvot Gadol")).refs_from(l.section_ref())
                row['chimukh'] = m + 1
                row['smk'] = ls
                row['smg'] = smg_ls
                print row
                dictList.append(row)
            cnt += 1
        # for link in ls:
        #     print link.refs
        #     cnt += 1
    print cnt
    toCsv('chinukh_smg', ['chimukh','smk','smg'], dictList)


def toCsv(csvfilename, headers, dictList):
    with open(u'{}.csv'.format(csvfilename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, headers) #fieldnames = obj_list[0].keys())
        writer.writeheader()
        writer.writerows(dictList)


def siman_exctractor(text, header):
    if not text:
        return
    if isinstance(text, list):
        double = []
        for t in text:
            double.append(siman_exctractor(t, header))
        return double
    text = re.sub(u"[;.,']", u"", text)
    lte = {'smk': [u'סימן', u'סעיף'], 'rambam':[u'מצוות', u'וע"ש'], 'smg':[], 'mishneh':[], 'shulchanArukh':[]}
    list_to_egnore = lte[header]
    simanim = []
    split = iter(re.split(u'\s', text))
    for word in split:
        if not word or (word in list_to_egnore):
            continue
        if header == 'rambam':
            if word == u'עשה':
                simanim.append(u'Positive Commandments')
                continue
            elif word == u"לא" and split.next() == u"תעשה":
                simanim.append(u'Negative Commandments')
                continue
        if header == 'smg':
            if word == u'עשין':
                simanim.append(u'Positive Commandments')
                continue
            elif re.search(u"לאוו?ין", word):
                simanim.append(u'Negative Commandments')
                continue
        if header in ['mishneh', 'shulchanArukh']:
            text = re.sub(u"'|,", u"", text.strip())
            while True:
                if not text:
                    return
                print text
                try:
                    ref = Ref(text)
                    print ref
                    return [ref.normal()]  # notice that this iterative logic doesn't catch refs with Vav
                except InputError:
                    split_text = re.split(u'\s', text)
                    text = u' '.join(split_text[:-1])
                    print '***'
        if re.search(u'-', word):
            borders = re.search(u"(.*?)-(.*)", word)
            start = getGematria(borders.group(1))
            end = getGematria(borders.group(2))
            for siman in range(start, end + 1):
                simanim.append(siman)
        if not is_hebrew_number(word):
            if not check_vav(word):
                # print smk_text, simanim
                return simanim
            else:
                simanim.append(check_vav(word))
                simanim.append(simanim)
        else:
            # if header == u'rambam':
            #     simanim.append(getGematria(word))
            #     simanim.append(simanim)
            # else:
            simanim.append(getGematria(word))
    # print smk_text, simanim
    return simanim


def siman_smk_exctractor(smk_text):

    split = re.split(u'\s', smk_text)
    simanim = []
    for word in split:
        if not word or word == u'סימן' or word == u'סעיף':
            continue
        word = re.sub(u"[;.,']", u"", word)
        if re.search(u'-', word):
            borders = re.search(u"(.*?)-(.*)", word)
            start = getGematria(borders.group(1))
            end = getGematria(borders.group(2))
            for siman in range(start, end+1):
                simanim.append(siman)
        if not is_hebrew_number(word):
            if not check_vav(word):
                # print smk_text, simanim
                return simanim
            else:
                simanim.append(check_vav(word))
        else:
            smk_siman = getGematria(word)
            simanim.append(smk_siman)
    # print smk_text, simanim
    return simanim


def check_vav(st):
    if not st:
        return False
    if st[0] == u'ו':
        if is_hebrew_number(st[1:]):
            return getGematria(st[1:])
        else:
            return False
    return False


def is_hebrew_number(st):
    matches = re.findall(hebrew_number_regex(), st)
    if len(matches) == 0:
        return False
    return matches[0] == st


def hebrew_number_regex():
    """
    Regular expression component to capture a number expressed in Hebrew letters
    :return string:
    \p{Hebrew} ~= [\u05d0–\u05ea]
    """
    rx = ur"""                                    # 1 of 3 styles:
    ((?=[\u05d0-\u05ea]+(?:"|\u05f4|'')[\u05d0-\u05ea])    # (1: ") Lookahead:  At least one letter, followed by double-quote, two single quotes, or gershayim, followed by  one letter
            \u05ea*(?:"|\u05f4|'')?                    # Many Tavs (400), maybe dbl quote
            [\u05e7-\u05ea]?(?:"|\u05f4|'')?        # One or zero kuf-tav (100-400), maybe dbl quote
            [\u05d8-\u05e6]?(?:"|\u05f4|'')?        # One or zero tet-tzaddi (9-90), maybe dbl quote
            [\u05d0-\u05d8]?                        # One or zero alef-tet (1-9)                                                            #
        |[\u05d0-\u05ea]['\u05f3]                    # (2: ') single letter, followed by a single quote or geresh
        |(?=[\u05d0-\u05ea])                        # (3: no punc) Lookahead: at least one Hebrew letter
            \u05ea*                                    # Many Tavs (400)
            [\u05e7-\u05ea]?                        # One or zero kuf-tav (100-400)
            [\u05d8-\u05e6]?                        # One or zero tet-tzaddi (9-90)
            [\u05d0-\u05d8]?                        # One or zero alef-tet (1-9)
    )"""

    return re.compile(rx, re.VERBOSE)

def refs_csv(csvlinkfile):
    sets_by_chinukh = []
    clusters = []
    link_node_cnt = 0
    with open(u'{}'.format(csvlinkfile), 'r') as csvfile:
        seg_reader = csv.DictReader(csvfile)
        for row in seg_reader:
            set_cnt = 0
            mitzvah_set = []
            mitzvah_set.append(Ref(u'Sefer HaChinukh.{}'.format(row[u'chinukh'])))
            if eval(row[u'smk']):
                for smki in eval(row[u'smk']):
                    if smki:
                        mitzvah_set.append(Ref(u'Sefer Mitzvot Katan, Remazim.{}'.format(smki)))
            rambam = eval(row[u'rambam'])
            if rambam:
                if not isinstance(rambam[0], list):
                    try:
                        mitzvah_set.append(Ref(u'Sefer HaMitzvot, {}.{}'.format(rambam[0].strip(), rambam[1])))
                    except IndexError:
                        print u'*problem {} in siman {} *'.format(rambam, row[u'chinukh'])
                else:
                    for ram in rambam:
                        if ram:
                            mitzvah_set.append(Ref(u'Sefer HaMitzvot, {}.{}'.format(ram[0].strip(), ram[1])))
            smg = eval(row[u'smg'])
            if smg:
                if isinstance(smg[0], list):
                    for smgi in smg:
                        if smgi:
                            mitzvah_set.append(Ref(u'Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smgi[0], smgi[1])))
                elif isinstance(smg[0], unicode):
                    try:
                        mitzvah_set.append(Ref(u'Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smg[0].strip(), smg[1])))
                    except IndexError:
                        print u'*problem {} in siman {} *'.format(smg, row[u'chinukh'])
            mishneh = row[u'mishneh']
            if mishneh:
                mishneh = eval(row[u'mishneh'])
                if len(mishneh) == 1:
                    mitzvah_set.append(Ref(mishneh[0]))
                else:
                    for mish in mishneh:
                        if mish:
                            mitzvah_set.append(Ref(mish[0]))
            sa = row[u'shulchanArukh']
            if sa:
                sa = eval(row[u'shulchanArukh'])
                if len(sa) == 1:
                    mitzvah_set.append(Ref(sa[0]))
                else:
                    for sai in sa:
                        if sai:
                            mitzvah_set.append(Ref(sai[0]))
            sets_by_chinukh.append(mitzvah_set)
            mitzvah_cluster = create_link_cluster(mitzvah_set, 30044, link_type="Sifrei Mitzvot", attrs={"generated_by": "viascraped_chinukh_sfm_linker", "auto": True})
            clusters.append(mitzvah_cluster)

    return sets_by_chinukh, clusters

def links_from_csv(csvlinkfile):
    # with open(u'{}'.format(csvlinkfile), 'r') as csvfile:
    #     seg_reader = csv.DictReader(csvfile)
    #     headers = seg_reader.fieldnames
    #     for row in seg_reader:
    #         for column in headers:
    #             if isinstance(row[column], list):
    #                 for r in


    return

def link_sfrMitzvot_shortCounting():
    links = []
    # Negative Commandments
    pos_sefer_mitzvot = Ref(u'Sefer HaMitzvot, Positive Commandments').all_segment_refs()
    for m, sefer_ref in enumerate(pos_sefer_mitzvot):
        mitzva_len =len(sefer_ref.all_segment_refs())
        link = ({"refs": [
            u'Mishneh Torah, Positive Commandments.{}'.format(m+1),
            u'Sefer HaMitzvot, Positive Commandments.{}.1-{}'.format(m+1, mitzva_len)
        ],
            "type": "Sifrei Mitzvot",
            "auto": True,
            "generated_by": "sfrrambam_shortcount_sfm_linker"
        })
        links.append(link)

    # Negative Mitzvot
    neg_sefer_mitzvot = Ref(u'Sefer HaMitzvot, Negative Commandments').all_segment_refs()
    for m, sefer_ref in enumerate(neg_sefer_mitzvot):
        mitzva_len =len(sefer_ref.all_segment_refs())
        link = ({"refs": [
            u'Mishneh Torah, Negative Commandments.{}'.format(m+1),
            u'Sefer HaMitzvot, Negative Commandments.{}.1-{}'.format(m+1, mitzva_len)
        ],
            "type": "Sifrei Mitzvot",
            "auto": True,
            "generated_by": "sfrrambam_shortcount_sfm_linker"
        })
        links.append(link)

    return links

if __name__ == "__main__":
    # rambam_chinukh_lnks = scrape_wiki()
    # post_link(rambam_chinukh_lnks, VERBOSE=True)
    # # scrape_links(u"siman_numbers")
    # links_ch_smk = links_chinukh_smk(u"smk_chinukh.csv")
    # post_link(links_ch_smk, VERBOSE=True)
    # chinukh_smg()
    # post_link(link_sfrMitzvot_shortCounting(), VERBOSE=True)
    # scrape_links(u'mitzvot_H_data_only_links', times=1)
    refs_csv(u'mitzvot_H_data_only_links.csv')

