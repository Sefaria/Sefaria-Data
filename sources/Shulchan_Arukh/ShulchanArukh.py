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

        for commentary in self.get_child():
            self.commentary_ids[commentary.titles['en']] = commentary.id

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

    def _add_siman(self, raw_text, siman_num):
        """
        Add a new siman to the volum. Takes raw text and wraps in a siman tag.
        :param raw_text: Text to be added
        :param siman_num: siman number
        :return: Siman object
        """
        return self._add_child(Siman, raw_text, siman_num)

    def mark_simanim(self, pattern, start_mark=None):
        """
        Mark up simanim in xml.
        :param pattern: regex pattern. The first capture group should indicate the siman number
        :param start_mark: regex pattern. If passed, will only begin scanning document from this location.
        Everything before will be thrown away.
        :return:
        """
        raw_text = unicode(self.Tag.string.extract())
        if start_mark is None:
            started = True
        else:
            started = False
        current_siman, siman_num = [], -1

        for line in raw_text.splitlines(True):  # keeps the endlines for later
            if started:
                new_siman = re.search(pattern, line)
                if new_siman is None:  # This is not a new siman
                    assert siman_num > 0  # Do not add text before the first siman marker has been found
                    current_siman.append(line)

                else:
                    if siman_num > 0:  # add the previous siman, will be -1 if this is the first siman marker in the text
                        assert len(current_siman) > 0
                        self._add_siman(u''.join(current_siman), siman_num)
                        current_siman = []
                    siman_num = getGematria(new_siman.group(1))
            else:
                if re.search(start_mark, line):
                    started = True

        else:  # add the last siman
            assert len(current_siman) > 0
            self._add_siman(u''.join(current_siman), siman_num)

class Siman(OrderedElement):
    name = 'siman'
    parent = 'Siman'

class Seif(OrderedElement):
    pass

class TextElement(Element):
    pass


class Xref(Element):
    pass

module_locals = locals()

class DuplicateChildError(Exception):
    pass