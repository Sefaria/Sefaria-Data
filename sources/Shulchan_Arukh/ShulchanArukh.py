# encoding=utf-8

import re
import codecs
from bs4 import BeautifulSoup, Tag
from data_utilities.util import Singleton, getGematria

"""
This module describes an object module for parsing the Shulchan Arukh and it's associated commentaries. The classes
outlined here are wrappers for BeautifulSoup Tag elements, with the necessary parsing and validation methods built in.
This allows for a steady accumulation of data to be saved on disk as an xml document.
"""

@Singleton
class CommentStore(dict):
    pass


class Element(object):
    """
    The most abstract class, this class defines the wrapping of the Tag element, as well as methods for going up and
    down the tree.
    """
    name = NotImplemented  # name of xml attribute associated with this class
    parent = NotImplemented
    child = NotImplemented  # This will be the default child. None for Elements where a default child cannot be defined.
    multiple_children = False


    def __init__(self, soup_tag):
        """
        :param Tag soup_tag:
        """
        self.Tag = soup_tag

    def get_parent(self):
        if self.parent is NotImplemented:
            raise NotImplementedError

        elif self.parent is None:
            return None

        else:
            parent_cls = module_locals[self.parent]
            parent_element = self.Tag.parent
            assert parent_cls.name == parent_element.name
            return parent_cls(parent_element)

    def get_child(self):
        if self.child is NotImplemented:
            raise NotImplementedError

        elif self.child is None:
            return None

        elif self.multiple_children:
            child_cls = module_locals[self.child]
            return [child_cls(child_element) for child_element in self.Tag.find_all(child_cls.name, recursive=False)]

        else:
            child_cls = module_locals[self.child]
            return child_cls(self.Tag.find(child_cls.name, recursive=False))

    def _add_child(self, child, raw_text, num):
        """
        Add a new ordered child to the parent. Takes raw text and wraps in a child tag.
        :param child: Child to be added. Must be the child type specified by the parent class
        :param raw_text: Text to be added
        :param num: volume number
        :return: Volume object
        """
        assert issubclass(child, OrderedElement)
        assert module_locals[self.child] == child
        raw_xml = u'<{} num="{}">{}</{}>'.format(child.name, num, raw_text, child.name)
        current_child = child(BeautifulSoup(raw_xml, 'xml').find(child.name))

        children = self.get_child()
        if len(children) == 0:
            self.Tag.append(current_child.Tag)
        else:
            # assert that volumes are stored in order
            assert OrderedElement.validate_collection(children)
            for volume in children:
                if current_child.num == volume.num:
                    raise DuplicateChildError(u'{} appears more than once!'.format(current_child.num))

                if current_child.num < volume.num:
                    volume.Tag.insert_before(current_child.Tag)
                    break
            else:
                self.Tag.append(current_child.Tag)
        return current_child

    def add_special(self, raw_text, name, found_after=None):
        """
        Helpful where something appears that doesn't fit into the regular data model (i.e. introductions,
        chapter titles, siman categories etc.) Appends to the end of the current tag
        :param raw_text: Raw text to be added
        :param name: name of the xml element
        :param found_after: If parent element (self) has ordered children, this keeps track of the location where this
        was found. If found before the first child segment, set to 0. If None, the attribute will not be set.
        :return:
        """
        raw_xml = u'<{}>{}</{}>'.format(name, raw_text, name)
        special = BeautifulSoup(raw_xml, 'xml').find(name)
        if found_after is not None:
            special['found_after'] = found_after
        self.Tag.append(special)

    def _mark_children(self, pattern, start_mark, specials, add_child_callback=None):
        """
        Mark up simanim in xml.
        :param pattern: regex pattern. The first capture group should indicate the siman number
        :param start_mark: regex pattern. If passed, will only begin scanning document from this location.
        Everything before will be thrown away.
        :param dict specials: Can be used to identify other data that needs to be marked up in addition to simanim,
        such as siman categories. Keys should be regex patterns, with value a dict with keys {'name', 'end'}. Name
        should be the name of the xml element this data should be wrapped with. The 'end' key is the regex that will
        mark a return to standard parsing. If not set, the only a single line will be marked.
        :param function add_child_callback: Function to add child
        :return:
        """
        if add_child_callback is None:
            raise NotImplementedError("Please use a class specific callback function for adding children")

        def is_special(line_text, special_patterns):
            if special_patterns is None:
                return False
            regexes = map(re.compile, special_patterns.keys())
            matches = filter(None, [r.search(line_text) for r in regexes])
            tot_matches = len(matches)
            if tot_matches == 0:
                return False
            elif tot_matches == 1:
                return matches[0].re.pattern
            else:
                raise AssertionError(u'{} matches more than 1 special pattern!'.format(matches[0].group()))

        raw_text = unicode(self.Tag.string.extract())
        if start_mark is None:
            started = True
        else:
            started = False
        current_child, child_num = [], -1
        special_mode = False  # Special parsing mode captures data that exists outside ordered structure
        found_after, special_pattern, end_pattern = 0, None, None

        for line in raw_text.splitlines(True):  # keeps the endlines for later
            if started:
                if special_mode:
                    if end_pattern is None:
                        self.add_special(line, specials[special_pattern]['name'], found_after)
                        special_mode = False
                    else:
                        if re.search(end_pattern, line):
                            assert len(current_child) > 0
                            self.add_special(''.join(current_child), specials[special_pattern]['name'], found_after)
                            current_child = []
                            special_mode = False
                        else:
                            current_child.append(line)

                else:
                    new_child = re.search(pattern, line)
                    if new_child:
                        if child_num > 0:  # add the previous siman, will be -1 if this is the first siman marker in the text
                            assert len(current_child) > 0
                            add_child_callback(u''.join(current_child), child_num)
                            current_child = []
                        child_num = getGematria(new_child.group(1))
                        continue

                    special_pattern = is_special(line, specials)
                    if special_pattern:
                        special_mode = True
                        if child_num > 0:
                            assert len(current_child) > 0
                            add_child_callback(u''.join(current_child), child_num)
                            current_child = []
                            found_after = child_num
                            child_num = -1
                        end_pattern = specials[special_pattern].get('end')

                    else:
                        assert child_num > 0  # Do not add text before the first siman marker has been found
                        current_child.append(line)
            else:
                if re.search(start_mark, line):
                    started = True

        else:  # add the last siman or special text
            if child_num == -1 and len(current_child) == 0:  # Last line was special, everything was added
                pass
            else:
                assert len(current_child) > 0
                if special_mode:
                    self.add_special(u''.join(current_child), specials[special_pattern]['name'], found_after)
                else:
                    add_child_callback(u''.join(current_child), child_num)


    def __unicode__(self):
        return unicode(self.Tag)


