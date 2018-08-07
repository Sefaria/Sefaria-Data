# encoding=utf-8

import os
import argparse
import requests
import unicodecsv
from sources import functions
from sefaria.model import *
from collections import Counter
from os.path import dirname as loc
from sources.Shulchan_Arukh.ShulchanArukh import *

root_dir = loc(loc(loc(os.path.abspath(__file__))))
xml_loc = os.path.join(root_dir, 'Yoreh_Deah.xml')


def get_alt_struct(book_title):
    base_text = root.get_base_text()
    with open('Shulchan_Arukh_YD_titles.csv') as fp:
        reader = unicodecsv.DictReader(fp)
        rows = [row for row in reader]
    assert len(rows) == len(base_text.Tag.find_all('topic'))

    root_node = SchemaNode()
    root_node.add_primary_titles('Topic', u'נושא', key_as_title=False)
    for row in rows:
        node = ArrayMapNode()
        node.add_primary_titles(row['en'], row['he'])
        node.wholeRef = re.sub(u"Shulchan Arukh, Yoreh De'ah", book_title, row['reference'])
        node.includeSections = True
        node.depth = 0
        root_node.append(node)
    return root_node.serialize()


def shulchan_arukh_index(server='http://localhost:8000', *args, **kwargs):
    original_index = functions.get_index_api(u"Shulchan Arukh, Yoreh De'ah", server=server)
    alt_struct = get_alt_struct(u"Shulchan Arukh, Yoreh De'ah")
    if 'alt_structs' not in original_index:
        original_index['alt_structs'] = {}
    original_index['alt_structs']['Topic'] = alt_struct
    return original_index


def commentary_schema(en_title, he_title):
    jnode = JaggedArrayNode()
    jnode.add_primary_titles(en_title, he_title)
    jnode.add_structure([u"Siman", u"Seif"])
    return jnode.serialize()


def add_siman_headers(ja):
    xml_simanim = root.get_base_text().get_simanim()
    text_simanim = iter(ja)
    for xml_siman in xml_simanim:
        text_siman = next(t for t in text_simanim if len(t) > 0)
        for title in xml_siman.Tag.find_all('title'):
            title_text = re.sub(u'\s*$', u'', title.text)
            if title_text == u'':
                continue
            if re.search(u'@', title_text) is not None:
                print u"Weird mark at Siman {}".format(xml_siman.num)
            seif_index = int(title['found_after'])
            text_siman[seif_index] = u'<b>{}</b><br>{}'.format(title_text, text_siman[seif_index])


def generic_cleaner(ja, clean_callback):
    assert isinstance(ja, list)
    for i, item in enumerate(ja):
        if isinstance(item, list):
            generic_cleaner(item, clean_callback)
        elif isinstance(item, basestring):
            ja[i] = clean_callback(item)
        else:
            raise TypeError


def traverse(ja):
    assert isinstance(ja, list)
    for sub_ja in ja:
        if isinstance(sub_ja, basestring):
            yield sub_ja
        else:
            for traversal in traverse(sub_ja):
                yield traversal


def clean_spaces(func):
    def new_func(s):
        s = func(s)
        s = re.sub(u'(\s){2,}', u'\g<1>', s)
        s = re.sub(u'\s+$', u'', s)
        s = re.sub(u'^\s+', u'', s)
        s = re.sub(u'\s+([^\u05d0-\u05ea])$', u'\g<1>', s)
        s = re.sub(u'>\s', u'>', s)
        return s
    return new_func


def base_post_parse(ja):
    @clean_spaces
    def clean(s):
        return re.sub(u'[*?]', u'', s)

    add_siman_headers(ja)
    generic_cleaner(ja, clean)


def clean_taz(ja):
    @clean_spaces
    def clean(s):
        return re.sub(u'(~77 ?\(?\)?)|(#\))|(\?)', u'', s)
    generic_cleaner(ja, clean)


def remove_question_marks(ja):
    """
    Used for:
    Be'er HaGolah
    Beur HaGrah
    Pithei Teshuva
    Torat HaShlamim
    Nekudat HaKesef
    """
    @clean_spaces
    def clean(s):
        return re.sub(u'\?', u'', s)
    generic_cleaner(ja, clean)


def shach_clean(ja):
    @clean_spaces
    def clean(s):
        s = re.sub(u'\?', u'', s)
        s = re.sub(u'\u05f4', u'"', s)
        return s
    generic_cleaner(ja, clean)
    generic_cleaner(ja, lambda x: re.split(u'~seg~', x))


