# -*- coding: utf-8 -*-

import django
django.setup()

import requests, codecs, json
import unicodecsv as csv
import pickle
from bs4 import BeautifulSoup
from sefaria.model import *
from sefaria.system.exceptions import InputError
from sefaria.helper.link import create_link_cluster
import regex as re
from sources.functions import post_link
from parsing_utilities.util import getGematria, numToHeb,isGematria

def scrape_wiki():
    url = "https://he.wikipedia.org/wiki/%D7%9E%D7%A0%D7%99%D7%99%D7%9F_%D7%94%D7%9E%D7%A6%D7%95%D7%95%D7%AA_%D7%A2%D7%9C_%D7%A4%D7%99_%D7%A1%D7%A4%D7%A8_%D7%94%D7%97%D7%99%D7%A0%D7%95%D7%9A"

    page = requests.get(url)
    soup_body = BeautifulSoup(page.text, "lxml")
    tables = soup_body.select(".mw-parser-output > table")

    pairs = []
    links = []
    chinukh_rambam  = {}
    for table in tables:
        table_tr = table.select("tr")
        for col in table_tr:
            pairs.append((col.contents[1].text.strip(), re.sub('</?td>', '', col.contents[-1].text).strip()))

    for pair in pairs:
        if re.search('ספר|מספר', pair[0]):
            continue
        neg_pos = "Negative" if re.search("לאו", pair[1]) else 'Positive'
        rambam = getGematria(re.sub('עשה|לאו', '', pair[1]).strip())
        chinukh = getGematria(pair[0])
        print(chinukh, rambam)
        chinukh_simanlen = len(Ref('Sefer HaChinukh.{}'.format(chinukh)).all_segment_refs())
        print(neg_pos)
        link = ({"refs": [
            'Sefer HaChinukh.{}.{}-{}'.format(chinukh, 1, chinukh_simanlen),
            'Mishneh Torah, {} Mitzvot.{}'.format(neg_pos, rambam)
        ],
            "type": "Sifrei Mitzvot",
            "auto": True,
            "generated_by": "chinukh_rambam_sfm_linker"  # _sfm_linker what is this parametor intended to be?
        })
        chinukh_rambam[chinukh]= {"rambam_wiki": [neg_pos, rambam], "rambam_url": "https://www.sefaria.org/Mishneh_Torah,_{}_Mitzvot.{}".format(neg_pos, rambam)}
        print(link['refs'])
        links.append(link)

    return links, chinukh_rambam

def get_link_data():
    '''

    :param csvfilename:
    :param times: times = 1 csv will present only the resolved refs, times = 2, will present also the orignol as a row before the resolved
    :return:
    '''

    url = "http://www.daat.ac.il/daat/mitsvot/tavla.asp"

    r = requests.get(url)
    soup_body = BeautifulSoup(r.content, "lxml")

    tables = soup_body.select("table")  # ("div > p")#("tr td > h2")

    rows = tables[1].find_all(border="1")[0].select("tr") # 616 first is the headers and two last aren't in Chinukh
    # pickling and dumping scraped rows into mitzvotHashem file
    # fi = codecs.open('mitzvotHashem', 'wb')
    with codecs.open('mitzvotHashem', 'wb', encoding='utf-8') as fi:
        for row in rows:
            fi.write(row.text)
    return rows

