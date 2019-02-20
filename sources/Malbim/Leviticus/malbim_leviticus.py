# encoding=utf-8

"""
Run pull_files.py to get the webpages locally.

Parsing strategy:
Start by extracting each siman so that we have a list of Siman instances. Each Siman instance will be should be able
to tell us where it belongs.

We need to be able to extract only the Malbim text from a Siman. We'll also need to configure footnotes.

Let's say that each Siman is composed of:
1) h2 Siman header
2) Base verse
3) Sifra Quote
4) Malbim text
5) footnotes

Find the h2 header with סימן written in it
The Base verse should be the next sibling. An <a> tag should be inside with a base ref.
The next element should contain a link to Sifra
The Sifra text will be the next sibling. It should be a <div style="font-weight:bold">

We should then hit a series of p, dl, ul elements which contain the main text.
An h3 indicates we've hit footnotes. At the footnotes, each p is a new footnote.

Anything else should mean stop. We'll want to keep track of all our "stop" conditions.

Footnotes: contain links which map markers to text. We can use that mapping.

Let's implement a builder class. We can feed it a Siman element and let it go from there. We'll have a second method
with the responsibility of identifying Simanim within a document.

We'll defer the text formatting to the Siman class

Extracting the Sifra ref is tricky. We've mapped all the node titles to Sefaria Refs. Some Simanim don't have enough
data to detect the full Ref though. For this, we can take the data from the previous Siman. This strategy could work for
missing base refs as well.
"""

import re
import codecs
import random
from data_utilities.util import getGematria as get_gematria
from bs4 import BeautifulSoup

import django
django.setup()
from sefaria.model import *


def extract_simanim(filename):
    with codecs.open(filename, 'r', 'utf-8') as fp:
        soup = BeautifulSoup(fp, 'lxml')
    return [siman for siman in soup.find_all('h2') if re.match(u'^\u05e1\u05d9\u05de\u05df', siman.text)]


