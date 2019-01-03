# encoding=utf-8

import re
import codecs
from collections import Counter
from data_utilities.util import getGematria, numToHeb, StructuredDocument


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
    seifim = []
    seif_regex = re.compile(gematria_for_range(1, lookahead+1, prefixes))

    for chap_line in chapter_lines:
        if not chap_line:
            continue
        elif re.match(u'^@22', chap_line):
            continue
        aoi = re.match(u'^@11([^@]+)@33', chap_line).group(1)
        has_seif = seif_regex.search(aoi)
        if has_seif:
            print aoi
            seifim.append(getGematria(has_seif.group(u'gem')))
            seif_regex = re.compile(gematria_for_range(seifim[-1]+1, lookahead+1, prefixes))
    return seifim


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
seif_prefixes = [
    u'ס"'
]
my_doc = StructuredDocument(u'gra_full.txt', u'@22([\u05d0-\u05ea]{1,4})')
chapter_1 = my_doc.get_section(4)
chap_seifim = chapter_1.split(u'\n')
seif_values = identify_seifim(chap_seifim, prefixes=seif_prefixes)
for s in seif_values:
    print s,
