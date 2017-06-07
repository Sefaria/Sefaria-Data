# -*- coding: utf-8 -*-

from sefaria.model import *
from sefaria.system.exceptions import InputError
from sefaria.utils import talmud
from sefaria.utils.hebrew import strip_nikkud
from collections import OrderedDict
import regex as re
import json, codecs
from data_utilities.util import getGematria


class CitationFinder():
    '''
    class to find all potential citations in a string. classifies citations as either sham, refs, or neither
    neither can still be a ref, but for some reason it isn't parsed correctly
    '''
    REF_INT = 0
    NON_REF_INT = 1
    SHAM_INT = 2
    IGNORE_INT = 3
    AFTER_TITLE_DELIMETER_RE = ur"[,.: \r\n]+"

    @staticmethod
    def get_ultimate_title_regex(title_list, title_node_dict, lang, compiled=True):
       #todo: consider situations that it is obvious it is a ref although there are no () ex: ברכות פרק ג משנה ה
        """
        returns regex to find either `(title address)` or `title (address)`
        title can be Sham
        :param title_list: str or list
        :param title_node_dict: dict or SchemaNode
        :return: regex
        """

        if not isinstance(title_list, list) and not isinstance(title_node_dict, dict):
            title_node_dict = {u"{}".format(title_list): title_node_dict}
            title_list = [title_list]

        #  todo: if title is sham then we don't want to find prefixes for it

        after_title_delimiter_re = ur"[,.: \r\n]+"
        start_paren_reg = ur"(?:[(\[{][^})\]]*)"
        end_paren_reg = ur"(?:[\])}]|\W[^({\[]*[\])}])"

        title_reg_list = []

        for title in title_list:
            node = title_node_dict[title]
            if node is None:  # title is unrecognized
                address_regex = CitationFinder.create_or_address_regexes(lang)
            else:
                address_regex = node.address_regex(lang)


            # inner_paren_reg = u"(?P<Title>" + re.escape(title) + u")" + after_title_delimiter_re + ur'(?:[\[({]' + address_regex + ur'[\])}])(?=\W|$)'
            inner_paren_reg = u"(?P<Title>" + re.escape(title) + u")" + after_title_delimiter_re + ur'(?:[\[({])' + address_regex + end_paren_reg
            outer_paren_reg = start_paren_reg + u"(?P<Title>" + re.escape(title) + u")" + after_title_delimiter_re + \
                          address_regex + end_paren_reg

            if title == u"שם":
                sham_reg = u"שם"
                stam_sham_reg = ur"(?:[(\[{])(?P<Title>" + sham_reg + u")(?:[\])}])"
                outer_paren_sham_reg = ur"(?:[(\[{])" + u"(?P<Title>" + re.escape(title) + u")" + after_title_delimiter_re + \
                              address_regex + end_paren_reg
                reg = u'(?:{})|(?:{})|(?:{})'.format(inner_paren_reg, outer_paren_sham_reg, stam_sham_reg)
            else:
               reg = u'(?:{})|(?:{})'.format(inner_paren_reg, outer_paren_reg)

            title_reg_list += [reg]

        full_crazy_ultimate_title_reg = u"|".join([u"(?:{})".format(title_reg) for title_reg in title_reg_list])

        if compiled:
            full_crazy_ultimate_title_reg = re.compile(full_crazy_ultimate_title_reg, re.VERBOSE)
        return full_crazy_ultimate_title_reg

    @staticmethod
    def get_address_regex_dict(lang):
        address_list_depth1 = [
            ["Integer"],
            ["Perek"],
            ["Mishnah"],
            ["Talmud"],
            ["Siman"],
            ["Seif"],
            ["Halakhah"],
            ["Volume"]
        ]

        jagged_array_nodes = {
            "{}".format(address_item[0]): CitationFinder.create_jan_for_address_type(address_item) for address_item in
            address_list_depth1
            }

        sham_regex = u"(?P<a0>{})".format(u"שם")

        address_regex_dict = OrderedDict()
        for addressName, jan in jagged_array_nodes.items():
            address_regex_dict["_".join(["Sham", addressName])] = {"regex": [sham_regex, jan.address_regex(lang)],
                                                                   "jan_list": [None, jan]}
            address_regex_dict["_".join([addressName, "Sham"])] = {"regex": [jan.address_regex(lang), sham_regex],
                                                                   "jan_list": [jan, None]}

        address_list_depth2 = [
            ["Integer", "Integer"],
            ["Perek", "Mishnah"],
            ["Perek", "Halakhah"],
            ["Siman", "Seif"],
            ["Volume", "Integer"],
            ["Volume", "Siman"]

        ]
        lengths = [0, 0]
        sectionNames = ['', '']

        for address_item in address_list_depth2:
            jan1 = jagged_array_nodes[address_item[0]]
            jan2 = jagged_array_nodes[address_item[1]]
            address_regex_dict["_".join(address_item)] = {"regex": [jan1.address_regex(lang), jan2.address_regex(lang)],
                                                          "jan_list": [jan1, jan2]}

        return address_regex_dict

    @staticmethod
    def create_or_address_regexes(lang):
        address_regex_dict = CitationFinder.get_address_regex_dict(lang)

        def regList2Regex(regList, isDepth2):
            #edit regList[1] to make the group name correct
            regList[1] = regList[1].replace(u"(?P<a0>", u"(?P<a1>")
            if isDepth2:
                tempReg = u"{}{}{}".format(regList[0], CitationFinder.AFTER_TITLE_DELIMETER_RE, regList[1])
            else:
                tempReg = u"{}({}{})?".format(regList[0], CitationFinder.AFTER_TITLE_DELIMETER_RE, regList[1])
            return tempReg

        depth2regex = u'|'.join([u'(?P<{}>{})'.format(groupName, regList2Regex(groupRegDict['regex'], True)) for groupName, groupRegDict in address_regex_dict.items()])
        depth1regex = u'|'.join([u'(?P<{}>{})'.format(groupName, regList2Regex(groupRegDict['regex'], False)) for groupName, groupRegDict in address_regex_dict.items()])
        return u"(?:{}|{})".format(depth2regex, depth1regex)

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
    def parse_sham_match(sham_match, lang, node):
        """
        TODO - convert the title that was found to a standard title string

        :param sham_match:
        :param lang:
        :return:
        """
        gs = sham_match.groupdict()
        sections = []
        for i in range(node.depth):
            gname = u"a{}".format(i)
            currSectionStr = gs.get(gname)
            if currSectionStr == u"שם":
                sections.append(None)
                continue
            elif currSectionStr is None:
                break # we haven't found anything beyond this point

            addressType = node._addressTypes[i]
            sections.append(addressType.toNumber(lang, gs.get(gname)))

        title = node.full_title("en")
        return [title, sections]

    @staticmethod
    def get_sham_ref_with_node(st, node, lang='he'):
        """
        used when you know the node that a sham ref belongs to in order to parse the ref according to the address types
        of that node
        :param st: string to search for sham ref
        :param node: node that we believe this sham ref belongs to
        :param lang:
        :return:
        """
        title_sham = u'שם'
        title_reg = CitationFinder.get_ultimate_title_regex(title_sham, node, lang, compiled=True)
        if node.full_title() in [u'I Samuel', u'II Samuel', u'I Kings', u'II Kings', u'I Chronicles', u'II Chronicles']:
            volume = re.search(u'שם (א|ב)\s', st)
            m = re.search(title_reg, st)
            if volume:
                st1 = re.sub(u'(א|ב)\s', u'', st, count=1, pos=m.start())
                m1 = re.search(title_reg, st1)
                if m1 and m1.groupdict()['a0'] and m1.groupdict()['a1']:
                    node = CitationFinder.node_volumes(node, volume.group(1))
                    return CitationFinder.parse_sham_match(m1, lang, node)
            return CitationFinder.parse_sham_match(m, lang, node)  # there should only be one match
        else:
            title_reg = CitationFinder.get_ultimate_title_regex(title_sham, node, lang, compiled=True)
            m = re.search(title_reg, st)
            if m:
                return CitationFinder.parse_sham_match(m, lang, node)
        raise InputError

    @staticmethod
    def get_potential_refs(st, lang='he'):
        REF_SCOPE = 15
        title_sham = u'שם'
        non_ref_titles = [u'לעיל', u'להלן', u'דף']
        ignore_titles = [u'משנה', u'ירושלמי', u'תוספתא', u'רש"י'] # see Ramban on Genesis 40:16:1
        # titles = list(reversed(library.get_titles_in_string(st, lang)))
        titles = library.get_titles_in_string(st, lang)
        titles.insert(0, title_sham)
        unique_titles = OrderedDict(zip(titles, range(len(titles))))
        refs = []
        sham_refs = []
        non_refs = []


        title_node_dict = {}
        for title in unique_titles.keys():
            node = library.get_schema_node(title, lang)
            if not isinstance(node, JaggedArrayNode):
                node = None
            title_node_dict[title] = node

        full_crazy_ultimate_title_reg = CitationFinder.get_ultimate_title_regex(unique_titles.keys(), title_node_dict, lang, compiled=True)
        ref_span_set = set()
        for m in re.finditer(full_crazy_ultimate_title_reg, st):
            ref_span_set = ref_span_set.union(range(m.start(), m.end()))
            title = m.groupdict().get('Title')
            node = title_node_dict[title]
            is_sham = title == title_sham
            if not is_sham:
                if node is None:
                    # this is a bad ref
                    non_refs += [(m, m.span(), CitationFinder.NON_REF_INT)]
                else:
                    try:
                        refs += [(library._get_ref_from_match(m, node, lang), m.span(), CitationFinder.REF_INT)]
                    except InputError:
                        # check if this ref failed because it has a Sham in it
                        hasSham = False
                        for i in range(3):
                            gname = u"a{}".format(i)
                            try:
                                if m.group(gname) == title_sham:
                                    hasSham = True
                                    break
                            except IndexError:
                                break

                        if hasSham:
                            sham_refs += [(CitationFinder.parse_sham_match(m, lang, node), m.span(), CitationFinder.SHAM_INT)]
                        else:  # failed for some unknown reason
                            non_refs += [(m, m.span(), CitationFinder.NON_REF_INT)]
            else:
                sham_refs += [(m.group(), m.span(), CitationFinder.SHAM_INT)]

        for title in non_ref_titles:
            node = None
            title_reg = CitationFinder.get_ultimate_title_regex(title, node, lang, compiled=True)
            for m in re.finditer(title_reg, st):
                if set(range(m.start(), m.end())).intersection(ref_span_set):
                    continue
                non_refs += [(m, m.span(), CitationFinder.NON_REF_INT)]
        all_refs = refs + non_refs + sham_refs
        # todo: instead of these lines, learn to differentiate by category (u'משנה', u'בבלי', u'ירושלמי', u'תוספתא')
        for title in ignore_titles:
            for ref in all_refs:
                pre_titles_regex = u'{}'.format(title)
                m = re.search(pre_titles_regex, st, endpos=ref[1][1])
                if m and set(range(m.start(), m.end() + REF_SCOPE)).intersection(ref_span_set):
                    all_refs.remove(ref)
                    all_refs.append((ref[0], ref[1], 3))


        # all_refs = refs + non_refs + sham_refs
        all_refs.sort(key=lambda x: x[1][0])

        return all_refs

    @staticmethod
    def node_volumes(node, volume):
        book = re.split('\s', node.full_title())
        book = book[1]
        if volume == u'א':
            title = u'I ' + book
            return library.get_schema_node(title)
        return library.get_schema_node(u'II ' + book)

