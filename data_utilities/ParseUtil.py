# encoding=utf-8

"""
This framework simplifies parsing data into nested lists (Jagged Arrays). For example, if one wishes to split a document
into Chapters and Verses, one can write a single method that identifies the chapters and a second method that identifies
the verses. Each of these methods would not need to be dependent on the other in any way.

Basic Usage:
Write methods which take a single argument and return a list. Instance methods, partial objects and
global variables can be used to pass more data to each method. If data regarding location within the JaggedArray is
needed, use a ParseState (view documentation on ParseState for more information).

For each level of the nested list, instantiate a Description with a name and and a parsing method.

Instantiate a ParsedDocument with the text titles (English and Hebrew) and the list of Description instances. If needed,
 a ParseState can be attached to the ParsedDocument.

Call ParsedDocument.parse_document with the data to be parsed. The item passed to parse_document will be passed to the
first parsing method defined in the description list.

The raw JaggedArray can be obtained with ParsedDocument.get_ja(). ParsedDocument.filter_ja can be called with a callback
method. The callback method will accept leaf items from the raw JaggedArray and will place it's return values as leaves
in a new JaggedArray.

An example of this framework being used can be found in:
sources/Shulchan_Arukh/scripts/OC_scripts/Mahatzit_HaShekel/Mahatzit.py


Some points on regarding parsing methods:

The parsing methods can accept any data type. They must return a list, but there are no restrictions on what is
contained inside that list.

Each parsing method will be called once for each item in the list it's parent parsing method returned. So if the first
parsing method returned a list of dictionaries, the second method should take a dictionary as it's input.

Do not expect the ParseState to have reliable information regarding levels of the document that have not been parsed
yet. For example, imagine a document that is to be parsed into Chapters and Verses. While parsing Verses, it will be
possible to obtain the Chapter number but not the Verse number. The full address will be available when calling
filter_ja.
"""

import django
django.setup()
from sefaria.model import *

from data_utilities.util import convert_dict_to_array
from collections import namedtuple


class DocElement(object):
    Doc = NotImplemented

    @staticmethod
    def build_structure(*args, **kwargs):
        raise NotImplementedError

    @classmethod
    def parse(cls, content, build_structure=False):
        raise NotImplementedError

    @classmethod
    def update_state(cls, refnum):
        cls.Doc.update_state(cls, refnum)

    def get_ja(self):
        raise NotImplementedError

    def filter_ja(self, callback, num, state=None, *args, **kwargs):
        raise NotImplementedError


class DocNode(DocElement):
    Child = DocElement
    Doc = NotImplemented

    def __init__(self, content, build_structure=False):
        self._children = self.Child.parse(content, build_structure=build_structure)

    @staticmethod
    def build_structure(*args, **kwargs):
        raise NotImplementedError

    @classmethod
    def parse(cls, content, build_structure=False):
        if build_structure:
            content = cls.build_structure(content)

        children = []
        for num, c in enumerate(content):
            cls.update_state(num)
            children.append(cls(c, build_structure=build_structure))

        return children

    def set_child(self, index, content):
        self._children[index] = self.Child(content)

    def get_ja(self):
        return [child.get_ja() for child in self._children]

    def filter_ja(self, callback, *args, **kwargs):
        children = []
        for num, child in enumerate(self._children):
            child.update_state(num)
            children.append(child.filter_ja(callback, *args, **kwargs))
        return children


class DocLeaf(DocElement):

    def __init__(self, content):
        self._content = content

    @staticmethod
    def build_structure(*args, **kwargs):
        raise NotImplementedError

    @classmethod
    def parse(cls, content, build_structure=False):
        if build_structure:
            content = cls.build_structure(content)

        children = []
        for num, c in enumerate(content):
            cls.update_state(num)
            children.append(cls(c))
        return children

    def get_ja(self):
        return self._content

    def filter_ja(self, callback, *args, **kwargs):
        return callback(self._content, *args, **kwargs)


Description = namedtuple('Description', ['name', 'build_structure'])