class Root(Element):

    """
    Root of the data tree.
    """
    name = 'root'
    parent = None
    child = None  # No default child is defined, call to BaseText or Commentaries explicitly

    def __init__(self, filename):
        self.filename = filename
        self.soup = self._load()
        super(Root, self).__init__(self.soup.root)

    def _load(self):
        with open(self.filename) as infile:
            soup = BeautifulSoup(infile, 'xml')
        return soup

    def export(self, new_file=None, pretty_print=False):
        """
        Export data tree to xml file
        :param new_file: Pass this parameter to save to a new file, otherwise this will overwrite the original file
        :param pretty_print:
        """
        if new_file is None:
            filename = self.filename
        else:
            filename = new_file
        with codecs.open(filename, 'w', 'utf-8') as outfile:
            if pretty_print:
                outfile.write(self.soup.prettify())
            else:
                outfile.write(unicode(self.soup))

    @staticmethod
    def create_skeleton(filename):
        """
        Create a blank xml document for a new parsing project
        :param filename: Name of file to store xml
        :param dict titles: keys: en_title, he_title
        """
        soup = BeautifulSoup('', 'xml')
        soup.append(soup.new_tag('root'))
        soup.root.append(soup.new_tag('base_text'))
        soup.root.append(soup.new_tag('commentaries'))

        with codecs.open(filename, 'w', 'utf-8') as outfile:
            outfile.write(unicode(soup))

    def get_base_text(self):
        return BaseText(self.Tag.base_text)

    def get_commentaries(self):
        return Commentaries(self.Tag.commentaries)

    def get_commentary_id(self, commentator, lang='en'):
        commentaries = self.get_commentaries()
        if lang == 'en':
            return commentaries.commentary_ids[commentator]
        elif lang == 'he':
            return commentaries.he_commentary_ids[commentator]
        else:
            raise AssertionError("Unknown language passed. Recognized values are 'en' or 'he'")