def text_to_csv_links(csvfilename, rows = False, times=1):
    if not rows:
        with codecs.open('mitzvotHashem', 'rb', encoding='utf-8') as fi:
            rows = fi.read()
            # the saving html page and rereading it is not quit working yet.
    _, wiki_chinukh_rambam = scrape_wiki()
    links = []
    cnt_long = 0
    for i, row in enumerate(rows):
        for rnd in range(times)[::-1]:
            row_link = {}
            if not i:
                continue
            citation_column = rows[i].select("td")
            row_link['chinukh'] = i
            row_link['smk'] = re.findall('''\u05e8\u05d1\u05d9 \u05d9\u05e6\u05d7\u05e7 \u05de\u05e7\u05d5\u05e8\u05d1\u05d9\u05dc, \u05e1\u05e4\u05e8 \u05de\u05e6\u05d5\u05d5\u05ea \u05e7\u05d8\u05df(.*)''',citation_column[-1].text)
            row_link['rambam'] = re.findall('''רמב"ם, ספר המצווו?ת(.*?)[;:.\n]''',citation_column[-1].text)
            row_link['smg'] = re.findall('''רבי משה מקוצי, ספר מצוות גדול(.*?)[;,:.\n]''',citation_column[-1].text)
            row_link['mishneh'] = re.findall('(רמב"ם הלכות.*?)(?:[;,:.\n]|ע"ש)',citation_column[-1].text)
            row_link['shulchanArukh'] = re.findall('שו"ע(.*?)[;:.\n]', citation_column[-1].text)
            row_link['pasuk'] = re.findall("((?:בראשית|שמות|ויקרא|במדבר|דברים).*?)\n", citation_column[-1].text)
            row_link['mitzvah Title chinukh'] = citation_column[1].select("h2")[0].text
            row_link['mitzvah Title Rambam'] = citation_column[-1].select("h2")[0].text
            for column in ['smk', 'rambam', 'smg', 'mishneh', 'shulchanArukh', 'pasuk', 'mitzvah Title chinukh', 'mitzvah Title Rambam']:
                if len(row_link[column]) > 1:
                    if rnd == 1:
                        if isinstance(row_link[column], str):
                            row_link[column] = row_link[column]
                        else:
                            row_link[column] = " |".join(row_link[column])
                    else:
                        row_link[column] = siman_exctractor(row_link[column], column)
                elif row_link[column]:
                    if rnd == 1:
                        row_link[column] = row_link[column][0]
                    else:
                        row_link[column] = siman_exctractor(row_link[column][0], column)
            if row_link["chinukh"] <= 613 and not rnd ==1:
                row_link["wiki_rambam"] = wiki_chinukh_rambam[row_link["chinukh"]]["rambam_wiki"]
                row_link["wiki_table"] = row_link["wiki_rambam"] == row_link["rambam"]
            links.append(row_link)

            if not rnd == 1:
                ref_row, url_row = row_to_Refs(row_link, fixing=False)
                if row_link["chinukh"] <= 613:
                    url_row["wiki_rambam"] = wiki_chinukh_rambam[row_link["chinukh"]]["rambam_url"]

                links.append(url_row)
                links.append(ref_row)

    print(cnt_long)
    with open('{}.csv'.format(csvfilename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, ['mitzvah Title chinukh', 'mitzvah Title Rambam', 'chinukh', 'smk', 'rambam', "wiki_rambam", "wiki_table", 'smg', 'mishneh', 'shulchanArukh', 'pasuk']) #fieldnames = obj_list[0].keys())
        writer.writeheader()
        writer.writerows(links)

    return


def links_chinukh_smk(filename):
        links = []
        with open(filename, 'r') as csvfile:
            file_reader = csv.DictReader(csvfile)
            for i, row in enumerate(file_reader):
                if not row:
                    continue
                chinukh_simanlen = len(Ref('Sefer HaChinukh.{}'.format(row["chinukh"])).all_segment_refs())
                for smki in eval(row["smk"]):
                    smk_siman_len = len(Ref('Sefer Mitzvot Katan.{}'.format(smki)).all_segment_refs()) if len(Ref('Sefer Mitzvot Katan.{}'.format(smki)).all_segment_refs()) !=0 else 1
                    link = ({"refs": [
                        'Sefer HaChinukh.{}.{}-{}'.format(row["chinukh"], 1, chinukh_simanlen),
                        'Sefer Mitzvot Katan.{}.{}-{}'.format(smki, 1, smk_siman_len)
                    ],
                        "type": "Sifrei Mitzvot",
                        "auto": True,
                        "generated_by": "chinukh_rambam_sfm_linker"  # _sfm_linker what is this parametor intended to be?
                    })
                    print(link['refs'])
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
                print(row)
                dictList.append(row)
            cnt += 1
        # for link in ls:
        #     print link.refs
        #     cnt += 1
    print(cnt)
    toCsv('chinukh_smg', ['chimukh', 'smk', 'smg'], dictList)

def toCsv(csvfilename, headers, dictList):
    with open('{}.csv'.format(csvfilename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, headers) #fieldnames = obj_list[0].keys())
        writer.writeheader()
        writer.writerows(dictList)


def siman_exctractor(text, header):
    if not text or re.search("Title", header):
        return
    if isinstance(text, list):
        double = []
        for t in text:
            double.append(siman_exctractor(t, header))
        return double
    text = re.sub("[;.,']", "", text)
    lte = {'smk': ['סימן', 'סעיף'], 'rambam':['מצוות', 'וע"ש']}
    try:
        list_to_egnore = lte[header]
    except KeyError:
        list_to_egnore = []

    simanim = []
    split = iter(re.split('\s', text))
    for word in split:
        if not word or (word in list_to_egnore):
            continue
        if header == 'rambam':
            if word == 'עשה':
                simanim.append('Positive')
                continue
            elif word == "לא" and next(split) == "תעשה":
                simanim.append('Negative')
                continue
        if header == 'smg':
            if word == 'עשין':
                simanim.append('Positive Commandments')
                continue
            elif re.search("לאוו?ין", word):
                simanim.append('Negative Commandments')
                continue
        if header in ['mishneh', 'shulchanArukh','pasuk']:
            text = re.sub("'|,", "", text.strip())
            while True:
                if not text:
                    return
                print(text)
                try:
                    ref = Ref(text)
                    assert not ref.is_empty()
                    print(ref)
                    return [ref.normal()]  # notice that this iterative logic doesn't catch refs with Vav
                except (AssertionError, InputError):
                    split_text = re.split('\s', text)
                    text = ' '.join(split_text[:-1])
        if re.search('-', word):
            borders = re.search("(.*?)-(.*)", word)
            start = getGematria(borders.group(1))
            end = getGematria(borders.group(2))
            if (end - start) > 5:
                simanim.append(start)
                simanim.append(end)
            else:
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
            simanim.append(getGematria(word))
    # print smk_text, simanim
    return simanim


def siman_smk_exctractor(smk_text):

    split = re.split('\s', smk_text)
    simanim = []
    for word in split:
        if not word or word == 'סימן' or word == 'סעיף':
            continue
        word = re.sub("[;.,']", "", word)
        if re.search('-', word):
            borders = re.search("(.*?)-(.*)", word)
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
    if st[0] == 'ו':
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
    \p{Hebrew} ~= [\\u05d0–\\u05ea]
    """
    rx = r"""                                    # 1 of 3 styles:
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
    dicts_by_chinukh = []
    clusters = []
    link_node_cnt = 0
    with open('{}'.format(csvlinkfile), 'r') as csvfile:
        seg_reader = csv.DictReader(csvfile)

        for row in seg_reader:
            try:
                mitzvah_set = []
                mitzvah_dict = {}
                if int(row['chinukh']) <= 613:
                    mitzvah_set.append(range_ref(Ref('Sefer HaChinukh.{}'.format(row['chinukh']))))
                    mitzvah_dict['chinukh'] = Ref('Sefer HaChinukh.{}'.format(row['chinukh']))
                if eval(row['smk']):
                    for smki in eval(row['smk']):
                        if smki:
                            mitzvah_set.append(Ref('Sefer Mitzvot Katan, Remazim.{}'.format(smki)))
                            mitzvah_set.append(range_ref(Ref('Sefer Mitzvot Katan.{}'.format(smki))))
                            mitzvah_dict['smk'] = Ref('Sefer Mitzvot Katan, Remazim.{}'.format(smki))
            except (NameError, SyntaxError) as detail:
                print("chinukh {} ref is empty:".format(row['chinukh']), detail)
            try:
                rambam = eval(row['rambam'])
                if rambam:
                    if not isinstance(rambam[0], list):
                        try:
                            mitzvah_set.append(range_ref(Ref('Sefer HaMitzvot, {}.{}'.format(rambam[0].strip(), rambam[1]))))
                            mitzvah_dict['rambam'] = range_ref(Ref('Sefer HaMitzvot, {}.{}'.format(rambam[0].strip(), rambam[1])))
                        except IndexError:
                            print('*problem {} in siman {} *'.format(rambam, row['chinukh']))
                    else:
                        for ram in rambam:
                            if ram:
                                mitzvah_set.append(range_ref(Ref('Sefer HaMitzvot, {}.{}'.format(ram[0].strip(), ram[1]))))
                                mitzvah_dict['rambam']=range_ref(Ref('Sefer HaMitzvot, {}.{}'.format(ram[0].strip(), ram[1])))
            except NameError as detail:
                print("chinukh {} ref is empty:".format(row['chinukh']), detail)
            try:
                smg = eval(row['smg'])
                if smg:
                    if isinstance(smg[0], list):
                        for smgi in smg:
                            if smgi:
                                mitzvah_set.append(Ref('Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smgi[0], smgi[1])))
                                mitzvah_set.append(range_ref(Ref('Sefer Mitzvot Gadol, {}.{}'.format(smgi[0], smgi[1]))))
                                mitzvah_dict["smg"] = (Ref('Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smgi[0], smgi[1])))
                    elif isinstance(smg[0], str):
                        try:
                            mitzvah_set.append(Ref('Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smg[0].strip(), smg[1])))
                            mitzvah_set.append(range_ref(Ref('Sefer Mitzvot Gadol, {}.{}'.format(smg[0].strip(), smg[1]))))
                            mitzvah_dict["smg"] = (
                            Ref('Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smg[0].strip(), smg[1])))
                        except IndexError:
                            print('*problem {} in siman {} *'.format(smg, row['chinukh']))
            except NameError as detail:
                print("chinukh {} ref is empty:".format(row['chinukh']), detail)
            try:
                mishneh = row['mishneh']
                if mishneh:
                    mishneh = eval(row['mishneh'])
                    if len(mishneh) == 1:
                        mitzvah_set.append(Ref(mishneh[0]))
                        mitzvah_dict["mishneh"] = Ref(mishneh[0])
                    else:
                        for mish in mishneh:
                            if mish:
                                mitzvah_set.append(Ref(mish[0]))
                                mitzvah_dict["mishneh"] = Ref(mish[0])
            except NameError as detail:
                print("chinukh {} ref is empty:".format(row['chinukh']), detail)
            try:
                sa = row['shulchanArukh']
                if sa:
                    sa = eval(row['shulchanArukh'])
                    if len(sa) == 1:
                        mitzvah_set.append(Ref(sa[0]))
                        mitzvah_dict["sa"] = Ref(sa[0])
                    else:
                        for sai in sa:
                            if sai:
                                mitzvah_set.append(Ref(sai[0]))
                                mitzvah_dict["sa"] = Ref(sai[0])
                sets_by_chinukh.append(mitzvah_set)
            except NameError as detail:
                print("chinukh {} ref is empty:".format(row['chinukh']), detail)
            pasuk = eval(row['pasuk'])
            if pasuk:
                if not isinstance(pasuk[0], list):
                    if pasuk[0] and re.search('\d', pasuk[0]):
                        mitzvah_set.append(Ref(pasuk[0]))
                else:
                    for pas in pasuk:
                        if pas:
                            if re.search('\d', pas[0]):
                                mitzvah_set.append(Ref(pas[0]))

            dicts_by_chinukh.append(mitzvah_dict)
            mitzvah_cluster = create_link_cluster(mitzvah_set, 30044, link_type="Sifrei Mitzvot", attrs={"generated_by":"viascraped_chinukh_sfm_linker", "auto": True})
            clusters.append(mitzvah_cluster)

    print(clusters)
    print(sum(clusters))
    return sets_by_chinukh, clusters, dicts_by_chinukh

def link_sfrMitzvot_shortCounting():
    links = []
    # Negative Commandments
    pos_sefer_mitzvot = Ref('Sefer HaMitzvot, Positive Commandments').all_segment_refs()
    for m, sefer_ref in enumerate(pos_sefer_mitzvot):
        mitzva_len =len(sefer_ref.all_segment_refs())
        link = ({"refs": [
            'Mishneh Torah, Positive Mitzvot.{}'.format(m+1),
            'Sefer HaMitzvot, Positive Commandments.{}.1-{}'.format(m+1, mitzva_len)
        ],
            "type": "Sifrei Mitzvot",
            "auto": True,
            "generated_by": "sfrrambam_shortcount_sfm_linker"
        })
        links.append(link)

    # Negative Mitzvot
    neg_sefer_mitzvot = Ref('Sefer HaMitzvot, Negative Commandments').all_segment_refs()
    for m, sefer_ref in enumerate(neg_sefer_mitzvot):
        mitzva_len =len(sefer_ref.all_segment_refs())
        link = ({"refs": [
            'Mishneh Torah, Negative Mitzvot.{}'.format(m+1),
            'Sefer HaMitzvot, Negative Commandments.{}.1-{}'.format(m+1, mitzva_len)
        ],
            "type": "Sifrei Mitzvot",
            "auto": True,
            "generated_by": "sfrrambam_shortcount_sfm_linker"
        })
        links.append(link)

    return links


def range_ref(ref):
    #this shoulkd be a RASE
    if ref.is_empty():
        raise NameError('Empty Ref {}'.format(ref))
    ref_length = len(ref.all_segment_refs())
    if ref_length <1 or not ref.is_section_level():
        r= ref
    elif ref_length==1:
        r=Ref("{}.1".format(ref.normal()))
    else:
        r = Ref("{}.1-{}".format(ref.normal(), ref_length))
    return r


def copy_from_local(linkset = LinkSet({"type": "sifrei mitzvot"})):
    # query = {"type": "sifrei mitzvot"}
    # linkset = LinkSet(query)
    links = [l.contents() for l in linkset]
    # for link in links:
    #     for i, ref in enumerate(link["refs"]):
    #         if re.search("Sefer HaMitzvot", ref):
    #             link["refs"][i] = "Sefer HaMitzvot LaRambam"
    #             break

    # for link in links:
    #     ref_strings = link["refs"]
    #     for k, ref in enumerate(ref_strings):
    #         if text.Ref(ref).primary_category == u'Tanakh':  ## carfull Tanakh catagory refers also to Tanakh commentarys!
    #             newrefs = ref_strings[:]
    #             newrefs[k] = text.Ref(ref_strings[k]).section_ref().normal()
    #             broadLink = Link().load({'refs': [newrefs[k], newrefs[(k + 1) % 2]]})
    #             if broadLink:
    #                 # raise DuplicateRecordError(u"more than one broader link exists: {} - {}".format(broadLink[0].refs[0], broadLink[0].refs[1])
    #                 #
    #                 # tracker.delete(user, broadLink,)
    #                 broadLink.delete()
    #                 print 'deleting Link {} {}'.format(broadLink.refs[0], broadLink.refs[1])
    post_link(links, VERBOSE=True)
    return links


def seferHamitzvot_from_rasag_comm(rasagCsvName, with_orig = False):
        # ind_rasag_comm = library.get_index("Commentary on Sefer HaMitzvot of Rasag")
        segments = Ref('Commentary_on_Sefer_Hamitzvot_of_Rasag,_Positive_Commandments').all_segment_refs()
        segments.extend(Ref('Commentary_on_Sefer_Hamitzvot_of_Rasag,_Negative_Commandments').all_segment_refs())
        segments.extend(Ref('Commentary_on_Sefer_Hamitzvot_of_Rasag,_Laws_of_the_Courts').all_segment_refs())
        segments.extend(Ref('Commentary_on_Sefer_Hamitzvot_of_Rasag,_Communal_Laws').all_segment_refs())

        cnt = {"Rasag":0, "Sefer HaMitzvot":0, "Semag":0, "Semak":0}
        dict_list = []
        for seg in segments:
            # sfHmtzvot = re.search(u'(?:ספר המצו?ות|סה"מ).{1,4}(עשין|לאוין|עשה|לא תעשה).{0,20}', seg.text('he').text)
            sfHmtzvot = re.search('(?:ספר המצוות|סה"מ)\s{1,4}\((.*?)\)', seg.text('he').text)
            smg = re.search('סמ"ג \((.*?)\)', seg.text('he').text)
            smk = re.search('סמ"ק (\(.*?\))', seg.text('he').text)
            row_dict = {}
            row_orig = {}
            if sfHmtzvot:
                # row_dict["Rasag"] = re.search("(Sefer.*?\d*?):", seg.normal()).group(1)
                # row_orig["Rasag"] = re.search("(Sefer.*?\d*?):", seg.normal()).group(1)
                kind, simanim = rasag_exctractor(sfHmtzvot.group(1))
                # row_dict["Sefer HaMitzvot"] = ['Sefer HaMitzvot, {}.{}'.format(kind, siman) for siman in simanim]
                if kind:
                    row_dict["Sefer HaMitzvot"] = 'Sefer HaMitzvot, {}.{}'.format(kind, simanim[0])
                else:
                    print("no kind", sfHmtzvot.group(1))
                row_orig["Sefer HaMitzvot"] = sfHmtzvot.group()
                cnt["Sefer HaMitzvot"] += 1
            if smg:
                # row_dict["Rasag"] = re.search("(Sefer.*?\d*?):", seg.normal()).group(1)
                kind, simanim = rasag_exctractor(smg.group(1))
                # row_dict["Semag"] = ['Sefer Mitzvot Gadol, {}.{}'.format(kind, siman) for siman in simanim]
                if kind:
                    row_dict["Semag"] = 'Sefer Mitzvot Gadol, {}.{}'.format(kind, simanim[0])
                else:
                    print("no kind", smg.group(1))
                row_orig["Semag"] = smg.group()
                cnt["Semag"] += 1
            if smk:
                # row_dict["Rasag"] = re.search("(Sefer.*?\d*?):", seg.normal()).group(1)
                # simanim = siman_smk_exctractor(smk.group(1))
                smki = re.search("ב?סי'\s+(.*?)(?:\s*\))", smk.group(1))
                if smki:
                    siman = getGematria(smki.group(1))
                    row_dict["Semak"] = "Sefer Mitzvot Katan.{}".format(siman)
                    row_orig["Semak"] = smk.group()
                    cnt["Semak"] += 1
                else:
                    print('***siman***' + smk.group())

            if row_dict:
                cnt["Rasag"] += 1
                row_dict["Rasag"] = re.search("(Sefer.*?\d*?):", seg.normal()).group(1)
                row_orig["Rasag"] = seg.normal()
                if with_orig:
                    dict_list.append(row_orig)
                dict_list.append(row_dict)
        toCsv(rasagCsvName, ["Rasag", "Sefer HaMitzvot", "Semag", "Semak"], dict_list)
        print(cnt)


def rasag_exctractor(text):
    split = re.split("\s", text)
    simanim = []
    kind = None
    if re.search("(:?לאוין|לא תעשה)", split[0]):
            kind = 'Negative Commandments'
    elif re.search("(:?עשין|עשה)", split[0]):
            kind = 'Positive Commandments'
    for word in split[1:]:
        siman = getGematria(word)
        simanim.append(siman)
    return kind, simanim


def rasag_linking(csvlinkfile):
    links_rsg_shmtz = []
    links_rsg_smg = []
    links_rsg_smk = []

    with open('{}'.format(csvlinkfile), 'r') as csvfile:
        seg_reader = csv.DictReader(csvfile)
        for row in seg_reader:
            if row["Sefer HaMitzvot"]:
                link = ({"refs": [
                    row["Rasag"],
                    row["Sefer HaMitzvot"]
                ],
                    "type": "Sifrei Mitzvot",
                    "auto": True,
                    "generated_by": "sfrrambam_rsg_sfm_linker"
                })
                links_rsg_shmtz.append(link)
            if row["Semag"]:
                link = ({"refs": [
                    row["Rasag"],
                    row["Semag"]
                ],
                    "type": "Sifrei Mitzvot",
                    "auto": True,
                    "generated_by": "smg_rsg_sfm_linker"
                })
                links_rsg_smg.append(link)
            if row["Semak"]:
                link = ({"refs": [
                    row["Rasag"],
                    row["Semak"]
                ],
                    "type": "Sifrei Mitzvot",
                    "auto": True,
                    "generated_by": "smk_rsg_sfm_linker"
                })
                links_rsg_smk.append(link)
        links = links_rsg_shmtz + links_rsg_smg + links_rsg_smk
        return links


def row_to_Refs(row, fixing=True):
    if fixing:
        for k in list(row.keys()):
            try:
                if k not in ['mitzvah Title chinukh', 'mitzvah Title Rambam', "wiki_rambam", "wiki_table"]:
                    row[k] = eval(row[k])
            except SyntaxError:
                continue
    try:
        mitzvah_set = []
        mitzvah_set_small = []
        mitzvah_set_large = []
        mitzvah_dict = {'chinukh':[], 'smk':[], 'rambam':[], 'smg':[], 'mishneh':[], 'shulchanArukh':[], 'pasuk':[], 'rasag':[]}
        if int(row['chinukh']) <= 613:
            mitzvah_set.append(range_ref(Ref('Sefer HaChinukh.{}'.format(row['chinukh']))))
            mitzvah_dict['chinukh'].append(Ref('Sefer HaChinukh.{}'.format(row['chinukh'])))
        if (row['smk']):
            for smki in (row['smk']):
                if isinstance(smki, list):
                    for smkii in smki:
                        mitzvah_set_small.append(Ref('Sefer Mitzvot Katan, Remazim.{}'.format(smkii)))
                        mitzvah_set_large.append(range_ref(Ref('Sefer Mitzvot Katan.{}'.format(smkii))))
                        mitzvah_dict['smk'].append(Ref('Sefer Mitzvot Katan, Remazim.{}'.format(smkii)))
                else: # smki isinstance(smki, int):
                    mitzvah_set_small.append(Ref('Sefer Mitzvot Katan, Remazim.{}'.format(smki)))
                    mitzvah_set_large.append(range_ref(Ref('Sefer Mitzvot Katan.{}'.format(smki))))
                    mitzvah_dict['smk'].append(Ref('Sefer Mitzvot Katan, Remazim.{}'.format(smki)))
    except (NameError, SyntaxError, InputError):
        print("chinukh {} ref is empty:".format(row['chinukh']))
    try:
        rambam = (row['rambam'])
        if rambam:
            if not isinstance(rambam[0], list):
                try:
                    mitzvah_set_small.append(
                        range_ref(Ref('Mishneh Torah, {} Mitzvot.{}'.format(rambam[0].strip(), rambam[1]))))
                    mitzvah_set_large.append(range_ref(Ref('Sefer HaMitzvot, {} Commandments.{}'.format(rambam[0].strip(), rambam[1]))))
                    mitzvah_dict['rambam'].append(range_ref(
                        Ref('Mishneh Torah, {} Mitzvot.{}'.format(rambam[0].strip(), rambam[1]))))
                except IndexError:
                    print('*problem {} in siman {} *'.format(rambam, row['chinukh']))
            else:
                for ram in rambam:
                    if ram:
                        mitzvah_set_small.append(range_ref(Ref('Mishneh Torah, {} Mitzvot.{}'.format(ram[0].strip(), ram[1]))))
                        mitzvah_set_large.append(range_ref(Ref('Sefer HaMitzvot, {} Commandments.{}'.format(ram[0].strip(), ram[1]))))
                        mitzvah_dict['rambam'].append(range_ref(
                            Ref('Mishneh Torah, {} Mitzvot.{}'.format(ram[0].strip(), ram[1]))))
    except NameError as detail:
        print("chinukh {} ref is empty:".format(row['chinukh']), detail)
    try:
        smg = (row['smg'])
        if smg:
            if isinstance(smg[0], list):
                for smgi in smg:
                    if smgi:
                        mitzvah_set_small.append(Ref('Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smgi[0], smgi[1])))
                        mitzvah_set_large.append(range_ref(Ref('Sefer Mitzvot Gadol, {}.{}'.format(smgi[0], smgi[1]))))
                        mitzvah_dict["smg"].append(Ref('Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smgi[0], smgi[1])))
            elif isinstance(smg[0], str):
                try:
                    mitzvah_set_small.append(Ref('Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smg[0].strip(), smg[1])))
                    mitzvah_set_large.append(range_ref(Ref('Sefer Mitzvot Gadol, {}.{}'.format(smg[0].strip(), smg[1]))))
                    mitzvah_dict["smg"].append(
                        Ref('Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smg[0].strip(), smg[1])))
                except IndexError:
                    print('*problem {} in siman {} *'.format(smg, row['chinukh']))
    except NameError as detail:
        print("chinukh {} ref is empty:".format(row['chinukh']), detail)
    try:
        mishneh = row['mishneh']
        if mishneh:
            mishneh = (row['mishneh'])
            if len(mishneh) == 1:
                mitzvah_set_large.append(Ref(mishneh[0]))
                mitzvah_dict["mishneh"].append(Ref(mishneh[0]))
            else:
                for mish in mishneh:
                    if mish:
                        mitzvah_set_large.append(Ref(mish[0]))
                        mitzvah_dict["mishneh"].append(Ref(mish[0]))
    except NameError as detail:
        print("chinukh {} ref is empty:".format(row['chinukh']), detail)
    try:
        sa = row['shulchanArukh']
        if sa:
            sa = (row['shulchanArukh'])
            if len(sa) == 1:
                mitzvah_set_large.append(Ref(sa[0]))
                mitzvah_dict["shulchanArukh"].append(Ref(sa[0]))
            else:
                for sai in sa:
                    if sai:
                        mitzvah_set_large.append(Ref(sai[0]))
                        mitzvah_dict["shulchanArukh"].append(Ref(sai[0]))
        # sets_by_chinukh.append(mitzvah_set)
    except NameError as detail:
        print("chinukh {} ref is empty:".format(row['chinukh']), detail)
    pasuk = (row['pasuk'])
    if pasuk:
        if not isinstance(pasuk[0], list):
            if pasuk[0] and re.search('\d', pasuk[0]):
                mitzvah_set.append(Ref(pasuk[0]))
                mitzvah_dict['pasuk'].append(Ref(pasuk[0]))
        else:
            for pas in pasuk:
                if pas:
                    if re.search('\d', pas[0]):
                        mitzvah_set.append(Ref(pas[0]))
                        mitzvah_dict['pasuk'].append(Ref(pas[0]))
    try:
        rsg = (row['rasag'])
        if rsg:
            for rsgi in rsg:
                # if rsgi:
                mitzvah_set_small.append(Ref(rsgi))
                # mitzvah_set_large.append(rsgi)
                mitzvah_dict["rasag"].append(Ref(rsgi))
            # elif isinstance(rsg[0], unicode):
            #     try:
            #         mitzvah_set_small.append(Ref(rsg[0]))
            #         # mitzvah_set_large.append(rsg)
            #         mitzvah_dict[u"rasag"].append(Ref(rsg[0]))
            #     except IndexError:
            #         print u'*problem {} in siman {} *'.format(rsg, row[u'chinukh'])
    except NameError as detail:
        print("rsg {} ref is empty:".format(row['chinukh']))#, detail


    mitzvah_set_small.extend(mitzvah_set)
    mitzvah_set_large.extend(mitzvah_set)
    if fixing:
        return seg_from_refs(mitzvah_dict), mitzvah_set_small, mitzvah_set_large
    return seg_from_refs(mitzvah_dict)


def seg_from_refs(ref_dict):
    seg_dict = {'chinukh':'', 'smk':'', 'rambam':'', 'smg':'', 'mishneh':'', 'pasuk':'', 'shulchanArukh':'', 'rasag':''}
    seg_urls = {'chinukh':'', 'smk':'', 'rambam':'', 'smg':'', 'mishneh':'', 'pasuk':'', 'shulchanArukh':'', 'rasag':''}
    for column, refs in list(ref_dict.items()):
        # if column == 'shulchanArukh':
        #     continue
        for ref in refs:
            if ref:
                seg_dict[column] += ref.all_segment_refs()[0].text('he').text
                seg_dict[column] += '\n'
                url_format = re.sub(" ", "_", ref.normal())
                url_format = re.sub("_(\d)", r".\1", url_format)
                seg_urls[column] += 'https://www.sefaria.org/{}\n'.format(url_format)
                # if isinstance(ref.text('he').text, list):
                #     seg_dict[column] += (ref.text('he').text[0])
                # else:
                #     seg_dict[column] += (ref.text('he').text)
    return seg_dict, seg_urls


def cluster_lines(fixedFileName):
    sets_by_chinukh = []
    dicts_by_chinukh = []
    clusters = []
    link_node_cnt = 0
    only_cluster_lines = []
    with open('{}'.format(fixedFileName), 'r') as csvfile:
        seg_reader = csv.DictReader(csvfile)

        for i, row in enumerate(seg_reader):
            if not divmod(i, 4)[1] == 1:
                continue

            only_cluster_lines.append(row)
            _, mitzvah_set_small, mitzvah_set_large = row_to_Refs(row, fixing=True)
            mitzvah_cluster_small = create_link_cluster(mitzvah_set_small, 30044, link_type="Sifrei Mitzvot",
                                                  attrs={"generated_by": "viascraped_chinukh_sfm_linker_small", "auto": True})
            mitzvah_cluster_large = create_link_cluster(mitzvah_set_large, 30044, link_type="Sifrei Mitzvot",
                                                  attrs={"generated_by": "viascraped_chinukh_sfm_linker_large",
                                                         "auto": True})
            clusters.append(mitzvah_cluster_small)
            clusters.append(mitzvah_cluster_large)

    with open('only_cluster_lines.csv', 'w') as writetocsv:
        row_writer = csv.DictWriter(writetocsv, ['mitzvah Title chinukh', 'mitzvah Title Rambam', 'chinukh', 'smk', 'rambam', "wiki_rambam", "wiki_table", 'smg', 'mishneh', 'shulchanArukh', 'pasuk', 'rasag'])
        row_writer.writeheader()
        row_writer.writerows(only_cluster_lines)

    print(clusters)
    print(sum(clusters))
    return sets_by_chinukh, clusters, dicts_by_chinukh


def add_rasag_to_chart(readFrom, writeTo):
    ls_rsg_psukim = LinkSet({"$and": [{"refs": {"$regex": "^(Sefer Hamitzvot of Rasag).*"}}, {"refs": {"$regex":"^(Genesis|Exodus|Leviticus|Numbers|Deuteronomy).*" }}]})
    mitzvah_title = ''
    with open(writeTo, 'w') as writetocsv:
        writer = csv.DictWriter(writetocsv, ['mitzvah Title chinukh', 'mitzvah Title Rambam', 'chinukh', 'smk', 'rambam', "wiki_rambam", "wiki_table", 'smg', 'mishneh', 'shulchanArukh', 'pasuk', 'rasag'])
        writer.writeheader()
        with open('{}'.format(readFrom)) as csvfile:
            seg_reader = csv.DictReader(csvfile)
            for i, row in enumerate(seg_reader):
                if not divmod(i, 4)[1] == 1:
                    row['rasag']= []
                    writer.writerow(row)
                    mitzvah_title = row['mitzvah Title chinukh'] if row['mitzvah Title chinukh'] else mitzvah_title
                    continue
                row_dict = row
                row_dict['rasag'] = []
                pesukim = eval(row['pasuk'])
                for p in pesukim:
                    if not p:
                        row_dict['rasag'] += []
                        continue
                    pr = Ref(p) if isinstance(p, str) else Ref(p[0])
                    if not pr.is_segment_level():
                        row_dict['rasag'] += []
                        continue
                    rsg_mitzvah = ls_rsg_psukim.refs_from(pr)
                    print("rsg_mitzvot: ", rsg_mitzvah)
                    print(pr)
                    row_dict['rasag'] += [r.normal() for r in rsg_mitzvah]
                writer.writerow(row_dict)







def find_missing_links(base_title_book, regex_title_book, level = 1):
    """

    :param base_title_book: book title of the book to go through it's ref. title that can to get the Index obj
    :param regex_title_book: regex consisting of titles of books to be found in the refs.
    :param level: 0 - sections 1 - segments.
    :return: a list of segments that don't have any links with the regex in the books name
    """
    cnt_all = 0
    missing = []
    indb1 = library.get_index(base_title_book)
    if level == 0:
        segments = indb1.all_section_refs()
    else:
        segments = indb1.all_segment_refs()
    for seg in segments:
        cnt = 0
        refs = [r for i in range(len(seg.linkset())) for r in seg.linkset()[i].refs]
        for r in refs:
            if re.search(regex_title_book, r):
                cnt += 1
        if cnt == 0:
            cnt_all += 1
            missing.append(seg)
            print(seg)  # , cnt_all
    return missing


def link_tanakh_pesukim_via_Halakah(base_title_book, category="Tanakh", nodes_to_jump_from = []):
    ind = library.get_index(base_title_book)
    segments = ind.all_segment_refs()
    category_books = library.get_indexes_in_category(category)
    for seg in segments:
        category_set = []
        cnt = 0
        refs = [r for i in range(len(seg.linkset())) for r in seg.linkset()[i].refs]
        for r in refs:
            rr = Ref(r)
            if rr.index.title in category_books:
                category_set.append(r)
            # elif re.search(rr.index.title, ' '.join(nodes_to_jump_from)):

        if len(category_set) > 1:

            print('**********************')
            print(seg.text('he').text)
            for p in category_set:
                print(p)
                print(Ref(p).text('he').text)


def rasag_clustered_via_Torah_and(books_list = None, without_query = {}, clique_query = {}, exclude_clique = ""):
    """
    :param: books_list: list of books to be the party to connect to (onn the other side of the tanakh)
    :param without_qurey: without counting live links.
    :return: list of links starting in rasag throw torah to book_list, without links from without_query, and then clustered with all clique query
    """
    links = []
    woLS = LinkSet(without_query)
    clique_ls = LinkSet(clique_query)
    if not books_list:
        books_list = ["Mishneh Torah, Positive Mitzvot", "Mishneh Torah, Negative Mitzvot"]
                          #"Sefer Mitzvot Gadol", "Sefer Mitzvot Katan",
                          # "Mishneh Torah, Positive Mitzvot", "Mishneh Torah, Negative Mitzvot",
                          # "Sefer Yereim"]
    cat_tanakh = library.get_indexes_in_category("Tanakh")
    segments = library.get_index("Sefer Hamitzvot of Rasag").all_segment_refs()
    for seg in segments:
        ls = seg.linkset()
        if without_query and len(woLS.refs_from(seg)): # so not to look for connecting rsg via Rambam when rsg is connected already
            continue
        ts = [r for r in ls.refs_from(seg, as_tuple=False, as_link=False) if r.index.title in cat_tanakh]  # ts= tanakh set => pesukim connected to this Rasag seg/mitzva
        if not ts:
            # print "error file: is this a mitzvah? is it missing a pasuk? {}".format(seg)
            continue

        for p in ts:
            #### ls1: pasuk and sefrei mitzvot and maybe not siefreimitzvot typed ####
            # ls1 = p.linkset() # linkset of the pasuk
            # ls1 = LinkSet({"$and":[{"refs":"{}".format(seg)}, {"type":{"$ne":"sifrei mitzvot"}}]})
            ls1 = LinkSet({"$and": [{"refs": "{}".format(p)},{"type":{"$ne":"sifrei mitzvot"}}]})#{"refs": {"$regex":"^({})".format("|".join(books_list))}},
            sfm_pasuk_set = [r for r in ls1.refs_from(p) if r.index.title in books_list] # using refs_from to get the refs asa list and not link objects
            for mitzvah_ref in sfm_pasuk_set:
                clique_ref_list = clique_ls.refs_from(mitzvah_ref)
                clique_links = cliqueLinks(seg, clique_ref_list, type = "rsg_sfm_clique", exclude=exclude_clique)
                links.extend(clique_links)
                if re.search("(Katan|Gadol)", mitzvah_ref.normal()) and not re.search("Remazim", mitzvah_ref.normal()):
                    continue
                link = ({"refs": [mitzvah_ref.normal(), seg.normal()],
                         "type": "Sifrei Mitzvot",
                         "auto": True,
                         "generated_by": "rasag_sfm_linker"
                    })
                # print mitzvah_ref.normal(), "?&p2=", seg.normal()
                links.append(link)
    for l in links:
        print(l["refs"][0], "?p2=", l["refs"][1])
    print(len(links))
    return links


def cliqueLinks(ref, rl, type='clique', exclude = ""):
    """

    :param ref: a ref to connect each ref in rl to.
    :param rl: ref list that you want to connect ref to each function in rl.
    :param type: the typr these links are going to receive
    :param exclude: regex that refs containing this regex will be excluded for the link creation
    :return:
    """
    links = []
    for qr in rl:
        if exclude and re.search(exclude, qr):
            continue
        link = ({"refs": [ref.normal(), qr.normal()],
                 "type": type,
                 "auto": True,
                 "generated_by": "rasag_sfm_linker"
                 })
        links.append(link)
    return links


def pesukim_with_mto_mitzvah(fromindex="Sefer Hamitzvot of Rasag"):
    """
    prints out a report of pesukim that are connected to more then one segment (mitzvah) in the fromindex text
    :param fromindex: base text to check the linking to the pesukim per segment
    :return: a list of tupels with the pasuk and a tuple with the segs -  (pasuk, (seg1, seg2...))
    """
    cnt = 0
    psukim_segments = []
    rsg_ind = library.get_index(fromindex)
    segments = rsg_ind.all_segment_refs()
    cat_tanakh = library.get_indexes_in_category("Tanakh")
    for seg in segments:
        ls = seg.linkset()
        ts = [r for r in ls.refs_from(seg, as_tuple=False, as_link=False) if r.index.title in cat_tanakh]
        for p in ts:
            linksegs = []
            lsp = p.linkset()
            prs = [r for r in lsp.refs_from(p, as_tuple=False, as_link=False) if r.index.title == rsg_ind.title]
            if len(prs) > 1:
                ptext = p.text('he').text
                if type(ptext) == list:
                    ptext = ptext[0]
                print(p.normal())
                print(ptext + '\n')
                for r in prs:
                    print(r.text('he').text)
                    linksegs.append(r)
                print('***************')
                psukim_segments.append((p.normal(), linksegs))
                cnt += 1
    print(cnt)
    return psukim_segments


def report_rsg_not_cnnected(fromindex):
    cnt = 0
    psukim_segments = []
    rsg_ind = library.get_index(fromindex)
    segments = rsg_ind.all_segment_refs()
    cat_tanakh = library.get_indexes_in_category("Tanakh")
    lstanakh = LinkSet({"$and":[{"refs":{"$regex": "^(Genesis|Exodus|Leviticus|Numbers|Deuteronomy)"}}, {"refs":{"$regex": "^(Sefer Hamitzvot of Rasag)"}}]})
    ls = LinkSet({"type": "sifrei mitzvot"})#, {"refs": ""}]})
    for seg in segments:
        if lstanakh.refs_from(seg) and not ls.refs_from(seg):
        # if len(lstanakh.refs_from(seg)) >1:
            print(seg) # len(lstanakh.refs_from(seg))
            cnt+=1
    print(cnt)

if __name__ == "__main__":
    # rambam_chinukh_lnks = scrape_wiki()
    # post_link(rambam_chinukh_lnks, VERBOSE=True)
    # post_link(link_sfrMitzvot_shortCounting(), VERBOSE=True)
    # rows = get_link_data()
    # origns = text_to_csv_links(u'mitzvot_fixed_smg', rows,  times=2)
    # sets, clusters, mitzvah_dicts = refs_csv(u'mitzvot_test.csv')
    # copy_from_local()
    # seferHamitzvot_from_rasag_comm(u"rasag_all_refs", with_orig = True)
    # links = rasag_linking(u'almostRefs.csv')
    # post_link(links, VERBOSE=True)
    sets_by_chinukh, clusters, dicts_by_chinukh = cluster_lines("rsg.csv")
    # link_tanakh_pesukim_via_Halakah("Mishneh Torah, Negative Mitzvot")
    # find_missing_links("Mishneh Torah, Positive Mitzvot", "Sefer HaChinukh", level=1)
    # short_rambam = ["Mishneh Torah, Positive Mitzvot", "Mishneh Torah, Negative Mitzvot"]
    # rasag_links = rasag_clustered_via_Torah_and(books_list=short_rambam, without_query={"type": "sifrei mitzvot"}, clique_query={"type": "None"}, exclude_clique="")
    # post_link(rasag_links)
    # pesukim_with_mto_mitzvah()
    # add_rasag_to_chart("mitzvot_chart.csv", "rsg.csv")
    # sets_by_chinukh, clusters, dicts_by_chinukh = cluster_lines("rsg.csv")
    # report_rsg_not_cnnected("Sefer Hamitzvot of Rasag")

    # cnt = 0
    # ls = LinkSet({"$and": [{"refs": {"$regex": "^(Sefer Hamitzvot of Rasag).*"}}, {"refs": {"$regex": "^(Mishneh Torah, (Negative|Positive))"}}]}) #|Positive
    # ls_rsg_psukim = LinkSet({"$and": [{"refs": {"$regex": "^(Sefer Hamitzvot of Rasag).*"}},
    #                                   {"refs": {"$regex": "^(Genesis|Exodus|Leviticus|Numbers|Deuteronomy).*"}}]})
    # # for l in ls:
    # #     print l.refs
    # #     cnt +=1
    # # print cnt
    #
    # cnt = 0
    # cnt_rsg = 0
    # cnt_no_ramabm = 0
    # cnt_w_rambam = 0
    # cnt_pesukim = 0
    # for seg in library.get_index("Sefer Hamitzvot of Rasag").all_segment_refs():
    #     cnt_rsg+=1
    #     if ls_rsg_psukim.refs_from(seg):
    #         cnt_pesukim +=1
    #     if not ls.refs_from(seg):
    #         cnt_no_ramabm +=1
    #         if ls_rsg_psukim.refs_from(seg):
    #             print seg
    #             cnt+=1
    #     else:
    #         cnt_w_rambam +=1
    #
    # print "# segs with no rambam: ", cnt_no_ramabm
    # print "# segs of rsg that are conected to torah and not conected to rambam:", cnt
    # print "# segs w rambam", cnt_w_rambam
    # print "# seges with pesukim", cnt_pesukim
    # print "# rsg segments: ", cnt_rsg

    pass
