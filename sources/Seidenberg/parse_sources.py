# coding=utf-8
import codecs
import regex as re
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
            print line
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
                trefs.append([u"{} {}".format(book, sections), pages])

    # either this is just a source line, or the end of a book/source line
    else:
        line = line.replace(u"§","").replace("ch.","")
        m = refline_re.match(line)
        sections = m.group(1).strip()
        pages = m.group(2).strip()
        trefs.append([u"{} {}".format(book, sections), pages])

success = 0
failed = 0
for tref, pages in trefs:
    try:
        r = Ref(tref)
        print u"          {} -> {}".format(tref, r.normal())
        success += 1
    except Exception as e:
        print u"{} !!".format(tref)
        failed += 1

print
print "{}/{} Suceeded".format(success, success+failed)
print "{}/{} Failed".format(failed, success+failed)
