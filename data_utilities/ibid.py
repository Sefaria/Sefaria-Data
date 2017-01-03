# -*- coding: utf-8 -*-

from sefaria.model import *


class BookIbidTracker(object):
    """
    One instance per commentary
    """
    def __init__(self):
        self._table = {}  # Keys are tuples of (index, (sections))
        self._last_reference = None

    def registerRef(self, ref):
        pass

    def register(self, index_name, sections):
        """
        Every time we resolve a reference successfully, `register` is called, in order to record the reference.
        :param index_name:
        :param sections:
        :return:
        """
        assert library.get_index(index_name)
        assert isinstance(sections, list)
        d = {}
        ref = Ref(_obj=d)
        self._last_reference = ref

        # register this reference according to all possible future ways it could be referenced
        

    def resolve(self, index_name, sections):
        """

        :param index_name:
        :param sections: If any entry in this list is "None", then we treat that as a "שם" or "ibid", resolve it, and return a refrence
        :return: Ref
        """
        assert library.get_index(index_name)
        assert isinstance(sections, list)
        resolvedRef = Ref()
        self.register(resolvedRef)
