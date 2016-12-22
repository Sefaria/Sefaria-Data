# -*- coding: utf-8 -*-
#!/usr/bin/env python

#
# Generated Thu Oct 13 14:51:23 2016 by generateDS.py version 2.23a.
#
# Command line options:
#   ('-o', 'DCXML.py')
#   ('--super', 'DCXML')
#   ('-s', 'DCXMLsubs.py')
#   ('--external-encoding', 'utf-8')
#
# Command line arguments:
#   ./Sefaria-DC.xsd
#
# Command line:
#   /usr/local/bin/generateDS.py -o "DCXML.py" --super="DCXML" -s "DCXMLsubs.py" --external-encoding="utf-8" ./Sefaria-DC.xsd
#
# Current working directory (os.getcwd()):
#   Mesechtot Ketanot
#

import sys
import itertools
from lxml import etree as etree_
from sefaria.datatype.jagged_array import JaggedArray
from sefaria.model.schema import SchemaNode, JaggedArrayNode
import DCxml2 as supermod


def parsexml_(infile, parser=None, **kwargs):
    if parser is None:
        # Use the lxml ElementTree compatible parser so that, e.g.,
        #   we ignore comments.
        parser = etree_.ETCompatXMLParser()
    doc = etree_.parse(infile, parser=parser, **kwargs)
    return doc

#
# Globals
#

ExternalEncoding = 'utf-8'

# Global reference for id'd comments
commentStore = {}

# Global reference for non-id'd comments
unlinkedCommentStore = []

commentatorNames = {
    u"מסורת הש״ס": "Mesorat HaShas on Masechtot Ketanot",
    u"פי׳ החיד״א": "Commentary of Chida on Masechtot Ketanot",
    u"הגהות": "Haggahot on Masechtot Ketanot",
    u"הגהות הגרי״ב": "Haggahot R' Yeshaya Berlin on Masechtot Ketanot",
    u"בנין יהושע": "Binyan Yehoshua on Masechtot Ketanot",
    u"נוסחא חדשה": "New Nuschah on Masechtot Ketanot",
    u"נוסחאות כ״י": "Nuschaot from Manuscripts on Masechtot Ketanot",
    u"ראשון לציון": "Rishon Letzion on Masechtot Ketanot",
    u"נחלת יעקב": "Nahalat Yaakov on Masechtot Ketanot",
    u"תומת ישרים": "Tumat Yesharim on Masechtot Ketanot",
    u"הגהות ומראה מקומות": "Haggahot and Marei Mekomot on Masechtot Ketanot",
    u"כסא רחמים": "Kisse Rahamim on Masechtot Ketanot",
    u"הגהות מהריעב״ץ": "Haggahot Ya'avetz on Masechtot Ketanot",
    u"מצפה איתן": "Mitzpeh Etan on Masechtot Ketanot",
    u"לב חכמים": "Lev Hakhamim on Masechtot Ketanot",
    u"נוסחת הגר״א": "Gra's Nuschah on Masechtot Ketanot",
}

#
# Data representation classes
#


