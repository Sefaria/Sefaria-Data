# -*- coding: utf-8 -*-

import requests, codecs, json
import unicodecsv as csv
import pickle
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
    chinukh_rambam  = {}
    for table in tables:
        table_tr = table.select("tr")
        for col in table_tr:
            pairs.append((col.contents[1].text.strip(), re.sub(u'</?td>', u'', col.contents[-1].text).strip()))

    for pair in pairs:
        if re.search(u'ספר|מספר', pair[0]):
            continue
        neg_pos = u"Negative" if re.search(u"לאו", pair[1]) else u'Positive'
        rambam = getGematria(re.sub(u'עשה|לאו', u'', pair[1]).strip())
        chinukh = getGematria(pair[0])
        print chinukh, rambam
        chinukh_simanlen = len(Ref(u'Sefer HaChinukh.{}'.format(chinukh)).all_segment_refs())
        print neg_pos
        link = ({"refs": [
            u'Sefer HaChinukh.{}.{}-{}'.format(chinukh, 1, chinukh_simanlen),
            u'Mishneh Torah, {} Mitzvot.{}'.format(neg_pos, rambam)
        ],
            "type": "Sifrei Mitzvot",
            "auto": True,
            "generated_by": "chinukh_rambam_sfm_linker"  # _sfm_linker what is this parametor intended to be?
        })
        chinukh_rambam[chinukh]= {"rambam_wiki": [neg_pos, rambam], "rambam_url": "https://www.sefaria.org/Mishneh_Torah,_{}_Mitzvot.{}".format(neg_pos, rambam)}
        print link['refs']
        links.append(link)

    return links, chinukh_rambam

def get_link_data():
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
            row_link['smk'] = re.findall(u'''\u05e8\u05d1\u05d9 \u05d9\u05e6\u05d7\u05e7 \u05de\u05e7\u05d5\u05e8\u05d1\u05d9\u05dc, \u05e1\u05e4\u05e8 \u05de\u05e6\u05d5\u05d5\u05ea \u05e7\u05d8\u05df(.*)''',citation_column[-1].text)
            row_link['rambam'] = re.findall(u'''רמב"ם, ספר המצווו?ת(.*?)[;:.\n]''',citation_column[-1].text)
            row_link['smg'] = re.findall(u'''רבי משה מקוצי, ספר מצוות גדול(.*?)[;,:.\n]''',citation_column[-1].text)
            row_link['mishneh'] = re.findall(u'(רמב"ם הלכות.*?)(?:[;,:.\n]|ע"ש)',citation_column[-1].text)
            row_link['shulchanArukh'] = re.findall(u'שו"ע(.*?)[;:.\n]', citation_column[-1].text)
            row_link['pasuk'] = re.findall(u"((?:בראשית|שמות|ויקרא|במדבר|דברים).*?)\n", citation_column[-1].text)
            row_link['mitzvah Title chinukh'] = citation_column[1].select("h2")[0].text
            row_link['mitzvah Title Rambam'] = citation_column[-1].select("h2")[0].text
            for column in ['smk', 'rambam', 'smg', 'mishneh', 'shulchanArukh', 'pasuk', 'mitzvah Title chinukh', 'mitzvah Title Rambam']:
                if len(row_link[column]) > 1:
                    if rnd == 1:
                        if isinstance(row_link[column], unicode):
                            row_link[column] = row_link[column]
                        else:
                            row_link[column] = u" |".join(row_link[column])
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

    print cnt_long
    with open(u'{}.csv'.format(csvfilename), 'w') as csv_file:
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
    toCsv('chinukh_smg', ['chimukh', 'smk', 'smg'], dictList)

