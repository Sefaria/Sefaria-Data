#encoding=utf-8

import re
import os
import argparse
import requests
import unicodecsv
from sefaria.model import *
from data_utilities.util import ja_to_xml
from sources.Shulchan_Arukh.ShulchanArukh import *
from sources.functions import post_text, get_index_api, post_index, post_link, add_term

root = Root("../../Choshen_Mishpat.xml")
root.populate_comment_store()


def get_alt_struct(book_title):
    """
    Get topics from base
    Each node goes from <start>-<finish>
    start = 1
    end = next_topic.next_sibling['num']
    if next_topic.name == 'seif':
        use <parent.num>:next_sibling.num
    if at the end:
        use len(all_simanim)
    :param book_title:
    :return:
    """
    base_text = root.get_base_text()
    topics = [t for t in base_text.Tag.find_all('topic')]

    with open('Shulchan_Arukh_titles.csv') as infile:
        reader = unicodecsv.DictReader(infile)
        en_topics = [row['Shulchan Arukh - en'] for row in reader]
    assert len(en_topics) == len(topics)

    s_node = SchemaNode()
    s_node.add_primary_titles('Topic', u'נושא', False)

    start_siman, start_seif = 1, None
    for i, (topic, en_topic) in enumerate(zip(topics, en_topics)):
        node = ArrayMapNode()
        node.add_primary_titles(en_topic, re.sub(u' *\n *', u'', topic.text))
        node.depth = 0
        node.includeSections = True

        if len(topics) - i == 1:  #last item in topics
            end_siman = len(base_text.get_simanim())
            end_seif = None

        elif topics[i+1].next_sibling.name == 'seif':
            end_siman = int(topics[i+1].parent['num'])
            end_seif = int(topics[i+1].previous_sibling['num'])

        else:
            end_siman = int(topics[i+1].next_sibling['num']) - 1
            end_seif = None

        if end_seif:
            node.wholeRef = u'{} {}:1-{}:{}'.format(book_title, start_siman, end_siman, end_seif)
            start_seif = end_seif + 1
            start_siman = end_siman

        elif start_siman == end_siman:
            if start_seif:
                total_simanim = len(base_text.get_simanim()[start_siman-1].get_child())
                node.wholeRef = u'{} {}:{}-{}:{}'.format(book_title, start_siman, start_seif, end_siman, total_simanim)
            else:
                node.wholeRef = u'{} {}'.format(book_title, start_siman)
            start_seif = None
            start_siman = end_siman + 1

        elif start_seif:
            total_simanim = len(base_text.get_simanim()[end_siman - 1].get_child())
            node.wholeRef = u'{} {}:{}-{}:{}'.format(book_title, start_siman, start_seif, end_siman, total_simanim)
            start_seif = None

        else:
            node.wholeRef = u'{} {}-{}'.format(book_title, start_siman, end_siman)
            start_siman = end_siman + 1



        s_node.append(node)
    return s_node.serialize()


def generic_cleaner(ja, cb):
    for i, siman in enumerate(ja):
        for j, seif in enumerate(siman):
            ja[i][j] = cb(seif)


def shulchan_arukh_post_parse(shulchan_ja):
    xml_simanim = root.get_base_text().get_simanim()
    assert len(shulchan_ja) == len(xml_simanim)

    for siman_ja, xml_siman in zip(shulchan_ja, xml_simanim):
        if xml_siman.Tag.contents[0].name == 'title':
            title_text = re.sub(u' *\n *', u'', xml_siman.Tag.contents[0].text)
            siman_ja[0] = u'<b>{}</b><br>{}'.format(title_text, siman_ja[0])

        for i, seif in enumerate(siman_ja):
            seif = re.sub(ur'\(("|\?)\)|\?', u'', seif)
            seif = re.sub(u' {2,}', u' ', seif)
            seif = re.sub(ur'( (<[^>]+>)+) ', ur'\g<1>', seif)
            siman_ja[i] = seif


def sma_post_parse(sma_ja):
    for i, siman in enumerate(sma_ja):
        for j, seif in enumerate(siman):
            seif = re.sub(ur'\(("|\?)\)|#', u'', seif)
            seif = re.sub(ur'%+', u'\u261c', seif)
            seif = re.sub(u' {2,}', u' ', seif)
            sma_ja[i][j] = seif


def pithei_clean(ja):
    for i , siman in enumerate(ja):
        for j, seif in enumerate(siman):
            seif = re.sub(ur'%', u'', seif)
            seif = re.sub(u' {2,}', u' ', seif)
            ja[i][j] = seif


def gra_clean(ja):
    def clean(t):
        t = re.sub(ur'\*', u'', t)
        t = re.sub(u' {2,}', u' ', t)
        return t
    generic_cleaner(ja, clean)


def shach_clean_and_split(ja):
    def cb(t):
        t = re.sub(ur'\*|\?|\("\)', ur'', t)
        t = re.sub(ur' *\n *', u' ', t)
        t = re.sub(ur' {2,}', u' ', t)
        return [p for p in t.split(u'~seg~')]
    generic_cleaner(ja, cb)


def beer_hagola_clean(ja):
    def cb(t):
        t = re.sub(ur'\n', u' ', t)
        t = re.sub(ur'#|\+', u'\u261c', t)
        t = re.sub(ur'\?', u'', t)
        return re.sub(ur' {2,}', u' ', t)
    generic_cleaner(ja, cb)