class bookSub(supermod.book):
    def __init__(self, id=None, front=None, body=None, back=None):
        super(bookSub, self).__init__(id, front, body, back, )

    def populateCommentStore(self):

        for chap_index, chapter in enumerate(self.get_body().get_chapter()):
            for verse_index, verse in enumerate(chapter.get_verse()):
                refs = verse.get_xrefs()
                for ref in refs:
                    commentStore[ref.rid] = {'chapter': chap_index+1, 'verse': verse_index+1}

        try:
            for c in self.get_body().get_commentaries().get_commentary():
                linked = True
                heName = c.get_author()#.content_[0].getValue()
                enName = commentatorNames.get(heName)
                chapters = c.get_chapter() if c.get_chapter() else [c]
                current_chapter, current_verse, order = 0, 0, 0
                for chapter in chapters:
                    for p in chapter.get_phrase():
                        if p.id:
                            if commentStore.get(p.id) is None:
                                linked = False
                                continue
                            if (commentStore[p.id]["chapter"] != current_chapter) or (commentStore[p.id]["verse"]) != current_verse:
                                current_chapter = commentStore[p.id]["chapter"]
                                current_verse = commentStore[p.id]["verse"]
                                order = 0
                            order += 1
                            commentStore[p.id]["commentator"] = enName
                            commentStore[p.id]["order"] = order
                        else:
                            linked = False
                self.get_body().get_commentaries().linked[heName] = linked

        except AttributeError:
            return

    def getBaseTextArray(self):
        return self.get_body().getTextArray()
        # Note the offset issue w/ Semachot

    def review_commentaries(self):
        for commentary, linked in self.get_body().get_commentaries().linked.iteritems():
            print u'{} : {}'.format(commentary, linked)

    def check_commentary_chapters(self):
        problems = []
        for commentary in self.get_body().get_commentaries().get_commentary():
            if not commentary.validate_chapters():
                problems.append(commentary)
        return problems

    @staticmethod
    def commentary_ja_node(en_title, he_title):
        """
        Each commentary is a complex text, with a root schema and depth 3 JAnodes for each tractate. The JAnode for each
        tractate is essentially identical across commentaries. The root schema is what defines the particular
        commentator.
        :param en_title: English Title of base text
        :param he_title: Hebrew Title of base text
        :return: JaggedArrayNode
        """
        node = JaggedArrayNode()
        node.add_primary_titles(en_title, he_title)
        node.add_structure(['Chapter', 'Halakhah', 'Comment'])
        node.validate()
        return node

    @staticmethod
    def get_stored_links(base_title):
        links = []
        for comment in itertools.chain(commentStore.values(), unlinkedCommentStore):
            base_ref = '{} {}:{}'.format(base_title, comment['chapter'], comment['verse'])
            comment_ref = '{}, {}:{}:{}'.format(comment['commentator'], base_ref, comment['verse'], comment['order'])
            links.append({
                'refs': [base_ref, comment_ref],
                'type': 'commentary',
                'auto': True,
                'genrated_by': 'Masechtot Ketanot Parser'
            })
        return links

    @staticmethod
    def get_base_index(en_title, he_title):
        node = JaggedArrayNode()
        node.add_primary_titles(en_title, he_title)
        node.add_structure(['Chapter', 'Halakhah'])
        node.validate()

        return {
            'title': en_title,
            'categories': ["Masechtot Ketanot"],
            'schema': node.serialize()
        }


supermod.book.subclass = bookSub
# end class bookSub


class frontSub(supermod.front):
    def __init__(self, chapter=None, valueOf_=None, mixedclass_=None, content_=None):
        super(frontSub, self).__init__(chapter, valueOf_, mixedclass_, content_, )
supermod.front.subclass = frontSub
# end class frontSub


class backSub(supermod.back):
    def __init__(self, chapter=None, valueOf_=None, mixedclass_=None, content_=None):
        super(backSub, self).__init__(chapter, valueOf_, mixedclass_, content_, )
supermod.back.subclass = backSub
# end class backSub


class bodySub(supermod.body):
    def __init__(self, chapter=None, commentaries=None):
        super(bodySub, self).__init__(chapter, commentaries, )

    def getTextArray(self):
        return [c.getVerseArray() for c in self.chapter]

supermod.body.subclass = bodySub
# end class bodySub


class pgbrkSub(supermod.pgbrk):
    def __init__(self, id=None, valueOf_=None, mixedclass_=None, content_=None):
        super(pgbrkSub, self).__init__(id, valueOf_, mixedclass_, content_, )
supermod.pgbrk.subclass = pgbrkSub
# end class pgbrkSub


class commentariesSub(supermod.commentaries):
    def __init__(self, commentary=None):
        super(commentariesSub, self).__init__(commentary, )
        self.linked = {}

    def get_authors(self):
        return [commentator.author.valueOf_ for commentator in self.commentary]

    def is_linked_commentary(self, commentary):
        return self.linked[commentary.get_author()]

