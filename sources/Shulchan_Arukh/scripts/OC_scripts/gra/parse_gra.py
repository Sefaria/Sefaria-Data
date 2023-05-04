# encoding=utf-8

import re
import numpy
import codecs
import requests
import unicodecsv
from collections import Counter, namedtuple
from sources.functions import post_index, post_text
from parsing_utilities.util import getGematria, numToHeb, StructuredDocument, file_to_ja_g, ja_to_xml

import django
django.setup()
from sefaria.model import *  # noqa


def build_gemtaria_regex(specials=None):
    if not specials:
        specials = []
    dec1 = u'|'.join(list(u'אבגדהוזחט'))
    dec2 = u'|'.join(list(u'טיכלמנסעפצ'))
    dec3 = u'ת*ש*ר*ק*'
    dec2 = re.sub(u'י', u'\g<0>(?![\u05d4\u05d5])', dec2)
    dec2 = re.sub(u'ט', u'\g<0>(?=[\u05d5\u05d6])', dec2)
    group1 = dec1
    group2 = u'(({})({})?)'.format(dec2, dec1)
    group3 = u'(?={})({})({})?({})?'.format(u'[תשרק]', dec3, dec2, dec1)
    if specials:
        return u'(?<![\u05d0-\u05ea])(({})|({})|({})|({}))(?=\s|$)'.format(group3, group2, group1, u'|'.join(specials))
    else:
        return u'(?<![\u05d0-\u05ea])(({})|({})|({}))(?=\s|$)'.format(group3, group2, group1)


def gematria_for_range(start, length, prefixes=None):
    def gematria_for_number(number):
        he_num = numToHeb(number)
        if len(he_num) == 1:
            num_with_mark = he_num + u"'"
        else:
            num_with_mark = he_num[:-1] + u'"' + he_num[-1]
        return u'{}|{}'.format(num_with_mark, he_num)

    default_prefixes = [u'^', u'\s']
    if not prefixes:
        prefixes = []
    prefixes = default_prefixes + prefixes
    prefixes = u'({})'.format(u'|'.join(prefixes))

    patterns = [u"({})".format(gematria_for_number(num)) for num in range(start, start + length)]
    end_condition = u'(?=\s|$)'
    return prefixes + u'(?P<gem>{})'.format(u'|'.join(patterns)) + end_condition


special_gematrias = [
    u'תערב',
    u'תער',
    u'שדמ',
    u'ער',
    u'ערב',
    u'ערה'
]
gematria_regex = re.compile(build_gemtaria_regex(specials=special_gematrias))


def generate_full_file():
    all_lines = []
    for filename in ['gra1', 'gra2', 'gra3']:
        with codecs.open(filename, 'r', 'utf-8') as fp:
            all_lines.extend(fp.readlines())

    for i, line in enumerate(all_lines):
        if re.match(u'@22', line):
            l_stripped = re.sub(u'["\']', u'', line)
            current_chapter = gematria_regex.search(l_stripped).group(1)
            all_lines[i] = u'@22{}\n'.format(current_chapter)
    with codecs.open(u'gra_full.txt', 'w', 'utf-8') as fp:
        fp.writelines(all_lines)


def identify_seifim(chapter_lines, lookahead=3, prefixes=None):
    seifim, line_indexes = [], []
    seif_regex = re.compile(gematria_for_range(1, lookahead+1, prefixes))

    for line_num, chap_line in enumerate(chapter_lines):
        if not chap_line:
            continue
        elif re.match(u'^@22', chap_line):
            continue
        aoi = re.match(u'^@11([^@]+)@33', chap_line).group(1)
        has_seif = seif_regex.search(aoi)
        if has_seif:
            # print aoi
            seifim.append(getGematria(has_seif.group(u'gem')))
            line_indexes.append(line_num)
            seif_regex = re.compile(gematria_for_range(seifim[-1]+1, lookahead+1, prefixes))
    return seifim, line_indexes


# with codecs.open(u'gra_full.txt', 'r', 'utf-8') as fp:
#     lines = fp.readlines()


# simanim = [l for l in lines if re.match(u'@22', l)]
# previous_chapter, issues = 0, 0
# for siman in simanim:
#     # l_stripped = re.sub(u'["\']', u'', siman)
#     cur_chapter = getGematria(gematria_regex.search(siman).group(1))
#     if cur_chapter - previous_chapter != 1:
#         print u'Jump from {} to {}'.format(previous_chapter, cur_chapter)
#         print siman
#         issues += 1
#     previous_chapter = cur_chapter
# print issues

SeifTracker = namedtuple('SeifTracker', ['seif_number', 'seif_line_index'])

seif_prefixes = [
    u'ס"',
    u'ס'
]


def add_seifim_to_chapter(chap_text):
    chap_lines = chap_text.split(u'\n')
    seif_values, seif_indexes = identify_seifim(chap_lines, prefixes=seif_prefixes)
    trackers = [SeifTracker(*s) for s in zip(seif_values, seif_indexes)]

    if not trackers:
        trackers.append(SeifTracker(1, 1))
    if trackers[0].seif_line_index != 1:
        if trackers[0].seif_number > 1:
            trackers.insert(0, SeifTracker(1, 1))
        else:
            trackers[0] = SeifTracker(1, 1)

    for seif_value, seif_index in reversed(trackers):
        chap_lines.insert(seif_index, u'@44{}'.format(numToHeb(seif_value)))
    return u'\n'.join(chap_lines)


