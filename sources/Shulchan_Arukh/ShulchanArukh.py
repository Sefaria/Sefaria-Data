# encoding=utf-8

import re
import codecs
from bs4 import BeautifulSoup, Tag
from data_utilities.util import Singleton, getGematria, numToHeb, he_ord, he_num_to_char

"""
This module describes an object module for parsing the Shulchan Arukh and it's associated commentaries. The classes
outlined here are wrappers for BeautifulSoup Tag elements, with the necessary parsing and validation methods built in.
This allows for a steady accumulation of data to be saved on disk as an xml document.
"""


class CommentStore(dict):
    __metaclass__ = Singleton


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

    def _add_child(self, child, raw_text, num, enforce_order=False):
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
            for volume in children:
                if current_child.num == volume.num:
                    raise DuplicateChildError(u'{} appears more than once!'.format(current_child.num))

                if current_child.num < volume.num and enforce_order:
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

    def _mark_children(self, pattern, start_mark, specials, add_child_callback=None, enforce_order=False):
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
                            add_child_callback(u''.join(current_child), child_num, enforce_order)
                            current_child = []
                        child_num = getGematria(new_child.group(1))  #Todo needs to be a callback
                        continue

                    special_pattern = is_special(line, specials)
                    if special_pattern:
                        special_mode = True
                        if child_num > 0:
                            assert len(current_child) > 0
                            add_child_callback(u''.join(current_child), child_num, enforce_order)
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
                    add_child_callback(u''.join(current_child), child_num, enforce_order)

    def load_xrefs_to_commentstore(self, *args, **kwargs):
        for child in self.get_child():
            try:
                child.load_xrefs_to_commentstore(*args, **kwargs)
            except DuplicateCommentError as e:
                print e.message

    def load_comments_to_commentstore(self, *args, **kwargs):
        for child in self.get_child():
            child.load_comments_to_commentstore(*args, **kwargs)

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

    def populate_comment_store(self):
        comment_store = CommentStore()
        comment_store.clear()

        self.get_base_text().load_xrefs_to_commentstore()
        commentaries = self.get_commentaries()
        commentaries.load_xrefs_to_commentstore()
        commentaries.load_comments_to_commentstore()


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

    def add_volume(self, raw_text, vol_num, enforce_order=True):
        """
        Add a new volume to the book. Takes raw text and wraps in a volume tag.
        :param raw_text: Text to be added
        :param vol_num: volume number
        :param enforce_order: If True, will add volumes according to thier numerical order, otherwise, the will appear
        in the order they were added.
        :return: Volume object
        """
        return self._add_child(Volume, raw_text, vol_num, enforce_order)

    def remove_volume(self, num):
        for child in self.get_child():
            if int(child.num) == num:
                child.Tag.decompose()

    def get_volume(self, num):
        for child in self.get_child():
            if child.num == num:
                return child
        else:
            return None

    def load_xrefs_to_commentstore(self, *args, **kwargs):
        for child in self.get_child():
            child.load_xrefs_to_commentstore(self.titles['en'])



class BaseText(Record):
    name = 'base_text'
    parent = Root

    def load_comments_to_commentstore(self, *args, **kwargs):
        raise NotImplementedError("Comments in base text not included in commentstore")


class Commentary(Record):
    name = 'commentary'
    parent = 'Commentaries'

    def __init__(self, soup_tag):
        self.id = soup_tag['id']
        super(Commentary, self).__init__(soup_tag)

    def load_comments_to_commentstore(self):
        for child in self.get_child():
            child.load_comments_to_commentstore(self.titles['en'])


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
        self.he_commentary_ids[he_title] = commentary_id

        raw_commentary = BeautifulSoup(u'', 'xml').new_tag('commentary')
        raw_commentary['id'] = commentary_id
        commentary = Commentary(raw_commentary)
        commentary.add_titles(en_title, he_title)
        self.Tag.append(raw_commentary)
        return commentary

    def get_commentary_by_id(self, commentary_id):
        commentary = self.Tag.find('commentary', attrs={'id': commentary_id})
        if commentary is None:
            return None
        return Commentary(commentary)

    def get_commentary_by_title(self, title, lang='en'):
        try:
            if lang == 'en':
                commentary_id = self.commentary_ids[title]
            elif lang == 'he':
                commentary_id = self.he_commentary_ids[title]
            else:
                raise AssertionError("lang parameter must be 'en' or 'he'")
        except KeyError:
            return None
        return self.get_commentary_by_id(commentary_id)



