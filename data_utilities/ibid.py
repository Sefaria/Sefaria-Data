# -*- coding: utf-8 -*-

from sefaria.model import *
from sefaria.system.exceptions import InputError
from sefaria.utils import talmud
from collections import OrderedDict
import regex as re
from data_utilities.util import getGematria

class CitationFinder():
    '''
    class to find all potential citations in a string. classifies citations as either sham, refs, or neither
    neither can still be a ref, but for some reason it isn't parsed correctly
    '''
    REF_INT = 0
    NON_REF_INT = 1
    SHAM_INT = 2
    AFTER_TITLE_DELIMETER_RE = ur"[,.: \r\n]+"

    def get_ultimate_title_regex(self, title, lang, compiled=True):
       #todo: consider situations that it is obvious it is a ref although there are no () ex: ברכות פרק ג משנה ה
       #todo: recognize mishnah or talmud according to the addressTypes given
        """
        returns regex to find either `(title address)` or `title (address)`
        title can be Sham
        :param title: str
        :return: regex
        """
        node = library.get_schema_node(title, lang)
        if not node: # title is unrecognized
            address_regex = CitationFinder.create_or_address_regexes(lang)
        else:
            address_regex = node.address_regex(lang)

        inner_paren_reg = u"(?P<Title>" + re.escape(title) + u")" + CitationFinder.AFTER_TITLE_DELIMETER_RE + \
                          ur'(?:[\[({]' + address_regex + ur'[\])}])(?=\W|$)'

        # outer_paren_reg = ur"""(?<=							# look behind for opening brace
        #     [({]										# literal '(', brace,
        #     [^})]*										# anything but a closing ) or brace
        # )
        # """ + re.escape(title) + after_title_delimiter_re + address_regex + ur"""
        # (?=\W|$)                                        # look ahead for non-word char
        # (?=												# look ahead for closing brace
        #     [^({]*										# match of anything but an opening '(' or brace
        #     [)}]										# zero-width: literal ')' or brace
        # )"""

        outer_paren_reg = ur"""(?:
            [({]										# literal '(', brace,
            [^})]*										# anything but a closing ) or brace
        )
        """ + u"(?P<Title>" + re.escape(title) + u")" + CitationFinder.AFTER_TITLE_DELIMETER_RE + address_regex + ur"""
            [^({]*										# match of anything but an opening '(' or brace
            [)}]										# zero-width: literal ')' or brace
        """
        reg = u'(?:{})|(?:{})'.format(inner_paren_reg,outer_paren_reg)
        #reg = outer_paren_reg
        if compiled:
            reg = re.compile(reg, re.VERBOSE)
        return reg

    @staticmethod
    def get_address_regex_dict(lang):
        address_list_depth1 = [
            ["Integer"],
            ["Perek"],
            ["Mishnah"],
            ["Talmud"],
            #["Volume"]
        ]

        jagged_array_nodes = {
            "{}".format(address_item[0]): CitationFinder.create_jan_for_address_type(address_item) for address_item in
            address_list_depth1
            }

        sham_regex = u"(?P<a0>{})".format(u"שם")

        address_regex_dict = {}
        for addressName, jan in jagged_array_nodes.items():
            address_regex_dict["_".join(["Sham", addressName])] = {"regex": [sham_regex, jan.address_regex(lang)],
                                                                   "jan_list": [None, jan]}
            address_regex_dict["_".join([addressName, "Sham"])] = {"regex": [jan.address_regex(lang), sham_regex],
                                                                   "jan_list": [jan, None]}

        address_list_depth2 = [
            ["Integer", "Integer"],
            ["Perek", "Mishnah"],
            ["Talmud", "Integer"],
            # ["Perek", "Halakhah"],
            # ["Siman", "Seif"],
            #["Volume", "Integer"],
            # ["Volume","Siman"]
        ]

        for address_item in address_list_depth2:
            jan1 = jagged_array_nodes[address_item[0]]
            jan2 = jagged_array_nodes[address_item[1]]
            address_regex_dict["_".join(address_item)] = {"regex": [jan1.address_regex(lang), jan2.address_regex(lang)],
                                                          "jan_list": [jan1, jan2]}

        return address_regex_dict

    @staticmethod
    def create_or_address_regexes(lang):
        address_regex_dict = CitationFinder.get_address_regex_dict(lang)

        def regList2Regex(regList):
            #edit regList[1] to make the group name correct
            regList[1] = regList[1].replace(u"(?P<a0>", u"(?P<a1>")
            return u"{}({}{})?".format(regList[0], CitationFinder.AFTER_TITLE_DELIMETER_RE, regList[1])

        return u'(?:{})'.format(u'|'.join([u'(?P<{}>{})'.format(groupName, regList2Regex(groupRegDict['regex'])) for groupName, groupRegDict in address_regex_dict.items()]))

    @staticmethod
    def create_jan_for_address_type(address_type):
        depth = len(address_type)
        lengths = [0 for i in range(len(address_type))]
        sectionNames = ['' for i in range(len(address_type))]
        return JaggedArrayNode({
            'depth': depth,
            'addressTypes': address_type,
            'lengths': lengths,
            'sectionNames': sectionNames
        })

    @staticmethod
    def parse_sham_match(sham_match, lang):
        address_regex_dict = CitationFinder.get_address_regex_dict(lang)
        for groupName, groupRegexDict in address_regex_dict:
            groupMatch = sham_match.group(groupName)
            if groupMatch:

                break

    def get_potential_refs(self, st, lang = 'he'):
        title_sham = u'שם'

        unique_titles = set(library.get_titles_in_string(st, lang))
        unique_titles.add(title_sham)
        refs = []
        sham_refs = []
        non_refs = []

        for title in unique_titles:
            is_sham = title_sham == title
            node = library.get_schema_node(title, lang)

            title_reg = self.get_ultimate_title_regex(title, lang, compiled=True)
            for m in re.finditer(title_reg, st):
                if not is_sham:
                    if node is None or not isinstance(node, JaggedArrayNode):
                        # this is a bad ref
                        non_refs += [(m, m.span(), CitationFinder.NON_REF_INT)]
                    else:
                        try:
                            refs += [(library._get_ref_from_match(m, node, lang), m.span(), CitationFinder.REF_INT)]
                        except InputError:
                            non_refs += [(m, m.span(), CitationFinder.NON_REF_INT)]
                else:
                    sham_refs += [(m, m.span(), CitationFinder.SHAM_INT)]
        """
            try:
                refs_w_location, non_refs_w_locations = library._build_all_refs_from_string_w_locations(title, st,lang=lang, with_bad_refs=True)
                refs += refs_w_location
                potential_non_refs += non_refs_w_locations
            except AssertionError as e:
                pass



        # separate sham_refs from non_refs
        for pot_ref, location in potential_non_refs:
            if re.search(reg_sham, pot_ref):
                sham_refs += [(pot_ref, location)]
            else:
                 non_refs += [(pot_ref, location)]
        """
        all_refs = refs + non_refs + sham_refs
        all_refs.sort(key=lambda x: x[1][0])

        return all_refs


