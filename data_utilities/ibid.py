# -*- coding: utf-8 -*-

from sefaria.model import *
from sefaria.utils import talmud
from collections import OrderedDict
class BookIbidTracker(object):
    """
    One instance per commentary
    """
    def __init__(self, assert_simple = False):
        self._table = IbidDict()  # Keys are tuples of (index, (sections))
        self._section_length = 0
        self._last_cit = [None, None]
        self.assert_simple = assert_simple


        # if self._last_cit[0] and self._last_cit[1]:
        #     self._last_ref = Ref(u'{}.{}'.format(self._last_cit[0], '.'.join(self._last_cit[1])))
        # else:
        #     self._last_ref = None


    def registerRef(self, oref):
        """
        Every time we resolve a reference successfully, `register` is called, in order to record the reference.
        :param index_name:
        :param sections:
        :return:
        """
        assert isinstance(oref, Ref)
        if self.assert_simple:
            assert not oref.index.is_complex()

        # d = {}
        # ref = Ref(_obj=d)

        text_depth = len(oref.sections)  # since smag is a complex text we deal with, this line is needed
        # if self.assert_simple:
        #     text_depth = oref.index_node.depth
        self._table[(None, tuple([None] * text_depth))] = oref
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
        #todo: raise an error if can't find this sham constilation in table

        # recognize what kind of key we are looking for

        if not sections[-1]:
            # if the last element of sections is None, that means we might not know how long sections is meant to be. look it up in the table
            last_depth = self.get_last_depth(index_name, sections)
            sections = tuple(list(sections) + [None] * (max(len(sections), last_depth) - len(sections))) # choosing the depth of the ref to resolve
        key = []
        found_sham = False
        if False and not index_name and sections == [None, None]:  # it says only Sham (all were None)
            try:
                resolvedRef = self._table[(None,(None, None))]
                # notice that self._last_cit doesn't chnge so no need to reasign it
            except KeyError:
                raise Exception("Ibid table is empty. Can't retrieve book name")
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
                from_table = sections # that is it wasn't in _table
            new_sections = []
            # merge them, while preferring the sections that were retrieved from the citation
            for i, sect in enumerate(sections):
                if sect:
                    new_sections.append(sect)
                else:
                    new_sections.append(from_table[i])
            try:
                book_ref = Ref(index_name)
                if self.assert_simple:
                    assert not book_ref.index.is_complex()
                if self.assert_simple:
                    addressTypes = book_ref.index_node.addressTypes
                else:
                    addressTypes = [None]*len(new_sections)
                section_str_list = []
                for section, addressType in zip(new_sections, addressTypes):
                    if addressType == u'Talmud':
                        section_str_list += [talmud.section_to_daf(section)]
                    else:
                        section_str_list += [str(section)]

                resolvedRef = Ref(u'{}.{}'.format(index_name, '.'.join(section_str_list)))
            except:
                print 'error, problem with the Ref iteslf. ', u'{}.{}'.format(index_name, '.'.join(str(new_sections)))
                return "error, problem with the Ref iteslf", index_name, tuple(key)
            self._last_cit = [index_name, new_sections]
        if resolvedRef.is_empty():
            return "error, problem with the Ref iteslf", resolvedRef
        else:
            self.registerRef(resolvedRef)
        return resolvedRef

    def creat_keys(self, oref, i = 1):
        subs = [[None],[oref.sections[0]]]
        text_depth = len(oref.sections) # creating keys according to this specific ref depth
        # if self.assert_simple:
        #     text_depth = oref.index_node.depth
        while i < text_depth:
            subsi = filter(lambda item: len(item) == i, subs)
            for sub in subsi:
                new0 = sub[:]
                new0.extend([None])
                subs.append(new0)
                new1 = sub[:]
                new1.extend([oref.sections[i]])
                subs.append(new1)
            i += 1
        return filter(lambda item: len(item) == text_depth, subs)


    def ignore_book_name_keys(self):
        '''
        deletes all keys with no book name.
        called after a citation not resolved in Sefaria
        '''
        for k in self._table.keys():
            if not k[0]:
                del self._table[k]

    def get_last_depth(self,index_name, sections):
        last_depth = len(sections)
        for k, v in reversed(self._table.items()):
            if k[0] == index_name:
                last_depth = len(v.sections)
                break
        return last_depth


class IbidDict(OrderedDict):

    def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
        if key in self:
            self.pop(key)
        return super(IbidDict, self).__setitem__(key, value, dict_setitem)