class OrderedElement(Element):

    def __init__(self, soup_tag):
        self.num = int(soup_tag['num'])
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
                    if previous_element is None:
                        print 'First element is element {}'.format(element.num)
                    else:
                        print 'misordered element: {} followed by {}'.format(previous_element.num, element.num)
            previous_element = element
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

    def _add_siman(self, raw_text, siman_num, enforce_order=False):
        """
        Add a new siman to the volum. Takes raw text and wraps in a siman tag.
        :param raw_text: Text to be added
        :param siman_num: siman number
        :return: Siman object
        """
        return self._add_child(Siman, raw_text, siman_num, enforce_order)

    def mark_simanim(self, pattern, start_mark=None, specials=None, enforce_order=False):
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
        self._mark_children(pattern, start_mark, specials, add_child_callback=self._add_siman, enforce_order=enforce_order)

    def mark_seifim(self, pattern, start_mark=None, specials=None, enforce_order=False):
        errors = []
        for siman in self.get_child():
            assert isinstance(siman, Siman)
            try:
                siman.mark_seifim(pattern, start_mark, specials, enforce_order)
            except DuplicateChildError as e:
                errors.append(e.message)
        return errors

    def format_text(self, start_special, end_special, name):
        errors = []
        for siman in self.get_child():
            assert isinstance(siman, Siman)
            try:
                siman.format_text(start_special, end_special, name)
            except AssertionError as e:
                errors.append(e.message)
        return errors

    def mark_references(self, commentary_id, pattern, group=None):
        for child in self.get_child():
            child.mark_references(self.get_book_id(), commentary_id, pattern, group=group)

    def validate_simanim(self, complete=True, verbose=True):
        self.validate_collection(self.get_child(), complete, verbose)

    def validate_seifim(self, complete=True, verbose=True):
        for siman in self.get_child():
            assert isinstance(siman, Siman)
            if not siman.validate_seifim(complete, verbose=False):
                print "Found in Siman {}".format(siman.num)
                if verbose:
                    siman.validate_seifim(complete, verbose)

    def validate_references(self, pattern, code, group=1, key_callback=getGematria):
        """
        Pull all matches to a regular expression for each siman, then check that they all go in order
        :param pattern: regex pattern
        :param code: The exact code used to identify this reference
        :param group: regex group to capture the numeric part of the match
        :param key_callback: (str) -> int
        callback function to convert the capture group to an integer
        :return: bool
        """
        passed = True
        for siman in self.get_child():
            assert isinstance(siman, Siman)
            passed = siman.validate_references(pattern, code, group, key_callback)
        return passed

    def set_rid_on_seifim(self, base_id=0):
        book_id = self.get_book_id()
        for siman in self.get_child():
            siman.set_rid_on_seifim(base_id, book_id)

    def unlink_seifim(self, bad_rid):
        """
        It's possible that several seifim should not be linked to the base text. Given an `rid` (or list of `rid`s)
        this method will replace the rid field with 'no-link', which will prevent the Seif from being loaded to the
        commentStore
        :param bad_rid: rid to invalidate. Can accept a list
        """
        if isinstance(bad_rid, basestring):
            bad_rid_list = [bad_rid]
        elif isinstance(bad_rid, list):
            bad_rid_list = bad_rid
        else:
            raise TypeError("Cannot recognize type of rid field")

        for rid in bad_rid_list:
            seif = self.Tag.find(lambda x: x.name=='seif' and x.get('rid')==rid)
            assert seif is not None
            seif['rid'] = 'no-link'


    def validate_all_xrefs_matched(self, xref_finding_callback=lambda tag: tag.name=='xref'):
        """
        Find a group of xrefs, look up each id in CommentStore and make sure they have all field filled out.
        :param xref_finding_callback: Callback function that takes a BeautifulSoup Tag object and returns True or
        False. The verification will be run on all tags that are matched by this function. (This is equivalent to passing
        a function to the `find_all()` method on a BeautifulSoup Tag object. View BeautifulSoup documentation for more
        info.
        :return: list of errors found
        """
        comment_store = CommentStore()
        validation_set = self.Tag.find_all(xref_finding_callback)
        assert len(validation_set) > 0
        required_fields = ['base_title', 'siman', 'seif', 'commentator_title', 'commentator_siman', 'commentator_seif']
        errors = []

        for item in validation_set:
            if comment_store.get(item['id']) is None:
                errors.append("xref with id {} not found in comment store".format(item['id']))
            elif any([i not in comment_store[item['id']] for i in required_fields]):
                errors.append("xref with id {} missing required field".format(item['id']))
        if len(errors) == 0:
            print "No errors found"
        return errors

    def locate_references(self, pattern, verbose=True):
        """
        For each match to pattern, output the seif at which pattern was found
        :param pattern:
        :param verbose: If True will print out locations where matches were found
        :return: tuples (seif, siman) at which each location was found
        """
        locations = []
        for siman in self.get_child():
            seifim = siman.locate_references(pattern)
            for seif in seifim:
                locations.append((siman.num, seif))

        if verbose:
            for location in locations:
                print "Pattern found at Siman {}, Seif {}".format(*location)
            if len(locations) == 0:
                print "No matches found"
        return locations


