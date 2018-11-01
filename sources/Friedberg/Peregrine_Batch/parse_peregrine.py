# encoding=utf-8

import re
import regex
import django
django.setup()
import unicodecsv
from sefaria.model import *
from collections import Counter


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

with open("Friedberg_Texts.csv") as fp:
    rows = list(unicodecsv.DictReader(fp))

r_title_list = [Ref(t).he_normal() for t in library.get_indexes_in_category(u'Mishneh Torah')]
r_title_list = [re.sub(u'\u05de\u05e9\u05e0\u05d4 \u05ea\u05d5\u05e8\u05d4, ', u'', t) for t in r_title_list]
r_title_list = u'|'.join(r_title_list)

# refs = [derive_ref_from_row(r['hdr']) for r in rows]
bad = 0
weird_books = []
for r in rows:
    if not derive_ref_from_row(r['hdr']):
        book = regex.search(u'^(((?>[^\s]+)\s)+)(?>[^\s]+)\s[^\s]+$', r['hdr'])
        if book:
            weird_books.append(book.group(1))
        else:
            print "no book"
            print r['hdr']
            print ""
        title_search = re.search(r_title_list, r['hdr'])
        if not title_search:
            print r['hdr']
            print derive_ref_from_row.reprocess_row(r['hdr'])
            print ""

        bad += 1
    # if bad >= 25:
    #     break


print len(rows)
print bad
counts = Counter(weird_books)
print len(counts)
print u''
for b, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
    print b, count
