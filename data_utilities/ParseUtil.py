# encoding=utf-8

from collections import namedtuple

class DocElement(object):

    @staticmethod
    def build_structure(*args, **kwargs):
        raise NotImplementedError

    @classmethod
    def parse(cls, content, build_structure=False):
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


Description = namedtuple('Description', ['name', 'build_structure'])


class ParsedDocument(object):
    def __init__(self, descriptors):
        self._descriptors = descriptors
        self.structure_classes = self._generate_structure_classes()
        self.Child = self.structure_classes[0]
        self._children = None

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

        return reversed(structure_classes)

    def parse_document(self, content):
        self._children = self.Child.parse(content, build_structure=True)

    def set_child(self, index, content):
        self._children[index] = self.Child(content)
