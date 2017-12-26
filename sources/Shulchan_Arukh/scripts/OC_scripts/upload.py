#encoding=utf-8

import os
import regex
import bleach
import argparse
import requests
import unicodecsv
import collections
from sefaria.model import *
from sources import functions
from sources.Shulchan_Arukh.ShulchanArukh import *


def get_alt_struct(book_title):

    with open('Orach_Chaim_Topics.csv') as infile:
        reader = unicodecsv.DictReader(infile)
        rows = [row for row in reader]

    s_node = SchemaNode()
    s_node.add_primary_titles('Topic', u'נושא', key_as_title=False)
    for row in rows:
        node = ArrayMapNode()
        node.add_primary_titles(row['en'], row['he'])
        node.depth = 0
        node.includeSections = True
        node.wholeRef = u'{} {}-{}'.format(book_title, row['start'], row['end'])
        node.validate()
        s_node.append(node)
    return s_node.serialize()


def shaarei_special_links():
    with open('../../Shaarei Teshuvah added links.csv') as infile:
        reader = unicodecsv.reader(infile)
        rows = [row for row in reader]
    return [{
        'refs': row,
        'type': 'commentary',
        'auto': True,
        'generated_by': 'Shulchan Arukh Parser'
    } for row in rows]


def shulchan_arukh_index(server='http://localhost:8000', *args, **kwargs):
    original_index = functions.get_index_api("Shulchan Arukh, Orach Chayim", server=server)
    original_index['alt_structs'] = {'Topic': get_alt_struct("Shulchan Arukh, Orach Chayim")}
    return original_index


def commentary_index(en_title, he_title, commentator):
    jnode = JaggedArrayNode()
    jnode.add_primary_titles(en_title, he_title)
    jnode.add_structure(["Siman", "Seif"], address_types=["Siman", "Seif"])
    jnode.validate()

    index_dict = {
        "title": en_title,
        "categories": ["Halakhah", "Shulchan Arukh", "Commentary", commentator],
        "dependence": "Commentary",
        "collective_title": commentator,
        "alt_structs": {"Topic": get_alt_struct(en_title)},
        "schema": jnode.serialize(),
        "base_text_titels": ["Shulchan Arukh, Orach Chayim"]
    }
    return index_dict


def generic_cleaner(ja, clean):
    for i, siman in enumerate(ja):
        for j, seif in enumerate(siman):
            ja[i][j] = clean(seif)


def orach_chaim_clean(ja):
    def repl(x):
        stuff = {u'\u05f3': u"'", u'\u05c3': u':', u'\u05f4': u'"'}
        return stuff[x.group()]

    def clean(strn):
        strn = re.sub(u'(%|#+)', u'', strn)
        strn = re.sub(u'[\u05f3\u05c3\u05f4]', repl, strn)
        strn = re.sub(u'\(\)', u'', strn)
        strn = re.sub(ur'^([^(]+)\)', u'\g<1>', strn)
        strn = re.sub(ur'\s{2,}', u' ', strn)
        strn = regex.sub(ur'(\s(?:(?><i[^>]+)><\/i>)+)\s', u'\g<1>', strn)
        return strn

    generic_cleaner(ja, clean)


def add_siman_headers(ja):
    xml_simanim = root.get_base_text().get_simanim()
    assert len(ja) == len(xml_simanim)
    for siman, xml_siman in zip(ja, xml_simanim):
        title_text = re.sub(u' *\n *', u'', xml_siman.Tag.contents[0].text)
        if title_text == u'':
            continue
        if re.search(u'@', title_text) is not None:
            print u'Weird mark at Siman {}'.format(xml_siman.num)
        siman[0] = u'<b>{}</b><br>{}'.format(title_text, siman[0])


def taz_clean(ja):
    def clean(strn):
        replacements = [u"\(#\)", u"#\)", u"\[#\]", u"#\]", u"\?", u"%+"] #References to Levushei HaSrad
        for r in replacements:
            strn = re.sub(r, u"", strn)
        return strn
    generic_cleaner(ja, clean)

def eshel_clean(ja):
    def clean(strn):
        strn = strn.replace(u'\u201c', u'"')
        return strn.replace(u"?", u"")
    generic_cleaner(ja, clean)