def shach_index(en_title, he_title, commentator):
    root_node = SchemaNode()
    root_node.add_primary_titles(en_title, he_title)
    d_node = JaggedArrayNode()
    d_node.key = 'default'
    d_node.default = True
    d_node.add_structure(["Siman", "Seif", "Paragraph"])
    d_node.toc_zoom = 2
    root_node.append(d_node)

    safek_node = JaggedArrayNode()
    safek_node.add_primary_titles(u"S'fek S'feka Summary", u'דיני ספק ספקא בקצרה')
    safek_node.add_structure([u'Seif'])
    root_node.append(safek_node)

    alt_root = SchemaNode(get_alt_struct(en_title))
    safek_alt = ArrayMapNode()
    safek_alt.add_primary_titles(u"S'fek S'feka", u"דיני ספק ספקא")
    safek_alt.wholeRef = u"{} 110".format(en_title)
    safek_alt.depth = 0
    safek_alt.includeSections = True
    alt_root.append(safek_alt)
    summary_alt = ArrayMapNode()
    summary_alt.add_primary_titles(u"S'fek S'feka Summary", u'דיני ספק ספקא בקצרה')
    summary_alt.wholeRef = u"{}, S'fek S'feka Summary".format(en_title)
    summary_alt.depth = 0
    alt_root.append(summary_alt)

    return {
        u"title": en_title,
        u"categories": [u"Halakhah", u"Shulchan Arukh", u"Commentary", commentator],
        u"dependence": u"Commentary",
        u"collective_title": commentator,
        u"alt_structs": {u"Topic": alt_root.serialize()},
        u"schema": root_node.serialize(),
        u"base_text_titles": [u"Shulchan Arukh, Yoreh De'ah"]
    }


def commentary_index(en_title, he_title, commentator):
    if commentator == u'Siftei Kohen':
        return shach_index(en_title, he_title, commentator)
    else:
        return {
            u"title": en_title,
            u"categories": [u"Halakhah", u"Shulchan Arukh", u"Commentary", commentator],
            u"dependence": u"Commentary",
            u"collective_title": commentator,
            u"alt_structs": {u"Topic": get_alt_struct(en_title)},
            u"schema": commentary_schema(en_title, he_title),
            u"base_text_titles": [u"Shulchan Arukh, Yoreh De'ah"]
        }


def shach_sfek_sefeka():
    commentaries = root.get_commentaries()
    shach = commentaries.get_commentary_by_title(u"Siftei Kohen")
    sfek_tag = shach.Tag.find("Sfek_Sfeka_Summary")
    sfek_tag['num'] = 1
    sfek_siman = Siman(sfek_tag)
    sfek_siman.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})')
    sfek_siman.validate_seifim()
    sfek_siman.format_text(u'@32', u'@33', u'dh')
    return sfek_siman.render()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--title", default=None)
    parser.add_argument("-s", "--server", default="http://localhost:8000")
    parser.add_argument("-a", "--add_term", action="store_true", default=False)
    parser.add_argument("-v", "--verbose", action="store_true", default=False)
    parser.add_argument("-n", "--no_slack", action="store_true", default=False)
    user_args = parser.parse_args()

    base_text = u"Shulchan Arukh, Yoreh De'ah"
    he_base_text = u"שולחן ערוך יורה דעה"

    root = Root(xml_loc)
    root.populate_comment_store()

    if user_args.title is None:  # This is the Shulchan Arukh
        book_name, he_book_name = base_text, he_base_text
        book_ja = root.get_base_text().render()
        base_post_parse(book_ja)
        index = shulchan_arukh_index(user_args.server)
        links = []

    else:
        book_name = u"{} on {}".format(user_args.title, base_text)
        book_xml = root.get_commentaries().get_commentary_by_title(user_args.title)
        book_ja = book_xml.render()
        he_book_name = u"{} על {}".format(book_xml.titles['he'], he_base_text)
        links = book_xml.collect_links()
        if user_args.title == u'Nekudat HaKesef':
            for link in links:
                link['refs'][0] = re.sub(u'Turei Zahav|Siftei Kohen', u'\g<0> on {}'.format(base_text), link['refs'][0])
                link['refs'][1] = re.sub(u'Turei Zahav|Siftei Kohen', base_text, link['refs'][1])
            print links[0]['refs']

        index = commentary_index(book_name, he_book_name, user_args.title)
        if user_args.title == u'Siftei Kohen':
            shach_clean(book_ja)
        elif user_args.title == u'Turei Zahav':
            clean_taz(book_ja)
        else:
            remove_question_marks(book_ja)

        if user_args.add_term:
            functions.add_term(user_args.title, book_xml.titles['he'], server=user_args.server)
        functions.add_category(user_args.title, index['categories'], server=user_args.server)

    if user_args.verbose:
        print index
    functions.post_index(index, server=user_args.server)

    version = {
        "versionTitle": "Shulchan Arukh, Yoreh De'ah Lemberg PlaceHolder VersionTitle",
        "versionSource": "Change Me!!!!",
        "language": "he",
        "text": book_ja
    }
    if user_args.title == u'Siftei Kohen':
        functions.post_text(book_name, version, server=user_args.server)
        version["text"] = shach_sfek_sefeka()
        functions.post_text(u"{}, {}".format(book_name, u"S'fek S'feka Summary"), version, index_count="on", server=user_args.server)
    else:
        functions.post_text(book_name, version, index_count="on", server=user_args.server)

    flags = dict(versionTitleInHebrew=u"למברג יורה דעה אבל צריך לעדכן את הכותרת הזאת")
    if user_args.title is None:
        flags['priority'] = 2
    functions.post_flags(dict(ref=book_name, lang='he', vtitle=version['versionTitle']), flags, user_args.server)

    if links:
        functions.post_link(links, server=user_args.server)

    if user_args.no_slack:
        pass
    else:
        requests.post(os.environ["SLACK_URL"], json={"text": u"{} Upload Complete".format(
            user_args.title if user_args.title else u"Shulchan Arukh, Yoreh De'ah")})