class ParsedDocument(object):
    def __init__(self, en_name, he_name, descriptors):
        self.name = en_name
        self.he_name = he_name
        self._descriptors = descriptors
        self.structure_classes = self._generate_structure_classes()
        self._RootObj = type(self.name, (DocNode,), {
            'build_structure': staticmethod(lambda x: x),
            'Child': self.structure_classes[0],
            'Doc': self
        })
        self.Root = None
        self.state_tracker = None

    def _generate_structure_classes(self):
        assert all(isinstance(d, Description) for d in self._descriptors)
        structure_classes = []
        for d in reversed(self._descriptors):  # Create children before parents

            if not structure_classes:  # this is the leaf node
                current_child = type(d.name, (DocLeaf,), {
                    'build_structure': staticmethod(d.build_structure),
                    'Doc': self
                })

            else:
                current_child = type(d.name, (DocNode,), {
                    'build_structure': staticmethod(d.build_structure),
                    'Child': structure_classes[-1],
                    'Doc': self
                })
            structure_classes.append(current_child)

        return list(reversed(structure_classes))

    def parse_document(self, content):
        if self.state_tracker:
            self.state_tracker.reset()
        self.Root = self._RootObj(content, build_structure=True)

    def get_ja_node(self):
        ja_node = JaggedArrayNode()
        ja_node.add_primary_titles(self.name, self.he_name)
        ja_node.add_structure([d.name for d in self._descriptors])
        return ja_node

    def attach_state_tracker(self, state_tracker):
        assert isinstance(state_tracker, ParseState)
        self.state_tracker = state_tracker
        self.state_tracker.reset()

    def update_state(self, structure_class, num=None):
        if self.state_tracker is None or num is None:
            pass
        else:
            self.state_tracker.set_ref(structure_class, num)

    def filter_ja(self, callback, *args, **kwargs):
        if self.Root is None:
            raise AttributeError
        if self.state_tracker is not None:
            self.state_tracker.reset()
        return self.Root.filter_ja(callback, *args, **kwargs)

    def get_ja(self):
        if self.Root is None:
            raise AttributeError
        return self.Root.get_ja()

    def __getattr__(self, item):
        if self.Root is None:
            raise AttributeError
        return getattr(self.Root, item)


class ParseState(object):
    def __init__(self):
        self._state = {}

    def set_ref(self, section_type, refnum):
        if isinstance(section_type, basestring):
            self._state[section_type] = refnum
        else:
            while not isinstance(section_type, type):
                section_type = section_type.__class__
            self._state[section_type.__name__] = refnum

    def get_ref(self, section_type, one_indexed=False):
        try:
            refnum = self._state[section_type]
        except KeyError:
            raise StateError("Not tracking class {}".format(section_type))

        if one_indexed:
            return refnum + 1
        else:
            return refnum

    def reset(self):
        self._state.clear()


def run_on_list(func, include_matches=True, start_method=None):
    """
    Using a callback, breaks a list up into a list of lists.

    :param func: callback; returns bool (or None). Tip: `func` can be any object where callable(func) -> True.
    Class methods or callable objects can be passed here if state is needed to be saved from call to call.
    :param include_matches: Default behaviour is to keep every item in the list. If this is set to False, will skip over
    those items for which func(item) -> True
    e.g.
    >>> func = re.search('@22[a-z]', item)
    >>> items = ['@22a', 'hello', 'world', '@22b', 'foo', 'bar']
    >>> run_on_list(func, include_matches=True)
    [['@22a', 'hello', 'world'], ['@22b', 'foo', 'bar']]
    >>> run_on_list(func, include_matches=False)
    [['hello', 'world'], ['foo', 'bar']]
    :param start_method: A method to run at the beginning of a run. Useful when func is the __call__ method of an
    instance.
    :return: list of lists
    """
    def wrapper(items):
        if callable(start_method):
            start_method()
        indices = []
        for item_num, item in enumerate(items):
            if func(item):
                indices.append(item_num)
        indices.append(len(items))

        if include_matches:
            starts = indices[:-1]
        else:
            starts = [i+1 for i in indices[:-1]]
        ends = indices[1:]
        return [items[start:end] for start, end in zip(starts, ends)]

    return wrapper


class ClashError(Exception):
    pass


class StateError(Exception):
    pass


def directed_run_on_list(func, include_matches=True, one_indexed=False, start_method=None):
    """
    Using a callback, breaks a list into a list of lists. The callback must declare where in the list the following
    items should be placed, or return False / None. Will fail if multiple sections map to the same index.
    :param func: callback. Returns an integer, or False / None
    :param include_matches: Set to False to leave the item that signals a break out of the structure. See doc for
    run_on_list.
    :param one_indexed: Set to True if func returns 1-indexed values. I.e. if func returns 1, send to index 0.
    :param start_method: A method to run at the beginning of a run. Useful when func is the __call__ method of an
    instance.
    :return: list of lists
    """
    def wrapper(items):
        if callable(start_method):
            start_method()
        index_mapping = {}
        for item_num, item in enumerate(items):
            value = func(item)
            if value or value is 0:
                if value in index_mapping:
                    raise ClashError

                index_mapping[value] = item_num

        values = sorted(index_mapping.keys())
        list_mapping = {}

        current, next_ = values[:-1], values[1:]
        for start, end in zip(current, next_):
            if include_matches:
                list_mapping[start] = items[index_mapping[start]:index_mapping[end]]
            else:
                list_mapping[start] = items[index_mapping[start]+1:index_mapping[end]]

        try:
            last_value, last_index = values[-1], index_mapping[values[-1]]
        except IndexError:
            return []
        if not include_matches:
            last_index += 1
        list_mapping[last_value] = items[last_index:]

        if one_indexed:
            return convert_dict_to_array(list_mapping, list)[1:]
        else:
            return convert_dict_to_array(list_mapping, list)

    return wrapper
