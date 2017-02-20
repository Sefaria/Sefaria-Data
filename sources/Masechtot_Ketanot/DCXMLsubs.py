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

import re
import sys
import itertools
from collections import Counter
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
    u"מסורת הש״ס": "Mesorat HaShas",
    u"פי׳ החיד״א": "Commentary of Chida",
    u"הגהות": "Haggahot",
    u"הגהות הגרי״ב": "Haggahot R' Yeshaya Berlin",
    u"בנין יהושע": "Binyan Yehoshua",
    u"נוסחא חדשה": "New Nuschah",
    u"נוסחאות כ״י": "Nuschaot from Manuscripts",
    u"ראשון לציון": "Rishon Letzion",
    u"נחלת יעקב": "Nahalat Yaakov",
    u"תומת ישרים": "Tumat Yesharim",
    u"הגהות ומראה מקומות": "Haggahot and Marei Mekomot",
    u"כסא רחמים": "Kisse Rahamim",
    u"הגהות מהריעב״ץ": "Haggahot Ya'avetz",
    u"מצפה איתן": "Mitzpeh Etan",
    u"לב חכמים": "Lev Hakhamim",
    u"נוסחת הגר״א": "Gra's Nuschah",
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
                    if commentStore.get(ref.rid) is not None:
                        print '{} appears more than once'.format(ref.rid)
                    commentStore[ref.rid] = {'chapter': chap_index+1, 'verse': verse_index+1}

        try:
            for c in self.get_body().get_commentaries().get_commentary():
                linked = True
                heName = c.get_author()#.content_[0].getValue()
                if heName == 'UNKNOWN':
                    continue
                enName = commentatorNames[heName]
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
        commentator.  Deprecated - schema system has changed.
        :param en_title: English Title of base text
        :param he_title: Hebrew Title of base text
        :return: JaggedArrayNode
        """
        raise NotImplementedError("Don't use me!")
        node = JaggedArrayNode()
        node.add_primary_titles(en_title, he_title)
        node.add_structure(['Chapter', 'Halakhah', 'Comment'])
        node.validate()
        return node

    @staticmethod
    def get_stored_links(base_title):
        links = []
        for comment in itertools.chain(commentStore.values(), unlinkedCommentStore):
            try:
                base_ref = '{} {}:{}'.format(base_title, comment['chapter'], comment['verse'])
                comment_ref = '{} on {} {}:{}:{}'.format(comment['commentator'], base_title, comment['chapter'],
                                                       comment['verse'], comment['order'])
            except KeyError:
                continue
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
            'categories': ["Tanaitic", "Masechtot Ketanot"],
            'schema': node.serialize()
        }

    def chapter_page_map(self):
        return self.body.chapter_page_map()

    def get_page_numbers(self):
        return self.body.get_page_numbers()

    def get_base_verses(self):
        return self.body.get_base_verses()

    def check_base_verse_order(self):
        self.body.check_verse_order()

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

    def chapter_page_map(self):
        return [chapter.page_map() for chapter in self.get_chapter()]

    def get_page_numbers(self):
        numbers = []
        for chapter in self.get_chapter():
            numbers.extend(chapter.get_page_numbers())
        return numbers

    def get_base_verses(self):
        verses = []
        for chapter in self.get_chapter():
            verses.extend(chapter.get_verse())
        return verses

    def check_verse_order(self):
        no_issues = True
        issues = [chapter.check_verse_order() for chapter in self.get_chapter()]
        for chap_index, chapter in enumerate(issues):
            if len(chapter) == 0:
                continue
            else:
                no_issues = False
            for issue in chapter:
                print "Skip found at Chapter {} verse {}".format(chap_index+1, issue)
        if no_issues:
            print "All verses in correct order"

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

    def check_marked_phrases(self):
        for commentary in self.get_commentary():
            if commentary.get_author() == 'UNKNOWN':
                continue
            if not self.is_linked_commentary(commentary):
                commentary.check_marked_phrases()

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
        parsed = JaggedArray([[[]]])
        for phrase in self.get_phrase():
            indices = (commentStore[phrase.id]['chapter'], commentStore[phrase.id]['verse'], commentStore[phrase.id]['order'])
            text = phrase.get_comment().valueOf_.replace(u'\n', u' ')
            text = re.sub(u' +', u' ', text)
            text = re.sub(ur' (:|\.)', ur'\1', text)
            parsed.set_element([i-1 for i in indices], text)
        return parsed.array()

    def parse_unlinked(self):
        parsed = JaggedArray([[[]]])
        comment_counter = Counter()

        for chapter in self.get_chapter():
            chap_num = chapter.num
            for phrase in chapter.get_phrase():
                phrase_num = phrase.subchap

                if phrase_num is None:
                    raise AttributeError(u'Unlabeled phrase in {} chapter {}'.format(self.get_author(), chap_num))

                comment_number = comment_counter[(chap_num, phrase_num)]
                parsed.set_element([int(chap_num)-1, int(phrase_num)-1, comment_number], phrase.as_string())
                comment_counter[(chap_num, phrase_num)] += 1

                unlinkedCommentStore.append({
                    'commentator': commentatorNames[self.get_author()],
                    'chapter': chap_num,
                    'verse': phrase_num,
                    'order': str(comment_number+1)
                })
        return parsed.array()

    def build_index(self, base_title, he_base_title):
        """
        Builds the root schema node for the commentary
        :return: serialized index
        """
        node = JaggedArrayNode()
        he_author = self.get_author()
        en_author = commentatorNames[he_author]
        node.add_primary_titles('{} on {}'.format(en_author, base_title), u'{} על {}'.format(he_author, he_base_title))
        node.add_structure(['Chapter', 'Halakhah', 'Comment'])
        node.validate()
        return {
            'title': '{} on {}'.format(en_author, base_title),
            'categories': ['Tanaitic', 'Commentary', en_author, "Masechtot Ketanot"],
            'schema': node.serialize(),
            'collective_title': en_author,
            'dependence': "Commentary",
            'base_text_titles': [base_title]
        }

    def get_term_dict(self):
        he_author = self.get_author()
        en_author = commentatorNames[he_author]
        return {
            'name': en_author,
            'scheme': 'commentary_works',
            'titles': [
                {
                    'lang': 'en',
                    'text': en_author,
                    'primary': True
                },
                {
                    'lang': 'he',
                    'text': he_author,
                    'primary': True
                }
            ]
        }

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

    def correct_phrase_verses(self):
        errors = []
        for chapter in self.get_chapter():
            errors.append(chapter.correct_phrase_verses())
        for chapter, error in enumerate(errors):
            if len(error) > 0:
                print 'chapter {} errors found at: '.format(chapter+1),
                for i in error:
                    print '{}, '.format(i),
                else:
                    print '\n'

    def complete_subchaps(self):
        """
        Sometimes a commentary will have the first subchap in a series marked. This will fill in the rest.
        """

        for chapter in self.get_chapter():
            chapter.complete_subchaps()

    def phrases_by_page(self):
        """
        Get a mapping of of phrase by page
        :return: dict
        """
        pages = {}
        for chapter in self.get_chapter():
            for phrase in chapter.get_phrase():
                page_num = re.search(u'ph-[0-9]{1,2}-([0-9A-Z]{1,4})-[0-9]{1,2}', phrase.id).group(1)
                pages.setdefault(page_num, [])
                pages[page_num].append(phrase)
        return pages

    def check_marked_phrases(self):
        for chapter in self.get_chapter():
            if not chapter.check_marked_phrases():
                print u'Unmarked phrase in {} chapter {}'.format(self.get_author(), chapter.num)

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
            if phrase.subchap is None:
                phrase.subchap = str(index+1)

    def _get_verse_boundaries(self):
        current_verse, current_boundary = 1, [0, 0]
        boundaries = []
        phrases = self.get_phrase()

        for p_index, phrase in enumerate(phrases):
            verse = int(phrase.subchap)
            if verse == current_verse:
                current_boundary[1] = p_index
            elif verse - current_verse >= 1:  # have we hit the next verse?
                try:
                    first, second = phrases[p_index+1], phrases[p_index+2]
                except IndexError:
                    continue
                if (phrase.subchap == first.subchap) or (phrase.subchap == second.subchap):
                    current_verse = verse
                    boundaries.append(current_boundary)
                    current_boundary = [p_index, p_index]
            else:
                continue
        else:
            current_boundary[-1] == len(phrases) - 1
            boundaries.append(current_boundary)
        return boundaries

    def check_marked_phrases(self):
        return all([phrase.marked_subchap() for phrase in self.get_phrase()])

    def correct_phrase_verses(self):
        boundaries = self._get_verse_boundaries()
        phrases = self.get_phrase()
        errors = []
        for verse, boundary in enumerate(boundaries):
            for phrase in phrases[boundary[0]:boundary[1]]:
                phrase.subchap = phrases[boundary[0]].subchap
            if verse >= 1:  # check if there is a gap between verse boundaries
                if boundary[0] - boundaries[verse-1][1] != 1:
                    errors.append(verse+1)
        return errors

    def page_map(self):
        breaks = sorted(filter(None, [verse.last_page_break() for verse in self.get_verse()]))
        result = {
            'num': self.num,
            'first': None,
            'last': None
        }
        if len(breaks) > 0:
            result['first'] = breaks[0]
            result['last'] = breaks[-1]
        return result

    def get_page_numbers(self):
        numbers = []
        for verse in self.get_verse():
            numbers.extend(verse.get_page_numbers())
        return numbers

    def complete_subchaps(self):
        current_subchap = None
        for phrase in self.get_phrase():
            if phrase.subchap is None:
                assert current_subchap is not None
                phrase.subchap = current_subchap
            else:
                current_subchap = phrase.subchap

    def check_verse_order(self):
        previous_verse = 0
        issues = []
        for verse in self.get_verse():
            current_verse = int(re.search('ch[0-9]{1,2}-v([0-9]{1,2})', verse.num).group(1))
            if current_verse - previous_verse != 1:
                issues.append(current_verse)
            previous_verse = current_verse
        return issues


supermod.chapter.subclass = chapterSub
# end class chapterSub


class verseSub(supermod.verse):
    def __init__(self, num=None, label=None, p=None, pgbrk=None):
        super(verseSub, self).__init__(num, label, p, pgbrk, )

    def asString(self):
        raw_string = " ".join([p.asString() for p in self.p])
        return re.sub(ur" (\.|:)", ur"\1", raw_string)

    def get_xrefs(self):
        return [xref for xref in self.get_p()[0].get_xref()]

    def last_page_break(self):
        page = None
        for p in self.get_p():
            for pg in p.get_pgbrk():
                if pg is not None:
                    page = pg.id
        return page

    def get_page_numbers(self):
        numbers = []
        for p in self.get_p():
            for pg in p.get_pgbrk():
                if pg is not None:
                    numbers.append(pg.id)
        return numbers

supermod.verse.subclass = verseSub
# end class verseSub


class phraseSub(supermod.phrase):
    def __init__(self, id=None, label=None, dh=None, comment=None):
        super(phraseSub, self).__init__(id, label, dh, comment, )

    def as_string(self):
        dh = u'<b>{}</b>'.format(self.get_dh().get_valueOf_())
        comment = self.get_comment().get_valueOf_()
        raw_string = u'{} {}'.format(dh, comment)
        formatted = raw_string.replace(u'\n', u' ')
        formatted = re.sub(u' +', u' ', formatted)
        formatted = re.sub(ur' (:|\.)', ur'\1', formatted)
        return formatted

    def marked_subchap(self):
        if self.subchap is None:
            return False
        elif self.subchap == '0':
            return False
        else:
            return True

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
            try:
                return u' <i data-commentator="{}" data-order="{}"></i>'.format(commentData["commentator"], commentData["order"])
            except KeyError:
                return u' '
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
