# encoding=utf-8

import re
import codecs
import django
django.setup()
import unicodecsv
from sefaria.model import *
from bs4 import BeautifulSoup
from collections import Counter, defaultdict
from sefaria.datatype.jagged_array import JaggedArray


class DeriveRefFromRow(object):

    def __init__(self):
        self._super_regex = None
        self.replacements = {
            u'עבודת כוכבים': u'עבודה זרה וחוקות הגויים',
            u'תפילה ונשיאת כפים': u'תפילה וברכת כהנים',
            u'יום טוב': u'שביתת יום טוב',
            u'מלוה ולוה': u'מלווה ולווה',
            u'קדוש החדש': u'קידוש החודש',
            u'זכיה ומתנה': u'זכייה ומתנה',
            u'ערכין וחרמין': u'ערכים וחרמין',
            u'מלכים': u'מלכים ומלחמות',
            u'כלי המקדש': u'כלי המקדש והעובדין בו',
            u'סנהדרין': u'סנהדרין והעונשין המסורין להם',
            u'ביאת המקדש': u'ביאת מקדש',
            u'מעשר': u'מעשרות',
            u'תמידין ומוספין': u'תמידים ומוספין',
            u'איסורי מזבח': u'איסורי המזבח',
            u'בכורים': u'ביכורים ושאר מתנות כהונה שבגבולין',
            u'ביכורים': u'ביכורים ושאר מתנות כהונה שבגבולין',
            u'טומאת אוכלין': u'טומאת אוכלים',
            u'שאלה ופקדון': u'שאלה ופיקדון',
            u'גזלה ואבדה': u'גזילה ואבידה',
            u'רוצח ושמירת הנפש': u'רוצח ושמירת נפש',
            u'עבודת כוכבים וחקותיהם': u'עבודה זרה וחוקות הגויים',
            u'שאר אבות הטומאה': u'שאר אבות הטומאות',
            u'עבודת יוה"כ': u'עבודת יום הכפורים',
            u'עבודת יום הכיפורים': u'עבודת יום הכפורים',
            u'לולב': u'שופר וסוכה ולולב',
            u'שופר': u'שופר וסוכה ולולב',
            u'תפלה': u'תפילה וברכת כהנים',
            u'תפילה': u'תפילה וברכת כהנים',
            u'נשיאת כפים': u'תפילה וברכת כהנים',
            u'מגילה': u'מגילה וחנוכה',
            u'חנוכה': u'מגילה וחנוכה',
            u'תפילין': u'תפילין ומזוזה וספר תורה',
            u'ספר תורה': u'תפילין ומזוזה וספר תורה',
            u'תפלין': u'תפילין ומזוזה וספר תורה',
            u'מזוזה': u'תפילין ומזוזה וספר תורה',
            u'מקוואות': u'מקואות',
            u'קידוש החדש': u'קידוש החודש',
        }

    def reprocess_row(self, row_header):
        replacements = sorted(self.replacements.keys(), key=lambda x: len(x), reverse=True)

        return re.sub(u'|'.join(replacements), lambda x: self.replacements[x.group()], row_header)

    def __call__(self, row_header):
        if not self._super_regex:
            title_list = [Ref(t).he_normal() for t in library.get_indexes_in_category(u'Mishneh Torah')]
            title_list = [re.sub(u'\u05de\u05e9\u05e0\u05d4 \u05ea\u05d5\u05e8\u05d4, ', u'', t) for t in
                          title_list]
            title_list = u'|'.join(title_list)
            self._super_regex = re.compile(u'(?P<title>%s) (?:\u05e4\u05e8\u05e7 |\u05e4)'
                                           u'(?P<chap>[\u05d0-\u05ea"]+)\s'
                                           u'(?P<seg>[\u05d0-\u05ea"]+([\s,\-]{1,3}[\u05d0-\u05ea"]+)?)$' % title_list)

        if isinstance(row_header, dict):
            row_header = row_header['hdr']

        regex_result = self._super_regex.search(row_header)
        if not regex_result:
            row_header = self.reprocess_row(row_header)
        regex_result = self._super_regex.search(row_header)
        if not regex_result:
            return None

        chapter = re.sub(u'"', u'', regex_result.group('chap'))
        seg = re.sub(u'"', u'', regex_result.group('seg'))
        seg = re.sub(u'[^\u05d0-\u05ea]+', u'-', seg)
        proper_ref_string = u'(\u05de\u05e9\u05e0\u05d4 \u05ea\u05d5\u05e8\u05d4, {} {} {})'\
            .format(regex_result.group('title'), chapter, seg)
        possible_refs = library.get_refs_in_string(proper_ref_string, lang='he', citing_only=True)
        if len(possible_refs) == 0:
            print "Matched but didn't resolve ref"
            return None
        elif len(possible_refs) > 1:
            print u"Ambiguous Ref: {}".format(row_header)
            print u"Resolved to: {}".format(proper_ref_string)
            raise AssertionError
        else:
            return possible_refs[0]


