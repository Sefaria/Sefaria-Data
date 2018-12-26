# encoding=utf-8

import os
import re
import sys
import math
import json
import codecs
import bleach
import Levenshtein
from functools import partial
from collections import Counter
from tag_merge import merge_tags
from data_utilities.util import traverse_ja
from sources.Shulchan_Arukh.ShulchanArukh import *
from sources.functions import post_text, post_index, post_link, add_category
import django
django.setup()
from sefaria.model import *  # noqa


def standardize_tag_spacing(segment):
    """
    Make sure that all html tags (or series of html tags) present with a space before but no space after
    :param unicode segment:
    :return: unicode
    """
    segment = re.sub(u'\s?(?<![\[(>])((<[^<>]+>)+)(?![):<])\s?', u' \g<1>', segment)
    segment = re.sub(u'\s(?<![(>])((<[^<>]+>)+)(?=[):])(?!<)', u'\g<1>', segment)
    segment = re.sub(u'\[ \(', u'[(', segment)
    segment = re.sub(u'\) \]', u')]', segment)
    return u' '.join(segment.split())


remove_html = partial(bleach.clean, tags=[], attributes={}, strip=True)

txt_files = [
    u'Choshen_Mishpat_1.txt',
    u'Choshen_Mishpat_2.txt',
    u'urim_1.txt',
    u'urim_2.txt',
    u'tumim_1.txt',
    u'tumim_2.txt',
]


def startup(datafile):
    Root.create_skeleton(datafile)
    data_root = Root(datafile)
    data_base = data_root.get_base_text()
    data_base.add_titles(u"Shulchan Arukh, Choshen Mishpat", u"שולחן ערוך חושן משפט")
    data_commentaries = data_root.get_commentaries()
    data_commentaries.add_commentary(u"Urim VeTumim, Urim", u"אורים ותומים, אורים")
    data_commentaries.add_commentary(u"Urim VeTumim, Tumim", u"אורים ותומים, תומים")
    return data_root


def check_markers():
    for filename in txt_files:
        with codecs.open(filename, 'r', 'utf-8') as fp:
            txt = fp.read()
        counts = Counter(re.findall(u'@\d{2}', txt))
        print filename
        for code, counts in sorted(counts.items(), key=lambda x: x[1]):
            print u'{}: {}'.format(code, counts)
        print u'\n'


datafilename = u'urim_vetumim.xml'
if not os.path.exists(datafilename):
    root = startup(datafilename)
else:
    root = Root(datafilename)


def parse():
    base, commentaries = root.get_base_text(), root.get_commentaries()
    for vol_num, txt_file in zip([1, 2], txt_files[:2]):
        print u"\nWorking on {}".format(txt_file)
        base.remove_volume(vol_num)
        with codecs.open(txt_file, 'r', 'utf-8') as fp:
            volume = base.add_volume(fp.read(), vol_num)
        assert isinstance(volume, Volume)
        volume.mark_simanim(u'@00([\u05d0-\u05ea]{1,3})')
        print u"Validating Simanim"
        volume.validate_simanim()

        errors = volume.mark_seifim(u'@11([\u05d0-\u05ea]{1,3})')
        print "Validating Seifim"
        for e in errors:
            print e
        volume.validate_seifim()

        errors = volume.format_text(u'.^', u'$.', u'ramah')
        for e in errors:
            print e

        volume.mark_references(commentaries.commentary_ids[u"Urim VeTumim, Urim"], u"@55\(([\u05d0-\u05ea]{1,3})\)", group=1)
        volume.mark_references(commentaries.commentary_ids[u"Urim VeTumim, Tumim"], u"@66\(([\u05d0-\u05ea]{1,3})\)", group=1)

    urim = commentaries.get_commentary_by_title(u"Urim VeTumim, Urim")
    for vol_num, txt_file in zip([1, 2], txt_files[2:4]):
        print u"\nWorking on {}".format(txt_file)
        urim.remove_volume(vol_num)
        with codecs.open(txt_file, 'r', 'utf-8') as fp:
            volume = urim.add_volume(fp.read(), vol_num)
        assert isinstance(volume, Volume)

        volume.mark_simanim(u'@00([\u05d0-\u05ea]{1,3})')
        volume.validate_simanim(complete=False)
        print "Validating Seifim"
        errors = volume.mark_seifim(u'@22\(([\u05d0-\u05ea]{1,3})\)')
        for e in errors:
            print e
        volume.validate_seifim()

        errors = volume.format_text(u'@11', u'@33', u'dh')
        for e in errors:
            print e

        volume.set_rid_on_seifim()
        b_vol = base.get_volume(vol_num)
        assert isinstance(b_vol, Volume)
        root.populate_comment_store(verbose=True)
        errors = b_vol.validate_all_xrefs_matched(lambda x: x.name == 'xref' and re.search(u'@55', x.text) is not None)
        for e in errors:
            print e

    tumim = commentaries.get_commentary_by_title(u"Urim VeTumim, Tumim")
    for vol_num, txt_file in zip([1, 2], txt_files[4:]):
        print u"\nWorking on {}".format(txt_file)
        tumim.remove_volume(vol_num)
        with codecs.open(txt_file, 'r' ,'utf-8') as fp:
            volume = tumim.add_volume(fp.read(), vol_num)
        assert isinstance(volume, Volume)

        volume.mark_simanim(u'@00([\u05d0-\u05ea]{1,3})')
        volume.validate_simanim(complete=False)
        print "Validating Seifim"
        errors = volume.mark_seifim(u'@22([\u05d0-\u05ea]{1,3})')
        for e in errors:
            print e
        volume.validate_seifim()

        errors = volume.format_text(u'@11', u'@33', u'dh')
        for e in errors:
            print e

        volume.set_rid_on_seifim()
        b_vol = base.get_volume(vol_num)
        assert isinstance(b_vol, Volume)
        root.populate_comment_store(verbose=True)
        errors = b_vol.validate_all_xrefs_matched(lambda x: x.name == 'xref' and re.search(u'@66', x.text) is not None)
        for e in errors:
            print e

    root.export()