supermod.commentaries.subclass = commentariesSub
# end class commentariesSub


class commentarySub(supermod.commentary):
    def __init__(self, id=None, label=None, author=None, phrase=None, p=None, chapter=None):
        super(commentarySub, self).__init__(id, label, author, phrase, p, chapter, )

    def validate_chapters(self):
        last_chapter = 0
        for chapter in self.get_chapter():
            if int(chapter.num) - last_chapter != 1:
                return False
            last_chapter += 1
        return True

    def get_author(self):
        return self.author.content_[0].getValue()

    def print_bad_chapters(self):
        expected_chapter = 1
        for chapter in self.get_chapter():
            if int(chapter.num) != expected_chapter:
                print 'expected chapter {} found chapter {}'.format(expected_chapter, chapter.num)
                expected_chapter = int(chapter.num)

            expected_chapter += 1

    def parse_linked(self):
        parsed = JaggedArray([[[]]])  # all commentaries are depth 2?
        for phrase in self.get_phrase():
            indices = (commentStore[phrase.id]['chapter'], commentStore[phrase.id]['verse'], commentStore[phrase.id]['order'])
            text = phrase.get_comment().valueOf_.replace(u'\n', u'')
            parsed.set_element([i-1 for i in indices], text)
        return parsed.array()

    def build_node(self):
        """
        Builds the root schema node for the commentary
        :return: SchemaNode
        """
        node = SchemaNode()
        he_title = self.get_author()
        node.add_primary_titles(commentatorNames[he_title], he_title)
        return node

    def set_verses(self, verse_map):
        """
        Map each phrase to a verse
        :param verse_map: A list of lists. Outer list length == number of chapters. Inner list length == number of
        phrases per chapter
        """
        chapters = self.get_chapter()
        assert len(verse_map) == len(chapters)
        for chapter, inner_map in zip(chapters, verse_map):
            chapter.set_verses(inner_map)


supermod.commentary.subclass = commentarySub
# end class commentarySub


class authorSub(supermod.author):
    def __init__(self, valueOf_=None, mixedclass_=None, content_=None):
        super(authorSub, self).__init__(valueOf_, mixedclass_, content_, )
supermod.author.subclass = authorSub
# end class authorSub


class chapterSub(supermod.chapter):
    def __init__(self, num=None, label=None, phrase=None, p=None, pgbrk=None, verse=None):
        super(chapterSub, self).__init__(num, label, phrase, p, pgbrk, verse, )

    def getVerseArray(self):
        return [v.asString() for v in self.verse]

    def set_verses(self, verse_map):
        """
        Sets the verse attribute on phrases
        :param verse_map: List of integers which map each phrase to a verse (0-indexed). Must be the same length
        as the number of verses
        :return:
        """
        phrases = self.get_phrase()
        assert len(verse_map) == len(phrases)
        for index, phrase in zip(verse_map, phrases):
            phrase.verse = str(index+1)


supermod.chapter.subclass = chapterSub
# end class chapterSub


class verseSub(supermod.verse):
    def __init__(self, num=None, label=None, p=None, pgbrk=None):
        super(verseSub, self).__init__(num, label, p, pgbrk, )

    def asString(self):
        return " ".join([p.asString() for p in self.p])

    def get_xrefs(self):
        return [xref for xref in self.get_p()[0].get_xref()]
supermod.verse.subclass = verseSub
# end class verseSub


class phraseSub(supermod.phrase):
    def __init__(self, id=None, label=None, dh=None, comment=None):
        super(phraseSub, self).__init__(id, label, dh, comment, )
supermod.phrase.subclass = phraseSub
# end class phraseSub


class dhSub(supermod.dh):
    def __init__(self, valueOf_=None, mixedclass_=None, content_=None):
        super(dhSub, self).__init__(valueOf_, mixedclass_, content_, )
