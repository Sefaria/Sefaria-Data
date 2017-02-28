# encoding=utf-8

import codecs
from bs4 import BeautifulSoup, Tag

"""
This module describes an object module for parsing the Shulchan Arukh and it's associated commentaries. The classes
outlined here are wrappers for BeautifulSoup Tag elements, with the necessary parsing and validation methods built in.
This allows for a steady accumulation of data to be saved on disk as an xml document.
"""



class Element(object):
    """
    The most abstract class, this class defines the wrapping of the Tag element, as well as methods for going up and
    down the tree.
    """
    Name = NotImplemented  # name of xml attribute associated with this class
    Parent = NotImplemented
    Child = NotImplemented  # This will be the default child. None for Elements where a default child cannot be defined.
    multiple_children = False


    def __init__(self, soup_tag):
        """
        :param Tag soup_tag:
        """
        self.Tag = soup_tag

    def get_parent(self):
        if self.Parent is NotImplemented:
            raise NotImplementedError

        elif self.Parent is None:
            return None

        else:
            return self.Parent(self.Tag.parent)

    def get_child(self):
        if self.Child is NotImplemented:
            raise NotImplementedError

        elif self.Child is None:
            return None

        elif self.multiple_children:
            return [self.Child(child) for child in self.Tag.find_all(self.Child.Name, recursive=False)]

        else:
            return self.Child(self.Tag.find(self.Child.Name, recursive=False))


class Root(Element):

    """
    Root of the data tree.
    """
    Name = 'root'
    Parent = None
    Child = None  # No default child is defined, call to BaseText or Commentaries explicitly

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
        :param filename:
        """
        blank_canvas = u'<?xml version="1.0" encoding="utf-8"?>\n<root><base_text></base_text>' \
                       u'<commentaries></commentaries></root>'
        with codecs.open(filename, 'w', 'utf-8') as outfile:
            outfile.write(blank_canvas)

    def get_base_text(self):
        return BaseText(self.Tag.base_text)

    def get_commentaries(self):
        return Commentaries(self.Tag.commentaries)


class Record(Element):
    """
    Parent class for IndexRecords (entire books)
    """
    Child = Volume
    def __init__(self, soup_tag):
        super(Record, self).__init__(soup_tag)
        en_title = self.Tag.find('en_title', recursive=True)
        he_title = self.Tag.find('he_title', recursive=True)

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
        self.Tag.append(soup.new_tag('en_title'))
        self.Tag.en_title.append(en_title)
        self.Tag.append(soup.new_tag('he_title'))
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


class BaseText(Record):
    Name = 'base_text'
    Parent = Root


class Commentary(Record):
    Name = 'commentary'
    Parent = Commentaries

    def __init__(self, soup_tag):
        self.id = soup_tag.id
        if self.id is None:
            raise AttributeError("No id attribute")
        super(Commentary, self).__init__(soup_tag)


class Commentaries(Element):
    Name = 'commentaries'
    Parent = Root
    Child = Commentary
    multiple_children = True

    def __init__(self, soup_tag):
        super(Commentaries, self).__init__(soup_tag)
        self.commentary_ids = {}

        for commentary in self.get_child():
            self.commentary_ids[commentary.titles['en']] = commentary.id

    def add_commentary(self, en_title, he_title):
        pass
        #Todo

class OrderedElement(Element):
    pass

class Volume(OrderedElement):
    pass

class TextElement(Element):
    pass


class Xref(Element):
    pass