# parse()
root.populate_comment_store()
base_text = root.get_base_text().render()

# with open('Shulchan Arukh, Choshen Mishpat - he - Shulhan Arukh, Hoshen ha-Mishpat - Lemberg, 1898.json') as fp:
#     sef_base_text = json.load(fp, encoding='utf-8')['text'][:153]
sef_tc = Ref(u"Choshen Mishpat").text(u"he", u"Shulhan Arukh, Hoshen ha-Mishpat - Lemberg, 1898")
sef_base_text = sef_tc.text
sef_ja = sef_tc.ja()

base_segments, sef_segments = list(traverse_ja(base_text)), list(traverse_ja(sef_base_text))
# assert len(base_segments) == len(sef_segments)

problems = 0
for x_seg, sef_seg in zip(base_segments, sef_segments):
    if x_seg['indices'] != sef_seg['indices']:
        print "Weird!"

    x_text, sef_text = standardize_tag_spacing(x_seg['data']), standardize_tag_spacing(sef_seg['data'])

    try:
        sef_ja.set_element(sef_seg['indices'], merge_tags(sef_text, x_text))
    except AssertionError:
        problems += 1
        print map(lambda x: x+1, x_seg['indices'])
        if problems % 10 == 0:
            print ''

        print remove_html(x_text), u'\n'
        print remove_html(sef_text)
        print Levenshtein.distance(remove_html(x_text), remove_html(sef_text))

        print '\n\n'

if problems:
    print problems
    print "Problems, so exiting early"
    sys.exit(0)


def build_index(title):
    he_title = {
        u"Urim": u"אורים",
        u"Tumim": u",תומים"
    }[title]
    title = u"Urim VeTumim, {}".format(title)
    he_title = u"אורים ותומים, {}".format(he_title)
    j_node = JaggedArrayNode()
    j_node.add_structure([u'Siman', u'Seif'])
    j_node.add_primary_titles(title, he_title)
    return {
        u'title': title,
        u'categories': [u"Halakhah", u"Shulchan Arukh", u"Commentary", u"Urim VeTumim"],
        u"dependence": u"Commentary",
        u"collective_title": title,
        u"schema": j_node.serialize(),
        u"base_text_titles": [u"Shulchan Arukh, Choshen Mishpat"]
    }


urim_vetumim = root.get_commentaries()
server = 'http://urim.sandbox.sefaria.org'
add_category(u"Urim VeTumim", [u"Halakhah", u"Shulchan Arukh", u"Commentary", u"Urim VeTumim"], server=server)


version_json = {
    u"versionTitle": u"Urim veTumim, Warsaw 1881",
    u"versionSource": u"http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001167224",
    u"language": u"he"
}


def split_version(version_dict, splits):
    def edges(length, num_splits):
        ratio = float(length) / float(num_splits)
        indices = [math.trunc(ratio*i) for i in range(num_splits+1)]
        return zip(indices[:-1], indices[1:])

    volumes = []
    for vol_num, (start, end) in enumerate(edges(len(version_dict['text']), splits), 1):
        new_version = {
            u'versionTitle': u'{}, Vol {}'.format(version_dict[u'versionTitle'], vol_num),
            u'versionSource': version_dict[u'versionSource'],
            u'language': version_dict[u'language'],
            u'text': [t if start <= ind < end else [] for ind, t in enumerate(version_dict[u'text'])]
        }
        volumes.append(new_version)
    return volumes


def upload_commentary(title):
    c_index = build_index(title)
    c_xml = urim_vetumim.get_commentary_by_title(u"Urim VeTumim, {}".format(title))
    c_text = c_xml.render()
    c_links = c_xml.collect_links()
    for l in c_links:
        l['refs'] = [re.sub(u' on Shulchan Arukh, Choshen Mishpat', u'', lr) for lr in l['refs']]
    post_index(c_index, server)
    version_json[u"text"] = c_text
    if title == u"Tumim":
        for v in split_version(version_json, 2):
            post_text(u"Urim VeTumim, {}".format(title), v, index_count=u"on", server=server)
    else:
        post_text(u"Urim VeTumim, {}".format(title), version_json, index_count=u"on", server=server)
    post_link(c_links, weak_network=True)


upload_commentary(u"Urim")
upload_commentary(u"Tumim")

choshen_mishpat_version = {
    u"versionTitle": sef_tc.vtitle,
    u"versionSource": sef_tc.version().versionSource,
    u"language": u"he",
    u"text": sef_tc.text
}
post_text(u"Shulchan Arukh, Choshen Mishpat", choshen_mishpat_version, index_count="on", server=server)
