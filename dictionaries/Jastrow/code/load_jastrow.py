"""
from object_model import DCXMLsubs as model

root = model.parse('../data/01-Merged XML/Jastrow-full.xml', silence=True)
front = root.front
back = root.back

entries = root.entries()
print "Found {} entries".format(len(entries))
"""
import codecs
import xml.etree.ElementTree as ET


class Dictionary(object):
    def __init__(self):
        self._entries = []

    def add_entry(self, entry):
        self._entries += [entry]

    def to_html(self):
        out = u"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
            <meta charset="utf-8"/>
            <link rel="stylesheet" href="jastrow.css">
            </head>
            <body>
        """
        for e in self._entries:
            out += e.to_html()
            out += u"<br/>"
        out += u"</body></html>"
        return out


class Entry(object):
    tag_map = {"bold":"b",
               "italic":"i",
               "underline":"u",
               "pgbrk": None,
               "head-word": "div",
               "hw-number": "div",
               "pos": "div",
               "language-key": "div",
               "language-reference": "div",
               "senses": "div",
               "notes": "div",
               "plural-form": "div",
               "binyan": "div",
               "derivatives": "div",
               "sense": "div",
               "number": "div",
               "definition": "div",
               "binyan-form": "div",
               "binyan-name": "div",
               "alternative": "div",
               "entry":"div"
               }

    def __init__(self, element):
        """
        :param element: etree Entry element
        """
        self._element = element
        self.id = element.attrib["id"]
        self._vol = self.id[0]
        '''
        self.headwords = [e.text for e in element.findall("head-word")]
        self.pos = element.find("pos")
        self.languageKey = element.find("language-key")
        self.sense = element.find("senses")
        self.notes = element.find("notes")
        '''

    def url(self):
        return u'Jastrow-{}.html#{}'.format(self._vol, self.id)

    def _html_walker(self, elem):
        tag = elem.tag
        if not isinstance(tag, basestring) and tag is not None:
            return

        out = u""

        if tag == "xref":
            rid = elem.attrib["rid"]
            if rid == "unknown":
                out_tag = "div"
            else:
                rvol = rid[0]
                if rvol == self._vol:
                    return u'<a class="xref" href="#{}">{}</a>'.format(rid, elem.text)
                else:
                    return u'<a class="xref" href="Jastrow-{}.html#{}">{}</a>'.format(rvol, rid, elem.text)

        else:
            out_tag = self.tag_map.get(tag, tag)

        if out_tag:
            if out_tag == "div":
                out += u"<{} class='{}'>".format(out_tag, tag)
            else:
                out += u"<{}>".format(out_tag)
        if elem.text:
            out += elem.text
        for sub in elem:
            out += self._html_walker(sub)
        if out_tag:
            out += u"</{}>".format(out_tag)
        if elem.tail:
            out += elem.tail
        return out

    def to_html(self):
        out = u'<a name="{}"></a>'.format(self.id)
        out += self._html_walker(self._element)
        return out


tree = ET.parse('../data/01-Merged XML/Jastrow-full.xml')
root = tree.getroot()
chapters = root.find("body").findall("chapter")

for i, chapter in enumerate(chapters):
    d = Dictionary()
    letter_code = chr(ord('A') + i)
    print letter_code
    raw_entries = chapter.findall("entry")
    for e in raw_entries:
        entry = Entry(e)
        d.add_entry(entry)
    with codecs.open('../html/Jastrow-{}.html'.format(letter_code), "w", "utf-8") as o:
        o.write(d.to_html())