def toCsv(csvfilename, headers, dictList):
    with open(u'{}.csv'.format(csvfilename), 'w') as csv_file:
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
    text = re.sub(u"[;.,']", u"", text)
    lte = {'smk': [u'סימן', u'סעיף'], 'rambam':[u'מצוות', u'וע"ש']}
    try:
        list_to_egnore = lte[header]
    except KeyError:
        list_to_egnore = []

    simanim = []
    split = iter(re.split(u'\s', text))
    for word in split:
        if not word or (word in list_to_egnore):
            continue
        if header == 'rambam':
            if word == u'עשה':
                simanim.append(u'Positive')
                continue
            elif word == u"לא" and split.next() == u"תעשה":
                simanim.append(u'Negative')
                continue
        if header == 'smg':
            if word == u'עשין':
                simanim.append(u'Positive Commandments')
                continue
            elif re.search(u"לאוו?ין", word):
                simanim.append(u'Negative Commandments')
                continue
        if header in ['mishneh', 'shulchanArukh','pasuk']:
            text = re.sub(u"'|,", u"", text.strip())
            while True:
                if not text:
                    return
                print text
                try:
                    ref = Ref(text)
                    assert not ref.is_empty()
                    print ref
                    return [ref.normal()]  # notice that this iterative logic doesn't catch refs with Vav
                except (AssertionError, InputError):
                    split_text = re.split(u'\s', text)
                    text = u' '.join(split_text[:-1])
        if re.search(u'-', word):
            borders = re.search(u"(.*?)-(.*)", word)
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
    dicts_by_chinukh = []
    clusters = []
    link_node_cnt = 0
    with open(u'{}'.format(csvlinkfile), 'r') as csvfile:
        seg_reader = csv.DictReader(csvfile)

        for row in seg_reader:
            try:
                mitzvah_set = []
                mitzvah_dict = {}
                if int(row[u'chinukh']) <= 613:
                    mitzvah_set.append(range_ref(Ref(u'Sefer HaChinukh.{}'.format(row[u'chinukh']))))
                    mitzvah_dict[u'chinukh'] = Ref(u'Sefer HaChinukh.{}'.format(row[u'chinukh']))
                if eval(row[u'smk']):
                    for smki in eval(row[u'smk']):
                        if smki:
                            mitzvah_set.append(Ref(u'Sefer Mitzvot Katan, Remazim.{}'.format(smki)))
                            mitzvah_set.append(range_ref(Ref(u'Sefer Mitzvot Katan.{}'.format(smki))))
                            mitzvah_dict[u'smk'] = Ref(u'Sefer Mitzvot Katan, Remazim.{}'.format(smki))
            except (NameError, SyntaxError) as detail:
                print u"chinukh {} ref is empty:".format(row[u'chinukh']), detail
            try:
                rambam = eval(row[u'rambam'])
                if rambam:
                    if not isinstance(rambam[0], list):
                        try:
                            mitzvah_set.append(range_ref(Ref(u'Sefer HaMitzvot, {}.{}'.format(rambam[0].strip(), rambam[1]))))
                            mitzvah_dict[u'rambam'] = range_ref(Ref(u'Sefer HaMitzvot, {}.{}'.format(rambam[0].strip(), rambam[1])))
                        except IndexError:
                            print u'*problem {} in siman {} *'.format(rambam, row[u'chinukh'])
                    else:
                        for ram in rambam:
                            if ram:
                                mitzvah_set.append(range_ref(Ref(u'Sefer HaMitzvot, {}.{}'.format(ram[0].strip(), ram[1]))))
                                mitzvah_dict[u'rambam']=range_ref(Ref(u'Sefer HaMitzvot, {}.{}'.format(ram[0].strip(), ram[1])))
            except NameError as detail:
                print u"chinukh {} ref is empty:".format(row[u'chinukh']), detail
            try:
                smg = eval(row[u'smg'])
                if smg:
                    if isinstance(smg[0], list):
                        for smgi in smg:
                            if smgi:
                                mitzvah_set.append(Ref(u'Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smgi[0], smgi[1])))
                                mitzvah_set.append(range_ref(Ref(u'Sefer Mitzvot Gadol, {}.{}'.format(smgi[0], smgi[1]))))
                                mitzvah_dict[u"smg"] = (Ref(u'Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smgi[0], smgi[1])))
                    elif isinstance(smg[0], unicode):
                        try:
                            mitzvah_set.append(Ref(u'Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smg[0].strip(), smg[1])))
                            mitzvah_set.append(range_ref(Ref(u'Sefer Mitzvot Gadol, {}.{}'.format(smg[0].strip(), smg[1]))))
                            mitzvah_dict[u"smg"] = (
                            Ref(u'Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smg[0].strip(), smg[1])))
                        except IndexError:
                            print u'*problem {} in siman {} *'.format(smg, row[u'chinukh'])
            except NameError as detail:
                print u"chinukh {} ref is empty:".format(row[u'chinukh']), detail
            try:
                mishneh = row[u'mishneh']
                if mishneh:
                    mishneh = eval(row[u'mishneh'])
                    if len(mishneh) == 1:
                        mitzvah_set.append(Ref(mishneh[0]))
                        mitzvah_dict[u"mishneh"] = Ref(mishneh[0])
                    else:
                        for mish in mishneh:
                            if mish:
                                mitzvah_set.append(Ref(mish[0]))
                                mitzvah_dict[u"mishneh"] = Ref(mish[0])
            except NameError as detail:
                print u"chinukh {} ref is empty:".format(row[u'chinukh']), detail
            try:
                sa = row[u'shulchanArukh']
                if sa:
                    sa = eval(row[u'shulchanArukh'])
                    if len(sa) == 1:
                        mitzvah_set.append(Ref(sa[0]))
                        mitzvah_dict[u"sa"] = Ref(sa[0])
                    else:
                        for sai in sa:
                            if sai:
                                mitzvah_set.append(Ref(sai[0]))
                                mitzvah_dict[u"sa"] = Ref(sai[0])
                sets_by_chinukh.append(mitzvah_set)
            except NameError as detail:
                print u"chinukh {} ref is empty:".format(row[u'chinukh']), detail
            pasuk = eval(row[u'pasuk'])
            if pasuk:
                if not isinstance(pasuk[0], list):
                    if pasuk[0] and re.search(u'\d', pasuk[0]):
                        mitzvah_set.append(Ref(pasuk[0]))
                else:
                    for pas in pasuk:
                        if pas:
                            if re.search(u'\d', pas[0]):
                                mitzvah_set.append(Ref(pas[0]))

            dicts_by_chinukh.append(mitzvah_dict)
            mitzvah_cluster = create_link_cluster(mitzvah_set, 30044, link_type="Sifrei Mitzvot", attrs={"generated_by":"viascraped_chinukh_sfm_linker", "auto": True})
            clusters.append(mitzvah_cluster)

    print clusters
    print sum(clusters)
    return sets_by_chinukh, clusters, dicts_by_chinukh

def link_sfrMitzvot_shortCounting():
    links = []
    # Negative Commandments
    pos_sefer_mitzvot = Ref(u'Sefer HaMitzvot, Positive Commandments').all_segment_refs()
    for m, sefer_ref in enumerate(pos_sefer_mitzvot):
        mitzva_len =len(sefer_ref.all_segment_refs())
        link = ({"refs": [
            u'Mishneh Torah, Positive Mitzvot.{}'.format(m+1),
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
            u'Mishneh Torah, Negative Mitzvot.{}'.format(m+1),
            u'Sefer HaMitzvot, Negative Commandments.{}.1-{}'.format(m+1, mitzva_len)
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
        raise NameError(u'Empty Ref {}'.format(ref))
    ref_length = len(ref.all_segment_refs())
    if ref_length <=1:
        return ref
    r = Ref(u"{}.1-{}".format(ref.normal(), ref_length))
    return r


def copy_from_local():
    query = {"type": "sifrei mitzvot"}
    linkset = LinkSet(query)
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
        # ind_rasag_comm = library.get_index("Commentary on Sefer Hamitzvot of Rasag")
        segments = Ref('Commentary_on_Sefer_Hamitzvot_of_Rasag,_Positive_Commandments').all_segment_refs()
        segments.extend(Ref('Commentary_on_Sefer_Hamitzvot_of_Rasag,_Negative_Commandments').all_segment_refs())
        segments.extend(Ref('Commentary_on_Sefer_Hamitzvot_of_Rasag,_Laws_of_the_Courts').all_segment_refs())
        segments.extend(Ref('Commentary_on_Sefer_Hamitzvot_of_Rasag,_Communal_Laws').all_segment_refs())

        cnt = {"Rasag":0, "Sefer HaMitzvot":0, "Semag":0, "Semak":0}
        dict_list = []
        for seg in segments:
            # sfHmtzvot = re.search(u'(?:ספר המצו?ות|סה"מ).{1,4}(עשין|לאוין|עשה|לא תעשה).{0,20}', seg.text('he').text)
            sfHmtzvot = re.search(u'(?:ספר המצוות|סה"מ)\s{1,4}\((.*?)\)', seg.text('he').text)
            smg = re.search(u'סמ"ג \((.*?)\)', seg.text('he').text)
            smk = re.search(u'סמ"ק (\(.*?\))', seg.text('he').text)
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
                    print "no kind", sfHmtzvot.group(1)
                row_orig["Sefer HaMitzvot"] = sfHmtzvot.group()
                cnt["Sefer HaMitzvot"] += 1
            if smg:
                # row_dict["Rasag"] = re.search("(Sefer.*?\d*?):", seg.normal()).group(1)
                kind, simanim = rasag_exctractor(smg.group(1))
                # row_dict["Semag"] = ['Sefer Mitzvot Gadol, {}.{}'.format(kind, siman) for siman in simanim]
                if kind:
                    row_dict["Semag"] = 'Sefer Mitzvot Gadol, {}.{}'.format(kind, simanim[0])
                else:
                    print "no kind", smg.group(1)
                row_orig["Semag"] = smg.group()
                cnt["Semag"] += 1
            if smk:
                # row_dict["Rasag"] = re.search("(Sefer.*?\d*?):", seg.normal()).group(1)
                # simanim = siman_smk_exctractor(smk.group(1))
                smki = re.search(u"ב?סי'\s+(.*?)(?:\s*\))", smk.group(1))
                if smki:
                    siman = getGematria(smki.group(1))
                    row_dict["Semak"] = "Sefer Mitzvot Katan.{}".format(siman)
                    row_orig["Semak"] = smk.group()
                    cnt["Semak"] += 1
                else:
                    print u'***siman***' + smk.group()

            if row_dict:
                cnt["Rasag"] += 1
                row_dict["Rasag"] = re.search("(Sefer.*?\d*?):", seg.normal()).group(1)
                row_orig["Rasag"] = seg.normal()
                if with_orig:
                    dict_list.append(row_orig)
                dict_list.append(row_dict)
        toCsv(rasagCsvName, ["Rasag", "Sefer HaMitzvot", "Semag", "Semak"], dict_list)
        print cnt


def rasag_exctractor(text):
    split = re.split(u"\s", text)
    simanim = []
    kind = None
    if re.search(u"(:?לאוין|לא תעשה)", split[0]):
            kind = u'Negative Commandments'
    elif re.search(u"(:?עשין|עשה)", split[0]):
            kind = u'Positive Commandments'
    for word in split[1:]:
        siman = getGematria(word)
        simanim.append(siman)
    return kind, simanim


def rasag_linking(csvlinkfile):
    links_rsg_shmtz = []
    links_rsg_smg = []
    links_rsg_smk = []

    with open(u'{}'.format(csvlinkfile), 'r') as csvfile:
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
        for k in row.keys():
            try:
                if k not in ['mitzvah Title chinukh', 'mitzvah Title Rambam', "wiki_rambam", "wiki_table"]:
                    row[k] = eval(row[k])
            except SyntaxError:
                continue
    try:
        mitzvah_set = []
        mitzvah_set_small = []
        mitzvah_set_large = []
        mitzvah_dict = {'chinukh':[], 'smk':[], 'rambam':[], 'smg':[], 'mishneh':[], 'shulchanArukh':[], 'pasuk':[]}
        if int(row[u'chinukh']) <= 613:
            mitzvah_set.append(range_ref(Ref(u'Sefer HaChinukh.{}'.format(row[u'chinukh']))))
            mitzvah_dict[u'chinukh'].append(Ref(u'Sefer HaChinukh.{}'.format(row[u'chinukh'])))
        if (row[u'smk']):
            for smki in (row[u'smk']):
                if isinstance(smki, list):
                    for smkii in smki:
                        mitzvah_set_small.append(Ref(u'Sefer Mitzvot Katan, Remazim.{}'.format(smkii)))
                        mitzvah_set_large.append(range_ref(Ref(u'Sefer Mitzvot Katan.{}'.format(smkii))))
                        mitzvah_dict[u'smk'].append(Ref(u'Sefer Mitzvot Katan, Remazim.{}'.format(smkii)))
                else: # smki isinstance(smki, int):
                    mitzvah_set_small.append(Ref(u'Sefer Mitzvot Katan, Remazim.{}'.format(smki)))
                    mitzvah_set_large.append(range_ref(Ref(u'Sefer Mitzvot Katan.{}'.format(smki))))
                    mitzvah_dict[u'smk'].append(Ref(u'Sefer Mitzvot Katan, Remazim.{}'.format(smki)))
    except (NameError, SyntaxError, InputError):
        print u"chinukh {} ref is empty:".format(row[u'chinukh'])
    try:
        rambam = (row[u'rambam'])
        if rambam:
            if not isinstance(rambam[0], list):
                try:
                    mitzvah_set_small.append(
                        range_ref(Ref(u'Mishneh Torah, {} Mitzvot.{}'.format(rambam[0].strip(), rambam[1]))))
                    mitzvah_set_large.append(range_ref(Ref(u'Sefer HaMitzvot, {} Commandments.{}'.format(rambam[0].strip(), rambam[1]))))
                    mitzvah_dict[u'rambam'].append(range_ref(
                        Ref(u'Sefer HaMitzvot, {} Commandments.{}'.format(rambam[0].strip(), rambam[1]))))
                except IndexError:
                    print u'*problem {} in siman {} *'.format(rambam, row[u'chinukh'])
            else:
                for ram in rambam:
                    if ram:
                        mitzvah_set_small.append(range_ref(Ref(u'Mishneh Torah, {} Mitzvot.{}'.format(ram[0].strip(), ram[1]))))
                        mitzvah_set_large.append(range_ref(Ref(u'Sefer HaMitzvot, {} Commandments.{}'.format(ram[0].strip(), ram[1]))))
                        mitzvah_dict[u'rambam'].append(range_ref(
                            Ref(u'Sefer HaMitzvot, {} Commandments.{}'.format(ram[0].strip(), ram[1]))))
    except NameError as detail:
        print u"chinukh {} ref is empty:".format(row[u'chinukh']), detail
    try:
        smg = (row[u'smg'])
        if smg:
            if isinstance(smg[0], list):
                for smgi in smg:
                    if smgi:
                        mitzvah_set_small.append(Ref(u'Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smgi[0], smgi[1])))
                        mitzvah_set_large.append(range_ref(Ref(u'Sefer Mitzvot Gadol, {}.{}'.format(smgi[0], smgi[1]))))
                        mitzvah_dict[u"smg"].append(Ref(u'Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smgi[0], smgi[1])))
            elif isinstance(smg[0], unicode):
                try:
                    mitzvah_set_small.append(Ref(u'Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smg[0].strip(), smg[1])))
                    mitzvah_set_large.append(range_ref(Ref(u'Sefer Mitzvot Gadol, {}.{}'.format(smg[0].strip(), smg[1]))))
                    mitzvah_dict[u"smg"].append(
                        Ref(u'Sefer Mitzvot Gadol, {}, Remazim.{}'.format(smg[0].strip(), smg[1])))
                except IndexError:
                    print u'*problem {} in siman {} *'.format(smg, row[u'chinukh'])
    except NameError as detail:
        print u"chinukh {} ref is empty:".format(row[u'chinukh']), detail
    try:
        mishneh = row[u'mishneh']
        if mishneh:
            mishneh = (row[u'mishneh'])
            if len(mishneh) == 1:
                mitzvah_set_large.append(Ref(mishneh[0]))
                mitzvah_dict[u"mishneh"].append(Ref(mishneh[0]))
            else:
                for mish in mishneh:
                    if mish:
                        mitzvah_set_large.append(Ref(mish[0]))
                        mitzvah_dict[u"mishneh"].append(Ref(mish[0]))
    except NameError as detail:
        print u"chinukh {} ref is empty:".format(row[u'chinukh']), detail
    try:
        sa = row[u'shulchanArukh']
        if sa:
            sa = (row[u'shulchanArukh'])
            if len(sa) == 1:
                mitzvah_set_large.append(Ref(sa[0]))
                mitzvah_dict[u"shulchanArukh"].append(Ref(sa[0]))
            else:
                for sai in sa:
                    if sai:
                        mitzvah_set_large.append(Ref(sai[0]))
                        mitzvah_dict[u"shulchanArukh"].append(Ref(sai[0]))
        # sets_by_chinukh.append(mitzvah_set)
    except NameError as detail:
        print u"chinukh {} ref is empty:".format(row[u'chinukh']), detail
    pasuk = (row[u'pasuk'])
    if pasuk:
        if not isinstance(pasuk[0], list):
            if pasuk[0] and re.search(u'\d', pasuk[0]):
                mitzvah_set.append(Ref(pasuk[0]))
                mitzvah_dict[u'pasuk'].append(Ref(pasuk[0]))
        else:
            for pas in pasuk:
                if pas:
                    if re.search(u'\d', pas[0]):
                        mitzvah_set.append(Ref(pas[0]))
                        mitzvah_dict[u'pasuk'].append(Ref(pas[0]))

    mitzvah_set_small.extend(mitzvah_set)
    mitzvah_set_large.extend(mitzvah_set)
    if fixing:
        return seg_from_refs(mitzvah_dict), mitzvah_set_small, mitzvah_set_large
    return seg_from_refs(mitzvah_dict)


def seg_from_refs(ref_dict):
    seg_dict = {'chinukh':u'', 'smk':u'', 'rambam':u'', 'smg':u'', 'mishneh':u'', 'pasuk':u'', 'shulchanArukh':u''}
    seg_urls = {'chinukh':u'', 'smk':u'', 'rambam':u'', 'smg':u'', 'mishneh':u'', 'pasuk':u'', 'shulchanArukh':u''}
    for column, refs in ref_dict.items():
        # if column == 'shulchanArukh':
        #     continue
        for ref in refs:
            if ref:
                seg_dict[column] += ref.all_segment_refs()[0].text('he').text
                seg_dict[column] += u'\n'
                url_format = re.sub(u" ", u"_", ref.normal())
                url_format = re.sub(u"_(\d)", ur".\1", url_format)
                seg_urls[column] += u'https://www.sefaria.org/{}\n'.format(url_format)
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
    with open(u'{}'.format(fixedFileName), 'r') as csvfile:
        seg_reader = csv.DictReader(csvfile)

        for i, row in enumerate(seg_reader):
            if not divmod(i, 4)[1] == 1:
                continue
            _, mitzvah_set_small, mitzvah_set_large = row_to_Refs(row, fixing=True)
            mitzvah_cluster_small = create_link_cluster(mitzvah_set_small, 30044, link_type="Sifrei Mitzvot",
                                                  attrs={"generated_by": "viascraped_chinukh_sfm_linker_small", "auto": True})
            mitzvah_cluster_large = create_link_cluster(mitzvah_set_large, 30044, link_type="Sifrei Mitzvot",
                                                  attrs={"generated_by": "viascraped_chinukh_sfm_linker_large",
                                                         "auto": True})
            clusters.append(mitzvah_cluster_small)
            clusters.append(mitzvah_cluster_large)

    print clusters
    print sum(clusters)
    return sets_by_chinukh, clusters, dicts_by_chinukh


if __name__ == "__main__":
    # rambam_chinukh_lnks = scrape_wiki()
    # post_link(rambam_chinukh_lnks, VERBOSE=True)
    # post_link(link_sfrMitzvot_shortCounting(), VERBOSE=True)
    # rows = get_link_data()
    # origns = text_to_csv_links(u'table_w_wiki', rows,  times=2)
    # sets, clusters, mitzvah_dicts = refs_csv(u'mitzvot_test.csv')
    copy_from_local()
    # seferHamitzvot_from_rasag_comm(u"rasag_all_refs", with_orig = True)
    # links = rasag_linking(u'almostRefs.csv')
    # post_link(links, VERBOSE=True)
    # cluster_lines("table_w_wiki.csv")