supermod.dh.subclass = dhSub
# end class dhSub


class commentSub(supermod.comment):
    def __init__(self, xref=None, valueOf_=None, mixedclass_=None, content_=None):
        super(commentSub, self).__init__(xref, valueOf_, mixedclass_, content_, )
supermod.comment.subclass = commentSub
# end class commentSub


class pSub(supermod.p):
    def __init__(self, xref=None, pgbrk=None, valueOf_=None, mixedclass_=None, content_=None):
        super(pSub, self).__init__(xref, pgbrk, valueOf_, mixedclass_, content_, )

    def _mcAsString(self, mc):
        if mc.getCategory() == mc.CategoryText:
            if mc.getValue().strip():
                return mc.getValue().strip().replace(u"\n", u" ")
            else:
                return u""
        elif mc.getCategory() == mc.CategoryComplex:
            if mc.getName() == "xref":
                return mc.getValue().asITagString()
            elif mc.getName() == "pgbrk":
                return u" "
        else:
            raise Exception("What am I?")

    def asString(self):
        return "".join([self._mcAsString(mc) for mc in self.content_])


supermod.p.subclass = pSub
# end class pSub


class xrefSub(supermod.xref):
    def __init__(self, rid=None, valueOf_=None, mixedclass_=None, content_=None):
        super(xrefSub, self).__init__(rid, valueOf_, mixedclass_, content_, )

    def asITagString(self):
        commentData = commentStore.get(self.get_rid())
        if commentData:
            return u' <i data-commentator="{}" data-order="{}"></i>'.format(commentData["commentator"], commentData["order"])
        else:
            raise Exception("Where am I?")

supermod.xref.subclass = xrefSub
# end class xrefSub


class labelSub(supermod.label):
    def __init__(self, valueOf_=None, mixedclass_=None, content_=None):
        super(labelSub, self).__init__(valueOf_, mixedclass_, content_, )
supermod.label.subclass = labelSub
# end class labelSub


class italicSub(supermod.italic):
    def __init__(self, valueOf_=None, mixedclass_=None, content_=None):
        super(italicSub, self).__init__(valueOf_, mixedclass_, content_, )
supermod.italic.subclass = italicSub
# end class italicSub


class boldSub(supermod.bold):
    def __init__(self, valueOf_=None, mixedclass_=None, content_=None):
        super(boldSub, self).__init__(valueOf_, mixedclass_, content_, )
supermod.bold.subclass = boldSub
# end class boldSub


class underlineSub(supermod.underline):
    def __init__(self, valueOf_=None, mixedclass_=None, content_=None):
        super(underlineSub, self).__init__(valueOf_, mixedclass_, content_, )
supermod.underline.subclass = underlineSub
# end class underlineSub


class bold_italicSub(supermod.bold_italic):
    def __init__(self, valueOf_=None, mixedclass_=None, content_=None):
        super(bold_italicSub, self).__init__(valueOf_, mixedclass_, content_, )
supermod.bold_italic.subclass = bold_italicSub
# end class bold_italicSub


class supSub(supermod.sup):
    def __init__(self, valueOf_=None, mixedclass_=None, content_=None):
        super(supSub, self).__init__(valueOf_, mixedclass_, content_, )
supermod.sup.subclass = supSub
# end class supSub


class subSub(supermod.sub):
    def __init__(self, valueOf_=None, mixedclass_=None, content_=None):
        super(subSub, self).__init__(valueOf_, mixedclass_, content_, )
supermod.sub.subclass = subSub
# end class subSub


class figSub(supermod.fig):
    def __init__(self, id=None, position=None, float_=None, label=None, caption=None, img=None):
        super(figSub, self).__init__(id, position, float_, label, caption, img, )
supermod.fig.subclass = figSub
# end class figSub


class captionSub(supermod.caption):
    def __init__(self, title=None, p=None):
        super(captionSub, self).__init__(title, p, )