def chok_clean(ja):
    def repl(x):
        stuff = {u'\u05f3': u"'", u'\u05c3': u':', u'\u05f4': u'"'}
        return stuff[x.group()]

    def clean(strn):
        strn =  strn.replace(u"?", u"")
        strn = re.sub(u'[\u05f3\u05c3\u05f4]', repl, strn)
        return strn

    generic_cleaner(ja, clean)

def ateret_clean(ja):
    def clean(strn):
        strn = strn.replace(u"?", u"")
        strn = re.sub(u'^\u2022 *', u'', strn)
        return strn
    generic_cleaner(ja, clean)

def shaarei_clean(ja):
    return

def beer_clean(ja):
    def clean(strn):
        return re.sub(u'\?', u'', strn)
    generic_cleaner(ja, clean)

def check_marks(comm, clean):
    finds = []
    commentary_text = clean(comm.render())

    for siman_text in commentary_text:
        for seif_text in siman_text:
            finds += re.findall(u"[^\s\u05d0-\u05ea\'\"\.\:,;\)\(\]\[]{1,7}", bleach.clean(seif_text, [], strip=True))
    all_finds = collections.Counter(finds)

    for key, value in all_finds.items():
        print u"{} -> {} occurrences".format(key, value)

    return commentary_text


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--title", default=None)
    parser.add_argument("-s", "--server", default="http://localhost:8000")
    parser.add_argument("-v", "--verbose", action='store_true', default=False)
    parser.add_argument("-a", "--add_term", action='store_true', default=False)
    user_args = parser.parse_args()


    root = Root('../../Orach_Chaim.xml')
    root.populate_comment_store()

    base_text_title = u"Shulchan Arukh, Orach Chayim"
    he_base_title = u"שולחן ערוך אורח חיים"
    links = []

    post_parse = {
        u"Turei Zahav": taz_clean,
        u"Eshel Avraham": eshel_clean,
        u"Ateret Zekenim": ateret_clean,
        u"Chok Yaakov": chok_clean,
        u"Sha'arei Teshuvah": shaarei_clean,
        u"Be'er HaGolah": beer_clean,
    }

    if user_args.title is None:
        book_name, he_book_name = base_text_title, he_base_title
        book_ja = root.get_base_text().render()
        index = shulchan_arukh_index(user_args.server)
        orach_chaim_clean(book_ja)
        add_siman_headers(book_ja)

    else:
        book_name = u"{} on {}".format(user_args.title, base_text_title)
        book_xml = root.get_commentaries().get_commentary_by_title(user_args.title)
        book_ja = book_xml.render()
        he_book_name = u"{} על {}".format(book_xml.titles['he'], he_base_title)
        links = book_xml.collect_links()
        if user_args.title == u"Sha'arei Teshuvah":
            links += shaarei_special_links()
        index = commentary_index(book_name, he_book_name, user_args.title)
        post_parse[user_args.title](book_ja)

        if user_args.add_term:
            functions.add_term(user_args.title, book_xml.titles['he'], server=user_args.server)

        functions.add_category(user_args.title, index['categories'], server=user_args.server)

    if user_args.verbose:
        print index

    functions.post_index(index, server=user_args.server)

    # version = {
    #     "versionTitle": "Maginei Eretz; Shulchan Aruch Orach Chaim, Lemberg, 1893",
    #     "versionTitleInHebrew": u"""ספר מגיני ארץ; שלחן ערוך. למברג, תרנ"ג""",
    #     "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002084080",
    #     "language": "he",
    #     "text": book_ja,
    # }
    version = {
        "versionTitle": "Maginei Eretz: Shulchan Aruch Orach Chaim, Lemberg, 1893",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002084080",
        "language": "he",
        "text": book_ja,
    }
    functions.post_text(book_name, version, index_count="on", server=user_args.server)
    if links:
        functions.post_link(links, server=user_args.server)

    # for title, clean_func in post_parse.items():
    #     print
    #     print title
    #     comm = commentaries.get_commentary_by_title(title.split(" on")[0])
    #     comm = check_marks(comm, clean_func)
    #
    # print
    # print "Checking Orach Chaim"
    # base = check_marks(root.get_base_text(), orach_chaim_clean)
    functions.post_flags({'ref': book_name, 'lang': 'he', 'vtitle': version['versionTitle']},
                         {"versionTitleInHebrew": u"""ספר מגיני ארץ: שלחן ערוך. למברג, תרנ"ג""",}, user_args.server)

    try:
        requests.post(os.environ['SLACK_URL'], json={'text':'{} uploaded successfully'.format(book_name)})
    except KeyError:
        pass