class Record(Element):
    """
    Parent class for IndexRecords (entire books)
    """
    child = 'Volume'
    multiple_children = True
    def __init__(self, soup_tag):
        super(Record, self).__init__(soup_tag)
        en_title = self.Tag.find('en_title', recursive=False)
        he_title = self.Tag.find('he_title', recursive=False)

        if en_title is None or he_title is None:
            self.titles = None
        else:
            self.titles = {'en': en_title.text, 'he': he_title.text}

    def add_titles(self, en_title, he_title):

        if self.titles is not None:
            self._remove_titles()

        self.titles = {'en': en_title, 'he': he_title}

        # add titles to xml
        soup = BeautifulSoup(u'', 'xml')
        self.Tag.insert(0, soup.new_tag('en_title'))
        self.Tag.en_title.append(en_title)
        self.Tag.insert(1, soup.new_tag('he_title'))
        self.Tag.he_title.append(he_title)

    def _remove_titles(self):
        self.titles = None

        he_title = self.Tag.find('he_title', recursive=False)
        en_title = self.Tag.find('en_title', recursive=False)

        if he_title:
            he_title.decompose()
        if en_title:
            en_title.decompose()

    def get_simanim(self):
        #Todo
        pass

    def add_volume(self, raw_text, vol_num):
        """
        Add a new volume to the book. Takes raw text and wraps in a volume tag.
        :param raw_text: Text to be added
        :param vol_num: volume number
        :return: Volume object
        """
        return self._add_child(Volume, raw_text, vol_num)



class BaseText(Record):
    name = 'base_text'
    parent = Root


class Commentary(Record):
    name = 'commentary'
    parent = 'Commentaries'

    def __init__(self, soup_tag):
        self.id = soup_tag['id']
        super(Commentary, self).__init__(soup_tag)


class Commentaries(Element):
    name = 'commentaries'
    parent = 'Root'
    child = 'Commentary'
    multiple_children = True

    def __init__(self, soup_tag):
        super(Commentaries, self).__init__(soup_tag)
        self.commentary_ids = {}
        self.he_commentary_ids = {}

        for commentary in self.get_child():
            self.commentary_ids[commentary.titles['en']] = commentary.id
            self.he_commentary_ids[commentary.titles['he']] = commentary.id

    def add_commentary(self, en_title, he_title):
        assert self.commentary_ids.get(en_title) is None
        commentary_id = len(self.commentary_ids) + 1
        self.commentary_ids[en_title] = commentary_id

        raw_commentary = BeautifulSoup(u'', 'xml').new_tag('commentary')
        raw_commentary['id'] = commentary_id
        commentary = Commentary(raw_commentary)
        commentary.add_titles(en_title, he_title)
        self.Tag.append(raw_commentary)
        return commentary



class OrderedElement(Element):

    def __init__(self, soup_tag):
        self.num = soup_tag['num']
        super(OrderedElement, self).__init__(soup_tag)

    def validate_order(self, previous=None):
        """
        Checks that num of this element follows that of previous
        :param previous: Previous element in an array of OrderedElements. If None will return True (useful for first element)
        :return: bool
        """
        if previous is None:
            return True
        else:
            assert isinstance(previous, OrderedElement)
            if self.num <= previous.num:
                return False
            else:
                return True

    def validate_complete(self, previous=None):
        """
        Checks that the num of this element is exactly 1 more than the previous element. If previous is None, will
        return True only if the num of self is 0 or 1.
        :param previous: Previous OrderedElement in array of elements. If first element, pass None.
        :return: bool
        """
        if previous is None:
            return self.num == 1 or self.num == 0
        else:
            assert isinstance(previous, OrderedElement)
            return (self.num - previous.num) == 1

    @staticmethod
    def validate_collection(element_list, complete=False, verbose=False):
        """
        Run a validation on an array of ordered elements
        :param list[OrderedElement] element_list: list of OrderedElement instances
        :param complete: True will run the validate_complete method, otherwise will check only ascending order.
        :param verbose: Set to True to view print statements regrading locations of missing elements
        :return: bool
        """
        passed = True
        previous_element = None
        for element in element_list:
            if complete:
                validation = element.validate_complete
            else:
                validation = element.validate_order
            if not validation(previous_element):
                passed = False
                if verbose:
                    print 'misordered element at location {}'.format(element.num)
        if verbose and passed:
            print 'Validation Successful'
        return passed