class IndexIbidFinder(object):

    def __init__(self, index, assert_simple = True):
        '''
        this searches through `index` and finds all references. resolves all ibid refs
        :param index: Index
        '''
        self._index = index
        self._tr = BookIbidTracker(assert_simple=assert_simple)
        self._citationFinder = CitationFinder()

    def find_all_shams_in_st(self, st, lang = 'he'):
        '''

        :param st: source text
        :param lang:
        :return: a list of tuples (Refs objects that originally were Shams, location)
        '''
        from sefaria.utils.hebrew import strip_nikkud
        st = strip_nikkud(st)
        sham_refs = []
        reg = u'(\(|\([^)]* )שם(\)| [^(]*\))'  # finds shams in parenthesis without רבשם
        for sham in re.finditer(reg, st):
            matched = sham.group()
            if len(re.split('\s+', matched)) > 6: # todo: find stitistics of the cutoff size of a ref-citation 6 is a guess
                continue
            try:
                sham_refs += [(self.parse_sham(matched),sham.span())]
            except IbidKeyNotFoundException:
                pass
            except IbidRefException:
                pass # maybe want to call ignore her?
        return sham_refs

    def parse_sham(self, sham_ref):
        '''

        :param sham_ref:
        :return: (index_name , [sections])
        '''
        reg_sham = u'שם'
        sham_ref = re.sub(u'\((.*)\)', ur'\1', sham_ref)
        sham_split = re.split(u'\s+', sham_ref)
        index_name = sham_split[0]
        sections = []
        if index_name == reg_sham:
            index_name = None
        else:
            try:
                index_name = library.get_schema_node(index_name, 'he').full_title()
            except AttributeError:
                self._tr.ignore_book_name_keys()
        if sham_split > 1:
            sections = sham_split[1:]
            sections = [None if sec == reg_sham else getGematria(sec) for sec in sections]

        return (index_name , sections)


    def ibid_find_and_replace(self, st, lang='he', citing_only=False, replace=True):
        #todo: implemant replace = True
        """
        Returns an list of Ref objects derived from string

        :param string st: the input string
        :param lang: "he" note: "en" is not yet supported in ibid
        :param citing_only: boolean whether to use only records explicitly marked as being referenced in text.
        :return: list of :class:`Ref` objects
        """
        refs = []
        ref_with_location = []
        assert lang == 'he'
        # todo: support english

        from sefaria.utils.hebrew import strip_nikkud

        st = strip_nikkud(st)
        all_refs = self._citationFinder.get_potential_refs(st, lang)
        for item, location, type in all_refs:
            if type == CitationFinder.REF_INT:
                refs += [self._tr.resolve(item.index_node.full_title(), item.sections)]
            elif type == CitationFinder.NON_REF_INT:
                self._tr.ignore_book_name_keys()
            elif type == CitationFinder.SHAM_INT:
                refs += [self._tr.resolve()]

        """
        unique_titles = set(library.get_titles_in_string(st, lang, citing_only))
        for title in unique_titles:
            try:
                ref_with_location += library._build_all_refs_from_string_w_locations(title, st, lang)
            except AssertionError as e:
                print u"Skipping Schema Node: {}".format(title)
        shams = self.find_all_shams_in_st(st, lang=lang)
        ref_with_location.extend(shams)
        ref_with_location.sort(key=lambda x: x[1][0])

        tracker = BookIbidTracker(assert_simple=True)
        for item, location in ref_with_location:
            if isinstance(item, Ref):
                refs += [tracker.resolve(item.index_node.full_title(), item.sections)]
            else:
                refs += [tracker.resolve(item[0], item[1])]
        """




        return refs

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
        key = []
        found_sham = False
        last_depth = self.get_last_depth(index_name, sections)
        if not index_name or len(sections) == 0 or not sections[0]: # tzmod to beginning
            sections = tuple([None] * (max(len(sections), last_depth) - len(sections)) + list(sections)) # choosing the depth of the ref to resolve
        elif len(sections) > 0 and not sections[-1]:
            sections = tuple(list(sections) + [None] * (
                max(len(sections), last_depth) - len(
                    sections)))
        if False and not index_name and sections == [None, None]:  # it says only Sham (all were None)
            try:
                resolvedRef = self._table[(None,(None, None))]
                # notice that self._last_cit doesn't chnge so no need to reasign it
            except KeyError:
                raise IbidKeyNotFoundException("Ibid table is empty. Can't retrieve book name")
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
                    raise IbidKeyNotFoundException("couldn't find this key")
                    # print "error, couldn't find this key", index_name, tuple(key)
                    # return "error, couldn't find this key", index_name, tuple(key)
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
                raise IbidRefException(u"problem with the Ref iteslf. {}.{}".format(index_name, '.'.join(str(new_sections))))
                # print 'error, problem with the Ref iteslf. ', u'{}.{}'.format(index_name, '.'.join(str(new_sections)))
                # return "error, problem with the Ref iteslf", index_name, tuple(key)
            self._last_cit = [index_name, new_sections]
        if resolvedRef.is_empty():
            raise IbidRefException('problem with the Ref iteslf')
            # return "error, problem with the Ref iteslf", resolvedRef
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

class IbidKeyNotFoundException(Exception):
    pass

class IbidRefException(Exception):
    # when a Ref is structured correctly but can't be found (ex: 'Genesis 60')
    pass