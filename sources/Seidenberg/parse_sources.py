# coding=utf-8
import codecs
import regex as re
import unicodecsv as csv
from sefaria.model import *


filename = "sources.txt"
lines = [line.rstrip('\n') for line in codecs.open(filename, "r", "utf-8")]
justbook_re = re.compile(ur"(?!.*,\s*[0-9-]+$)(.*)")
bookline_re = re.compile(ur"([^1-9,§]*)\s?([0-9a-d:§() -]*)?(?:,(.*))?")
refline_re = re.compile(ur"([0-9a-d:-]*),(.*)")

book = ""
trefs = []
orefs = []

for line in lines:

    if not (line[0].isdigit() or line[0:3] == "ch." or line[0] == u"§"):
        # set new book
        m = justbook_re.match(line)
        if m:
            book = m.group(1).strip()
            # print line
        else:
            m = bookline_re.match(line)
            book = m.group(1).strip()
            sections = m.group(2)
            if sections:
                sections = sections.strip()
            pages = m.group(3)
            if pages:
                pages = pages.strip()
            # print u"{}    - {}  |  {}  |  {}".format(current, m.group(1), m.group(2), m.group(3))

            if sections:
                sections = sections.replace(u"§",u"").replace(u"ch.",u"")
                # print [u"1"] + [u"{} {}".format(book, sections), pages]
                trefs.append([u"{} {}".format(book, sections), pages])

    # either this is just a source line, or the end of a book/source line
    else:
        line = line.replace(u"§","").replace("ch.","")
        m = refline_re.match(line)
        sections = m.group(1).strip()
        pages = m.group(2).strip()
        # print [u"2"] + [u"{} {}".format(book, sections), pages]
        trefs.append([u"{} {}".format(book, sections), pages])

success = 0
failed = 0

"""
0 Ref
1 Resolved (Yes/No)
2 Pages
3 Hebrew Available
4 Other English Available
5 Text Placed

"""

with codecs.open('ecology.csv', 'wb', "utf-8") as csvfile:
    spamwriter = csv.writer(csvfile, encoding='utf-8')

    spamwriter.writerow(["Reference", "Ref in Sefaria", "Pages in K&E", "Hebrew in Sefaria", "Other English in Sefaria", "Text Placed"])
    for tref, pages in trefs:
        try:
            r = Ref(tref)
            spamwriter.writerow([r.normal(),
                                 u"yes",
                                 pages,
                                 u"yes" if r.is_text_fully_available("he") else u"no",
                                 u"yes" if r.is_text_translated() else u"no",
                                 u"no"])
            success += 1
        except Exception as e:
            print u"{} {} !!".format(tref, pages)
            spamwriter.writerow([tref, u"no", pages, u"no", u"no", u"no"])
            failed += 1

print
print "{}/{} Suceeded".format(success, success + failed)
print "{}/{} Failed".format(failed, success + failed)