class Volume(OrderedElement):
    name = 'volume'
    child = 'Siman'
    multiple_children = True

    def get_book_id(self):
        if self.Tag.parent.name == 'base_text':
            return 0
        else:
            return Commentary(self.Tag.parent).id

    def _add_siman(self, raw_text, siman_num):
        """
        Add a new siman to the volum. Takes raw text and wraps in a siman tag.
        :param raw_text: Text to be added
        :param siman_num: siman number
        :return: Siman object
        """
        return self._add_child(Siman, raw_text, siman_num)

    def mark_simanim(self, pattern, start_mark=None, specials=None):
        """
        Mark up simanim in xml.
        :param pattern: regex pattern. The first capture group should indicate the siman number
        :param start_mark: regex pattern. If passed, will only begin scanning document from this location.
        Everything before will be thrown away.
        :param dict specials: Can be used to identify other data that needs to be marked up in addition to simanim,
        such as siman categories. Keys should be regex patterns, with value a dict with keys {'name', 'end'}. Name
        should be the name of the xml element this data should be wrapped with. The 'end' key is the regex that will
        mark a return to standard parsing. If not set, the only a single line will be marked.
        :return:
        """
        self._mark_children(pattern, start_mark, specials, add_child_callback=self._add_siman)

    def mark_seifim(self, pattern, start_mark, specials=None):
        for siman in self.get_child():
            assert isinstance(siman, Siman)
            siman.mark_seifim(pattern, start_mark, specials)

    def format_text(self, start_special, end_special, name):
        for siman in self.get_child():
            assert isinstance(siman, Siman)
            siman.format_text(start_special, end_special, name)

    def mark_references(self, commentary_id, pattern):
        for child in self.get_child():
            child.mark_references(self.get_book_id(), commentary_id, self.num, pattern)

class Siman(OrderedElement):
    name = 'siman'
    parent = 'Volume'
    child = 'Seif'
    multiple_children = True

    def _add_seif(self, raw_text, seif_number):
        self._add_child(Seif, raw_text, seif_number)

    def mark_seifim(self, pattern, start_mark, specials=None):
        self._mark_children(pattern, start_mark, specials, add_child_callback=self._add_seif)

    def format_text(self, start_special, end_special, name):
        for seif in self.get_child():
            assert isinstance(seif, Seif)
            seif.format_text(start_special, end_special, name)

    def mark_references(self, base_id, com_id, pattern, found=0, group=None):
        for child in self.get_child():
            found = child.mark_references(base_id, com_id, self.num, pattern, found, group)
        return found

