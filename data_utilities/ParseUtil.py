# encoding=utf-8

import django
django.setup()
from sefaria.model import *

from data_utilities.util import convert_dict_to_array
from collections import namedtuple


class DocElement(object):

    @staticmethod
    def build_structure(*args, **kwargs):
        raise NotImplementedError

    @classmethod
    def parse(cls, content, build_structure=False):
        raise NotImplementedError

    def get_ja(self):
        raise NotImplementedError

    def filter_ja(self, callback, *args, **kwargs):
        raise NotImplementedError


class DocNode(DocElement):
    Child = DocElement

    def __init__(self, content, build_structure=False):
        self._children = self.Child.parse(content, build_structure)

    @staticmethod
    def build_structure(*args, **kwargs):
        raise NotImplementedError

    @classmethod
    def parse(cls, content, build_structure=False):
        if build_structure:
            content = cls.build_structure(content)
        return [cls(c, build_structure) for c in content]

    def set_child(self, index, content):
        self._children[index] = self.Child(content)

    def get_ja(self):
        return [child.get_ja() for child in self._children]

    def filter_ja(self, callback, *args, **kwargs):
        return [child.filter_ja(callback, *args, **kwargs) for child in self._children]


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
        return [cls(c) for c in content]

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
            'Child': self.structure_classes[0]
        })
        self.Root = None

    def _generate_structure_classes(self):
        assert all(isinstance(d, Description) for d in self._descriptors)
        structure_classes = []
        for d in reversed(self._descriptors):  # Create children before parents

            if not structure_classes:  # this is the leaf node
                current_child = type(d.name, (DocLeaf,), {'build_structure': staticmethod(d.build_structure)})

            else:
                current_child = type(d.name, (DocNode,), {
                    'build_structure': staticmethod(d.build_structure),
                    'Child': structure_classes[-1]
                })
            structure_classes.append(current_child)

        return list(reversed(structure_classes))

    def parse_document(self, content):
        self.Root = self._RootObj(content, build_structure=True)

    def get_ja_node(self):
        ja_node = JaggedArrayNode()
        ja_node.add_primary_titles(self.name, self.he_name)
        ja_node.add_structure([d.name for d in self._descriptors])
        return ja_node

    def __getattr__(self, item):
        if self.Root is None:
            raise AttributeError
        return getattr(self.Root, item)


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

        last_value, last_index = values[-1], index_mapping[values[-1]]
        if not include_matches:
            last_index += 1
        list_mapping[last_value] = items[last_index:]

        if one_indexed:
            return convert_dict_to_array(list_mapping, list)[1:]
        else:
            return convert_dict_to_array(list_mapping, list)

    return wrapper