def netivot_hiddushum_clean(ja):
    def cb(t):
        t = re.sub(ur'\n', u' ', t)
        t = re.sub(ur'\*|\?', u'' ,t)
        t = re.sub(ur'[()]{2}', u'\u261c', t)
        t = re.sub(ur'\("\)', u'', t)
        return re.sub(ur' {2}', u' ', t)
    generic_cleaner(ja, cb)



def split_segments(text_ja):
    for i, siman in enumerate(text_ja):
        for j, seif in enumerate(siman):
            text_ja[i][j] = [re.sub(u' *\n *', u' ', sub_sec) for sub_sec in seif.split(u'~seg~')]


def clean_beurim(ja):
    def cb(t):
        t = re.sub(ur'[()]{2}', u'\u261c', t)
        t = re.sub(ur'\("\)', u'', t)
        t = re.sub(ur'\?|\*', u'', t)
        t = re.sub(ur'\n', u' ', t)
        return re.sub(u' {2,}', u' ', t)
    generic_cleaner(ja, cb)


def shulchan_arukh_index(server='http://localhost:8000', *args, **kwargs):
    original_index = get_index_api("Shulchan Arukh, Choshen Mishpat", server=server)
    alt_struct = get_alt_struct("Shulchan Arukh, Choshen Mishpat")
    original_index['alt_structs'] = {'Topic': alt_struct}
    return original_index


def create_simple_index(en_title, he_title, commentator, depth=2, *args, **kwargs):
    jnode = JaggedArrayNode()
    jnode.add_primary_titles(en_title, he_title)
    if depth == 2:
        jnode.add_structure(["Siman", "Seif"], address_types=["Siman", "Seif"])
    elif depth == 3:
        jnode.add_structure(["Siman", "Seif", "Paragraph"], address_types=["Siman", "Seif", "Integer"])
        jnode.toc_zoom = 2
    else:
        raise ValueError("Depth must be set to 2 or 3")
    jnode.validate()

    index_dict =  {
        'title': en_title,
        'categories': ["Halakhah", "Shulchan Arukh", "Commentary", commentator],
        'dependence': "Commentary",
        'collective_title': commentator,
        'alt_structs': {'Topic': get_alt_struct(en_title)},
        'schema': jnode.serialize()
    }
    return index_dict


def depth_3_index(en_title, he_title, commentator, *args, **kwargs):
    return create_simple_index(en_title, he_title, commentator, depth=3)


def gra_index(*args, **kwargs):
    pre_index = create_simple_index(*args, **kwargs)
    pre_index['authors'] = "Gra"
    return pre_index


post_parse = {
    u'Shulchan Arukh, Choshen Mishpat': shulchan_arukh_post_parse,
    u'Ketzot HaChoshen on Shulchan Arukh, Choshen Mishpat': split_segments,
    u"Me'irat Einayim on Shulchan Arukh, Choshen Mishpat": sma_post_parse,
    u'Pithei Teshuva on Shulchan Arukh, Choshen Mishpat': pithei_clean,
    u'Beur HaGra on Shulchan Arukh, Choshen Mishpat': gra_clean,
    u'Siftei Kohen on Shulchan Arukh, Choshen Mishpat': shach_clean_and_split,
    u"Be'er HaGolah on Shulchan Arukh, Choshen Mishpat": beer_hagola_clean,
    u"Netivot HaMishpat, Hidushim on Shulchan Arukh, Choshen Mishpat": netivot_hiddushum_clean
}

index_methods = {
    u'Shulchan Arukh, Choshen Mishpat': shulchan_arukh_index,
    u'Ketzot HaChoshen on Shulchan Arukh, Choshen Mishpat': depth_3_index,
    u'Beur HaGra on Shulchan Arukh, Choshen Mishpat': gra_index,
    u'Siftei Kohen on Shulchan Arukh, Choshen Mishpat': depth_3_index,
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--title", default=None)
    parser.add_argument("-s", "--server", default="http://localhost:8000")
    parser.add_argument("-a", "--add_term", action='store_true', default=False)
    parser.add_argument("-v", "--verbose", action='store_true', default=False)
    user_args = parser.parse_args()

    base_text = u'Shulchan Arukh, Choshen Mishpat'
    he_base_text = u'שולחן ערוך חושן משפט'
    links = []

    if user_args.title is None:  # This is the Shulchan Arukh
        book_name, he_book_name = base_text, he_base_text
        book_ja = root.get_base_text().render()
    else:
        book_name = u'{} on {}'.format(user_args.title, base_text)
        book_xml = root.get_commentaries().get_commentary_by_title(user_args.title)
        book_ja = book_xml.render()
        he_book_name = u'{} על {}'.format(book_xml.titles['he'], he_base_text)
        links = book_xml.collect_links()

        if user_args.add_term:
            add_term(user_args.title, book_xml.titles['he'], server=user_args.server)

    index = index_methods.get(book_name, create_simple_index)(en_title=book_name, he_title=he_book_name,
                                         commentator=user_args.title, server=user_args.server)
    if user_args.verbose:
        print index

    post_index(index, server=user_args.server)

    if post_parse.get(book_name):
        post_parse[book_name](book_ja)
    version = {
        'versionTitle': "Shulhan Arukh, Hoshen ha-Mishpat; Lemberg, 1898",
        'versionSource': "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002097773",
        'language': 'he',
        'text': book_ja
    }
    post_text(book_name, version, index_count='on', server=user_args.server)
    if links:
        post_link(links, server=user_args.server)

    requests.post(os.environ['SLACK_URL'], json={'text': 'Upload Complete'})