class Seif(OrderedElement):
    name = 'seif'
    parent = 'Siman'
    child = 'TextElement'
    multiple_children = True

    def __init__(self, soup_tag):
        self.rid = None
        super(OrderedElement, self).__init__(soup_tag)

    def get_child(self):
        return [TextElement(c) for c in self.Tag.children]

    def format_text(self, start_special, end_special, name):
        """
        Mark up the text into regular and "special" formatting. Can only handle one type of special formatting. Useful
        for marking dh in bold, or רמ"א in the base text.
        :param start_special: regex pattern to match beginning of formatted text. Warning: Two consecutive start_special
        patterns will cause this method to fail.
        :param end_special: regex pattern to match end of formatted text. This pattern will be ignored if not preceded
        by a start_special pattern.
        :param name: Name of tag to wrap formatted text in.
        :return:
        """
        def add_formatted_text(words, element_name):
            if len(words) == 0:
                return
            else:
                self.add_special(u' '.join(words), element_name)

        assert self.Tag.string is not None  # This can happen if xml elements are already present of if Tag is self-closing.
        text_array = self.Tag.string.extract().split()

        is_special = False
        element_words = []
        for word in text_array:
            if re.search(start_special, word):
                if is_special:  # Two consecutive special patterns have been found
                    raise AssertionError('Two consecutive formatting patterns found')
                else:
                    word = re.sub(start_special, u'', word)
                    if len(element_words) > 0:
                        element_words.append(u'')  # adds a space to the end of the text element
                        self.add_special(u' '.join(element_words), name=u'reg-text')
                    element_words = []
                    is_special = True

            elif re.search(end_special, word):
                if is_special:
                    assert len(element_words) > 0  # Do not allow formatted text with no text
                    element_words.append(u'')
                    self.add_special(u' '.join(element_words), name=name)
                    element_words = []
                    is_special = False

                word = re.sub(end_special, u'', word)
            element_words.append(word)
        else:
            if is_special:
                add_formatted_text(element_words, element_name=name)
            else:
                add_formatted_text(element_words, element_name=u'reg-text')


    def set_rid(self, base_id, com_id, siman_num):
        if com_id == 0:  # 0 is reserved to reference the base text
            raise AssertionError("Base text seifim do not have an rid")

        self.rid = u'b{}-c{}-si{}-ord{}'.format(base_id, com_id, siman_num, self.num)
        self.Tag['rid'] = self.rid

    def mark_references(self, base_id, com_id, siman, pattern, found=0, group=None):
        for child in self.get_child():
            found = child.mark_references(base_id, com_id, siman, pattern, found, group)
        return found

class TextElement(Element):
    parent = 'Seif'
    child = 'Xref'
    multiple_children = True

    def mark_references(self, base_id, com_id, siman_num, pattern, found=0, group=None):
        """
        Mark a single set of references (i.e. all references from shach to Shulchan Arukh) based on a regular expression
        :param base_id: id of text where the mark appears. 0 is reserved for Shulchan Arukh itself
        :param com_id: id of commentary this mark refers to
        :param siman_num: Siman number where mark first appeared
        :param pattern: regex pattern to identify reference mark
        :param int found: Number of marks found in before this element.
        :param int group: If passed, the gematria of the text in this group will determine the comment order of this
         reference. If None, the order will just be set by counting the number of matches found by the expression
        :return: number of matches found in this element, offset by the number found before this element (adds to the
         `found` parameter passed to this method
        """
        # Make sure pattern will not touch the existing xrefs
        for xref in self.Tag.find_all('xref'):
            if re.search(pattern, xref.text):
                raise AssertionError('Pattern matches previously marked reference')

        pre_parsed_text = u''.join([unicode(c) for c in self.Tag.children])
        words = pre_parsed_text.split()

        for index, word in enumerate(words[:]):
            matched_ref = re.search(pattern, word)
            if matched_ref:
                found += 1
                if group is None:
                    order = found
                else:
                    order = getGematria(matched_ref.group(group))
                ref_id = u'b{}-c{}-si{}-ord{}'.format(base_id, com_id, siman_num, order)
                words[index] = u'<xref id="{}">{}</xref>'.format(ref_id, word)

        parsed_text = u'<{}>{}</{}>'.format(self.Tag.name, u' '.join(words), self.Tag.name)
        new_tag = BeautifulSoup(parsed_text, 'xml').find(self.Tag.name)
        self.Tag.replace_with(new_tag)
        self.Tag = new_tag

        return found


class Xref(Element):
    name = 'xref'
    parent = 'TextElement'

    def __init__(self, soup_tag):
        self.id = soup_tag['id']
        super(Xref, self).__init__(soup_tag)

    def __eq__(self, other):
        if isinstance(other, Xref):
            return self.id == other.id
        else:
            return False
    def __hash__(self):
        return hash(self.id)

module_locals = locals()

class DuplicateChildError(Exception):
    pass