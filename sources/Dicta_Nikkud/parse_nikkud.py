# encoding=utf-8

from __future__ import unicode_literals, print_function

import re
import os
import codecs
import bleach

import django
django.setup()

from sefaria.utils.hebrew import strip_nikkud
from data_utilities.dibur_hamatchil_matcher import match_text
from sefaria.model import *


davidson_vtitle = 'William Davidson Edition - Aramaic'
dicta_vtitle = 'Dicta Nikkud'


def prepare_sefaria_text(oref):
    """
    :param Ref oref:
    :return:
    """
    tc = oref.text('he', davidson_vtitle)
    text_list = tc.ja().flatten_to_array()
    return [bleach.clean(t, tags=[], attributes={}) for t in text_list]


def prepare_dicta_text(filename):
    with codecs.open(filename, 'r', 'utf-8') as fp:
        dicta_text = fp.read()

    return dicta_text.split()


def extract_ref_from_filename(filename):
    ref_match = re.search(r'(?:^|/)([^/]+)\.txt$', filename)
    if ref_match:
        return ref_match.group(1)
    else:
        return None


def align_file(filename):
    tref = extract_ref_from_filename(filename)
    oref = Ref(tref)

    with codecs.open(filename, 'r', 'utf-8') as fp:
        dicta_text = fp.read()

    with_nikkud, without_nukkud = dicta_text.split(), strip_nikkud(dicta_text).split()
    sefaria_text = prepare_sefaria_text(oref)

    dh_match = match_text(without_nukkud, sefaria_text)

    matches = dh_match['matches']
    segments = oref.all_segment_refs()
    assert len(segments) == len(matches)

    for segment, match in zip(segments, matches):
        tc = segment.text('he', dicta_vtitle)
        new_segment_text = u' '.join(with_nikkud[match[0]:match[1]+1])
        if not new_segment_text:
            new_segment_text = segment.text('he', davidson_vtitle).text

        tc.text = new_segment_text
        tc.save()
    

"""
dh matcher:
  load up a textChunk for the Ref associated with the file
  get a list of segment refs for this Ref
  convert textChunk to flat list
  bleach each element in the list
  split the dicta text into words
  remove nikkud from dicta
"""


def filename_sort_key(filename):
    tref = extract_ref_from_filename(filename)
    if not tref:
        return 100000

    return Ref(tref).sections


def create_nikkud_version():
    version = Version().load({'versionTitle': dicta_vtitle, 'language': 'he'})
    if version:
        version.delete()

    for ftitle in sorted(os.listdir('./Berakhot'), key=filename_sort_key):
        print(ftitle)
        ftitle = os.path.join('./Berakhot', ftitle)
        align_file(ftitle)


def compare_versions():
    oref = Ref("Berakhot 2a-46b")
    segments = oref.all_segment_refs()
    for segment in segments:
        davidson, dicta = segment.text('he', davidson_vtitle), segment.text('he', dicta_vtitle)
        if len(davidson.text.split()) != len(dicta.text.split()):
            print('Length mismatch in {}'.format(segment.normal()), davidson.text, dicta.text, '\n', sep='\n')


def prettify_text_segment(davidson_text, dicta_text):
    """
    :param unicode davidson_text:
    :param unicode dicta_text:
    :return: unicode
    """
    def add_html_to_word(davidson_word, dicta_word):
        tag_list = []
        for tag in re.findall(r'<[a-z]+>', davidson_word):
            tag_list.append(tag)

        tag_list.append(dicta_word)

        for tag in re.findall(r'</[a-z]+>', davidson_word):
            tag_list.append(tag)

        return ''.join(tag_list)

    # add colon to dicta text at end of sugya (ensure idempotency)
    if re.search(r':$', davidson_text) and not re.search(r':$', dicta_text):
        dicta_text = u'{}:'.format(dicta_text)

    # if no html exists in the davidson edition, we can return
    if bleach.clean(davidson_text, tags=[], attributes={}, strip=True) == davidson_text:
        return dicta_text

    dicta_text = bleach.clean(dicta_text, tags=[], attributes={}, strip=True)  # idempotency
    davidson_words, dicta_words = davidson_text.split(), dicta_text.split()

    # algorithm depends on 1-to-1 mapping of words
    if len(davidson_words) != len(dicta_words):
        raise AssertionError("length mismatch")

    return u' '.join([add_html_to_word(dav, dic) for dav, dic in zip(davidson_words, dicta_words)])


def prettify_text(tref):
    for segment in Ref(tref).all_segment_refs():
        davidson_tc, dicta_tc = segment.text('he', davidson_vtitle), segment.text('he', dicta_vtitle)
        try:
            new_dicta_text = prettify_text_segment(davidson_tc.text, dicta_tc.text)
        except AssertionError:
            print("Unable to fix formatting at {}".format(segment.normal()))
            continue

        new_dicta_text = fix_nikkud(new_dicta_text)

        if new_dicta_text != dicta_tc.text:
            dicta_tc.text = new_dicta_text
            dicta_tc.save()


def fix_nikkud(segment):
    """
    convert to כתיב מלא
    :param segment:
    :return:
    """
    #  Move any instances of Holam prior to a meteg-vuv to the vuv
    segment = re.sub(r'\u05b9\u05d5\u05bd', '\u05d5\u05b9', segment)
    # kibbutz prior to meteg-vuv, change the kibbutz to a shuruk
    segment = re.sub(r'\u05bb\u05d5\u05bd', '\u05d5\u05bc', segment)
    #  hataf-kamatz or kamatz or kamatz katan prior to meteg-vuv, change the mark to a holam
    segment = re.sub(r'[\u05c7\u05b3\u05b8]\u05d5\u05bd', '\u05db\u05b9', segment)

    return segment


if __name__ == '__main__':
    # create_nikkud_version()
    prettify_text('Berakhot 2a-46b')
    compare_versions()