supermod.caption.subclass = captionSub
# end class captionSub


class titleSub(supermod.title):
    def __init__(self, p=None):
        super(titleSub, self).__init__(p, )
supermod.title.subclass = titleSub
# end class titleSub


class imgSub(supermod.img):
    def __init__(self, src=None, width=None, height=None, valueOf_=None, mixedclass_=None, content_=None):
        super(imgSub, self).__init__(src, width, height, valueOf_, mixedclass_, content_, )
supermod.img.subclass = imgSub
# end class imgSub


class listSub(supermod.list):
    def __init__(self, id=None, list_type=None, label=None, title=None, list_item=None):
        super(listSub, self).__init__(id, list_type, label, title, list_item, )
supermod.list.subclass = listSub
# end class listSub


class list_itemSub(supermod.list_item):
    def __init__(self, id=None, label=None, p=None):
        super(list_itemSub, self).__init__(id, label, p, )
supermod.list_item.subclass = list_itemSub
# end class list_itemSub


def get_root_tag(node):
    tag = supermod.Tag_pattern_.match(node.tag).groups()[-1]
    rootClass = None
    rootClass = supermod.GDSClassesMapping.get(tag)
    if rootClass is None and hasattr(supermod, tag):
        rootClass = getattr(supermod, tag)
    return tag, rootClass


def parse(inFilename, silence=False):
    parser = None
    doc = parsexml_(inFilename, parser)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'book'
        rootClass = supermod.book
    rootObj = rootClass.factory()
    rootObj.build(rootNode)

    #bespoke
    commentStore.clear()
    del unlinkedCommentStore[:]
    rootObj.populateCommentStore()

    # Enable Python to collect the space used by the DOM.
    doc = None
    if not silence:
        sys.stdout.write('<?xml version="1.0" ?>\n')
        rootObj.export(
            sys.stdout, 0, name_=rootTag,
            namespacedef_='xmlns:t="http://www.w3.org/namespace/"',
            pretty_print=True)
    return rootObj


def parseEtree(inFilename, silence=False):
    parser = None
    doc = parsexml_(inFilename, parser)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'book'
        rootClass = supermod.book
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    mapping = {}
    rootElement = rootObj.to_etree(None, name_=rootTag, mapping_=mapping)
    reverse_mapping = rootObj.gds_reverse_node_mapping(mapping)
    if not silence:
        content = etree_.tostring(
            rootElement, pretty_print=True,
            xml_declaration=True, encoding="utf-8")
        sys.stdout.write(content)
        sys.stdout.write('\n')
    return rootObj, rootElement, mapping, reverse_mapping


def parseString(inString, silence=False):
    from StringIO import StringIO
    parser = None
    doc = parsexml_(StringIO(inString), parser)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'book'
        rootClass = supermod.book
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    if not silence:
        sys.stdout.write('<?xml version="1.0" ?>\n')
        rootObj.export(
            sys.stdout, 0, name_=rootTag,
            namespacedef_='xmlns:t="http://www.w3.org/namespace/"')
    return rootObj


def parseLiteral(inFilename, silence=False):
    parser = None
    doc = parsexml_(inFilename, parser)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'book'
        rootClass = supermod.book
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    if not silence:
        sys.stdout.write('#from DCXML import *\n\n')
        sys.stdout.write('import DCXML as model_\n\n')
        sys.stdout.write('rootObj = model_.rootClass(\n')
        rootObj.exportLiteral(sys.stdout, 0, name_=rootTag)
        sys.stdout.write(')\n')
    return rootObj


USAGE_TEXT = """
Usage: python ???.py <infilename>
"""


def usage():
    print(USAGE_TEXT)
    sys.exit(1)


def main():
    args = sys.argv[1:]
    if len(args) != 1:
        usage()
    infilename = args[0]
    parse(infilename)


if __name__ == '__main__':
    #import pdb; pdb.set_trace()
    main()
