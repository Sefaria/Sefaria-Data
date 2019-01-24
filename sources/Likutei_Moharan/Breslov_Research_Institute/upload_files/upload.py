# encoding = utf-8

import re
import unicodecsv
from xml.sax.saxutils import unescape
from data_utilities.util import convert_dict_to_array, ja_to_xml
from sources.functions import post_text

import django
django.setup()
from sefaria.model import *


class DocElement(object):

    def __init__(self, content):
        if hasattr(self, 'child'):
            self._children = self.child.parse(content)
        else:
            self._content = content

    def get_content(self):
        if hasattr(self, '_children'):
            return [child.get_content() for child in self._children]
        else:
            return self._content

    def get_children(self):
        if hasattr(self, '_children'):
            return self._children
        else:
            return None

    def parse_content(self, callback, *args, **kwargs):
        if hasattr(self, '_children'):
            return [child.parse_content(callback, *args, **kwargs) for child in self._children]
        else:
            return callback(self._content, *args, **kwargs)


class ClashError(Exception):
    pass


class Comment(DocElement):

    @classmethod
    def parse(cls, lines):
        return [cls(line) for line in lines]


class Seif(DocElement):
    child = Comment

    @classmethod
    def parse(cls, lines):
        seif_mapping = {}
        current_seif = -1

        for line_num, line in enumerate(lines):
            seif_mark = re.search(u'^<b>(\d+)\.?', line['English'])
            if seif_mark:
                seif_value = int(seif_mark.group(1))
                if seif_value in seif_mapping:
                    if seif_value == current_seif:
                        continue
                    else:
                        raise ClashError

                seif_mapping[seif_value] = line_num
                current_seif = seif_value
        if 1 not in seif_mapping:
            seif_mapping[1] = 0

        seifim = sorted(seif_mapping.keys())
        list_mapping = {}
        for seif, next_seif in zip(seifim[:-1], seifim[1:]):
            list_mapping[seif] = lines[seif_mapping[seif]:seif_mapping[next_seif]]
        last_seif = seifim[-1]
        list_mapping[last_seif] = lines[seif_mapping[last_seif]:]
        return [cls(l) for l in convert_dict_to_array(list_mapping, list)[1:]]

    def set_child(self, chld_index, content):
        self._children[chld_index] = self.child(content)


class Torah(DocElement):
    child = Seif

    @classmethod
    def parse(cls, lines):
        last_chap = 1
        indices = [0]
        for line_num, line in enumerate(lines):
            cur_chap = int(line['Chapter'])
            if cur_chap > last_chap:
                indices.append(line_num)
                last_chap = cur_chap
        indices.append(len(lines))

        ranges = zip(indices[:-1], indices[1:])
        return [cls(lines[i:j]) for i, j in ranges]


class Likutei(DocElement):
    child = Torah


def clean_english(english):
    english = re.sub(u'\.{3,}', u'\u2026', english)
    english = re.sub(u'([.)\u2026}])([a-zA-Z])', u'\g<1> \g<2>', english)
    english = english.replace(u'i. e', u'i.e')
    english = re.sub(u'(?<!\s)[({]', u' \g<0>', english)
    english = re.sub(u'(^|\s)(</?[a-z]>)(\s)', u'\g<1>\g<2>', english)
    english = re.sub(u'\s(</?[a-z]>)$', u'\g<2>', english)

    return u' '.join(english.split())


bracket_regex = re.compile(u'<b>{[^}]+}</b>$')


def collect_sections(j_array):
    for chapter in j_array.get_children():
        for seif in chapter.get_children():
            yield seif


def identify_fixes(seif):
    comment_list = seif.get_content()
    requires_fixing = []
    for index, (current, next_) in enumerate(zip(comment_list[:-1], comment_list[1:])):
        english = current['English']
        hebrew = next_['Hebrew']

        potential = bracket_regex.search(english)
        if not potential:
            continue
        en_refs = library.get_refs_in_string(potential.group(), 'en', True)
        if not en_refs:
            continue
        he_refs = library.get_refs_in_string(hebrew, 'he', True)
        en_refs = [r.section_ref() for r in en_refs]
        if any(r in he_refs for r in en_refs):
            requires_fixing.append(index)
    return requires_fixing