class Siman(OrderedElement):
    name = 'siman'
    parent = 'Volume'
    child = 'Seif'
    multiple_children = True

    def _add_seif(self, raw_text, seif_number, enforce_order=False):
        self._add_child(Seif, raw_text, seif_number, enforce_order)

    def mark_seifim(self, pattern, start_mark=None, specials=None, enforce_order=False):
        try:
            self._mark_children(pattern, start_mark, specials, add_child_callback=self._add_seif, enforce_order=enforce_order)
        except DuplicateChildError as e:
            raise DuplicateChildError('Siman {}, Seif {}'.format(self.num, e.message))

    def format_text(self, start_special, end_special, name):
        for seif in self.get_child():
            assert isinstance(seif, Seif)
            try:
                seif.format_text(start_special, end_special, name)
            except AssertionError as e:
                raise AssertionError('Siman {}, {}'.format(self.num, e.message))

    def mark_references(self, base_id, com_id, pattern, found=0, group=None):
        for child in self.get_child():
            found = child.mark_references(base_id, com_id, self.num, pattern, found, group)
        return found

    def validate_seifim(self, complete=True, verbose=True):
        return self.validate_collection(self.get_child(), complete, verbose)

    def validate_references(self, pattern, code, group=1, key_callback=getGematria):
        """
        Pull all mathces to a regular expression, then check that they all go in order
        :param pattern: regex pattern
        :param code: The exact code used to identify this reference
        :param group: regex group to capture the numeric part of the match
        :param key_callback: (str) -> int
        callback function to convert the capture group to an integer
        :return: bool
        """
        passed = True
        matches, errors = [], []
        for seif in self.get_child():
            matches.extend(seif.grab_references(pattern))
        enumerated_matches = [key_callback(match.group(group)) for match in matches]
        previous = 0
        for index, i in enumerate(enumerated_matches):
            if i - previous != 1:
                if i == 1 and previous == 22:  # For refs that run through the he alphabet repeatedly, this handles the reset to א
                    pass
                else:
                    errors.append((previous, i, index))
                    passed = False
            previous = i
        if not passed:
            print 'Errors for code {} in Siman {}:'.format(code, self.num)
            for error in errors:
                print '\t{} followed by {} (tag {} in this Siman)'.format(*error)
        return passed

    def load_xrefs_to_commentstore(self, title):
        for child in self.get_child():
            child.load_xrefs_to_commentstore(title, self.num)

    def load_comments_to_commentstore(self, title):
        for child in self.get_child():
            try:
                child.load_comments_to_commentstore(title, self.num)
            except MissingCommentError as e:
                print e.message

    def set_rid_on_seifim(self, base_id, book_id):
        for seif in self.get_child():
            seif.set_rid(base_id, book_id, self.num)

    def locate_references(self, pattern):
        """
        For each match to pattern, output the seif at which pattern was found
        :param pattern:
        :return: list of integers that represent the seif number at which a match was found. E.g. if the pattern !@#$
        was found once in seif 5 and twice in seif 7 this will return [1, 2].
        """
        matches = []
        for seif in self.get_child():
            num_patterns = len(seif.grab_references(pattern))
            for _ in range(num_patterns):
                matches.append(seif.num)
        return matches



class Seif(OrderedElement):
    name = 'seif'
    parent = 'Siman'
    child = 'TextElement'
    multiple_children = True

    def __init__(self, soup_tag):
        self.rid = soup_tag.get('rid')
        super(Seif, self).__init__(soup_tag)

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
                    raise AssertionError('Seif {}: Two consecutive formatting patterns ({}) found'.format(self.num, start_special))
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

    def grab_references(self, pattern):
        """
        Find all matches to regex pattern in this seif
        :param pattern: regex pattern
        :return: list of regex match objects
        """
        pattern = re.compile(pattern)
        return list(pattern.finditer(self.Tag.text))

    def load_xrefs_to_commentstore(self, title, siman):
        for child in self.get_child():
            child.load_xrefs_to_commentstore(title, siman, self.num)

    def load_comments_to_commentstore(self, title, siman):
        comment_store = CommentStore()

        if self.rid == 'no-link':
            return

        if comment_store.get(self.rid) is None:
            raise MissingCommentError("No Xref with id {} exists".format(self.rid))

        this_ref = comment_store[self.rid]
        if this_ref.get('commentator_title') is not None:
            raise DuplicateCommentError("Found 2 comments with rid: {}".format(self.rid))
        this_ref['commentator_title'] = title
        this_ref['commentator_siman'] = siman
        this_ref['commentator_seif'] = self.num

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

    def load_comments_to_commentstore(self, *args, **kwargs):
        raise NotImplementedError("Can't load comments at TextElement depth")


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

    def load_xrefs_to_commentstore(self, title, siman, seif):
        comment_store = CommentStore()
        if comment_store.get(self.id) is not None:
            if comment_store[self.id]['seif'] == seif:
                message = "Xref with id '{}' appears twice. Same Seif as previous appearance.".format(self.id)
                print message
            else:
                message = "Xref with id '{}' appears twice. Different Seif as previous appearance.".format(self.id)
                raise DuplicateCommentError(message)

        comment_store[self.id] = {
            'base_title': title,
            'siman': siman,
            'seif': seif
        }

    def load_comments_to_commentstore(self, *args, **kwargs):
        raise NotImplementedError("Can't load comments at Xref depth")