derive_ref_from_row = DeriveRefFromRow()


u"""
Parsing strategy:
Each index is a depth 3 JA. Use the book id and ref to determine where to place each comment.
I'll use a Counter to keep track of refs. The Rambam ref will give me the super-section and section values, then
the value of that ref in the counter will give me the segment value.

For simplicity, I'll keep the exact value of the Rambam ref as well as the derived ref as a list of tuples this will
be my link list.


For a row:
1) Get index name
2) Get Rambam Ref
3) Compile section level Ref for this comment
4) Obtain segment level index from the comment_tracker
5) Set the element.
"""


class CommentStore(object):

    def __init__(self):
        self.texts = defaultdict(JaggedArray)
        self.comment_tracker = Counter()
        self.links = []
        with open("Friedberg_Texts_Metadata.csv") as fp:
            self.titles = {row['id']: {'en_name': row['en_name'], 'he_name': row['he_name']} for row in
                           unicodecsv.DictReader(fp)}

    def resolve_row(self, row_element):
        commentary = self.titles[row_element['bid']]['en_name']
        rambam_ref = derive_ref_from_row(row_element)

        index_title = u'{} on {}'.format(commentary, rambam_ref.book)
        section_level = u'{} {}:{}'.format(index_title, *rambam_ref.sections)

        self.comment_tracker[section_level] += 1
        ref_indices = rambam_ref.sections[:] + [self.comment_tracker[section_level]]
        full_ref = u'{} {}:{}:{}'.format(index_title, *ref_indices)

        insertion_indices = [i-1 for i in ref_indices]  # 0 index for ja address
        # check that our section is the correct size
        segments_in_section = self.texts[index_title].sub_array_length(insertion_indices[:-1])
        if segments_in_section is None:
            segments_in_section = 0
        assert segments_in_section == insertion_indices[-1]

        self.texts[index_title].set_element(insertion_indices, self.format_segment(row_element['text']), pad=u'')
        self.links.append((rambam_ref.normal(), full_ref))
        return full_ref

    @staticmethod
    def format_segment(segment_text):
        return segment_text

    def get_index_titles(self):
        return self.texts.keys()

    def get_text_array_for_index(self, index_title):
        if index_title not in self.texts:
            raise KeyError(index_title)
        return self.texts[index_title].array()


with open("Friedberg_Texts.csv") as fp:
    rows = list(unicodecsv.DictReader(fp))

# with open("Friedberg_Texts_Metadata.csv") as fp:
#     titles = {row['id']: {'en_name': row['en_name'], 'he_name': row['he_name']} for row in unicodecsv.DictReader(fp)}

storage = CommentStore()
my_refs = [storage.resolve_row(row) for row in rows]

for ref, row in zip(my_refs, rows):
    if re.search(u'<span class="Z Z S Z">', row[u'text']):
        print ref
        print row[u'text']
        print u''


all_tags, all_attrs, all_classes = set(), set(), Counter()
for row in rows:
    raw_xml = u'<root>{}</root>'.format(row[u'text'])
    soup = BeautifulSoup(raw_xml, 'xml')
    root = soup.root
    for n in root.find_all(True):
        all_tags.add(n.name)
        all_attrs.update(n.attrs.keys())
        all_classes[n.get(u'class', None)] += 1

print len(all_tags)
if len(all_tags) < 50:
    for n in all_tags:
        print n
print u''
print len(all_attrs)
if len(all_attrs) < 50:
    for n in all_attrs:
        print n
print u''
print len(all_classes)
if len(all_classes) < 50:
    for n in all_classes.items():
        print n