def make_correction(seif, index_list):
    assert isinstance(seif, Seif)
    for index in index_list:
        comments = seif.get_content()
        comment = comments[index]
        bad_segment = comment['English']
        problem = bracket_regex.search(bad_segment).group(0)
        bad_segment = bad_segment.replace(problem, u'')
        comment['English'] = bad_segment
        seif.set_child(index, comment)

        comment = comments[index+1]
        comment['English'] = u'{} {}'.format(problem, comment['English'])

        seif.set_child(index+1, comment)



my_lines = []
filenames = [
 u'Likutei_Moharan_1-50.csv',
 u'Likutei_Moharan_51-99.csv',
 u'Likutei_Moharan_100-286.csv'
]
filenames2 = [
 u'Likutei_Moharan_Part2_1-49.csv',
 u'Likutei_Moharan_Part2_50-125.csv',
]

server = 'https://www.sefaria.org'

for f in filenames:
    with open(f) as fp:
        my_lines += list(unicodecsv.DictReader(fp))

lik = Likutei(my_lines)

for thing in collect_sections(lik):
    issues = identify_fixes(thing)
    make_correction(thing, issues)


# lik_content = lik.parse_content(lambda x: unescape(x['English']))
v = {
    'versionSource': u'http://rabenubook.com/%D7%9C%D7%99%D7%A7%D7%95%D7%98%D7%99-%D7%9E%D7%95%D7%94%D7%A8%D7%B4%D7%9F-%D7%90/',
    'versionTitle': u'Likutei Moharan - rabenubook.com',
    'language': u'he',
    'status': u'locked',
    'license': u'Public Domain',
    'text': lik.parse_content(lambda x: x['Hebrew'])
}
post_text("Likutei Moharan", v, server=server)

v = {
    'versionSource': u'http://aleph.nli.org.il/F/?func=direct&doc_number=001105868&local_base=NNL01',
    'versionTitle': u'Likutey Moharan Volumes 1-11, trans. by Moshe Mykoff. Breslov Research Inst., 1986-2012',
    'language': u'en',
    'status': u'locked',
    'license': u'CC-BY-NC',
    'text': lik.parse_content(lambda x: clean_english(x['English']))
    # 'text': lik.parse_content(lambda x: unescape(x['English']))
}
post_text("Likutei Moharan", v, server=server, skip_links=True)

my_lines = []
for f in filenames2:
    with open(f) as fp:
        my_lines += list(unicodecsv.DictReader(fp))
lik = Likutei(my_lines)

my_content = lik.get_content()
for thing in collect_sections(lik):
    issues = identify_fixes(thing)
    make_correction(thing, issues)

v = {
    'versionSource': u'http://rabenubook.com/%D7%9C%D7%99%D7%A7%D7%95%D7%98%D7%99-%D7%9E%D7%95%D7%94%D7%A8%D7%B4%D7%9F-%D7%AA%D7%A0%D7%99%D7%A0%D7%90-%D7%AA%D7%95%D7%9B%D7%9F-%D7%A2%D7%A0%D7%99%D7%99%D7%A0%D7%99%D7%9D/',
    'versionTitle': u'Likutei Moharan Tinyana - rabenubook.com',
    'language': u'he',
    'status': u'locked',
    'license': u'Public Domain',
    'text': lik.parse_content(lambda x: x['Hebrew'])
}
post_text("Likutei Moharan, Part II", v, server=server)

v = {
    'versionSource': u'http://aleph.nli.org.il/F/?func=direct&doc_number=001105868&local_base=NNL01',
    'versionTitle': u'Likutey Moharan Volumes 12-15, trans. by Moshe Mykoff. Breslov Research Inst., 1986-2012',
    'language': u'en',
    'status': u'locked',
    'license': u'CC-BY-NC',
    'text': lik.parse_content(lambda x: clean_english(x['English']))
    # 'text': lik.parse_content(lambda x: unescape(x['English']))
}
post_text("Likutei Moharan, Part II", v, index_count="on", server=server)

# lik_content = lik.parse_content(lambda x: unescape(x['English']))
# ja_to_xml(lik2_content, ['Torah', 'Seif', 'Comment'])
# print lik2_content[0][0][0]
