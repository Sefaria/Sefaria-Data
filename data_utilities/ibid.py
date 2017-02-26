# -*- coding: utf-8 -*-

from sefaria.model import *


class BookIbidTracker(object):
    """
    One instance per commentary
    """
    def __init__(self):
        self._table = {}  # Keys are tuples of (index, (sections))
        self._section_length = 0
        self._last_cit = [None, None]
        if self._last_cit[0] and self._last_cit[0]:
            self._last_ref = Ref(u'{}.{}'.format(self._last_cit[0], '.'.join(self._last_cit[1])))
        else:
            self._last_ref = None


    def registerRef(self, oref):
        """
        Every time we resolve a reference successfully, `register` is called, in order to record the reference.
        :param index_name:
        :param sections:
        :return:
        """
        assert isinstance(oref, Ref)


        # d = {}
        # ref = Ref(_obj=d)
        self._table[(None,(None, None))] = oref
        for key_tuple in self.creat_keys(oref):
            self._table[(oref.book,tuple(key_tuple))] = oref

        # register this reference according to all possible future ways it could be referenced

    def resolve(self, index_name, sections):
        """

        :param index_name:
        :param list sections: If any entry in this list is "None", then we treat that as a "שם" or "ibid", resolve it, and return a refrence
        :return: Ref
        """
        #todo: assert if table is empty.
        #todo: print out an error statment if can't find this sham constilation in table

        # recognize what kind of key we are looking for
        found_sham = False
        key = []
        if not index_name and sections == [None, None]:  # it says only Sham (all were None)
                resolvedRef = self._table[(None,(None, None))]
                # notice that self._last_cit doesn't chnge so no need to reasign it
        else:
            if not index_name:
                index_name = self._last_cit[0]
            for i, sect in enumerate(sections):
                if found_sham:  # we are after the place that we need info from
                    key.append(None)
                else:
                    key.append(sections[i])
                if not sect:  # change bool on the first sham you meet
                    found_sham = True
            # if self._table.has_key(index_name, tuple(key)):
            if found_sham:
                try:
                    from_table = self._table[(index_name, tuple(key))].sections
                except:
                    print "error, couldn't find this key", index_name, tuple(key)
                    return "error, couldn't find this key", index_name, tuple(key)
            else:
                from_table = sections # that is it wasn't found in _table
            new_sections = []
            # merge them, shile prefering the sections that were retrived from the citation
            for i, sect in enumerate(sections):
                if sect:
                    new_sections.append(str(sect))
                else:
                    new_sections.append(str(from_table[i]))
            try:
                resolvedRef = Ref(u'{}.{}'.format(index_name, '.'.join(new_sections)))
            except:
                print 'error, problem with the Ref iteslf. ', u'{}.{}'.format(index_name, '.'.join(new_sections))
                return "error, problem with the Ref iteslf", index_name, tuple(key)
            self._last_cit = [index_name, new_sections]
        if resolvedRef.is_empty():
            return "error, problem with the Ref iteslf", resolvedRef
        else:
            self.registerRef(resolvedRef)
        return resolvedRef

    def creat_keys(self, oref, i = 1):

        subs = [[None],[oref.sections[0]]]
        a = len(oref.sections)
        while i < a:
            subsi = filter(lambda item: len(item) == i, subs)
            for sub in subsi:
                new0 = sub[:]
                new0.extend([None])
                subs.append(new0)
                new1 = sub[:]
                new1.extend([oref.sections[i]])
                subs.append(new1)
            i += 1
        return filter(lambda item: len(item) == a, subs)