# my_doc = StructuredDocument(u'gra_full.txt', u'@22([\u05d0-\u05ea]{1,4})')
# for chapter in my_doc.get_chapter_values():
#     my_doc.edit_section(chapter, add_seifim_to_chapter)


def structure_comments(seif):
    def repl(x):
        replacements = {
            u'@11': u'<b>',
            u'@33': u'</b>'
        }
        return replacements[x.group()]

    # comments = seif.split(u'\n')
    return [re.sub(u'@[13]{2}', repl, c) for c in seif]


expressions = [u'@22(?P<gim>[\u05d0-\u05ea]{1,4})', u'@44(?P<gim>[\u05d0-\u05ea]{1,3})']
with codecs.open('gra_with_seifim.txt', 'r', 'utf-8') as fp:
    gra_ja = file_to_ja_g(3, fp, expressions, structure_comments, gimatria=True)

# ja_to_xml(gra_ja.array(), [u'Siman', u'Seif', u'Comment'])
remote_index = requests.get(u'https://www.sefaria.org/api/v2/raw/index/Shulchan_Arukh,_Orach_Chayim').json()
alts = remote_index['alt_structs']
for node in alts['Topic']['nodes']:
    node['wholeRef'] = re.sub(u'Shulchan Arukh', u'Beur HaGra on Shulchan Arukh', node['wholeRef'])

jnode = JaggedArrayNode()
jnode.add_primary_titles(u'Beur HaGra on Shulchan Arukh, Orach Chayim', u'ביאור הגר"א על שולחן ערוך אורך חיים')
jnode.add_structure([u'Siman', u'Seif', u'Comment'])
jnode.toc_zoom = 2
g_index = {
    u'title': u'Beur HaGra on Shulchan Arukh, Orach Chayim',
    u'categories': [u"Halakhah", u"Shulchan Arukh", u"Commentary", u"Beur HaGra"],
    u'base_text_titles': [u'Shulchan Arukh, Orach Chayim'],
    u'collective_title': u'Beur HaGra',
    u'dependence': u'Commentary',
    u'base_text_mapping': u'many_to_one',
    u'schema': jnode.serialize(),
    u'alt_structs': alts
}

g_version = {
    u"versionTitle": u"Maginei Eretz: Shulchan Aruch Orach Chaim, Lemberg, 1893",
    u"versionSource": u"http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002084080",
    u"language": u"he",
    u"text": gra_ja.array(),
}
server = 'http://graoc.sandbox.sefaria.org'
# post_index(g_index, server)
# post_text(g_index[u'title'], g_version, index_count='on', skip_links=True, server=server)


def is_good_seif(seif_list, seif_index, base_seifim):
    """
    Identify seifim which are not suspect of containing errors. The errors we are looking for is missing the start of
    the next seif. We can be sure that this is not an issue if the following seif is present (i.e. if "2" is followed
    by "3").
    :param list seif_list: list of seifim (chapter
    :param int seif_index: index of seif in seif_list
    :return:
    """
    if seif_index >= len(seif_list) - 1:  # last seifim are suspect
        if seif_index == base_seifim - 1:
            return True
        return False

    elif len(seif_list[seif_index]) == 0:  # empty seif
        return False

    elif len(seif_list[seif_index + 1]) == 0:  # following seif is empty
        return False
    else:
        return True


SeifLocation = namedtuple('SeifLocation', ['chapter', 'seif', 'length'])
seif_lengths, probelm_seifim = [], []
for chap_num, chapter in enumerate(gra_ja.array()):
    base_ref = Ref(u"Shulchan Arukh, Orach Chayim {}".format(chap_num + 1))
    base_seifim = len(base_ref.all_subrefs())
    for index, seif in enumerate(chapter):
        if is_good_seif(chapter, index, base_seifim):  # or index == base_seifim - 1:
            seif_lengths.append(len(seif))
        else:
            probelm_seifim.append(seif)

print len(seif_lengths), len(probelm_seifim)

max_dev = int(numpy.rint(numpy.mean(seif_lengths) + numpy.std(seif_lengths)))

print max_dev

probelm_seifim = []
for chap_num, chapter in enumerate(gra_ja.array()):
    base_ref = Ref(u"Shulchan Arukh, Orach Chayim {}".format(chap_num + 1))
    base_seifim = len(base_ref.all_subrefs())
    for index, seif in enumerate(chapter):
        if not is_good_seif(chapter, index, base_seifim):
            if len(seif) >= max_dev:
                probelm_seifim.append(SeifLocation(chap_num+1, index+1, len(seif)))

print len(probelm_seifim)
rows = [dict(problem._asdict()) for problem in probelm_seifim]  # despite convention, not a protected member
with open('gra_problem_seifim.csv', 'w') as fp:
    writer = unicodecsv.DictWriter(fp, SeifLocation._fields)
    writer.writeheader()
    writer.writerows(rows)