class IndexIbidFinder(object):

    def __init__(self, index, assert_simple = True):
        '''
        this searches through `index` and finds all references. resolves all ibid refs
        :param index: Index
        '''
        self._index = index
        self._assert_simple = assert_simple
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

    def find_in_segment(self, st, lang='he', citing_only=False, replace=True):
        #todo: implemant replace = True
        """
        Returns a list of Ref objects derived from string

        :param string st: the input string
        :param lang: "he" note: "en" is not yet supported in ibid
        :param citing_only: boolean whether to use only records explicitly marked as being referenced in text.
        :return: list of :class:`Ref` objects, list of locations and list of ref types (either REF or SHAM, defined in CitationFinder)
        """
        refs = []
        locations = []
        types = []
        failed_refs = []
        # failed_non_refs = []
        failed_shams = []
        assert lang == 'he'
        # todo: support english

        st = strip_nikkud(st)
        all_refs = self._citationFinder.get_potential_refs(st, lang)
        for item, location, type in all_refs:
            if type == CitationFinder.REF_INT:
                try:
                    refs += [self._tr.resolve(item.index_node.full_title(), item.sections)]
                    locations += [location]
                    types += [type]
                    #refs += [(self._tr.resolve(item.index_node.full_title(), item.sections), 'ref')]
                except (IbidRefException, IbidKeyNotFoundException) as e:
                    failed_refs += [item.normal()]
            elif type == CitationFinder.NON_REF_INT or type == CitationFinder.IGNORE_INT:
                # failed_non_refs += [item.group()]
                self._tr.ignore_book_name_keys()
            elif type == CitationFinder.SHAM_INT:
                try:
                    if isinstance(item, unicode):
                        refs += [self._tr.resolve(None, match_str=item)]
                        locations += [location]
                        types += [type]
                        #refs += [(self._tr.resolve(None, match_str=item), 'sham')]
                    else:
                        refs += [self._tr.resolve(item[0], sections=item[1])]
                        locations += [location]
                        types += [type]
                        #refs += [(self._tr.resolve(item[0], sections=item[1]), 'sham')]
                except (IbidRefException, IbidKeyNotFoundException, InputError) as e:
                    failed_shams += [item]

        return refs, locations, types  # , failed_refs, failed_non_refs, failed_shams

    def find_in_index(self, lang='he', citing_only=False, replace=True):
        """
        Returns an OrderedDict. keys: segments. values: dict {'refs': [Refs obj found in this seg], 'locations': [], 'types': []}
        """
        seg_refs = self._index.all_segment_refs()
        out = OrderedDict()

        prev_node = None
        for i, r in enumerate(seg_refs):

            if prev_node is None:
                prev_node = r.index_node
            elif prev_node != r.index_node:
                prev_node = r.index_node
                self.reset_tracker()

            print r, i, len(seg_refs)
            st = r.text(lang=lang).text
            refs, locations, types = self.find_in_segment(st, lang, citing_only, replace)
            out[r.normal()] = {
                'refs': refs,
                'locations': locations,
                'types': types
            }
        return out


    def reset_tracker(self):
        self._tr = BookIbidTracker(assert_simple=self._assert_simple)


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
        self._last_cit = [oref.book,tuple(oref.sections)]
        # register this reference according to all possible future ways it could be referenced

    def resolve(self, index_name, sections=None, match_str=None):
        """
        note: if index_name is None match_str must be not None
        :param index_name: index name or "None" if it is a sham title citation
        :param list sections: If any entry in this list is "None", then we treat that as a "שם" or "ibid", resolve it, and return a refrence
        :param unicode match_str: optional match string. if this is provided, sections are ignored. index_name is assumed to be
        :return: Ref
        """
        #todo: assert if table is empty.
        #todo: raise an error if can't find this sham constilation in table
        title = None
        is_index_sham = index_name is None
        if index_name is None:
            index_name = self._last_cit[0]
            if index_name is not None:
                if match_str is not None:
                    # if index_name in [u'I Samuel', u'II Samuel']: #to disambiguate books that have 2 volumes.
                    #     re.search('', match_str)
                    node = library.get_schema_node(index_name)  # assert JaggedArrayNode?
                    title, sections = CitationFinder.get_sham_ref_with_node(match_str, node, lang='he')
            else:
                raise IbidKeyNotFoundException("couldn't find this key")

        if sections is not None:
            last_depth = self.get_last_depth(index_name, sections)
            if is_index_sham or len(sections) == 0 or not sections[0]: # tzmod to beginning
                sections = tuple([None] * (max(len(sections), last_depth) - len(sections)) + list(sections))  # choosing the depth of the ref to resolve
            elif len(sections) > 0 and not sections[-1]:
                sections = tuple(list(sections) + [None] * (
                    max(len(sections), last_depth) - len(
                        sections)))
        """if False and not index_name and sections == [None, None]:  # it says only Sham (all were None)
            try:
                resolvedRef = self._table[(None,(None, None))]
                # notice that self._last_cit doesn't chnge so no need to reasign it
            except KeyError:
                raise IbidKeyNotFoundException("Ibid table is empty. Can't retrieve book name")
        else:"""

        # recognize what kind of key we are looking for
        key = []
        found_sham = False
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
            if title and title != index_name:
                index_name = title
            resolvedRef = Ref(u'{}.{}'.format(index_name, '.'.join(section_str_list)))
        except:
            raise IbidRefException(u"problem with the Ref iteslf. {}.{}".format(index_name, '.'.join(str(new_sections))))
            # print 'error, problem with the Ref iteslf. ', u'{}.{}'.format(index_name, '.'.join(str(new_sections)))
            # return "error, problem with the Ref iteslf", index_name, tuple(key)

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
        try:
            del self._table[(None, (None, None))]
        except KeyError:
            pass
        self._last_cit = [None, None]  # reset last citation seen

    def get_last_depth(self,index_name, sections):
        last_depth = len(sections)
        for k, v in reversed(self._table.items()):
            if k[0] == index_name:
                last_depth = len(v.sections)
                break
        return last_depth

    def use_type_get_index(self, st):
        address_regex = CitationFinder.get_ultimate_title_regex(title=u"שם", node=None, lang='he')
        # address_regex = CitationFinder.create_or_address_regexes(lang='he')
        m = re.search(address_regex, st)
        for k, v in m.groupdict().items():
            if v and not re.search("Title|a0|a1", k):
                address_type = k
        return address_type


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