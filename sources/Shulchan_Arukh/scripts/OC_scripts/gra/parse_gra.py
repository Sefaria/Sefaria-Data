# encoding=utf-8

import re
import codecs
from collections import Counter


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
        return u'(({})|({})|({})|({}))(?=\s|$)'.format(group3, group2, group1, u'|'.join(specials))
    else:
        return u'(({})|({})|({}))(?=\s|$)'.format(group3, group2, group1)


gematria_regex = re.compile(build_gemtaria_regex())

lines = []
for filename in ['gra1', 'gra2', 'gra3']:
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines.extend(fp.readlines())

prefixes = Counter()
for line in lines:
    if re.match(u'@22', line):
        line = re.sub(u'''["']''', u'', line)
        stripped_line = gematria_regex.sub(u'', line)
        prefixes[stripped_line] += 1

print len(prefixes)
for p, count in prefixes.items():
    print p, count