module_locals = locals()

class DuplicateChildError(Exception):
    pass

class DuplicateCommentError(Exception):
    pass

class MissingCommentError(Exception):
    pass


def out_of_order_gematria(regex, siman):
    replacements = {}
    matches = list(re.finditer(regex, siman))
    values = [getGematria(match.group(1)) for match in matches]

    for index, value in enumerate(values):
        if index == 0 or index == len(values) - 1:  # This analysis won't work for the first and last items
            continue
        previous_value, next_value = values[index - 1], values[index + 1]
        if value - previous_value != 1:
            if next_value - previous_value == 2:
                replacements[matches[index].group(0)] = {
                    'start': matches[index].start(),
                    'replacement': matches[index].group(0).replace(matches[index].group(1),
                                                                   numToHeb(previous_value + 1))
                }
    return replacements


def out_of_order_he_letters(regex, siman):
    replacements = {}
    matches = list(re.finditer(regex, siman))
    values = [he_ord(match.group(1)) for match in matches]

    for index, value in enumerate(values):
        if index == 0 or index == len(values) - 1:  # This analysis won't work for the first and last items
            continue
        previous_value, next_value = values[index-1], values[index+1]
        if (value - previous_value) % 22 != 1:
            if (next_value - previous_value) % 22 == 2:
                fixed = (previous_value + 1) % 22
                if fixed == 0:
                    fixed = 22
                replacements[matches[index].group(0)] = {
                    'start': matches[index].start(),
                    'replacement': matches[index].group(0).replace(matches[index].group(1),
                                                                   he_num_to_char(fixed))
                }
    return replacements


def correct_marks(siman, pattern, error_finder=out_of_order_gematria):
    """
    Takes a siman as a string and attempts to make corrections to the codes in that siman. Specifically, this corrects
    those codes where a single code is misnumbered, but the preceding and following codes are correct. In that case,
    this method will replace the offending code with the correct number to allow a correct count.
    Example: @22d, @22h, @22f will reset to @22d, @22e, @22f (English is standing in for hebrew for display purposes).
    :param unicode siman: Unicode string representing a single siman
    :param pattern: regular expression pattern. Group 1 must map to an integer
    :param error_finder: callback function used to identify errors. Must return a dictionary
    :return: Fixed siman as a string
    """
    def repair(match_obj):
        if replacements.get(match_obj.group(0)):
            if match_obj.start() == replacements[match_obj.group(0)]['start']:
                return replacements[match_obj.group(0)]['replacement']
        return match_obj.group(0)

    regex = re.compile(pattern)

    replacements = error_finder(regex, siman)
    return regex.sub(repair, siman)


def correct_marks_in_file(filename, siman_pattern, code_pattern, error_finder=out_of_order_gematria,
                          overwrite=True, start_mark=None):
    """
    Runs the method "correct_marks" over a single file
    :param filename: path to file that is to be corrected
    :param siman_pattern: Pattern to identify new Simanim. Should be at the beginning of a line
    :param code_pattern: Pattern to match the codes. Must have two groups, one for the code, another for the number
    :param error_finder: callback function used to identify errors. Must return a dictionary
    :param overwrite: If True will rewrite the file that was read in. If False, will append "_test" to the end of the
    filename (before the extension).
    :param start_mark: A pattern that can be used to identify where changes can begin. If None, will begin from the
    start of the file.
    :return:
    """
    with codecs.open(filename, 'r', 'utf-8') as infile:
        lines = infile.readlines()
    if not overwrite:
        filename = re.sub(ur'\..{3}$', ur'_test\g<0>', filename)
    outfile = codecs.open(filename, 'w', 'utf-8')
    if start_mark is None:
        started = True
    else:
        started = False
    current_siman = []

    for line in lines:
        if not started:
            outfile.write(line)
            if re.search(start_mark, line):
                started = True
            continue

        if re.match(siman_pattern, line):
            outfile.write(
                correct_marks(u''.join(current_siman), code_pattern, error_finder))
            current_siman = []
        current_siman.append(line)
    else:
        outfile.write(
            correct_marks(u''.join(current_siman), code_pattern, error_finder))

    outfile.close()