class SimanBuilder(object):

    def __init__(self, siman_header, announcer):
        self.last_element = siman_header
        self.announcer = announcer
        self.sifra_mapping = self._sifra_mapping()
        self.siman_attrs = {}
        self.siman_attrs['siman_num'] = self.get_siman_num()
        self.siman_attrs['base_refs'] = self.get_base_refs()
        self.siman_attrs['sifra_ref'] = self.get_sifra_refs()

    @staticmethod
    def _sifra_mapping():
        return {
            u'ספרא פרשת ויקרא נדבה': u'ויקרא דבורא דנדבה',
            u'ספרא פרשת ויקרא חובה': u'ויקרא דבורא דחובה',
            u'ספרא פרשת צו': u'צו',
            u'ספרא פרשת צו מכילתא דמלואים': u'צו, מכילתא דמילואים א',
            u'ספרא פרשת שמיני': u'שמיני',
            u'ספרא פרשת שמיני מכילתא דמלואים': u'שמיני, מכילתא דמילואים ב',
            u'ספרא פרשת תזריע יולדת': u'תזריע פרשת יולדת',
            u'ספרא פרשת תזריע נגעים': u'תזריע פרשת נגעים',
            u'ספרא פרשת מצורע מצורע': u'מצורע',
            u'ספרא פרשת מצורע זבים': u'מצורע פרשת זבים',
            u'ספרא פרשת אחרי מות': u'אחרי מות',
            u'ספרא פרשת קדושים': u'קדושים',
            u'ספרא פרשת אמור': u'אמור',
            u'ספרא פרשת בהר': u'בהר',
            u'ספרא פרשת בחקתי': u'בחוקתי',
        }

    def get_siman_num(self):
        siman_regex = re.compile(u'\u05e1\u05d9\u05de\u05df[_ ]([\u05d0-\u05ea]{1,4})')
        siman_tag = self.last_element.find(attrs={'id': siman_regex})
        siman_he_value = siman_regex.search(siman_tag['id']).group(1)
        return get_gematria(siman_he_value)

    def get_base_refs(self):
        def get_next_base_ref():
            verse_element = self.last_element.find_next_sibling()
            try:
                if not Ref.is_ref(verse_element.a.text):
                    return None
            except AttributeError:
                return None
            base_ref = Ref(verse_element.a.text)
            self.last_element = verse_element
            return base_ref

        # advance beyond the refs in case there are more than 1
        base_refs = []
        while True:
            next_ref = get_next_base_ref()
            if next_ref is None:
                break
            else:
                base_refs.append(next_ref)
        return base_refs

    def get_sifra_refs(self):
        ref_element = self.last_element.find_next_sibling()
        text_element = ref_element.find_next_sibling()
        if text_element.name != 'div' and text_element.get('style', '') != "font-weight:bold":
            self.announcer.announce()
        self.last_element = ref_element
        my_text = text_element.text

        he_ref = ref_element.text.replace(u'(מלבי"ם) ', u'').rstrip().lstrip()

        possible_sections = [
            u'פרק',
            u'פרשה',
            u'מכילתא דמלואים',
        ]
        section = re.search(u'\s?(({}).*)'.format(u'|'.join(possible_sections)), he_ref)
        if section is None:
            print u'No section at Siman {}, file:'.format(self.siman_attrs['siman_num']),
            self.announcer.announce()
            return None

        section = section.group(1)
        core_ref = he_ref.replace(section, u'').rstrip()
        core_ref = re.sub(u'[^\u05d0-\u05ea ]', u'', core_ref)
        core_ref = self.sifra_mapping[core_ref]
        section = re.sub(u'[^\u05d0-\u05ea ]', u'', section)

        if re.search(u'צו', core_ref):
            section = section.replace(u'דמלואים', u'דמילואים א')
        elif re.search(u'שמיני', core_ref):
            section = section.replace(u'דמלואים', u'דמילואים ב')
        # self.sifras.add(temp_he_ref)
        # print he_ref
        # print ref_element.text
        # print my_text
        segments = [m.group(1) for m in re.finditer(u'\[([\u05d0-\u05ea]{1,3})]', my_text)]
        if len(segments) > 1:
            segment_part = u'{}-{}'.format(segments[0], segments[-1])
        elif len(segments) == 1:
            segment_part = segments[0]
        else:
            # print u'No segments at Siman {}, file:'.format(self.siman_attrs['siman_num']),
            # self.announcer.announce()
            return None

        # for r in sifra_refs:
        #     print r
        # print 'Done'
        full_ref = u'{}, {}, {} {}'.format(u'ספרא', core_ref, section, segment_part)
        ref_list = self.handle_complex_refs(full_ref)
        for r in ref_list:
            if not Ref.is_ref(r):
                print u'Bad ref at Siman {}, file:'.format(self.siman_attrs['siman_num']),
                self.announcer.announce()
                print r
        return ref_list

    def handle_complex_refs(self, cur_ref):
        cur_ref = u' '.join(cur_ref.split())

        if re.search(u'ספרא, ויקרא דבורא דחובה, פרשה א ופרק א', cur_ref):
            if 191 <= self.siman_attrs['siman_num'] < 196:
                ref_list = [cur_ref.replace(u'פרשה א ופרק א', u'פרשה א')]
            elif self.siman_attrs['siman_num'] > 196:
                ref_list = [cur_ref.replace(u'פרשה א ופרק א', u'פרק א')]
            else:
                ref_list = [
                    u'ספרא, ויקרא דבורא דחובה, פרשה א ז-יד',
                    u'ספרא, ויקרא דבורא דחובה, פרק א א-ג'
                ]

        elif re.search(u'ספרא, ויקרא דבורא דחובה, פרשה ח ופרק יב', cur_ref):
            if 293 <= self.siman_attrs['siman_num'] < 299:
                ref_list = [cur_ref.replace(u'פרשה ח ופרק יב', u'פרשה ח')]
            elif 299 < self.siman_attrs['siman_num'] <= 300:
                ref_list = [cur_ref.replace(u'פרשה ח ופרק יב', u'פרק יב')]
            else:
                ref_list = [
                    u'ספרא, ויקרא דבורא דחובה, פרשה ח ח',
                    u'ספרא, ויקרא דבורא דחובה, פרק יב א-ד'
                ]

        elif re.search(u'ספרא, ויקרא דבורא דנדבה, פרשה יא ופרק יג', cur_ref):
            if self.siman_attrs['siman_num'] == 128:
                ref_list = [cur_ref.replace(u'פרשה יא ופרק יג', u'פרשה יא')]
            elif self.siman_attrs['siman_num'] == 129:
                ref_list = [
                    u'ספרא, ויקרא דבורא דנדבה, פרשה יא ו',
                    u'ספרא, ויקרא דבורא דנדבה, פרק יג א-ה'
                ]
            else:
                ref_list = [cur_ref.replace(u'פרשה יא ופרק יג', u'פרק יג')]

        elif re.search(u'ספרא, תזריע פרשת נגעים, פרקים יגיד', cur_ref):
            if self.siman_attrs['siman_num'] == 160:
                ref_list = [
                    u'ספרא, תזריע פרשת נגעים, פרק יג א-יב',
                    u'ספרא, תזריע פרשת נגעים, פרק יד א'
                ]
            else:
                ref_list = [cur_ref.replace(u'פרקים יגיד', u'פרק יד')]

        elif cur_ref == u'ספרא, שמיני, פרשה י מ-ג':
            ref_list = [u'ספרא, שמיני, פרשה י א-ג']

        elif cur_ref == u'ספרא, צו, פרק ז לי-ב':
            ref_list = [u'ספרא, צו, פרק ז א-ב']

        elif cur_ref == u'ספרא, קדושים, פרשה ג את':
            ref_list = [u'ספרא, קדושים, פרשה ג ג']

        elif cur_ref == u'ספרא, בחוקתי, פרשה ח א-ט':
            ref_list = [u'ספרא, בחוקתי, פרשה ה א-ט']

        else:
            ref_list = [cur_ref]

        return ref_list

    def get_main_text(self):
        pass

    def get_footnotes(self):
        pass

    def retrieve_siman(self):
        return Siman(**self.siman_attrs)


class Siman(object):
    def __init__(self, siman_num, base_ref, sifra_ref, main_text, footnotes):
        self.siman_num = siman_num
        self.base_ref = base_ref
        self.sifra_ref = sifra_ref
        self.main_text_raw = main_text
        self.footnotes = footnotes
        self.formated_text = self._format_text()

    def _format_text(self):
        return self.main_text_raw


class Announcer(object):
    def __init__(self):
        self.loc = -1
        self.announcements = 0

    def set_loc(self, loc):
        self.loc = loc

    def announce(self):
        print self.loc
        self.announcements += 1

    def num_announcements(self):
        return self.announcements


things = set()
my_screamer = Announcer()
# for i in range(64, 65):
for i in range(274):
    # if i % 20 == 0:
    #     print i,
    my_screamer.set_loc(i)
    if i == 53:
        continue
    # if i % 20 == 0 and i > 0:
    #     print i,
    my_simanim = extract_simanim('./webpages/{}.html'.format(i))
    for foo in my_simanim:
        s = SimanBuilder(foo, my_screamer)
        # things.update(s.sifras)

print my_screamer.num_announcements()

# print ''
# print len(things)
# for t, u in things.items():
#     print t.rstrip(), u
# for t in things:
#     print t.rstrip().lstrip()
# print things
