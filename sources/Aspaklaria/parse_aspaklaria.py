#encoding=utf-8

import django
django.setup()

# import subprocess
import random
import argparse
from tqdm import *
from sefaria.model import *
from sefaria.system import exceptions
from bs4 import BeautifulSoup, element
from sources.functions import *
import string
import traceback
import unicodecsv as csv
# import json
import pickle
from data_utilities.util import getGematria, numToHeb
import codecs
from aspaklaria_connect import client
from data_utilities.ibid import *
# import pstats
# import cProfile
# from index_title_catcher import *  # get_index_via_titles
from sefaria.system.database import db
# import matplotlib.pyplot as plt  # %matplotlib
import itertools
from sources.EinMishpat.ein_parser import is_hebrew_number, hebrew_number_regex
from research.knowledge_graph.sefer_haagada.main import disambiguate_ref_list
from sefaria.utils.hebrew import is_hebrew
from data_utilities.dibur_hamatchil_matcher import match_text
# from aspaklaria_settings import ASPAKLARIA_HTML_FILES

db_aspaklaria = client.aspaklaria

# in order to print Hebrew on K8S
import sys
reload(sys)
sys.setdefaultencoding('utf8')

class Parser(object):

    def __init__(self):
        self.term_dict, self.he_term_str = he_term_mapping()
        self.missing_authors = set()
        self.pp_table = Parser.perek_parasha_table()

    @staticmethod
    def perek_parasha_table(): #chumash, perek, pasuk=''):
        # create a dictionary of parashot names to refs in them
        def refs2parashah(parashah_name, t):
            """

            :param parashah_name: parashah_name (ex. noah)
            :param t: a copy of the table created already so if there is a perek devided btween two parashot it will get a list of the two
            :return: new_table: a new dict. keys: Refs of all the Pesukim and Perakim contained (also partially) in the Parashah
            """
            new_table = dict()
            prev_perk_key = Ref('שמואל א')  # this is just for a default Ref that is a Ref obj but not in Torah
            # parashah_name = 'פרשת {}'.format(parashah_name)
            for ref in table[parashah_name].all_segment_refs():
                new_table[ref] = parashah_name
                perek_key = Ref('{} {}'.format(ref.index.title, ref.sections[0]))
                if perek_key.normal() != prev_perk_key.normal():
                    prev_perk_key = perek_key
                    if perek_key not in t.keys():
                        new_table[perek_key] = parashah_name
                    elif t[perek_key] != parashah_name:
                        new_table[perek_key]=[t[perek_key]]+[parashah_name]
            return new_table
        table = dict()
        for book in library.get_indexes_in_category('Torah'):
            ind = library.get_index(book)
            struct = ind.get_alt_structure('Parasha')
            parashot = struct.all_children()
            parashot = ['פרשת {}'.format(x.primary_title('he')) for x in parashot]
            for x in parashot[1::]:
                # parashah_name = x.primary_title('he')
                # parashah_name = 'פרשת {}'.format(parashah_name)
                parashah_name = x
                table[parashah_name] = Ref(parashah_name)  # .all_segment_refs()
                extend_table = refs2parashah(parashah_name, table.copy())
                # table.update(refs2parashah(parashah_name, table))
                table.update(extend_table)
            fposp = table[parashot[1]]  # [0]  # first_pasuk_of_secoend_parashah
            table[parashot[0]] = Ref('{} 1:1-{}:{}'.format(book, fposp.sections[0], fposp.sections[1])) # .all_segment_refs()
            extend_table = refs2parashah(parashot[0], table.copy())
            table.update(extend_table)
            # table.update(refs2parashah(parashot[0].primary_title('he'), table))
        return table

def he_term_mapping():
    all_terms = TermSet({})
    # all_terms += library.get_text_categories()
    he_titles = [[(term.get_primary_title(), x['text']) for x in term.title_group.titles if x['lang'] == 'he'] for term
                 in all_terms]
    en, he = zip(*reduce(lambda a,b: a+b, he_titles))
    he = map(lambda x: re.sub('"', "", x), he)
    he_key_term_dict = dict(zip(he, en))
    he_terms_str = '|'.join(he)
    he_terms_str = re.sub(re.escape(string.punctuation), '', he_terms_str)
    return he_key_term_dict, he_terms_str


def bs_read(fileName):
    with codecs.open(fileName, encoding='utf-8') as f:
        file_content = f.read()

    content = BeautifulSoup(file_content, "lxml")
    if not content.findAll('h1'):
        return
    headWord = clean_txt(content.findAll('h1')[0].text)
    t = Topic(headWord)
    b = AuthorCit('before')
    wait = True
    for tag in content.findAll():
        if tag.name != 'h1' and wait:
            wait = True
            continue
        wait = False
        if tag.name == 'h2':
            t.all_a_citations.append(b)
            b = AuthorCit(clean_txt(tag.text))
        else:
            txt = clean_txt(tag.text)
            b.cit_list.append(txt)
    t.all_a_citations.append(b)

    tanakh = []
    if t.all_a_citations[0].author == 'before':
        for ic, c in enumerate(t.all_a_citations[0].cit_list):
            if c == t.headWord:
                pass
            elif re.search('ראה', c) and re.search(':', c):
                txt_split = c.split(':')
                see = re.sub("[\(\)]", '', txt_split[1]).split(',')
                t.see = [re.sub(re.escape(string.punctuation), '', s) for s in see]
                # t.see = [re.sub(, '', s) for s in see]
            else:
                tanakh.append(c)
    t.all_a_citations.pop(0)
    if tanakh and t.all_a_citations:
        t.all_a_citations[0] = AuthorCit('תנך')
        t.all_a_citations[0].cit_list = tanakh

    return t


def transliterator(hestr):
    trans_table = {'א': 'a', 'ב': 'b', 'ג': 'g', 'ד': 'd', 'ה': 'h', 'ו': 'v', 'ז': 'z', 'ח': 'ch', 'ט': 't', 'י': 'y', 'כ': 'kh', 'ל': 'l', 'מ': 'm', 'נ': 'n', 'ס': 's', 'ע': "a'a", 'פ': 'p', 'צ': 'tz', 'ק': 'k', 'ר': 'r', 'ש': 'sh', 'ת': 't', 'ן': 'n', 'ף': 'f', 'ך': 'kh', 'ם': 'm', 'ץ': 'tz'
                   }
    enstr = ''
    for l in hestr:
        enstr+=trans_table[l] if l in trans_table.keys() else l
    return enstr


def clean_txt(text):
    cleaned = ' '.join(text.split())
    if cleaned and cleaned[-1] == ':':
        cleaned = cleaned[:-1]
    return cleaned


def parse_refs(topic):
    if topic.all_a_citations:
        for citbook in topic.all_a_citations:
            citbook.create_sources()
            pass


class AuthorCit(object):

    def __init__(self, author):
        self.author = author
        self.cit_list = []
        self.sources = []

    def create_sources(self):
        for i, cit in enumerate(self.cit_list):
            s = Source(cit, self.author)
            self.sources.append(s)


class Topic(object):

    def __init__(self, headWord):
        self.headWord = headWord
        self.all_a_citations = [] # list of BookCits
        self.see = None
        self.altTitles = None

    def parse_shams(self):
        cnt=0
        BT = BookIbidTracker()
        topic_table = []
        tanakh_books =library.get_indexes_in_category('Tanakh')
        comp_tanakh_comm = re.compile('(?P<commentator>^.*?(?P<complex>\s?על|,)\s+).*$')
        for i, cit in enumerate(self.all_a_citations):
            for source in cit.sources:
                ref_d = self.ref_dict(source)
                if ref_d:
                    topic_table.append(self.ref_dict(source))
                    BT.registerRef(source.ref)
                if source.ref and 'Tanakh'in source.ref.index.categories and source.ref.index.title not in tanakh_books:
                    match = re.search(comp_tanakh_comm, source.ref.he_normal())
                    tanakh_ref = Ref(re.sub(match.group('commentator'), '', source.ref.he_normal()))
                    BT.registerRef(tanakh_ref)
                if source.raw_ref and source.raw_ref.is_sham:
                    # print 'Sham Ref {}'.format(source.raw_ref.rawText)
                    if topic_table[-1]['author'] == source.raw_ref.author:
                        if 'Talmud' in topic_table[-1]['index'].categories:
                            source.ref = BT.resolve(None, match_str=source.author+source.raw_ref.rawText)
                        else:
                            try:
                                source.ref = BT.resolve(topic_table[-1]['index'].title, match_str= source.author + source.raw_ref.rawText) # assuming the index is definatly the same as the last one is not neccesary. and should check if there is a source.index first?
                            except AttributeError as e:
                                # print e, source.raw_ref.rawText
                                source.ref = None
                        if source.ref:
                            # print source.ref
                            BT.registerRef(source.ref)
                    if 'Tanakh' in topic_table[-1]['index'].categories and not source.ref:
                        tanakh_book = tanakh_ref.index.title
                        # if topic_table[-1]['index'].is_complex():
                        #     tanakh_book = tanakh_ref.index.title
                        # else:
                        #     tanakh_book = topic_table[-1]['index'].base_text_titles[0]
                        # this_he_title = '{} על {}'.format(source.raw_ref.author, Ref(tanakh_book).he_normal())
                        library.get_index(tanakh_book)
                        match_str = Ref(tanakh_book).he_normal() + re.sub('שם ', '', source.raw_ref.rawText, count=1) #re.sub('(\(|\))', '', this_he_title + re.sub('שם', '', '(שם שם כג)', count=1))
                        try:
                            try_ref = BT.resolve(tanakh_book, match_str=match_str)  # sections=[topic_table[-1]['section'],topic_table[-1]['segment']])
                        except (InputError, IbidRefException) as e:
                            try:
                                try_ref = Ref(re.sub('([^\s])\(', r'\1 (', match_str))
                            except InputError:
                                try_ref = None
                        if try_ref:
                            try:
                                ind = library.get_index(cit.author)
                            except:
                                try:
                                    ind = [ind for ind in source.indexs if re.search(try_ref.book, ind.title)][0]
                                except IndexError:
                                    print("SHAMS INDEX ERROR")
                                    print("Source indexs {}".format(", ".join([ind.title for ind in source.indexs])))
                                    print("Try_ref.book {}".format(try_ref.book))
                                    traceback.print_exc()
                            ref_struct = ind.all_segment_refs()[0].he_normal()
                            match = re.search(comp_tanakh_comm, ref_struct)
                            complex = match.group('complex')
                            try:
                                source.ref = Ref(cit.author + complex + " "+ try_ref.he_normal())
                            except InputError:
                                source.ref = Ref("{} {} {}".format(ind.title, try_ref.sections[0], try_ref.sections[1]))
                            BT.registerRef(source.ref)
                            # print source.ref
                        else:
                            source.ref = None
                            cnt+=1
                            print(cnt)
                            # print '{}'.format(e)
                # if source.ref and source.raw_ref.is_sham:
                #     Source.cnt_sham -= 1
                #     Source.cnt_resolved +=1

    def ref_dict(self, source):
        d = {}
        if source.ref:
            # if source.ref.index.title in library.get_indexes_in_category('Bavli'):
            #     print 'Bavli'
            if 'addressTypes' in source.ref.index.schema.keys() and 'Talmud' in source.ref.index.schema['addressTypes']:
                d['book'] = Ref(source.ref.book).he_normal()
            d['author'] = source.author
            d['index'] = source.ref.index
            d['section'] = source.ref.sections[0]
            d['segment'] = source.ref.sections[1] if len(source.ref.sections) > 1 else None
        if d:
            return d

    def parse_refs(self):
        if self.all_a_citations:
            for citbook in self.all_a_citations:
                citbook.create_sources()
                pass

class Source(object):
    # cnt = 0
    # cnt_sham = 0
    # cnt_resolved = 0
    # cnt_not_found = 0
    global parser
    parser = Parser()  # term_dict = he_term_mapping()
    indexSet_dict = dict()
    found_term_dict = dict()

    def __init__(self, text, author):
        self.text = text
        self.author = author
        self.index = None
        self.indexs = []
        self.cat = None
        self.raw_ref = None
        self.ref = None

        self.extract_raw_ref()
        # if hasattr(self.raw_ref, 'is_sham') and not self.raw_ref.is_sham:
        self.get_ref_from_api()
        # after failing by using the api let's try without.
        if not self.ref:
            self.get_ref_clean()
        else:  # there is a ref but it might be wrong so we are using the PM.
            try:
                self.pm_match_text()
            except:
                print("pm_matcher failed")

        # if self.raw_ref:
        #     Source.cnt+=1
        #     if self.raw_ref.is_sham:
        #         Source.cnt_sham += 1
        #     elif self.ref:  # found ref (presumably a correct ref :) )
        #         Source.cnt_resolved += 1
        #         res_text = '{}, {}\n{}\n\n'.format(self.raw_ref.author, self.raw_ref.rawText, self.ref.normal())
        #         write_to_file(res_text)
        #     else:
        #         Source.cnt_not_found += 1

    def extract_raw_ref(self):
        """
        looks for the ref in the end of the text in parentheses
        :return: does not return but creates a RawRef obj if the parentheses are found
        """
        if re.search('(\([^)]*?\)$)', self.text):
            self.raw_ref = RawRef(re.search('(\([^)]*?\)$)',self.text).group(1), self.author)
        # else:
        #     pass

    def extract_cat(self, include_dependant):
        look_here = []
        # library.get_index(self.author) if library.get_index(self.author) else None # needs to go into a try catch "sefaria.system.exceptions.BookNameError"
        author = re.sub('[{}]'.format(re.escape(string.punctuation)), '', self.author)
        try:
            self.index = library.get_index(author)
            return [self.index]
        except exceptions.BookNameError as e: #sefaria.system.exceptions.
            found_term = self.extract_term()
            if found_term:
                found_term = [found_term] if not isinstance(found_term, list) else filter(lambda x: x, found_term)
                cat_terms = filter(lambda term: term in library.get_text_categories(), found_term)
                self.cat = cat_terms  # found_term
                if self.cat:
                    look_here = reduce(lambda a,b: [x for x in b for y in a if x==y], [library.get_indexes_in_category(cat, include_dependant=include_dependant, full_records=True).array() for cat in self.cat])
                    return look_here
            else:
                return look_here
            #might need to use Terms to make lookup the category in english
            # Term().load({"name": self.author})
            # filter(lambda x: x['lang'] == 'he', t.contents()['titles'])[0]['text']

    def extract_term(self):
        # text_categories = library.get_text_categories()
        found_term = []
        author = re.sub('[{}]'.format(re.escape(string.punctuation)), '', self.author)
        def try_to_find(term_string, prefixes = True):
            #check that the string is not a word that has no meaning. like ה from אור ה
            if len(term_string) <=1:
                return []
            # is a known term
            found_term  = Source.found_term_dict.get(term_string, [])
            if found_term:
                return found_term
            else:
                found_term = parser.term_dict.get(term_string, [])
                if found_term:
                    Source.found_term_dict[term_string] = found_term
                    return found_term
                # else try string of a known Term
                match = re.search("\|([^|]*{}(\s[^|]*?\||\|))".format(term_string), parser.he_term_str)
                if match:
                    found_term = parser.term_dict.get(match.group(1).replace("|", ""), [])
                    Source.found_term_dict[term_string] = found_term
                    return found_term
                elif prefixes:
                    return try_to_find(re.sub('^[משהוכלב]', '', term_string), False)
                else:
                    return []

        found = try_to_find(author)
        found_term += found if isinstance(found, list) else [found]
        if not found_term:
            for word in author.split():
                found = try_to_find(word)
                found_term += found if isinstance(found, list) else [found]

        return found_term

        # found_term = parser.term_dict.get(author, [])
        # if not found_term and re.search(author, parser.he_term_str):
        #     found_he = re.search("\|(.*?{}.*?)\|".format(author), parser.he_term_str).group(1)
        #     found_term = parser.term_dict.get(found_he, [])
        # if not found_term:
        #     found_term = parser.term_dict.get(re.sub('^[משהוכלב]', '', author), [])
        # if not found_term:
        #     for word in author.split():
        #         found = parser.term_dict.get(word.replace('"', ""), [])
        #         if found:
        #             found_term.append(found)
        #         else:
        #             found_term.append(parser.term_dict.get(re.sub('(^[משהוכלב]|")', '', word), []))
        # return found_term if isinstance(found_term, list) else [found_term]

    def extract_indx(self):
        author = re.sub('[{}]'.format(re.escape(string.punctuation)), '', self.author)
        try:
            self.index = library.get_index(author)
            if self.index.title == 'Yalkut Shimoni on Torah':
                raise exceptions.BookNameError
        except exceptions.BookNameError as e:
            term_list = self.extract_term()
            if term_list:
                # term_list = map(lambda x: unicode.lower(x), term_list)
                inds_via_term = []
                for term in term_list:
                    indexset = Source.indexSet_dict.get(term, None)
                    if indexset is None:
                        indexset = IndexSet({"title": {"$regex": ".*(?i){}.*".format(term)}}).array()
                        Source.indexSet_dict[term] = indexset
                    inds_via_term += indexset
                # for title in [x['text'] for ind in inds_from_term for x in ind.schema['titles'] if x['lang'] == 'he']:
                #     print title
                inds_via_cats = reduce(lambda a, b: a and b, [library.get_indexes_in_category(term) for term in term_list])
                if Term().load_by_title(author):
                    inds_via_collective_title = library.get_indices_by_collective_title(author)
                    inds_via_cats+=inds_via_collective_title
                if bool(inds_via_cats) != bool(inds_via_term):  # only one of the index groups was filled
                    indexs = inds_via_term if inds_via_term else inds_via_cats
                    for ind in indexs:
                        if isinstance(ind, unicode):
                            self.indexs.append(library.get_index(ind))
                        elif isinstance(ind, Index):
                            self.indexs.append(ind)
                elif bool(inds_via_cats) and bool(inds_via_term):
                    if self.author == 'תלמוד בבלי':
                        self.indexs = inds_via_cats
                    elif self.author == 'משנה תורה':
                        self.indexs = inds_via_cats
                    elif self.author == 'ירושלמי':
                        self.indexs = library.get_indexes_in_category('Yerushalmi')
                    else:
                        self.indexs = inds_via_term
                # anyway add also books by author name
                indexs_via_author_name = self.get_indexes_from_author(self.author)
                if not indexs_via_author_name and re.search('^[משהוכלב]', self.author):
                    indexs_via_author_name = self.get_indexes_from_author(self.author[1::])
                # if self.indexs:
                self.indexs.extend(indexs_via_author_name)
                # else:
                #     self.indexs = indexs_via_author_name

    def get_ref_from_api(self):

        def clean_raw(st):
            st = re.sub('[)(]', '', st) # incase we put those parantheses on before to try and catch it with get_ref_in_string
            he_parashah_array = ["בראשית", "נח", "לך לך", "וירא", "חיי שרה", "תולדות", "ויצא", "וישלח", "וישב", "מקץ", "ויגש", "ויחי", "שמות", "וארא", "בא", "בשלח", "יתרו", "משפטים", "תרומה", "תצוה", "כי תשא", "ויקהל", "פקודי", "ויקרא", "צו", "שמיני", "תזריע", "מצורע", "אחרי מות", "קדושים", "אמור", "בהר", "בחוקתי", "במדבר", "נשא", "בהעלותך", "שלח", "קרח", "חקת", "בלק", "פנחס", "מטות", "מסעי", "דברים", "ואתחנן", "עקב", "ראה", "שופטים", "כי תצא", "כי תבוא", "נצבים", "וילך", "האזינו", "וזאת הברכה"]
            for s in ["דרוש", "פרק "]: # "מאמר ", "פרק"
                st = re.sub(s, "", st)
            if self.author == "משנה תורה":
                st = "הלכות " + st
            elif self.author == "ספר החינוך":
                for s in he_parashah_array:
                    st = re.sub(s, "", st)
                    st = re.sub("מצוה", "", st)
            elif self.author == 'מורה נבוכים':
                st = re.sub("פתיחה", 'הקדמה, פתיחת הרמב"ם ', st)
            elif self.author == 'כוזרי':
                st = re.sub("מאמר ", "", st)
            return st

        if self.raw_ref:
            ref_w_author = "(" + self.author + ", " + re.sub("[)(]", "", self.raw_ref.rawText) + ")"
            refs = library.get_refs_in_string(ref_w_author)
            if refs:
                # assert len(refs) == 1
                self.ref = refs[0]
                # print self.ref
            else:  # straight forward didn't find, so might be a sham. Or might need special casing.
                if re.search("^\(\s*שם", self.raw_ref.rawText):
                    self.raw_ref.is_sham = True
                else:
                    cleaned = clean_raw(self.raw_ref.rawText)
                    fixed_ref = "(" + self.author + ", " + re.sub("[)(]", "", cleaned) + ")"
                    # print "*** try new ref, fixed_ref = {}".format(fixed_ref)
                    # put in a new "try" because sometimes it is simpler then it seams :)
                    try:
                        refs = [Ref(re.sub("[()]", "",fixed_ref))]
                    except (exceptions.InputError, IndexError):
                        refs = library.get_refs_in_string(fixed_ref)

                    if refs:
                        self.ref = refs[0]
                        # print self.ref
                    else:
                        self.opt_titles = self.get_titles_in_string(re.sub('[)(,]', '', ref_w_author))
            # print self.raw_ref.rawText, '\n', ref_w_author
        else: # there isn't a self.ref means we couldn't find parenthises at the end, probably a continuation of the prev source/ cit (in cit_list)
            pass
        self.extract_indx()
        self.get_ref_step2()

    def get_titles_in_string(self, text):
        titles = library.get_titles_in_string(text)
        # if self.author == 'משנה תורה':
        #     match_text(text.split(), [])
        return titles

    def get_look_here_titles(self, look_here):
        """

        :param look_here:
        :return:
        """
        look_here_titles_he = [index.all_titles('he') for index in look_here if isinstance(index, Index)] #[index.all_titles('he') for index in look_here if isinstance(index, Index)] if all(isinstance(look_here_i, Index) for look_here_i in look_here) else look_here
        look_here_titles_he = list(itertools.chain(*look_here_titles_he))
        look_here_titles_en = [index.get_title('en') for index in look_here] if all(isinstance(look_here_i, Index) for look_here_i in look_here) else look_here
        look_here_titles = look_here_titles_en+look_here_titles_he
        shared_word_in_titles = []
        try:
            shared_word_in_titles = '({})'.format('|'.join(list(set.intersection(*[set(x.split()) for x in look_here_titles]))))
        except AttributeError:
            if any(type(book) != unicode for book in look_here_titles):
                look_here_titles = [book for book in look_here_titles if isinstance(book, unicode)]
                shared_word_in_titles = '({})'.format(
                    '|'.join(list(set.intersection(*[set(x.split()) for x in look_here_titles]))))

        if re.sub("[()]", "", shared_word_in_titles):
            look_here_titles = map(lambda x: (x, re.sub(shared_word_in_titles, '', x).strip()), look_here_titles)
        else:
            look_here_titles = map(lambda x: tuple([x]) if isinstance(x, unicode) else tuple(x), look_here_titles)
        return look_here_titles

        # except AttributeError:
        #     pass  # todo: check what this is about
        #     return []

    def get_ref_step2(self):
        """
        after get_ref_from_api() we want to call this function.
        It should discard/change wrongly caught refs, like ones caught bavli instead of Yerushalmi or mishanah instead of Tosefta.
        :return: doesn't return but changes self.ref
        """
        wrong_ref = self.check_for_wrong_ref() or self.wrong_ref_pp()

        # if self.ref:  # probabaly should be calculated once
        #     if self.author != "תנך"  and self.ref.index.title in library.get_indexes_in_category('Tanakh'):
        #         include_dependant = True
        #         wrong_ref = True
        #     elif self.author != "תלמוד בבלי"  and self.ref.index.title in library.get_indexes_in_category('Bavli'):
        #         include_dependant = False
        #         wrong_ref = True

        if self.ref:
            if wrong_ref:  # or (self.raw_ref and not self.ref and not self.raw_ref.is_sham):
                new_ref = None
                include_dependant = True
                if self.author == "משנה תורה":
                    include_dependant = False
                look_here = self.get_index_options(include_dependant=include_dependant)
                if look_here:
                    new_ref = self.get_new_ref_w_look_here(look_here)
                else:  # couldn't find a indexs for this author
                    parser.missing_authors.add(self.author)
                # if look_here and (self.index or wrong_ref):
                #     # than try to get the true title from the cat from look_here
                #     look_here_shared_title_word = '({})'.format(
                #         '|'.join(list(set.intersection(*[set(x.title.split()) for x in look_here]))))
                #     alt_ref_titles = map(lambda x: x['text'], self.ref.index.schema['titles'])
                #     found_index = [ind for ind in look_here for tanakh_book in alt_ref_titles if
                #                    tanakh_book in re.sub(look_here_shared_title_word, '', ind.title).strip()]
                #     if found_index:
                #         if len(set(found_index)) > 1:  # assert len(found_index) == 0
                #             print "more than one index option"  # todo: problem with אלשיך דברים and with books I, II
                #             print found_index[0].title, found_index[-1].title
                #         self.index = found_index[0]
                #         try:
                #             new_ref = Ref('{} {}'.format(self.index.title, re.sub(self.ref.index.title, '', self.ref.normal()).strip()))
                #             print "deleting wrong: {} found new Index: {} new ref: {}".format(self.ref, self.index, new_ref)
                #             self.ref = new_ref
                #         except exceptions.InputError as e:
                #             print "inputError for this string {}, extracted from this rawref {}".format('{} {}'.format(self.index.title, re.sub(self.ref.index.title, '', self.ref.normal()).strip()), self.raw_ref)
                # tanakh is wrong but can't find the index ex: רש"ר הירש
                if self.index and not self.ref:
                    ind = self.index
                    #todo: look into the original catching see why it is not catching kalla. also see how to copy the intresting parts to here
                    self.raw_ref.book = ind.title
                    split_raw_text = re.sub('[\(\)]', '', self.raw_ref.rawText).split()
                    self.raw_ref.section_level = split_raw_text

                    pass
                if not self.index and not new_ref:# todo: it was an or why? turend into an and lets see if/what it breaks.
                    self.change_look_here(author = 'תרגום יונתן', new_author = 'תרגום', category = 'Writings')
                    if not self.index:
                        # print "deleting wrong: {} couldn't find an index".format(self.ref)
                        self.ref = None
            else:  # not wrong_ref. and found a ref, might just be a correct ref. todo: how to test it is correct?
                pass
            # try to get the ref from the index via the titles found (without an index - ex. ילקוט שמעוני, דניאל תתרסה)
            # it is look at nodes names when we are not testing giving wrong Ref?
        elif hasattr(self, "opt_titles") and self.opt_titles:
            indexs = self.extract_cat(include_dependant=True)
            if indexs:
                indexs.extend(self.indexs)
                # if self.author == 'משנה תורה':
                #     self.reduce_indexs_with_matcher()
            node_name = ''
            for opt_title in self.opt_titles:
                try:
                    new_index = library.get_index(opt_title)
                    if not indexs or new_index.is_complex():  # or library.get_title_node_dict('he')[opt_title] != library.get_title_node_dict('en')[new_index.title]
                        self.index = new_index
                        possible_nodes = new_index.all_titles('he')
                        node_guess = intersect_list_string(possible_nodes, self.raw_ref.rawText)
                        if not self.ref and node_guess:
                            try:
                                r = Ref(node_guess)
                                if not self.check_for_wrong_ref(r):
                                    self.ref = r
                            except InputError:
                                self.ref = ''
                                print('the node guess is not a Ref')
                        elif node_guess:
                            # then we should check witch is the better option
                            # maybe using the length of matching words in regards to the titles
                            ref_opt1 = self.ref.he_normal()
                            ref_opt2 = node_guess
                            sets = strings2sets(ref_opt1,ref_opt2, self.raw_ref.rawText)
                            if abs(len(set[1])-len(set[2])) < abs(len(set[0])-len(set[2])):
                                self.ref = Ref(node_guess)
                    elif new_index not in indexs:
                        intersected = self.intersected_indexes(new_index, indexs)
                        if intersected:
                            node_name = Ref(intersected[0].title).he_normal()  # TODO: find cases with list longer than one and figure it out.
                            self.index = intersected
                except (exceptions.BookNameError, TypeError):
                    # print "excepted {}".format(opt_title)
                    pass
                if node_name:
                    try:
                        new_string = re.sub(opt_title, node_name, self.text)
                        new_string = re.sub('[()]', '', new_string)  # because we are going to use Ref rather than library.get_refs_in_string() that needes the parentheses
                        self.ref = Ref(new_string)
                    except exceptions.InputError:
                        try:
                            self.ref = Ref(','.join(new_string.split(',')[0:2]))
                        except exceptions.InputError:
                            # try again without the name of the node, but with the index recognizing that the node is in that index
                            try:
                                new_string = re.sub(opt_title, "", new_string)
                                self.ref = Ref(new_string)
                            except exceptions.InputError:
                                    print("we tried")
                                    self.ref = None
        elif (self.indexs or self.index) and self.raw_ref and not self.raw_ref.is_sham:
            self.ref_opt = []
            if not self.indexs:
                self.indexs = [self.index]
            for ind in self.indexs:
                new_index = ind if isinstance(ind, Index) else library.get_index(ind)
                self.index = new_index
                possible_nodes = new_index.all_titles('he')
                ns_titles_and_refs = []
                if hasattr(new_index, 'alt_structs'):
                    ns=[]
                    ns_titles_and_refs = dict()
                    [ns.extend(alt['nodes']) for alt in new_index.alt_structs.values()]
                    if any('titles' in nsone.keys() for nsone in ns): # 'titles' in ns[0].keys():
                        ns_titles_and_refs = dict([(x['titles'][1]['text'], x['wholeRef']) for x
                             in ns if ('wholeRef' in x.keys() and 'titles' in x.keys())])
                    if any('sharedTitle' in nsone.keys() for nsone in ns): # todo: old code: 'sharedTitle' in ns[0].keys():
                        ns_titles_and_refs.update(dict([(Term().load_by_title(x['sharedTitle']).get_primary_title('he')
, x['wholeRef']) for x in ns if 'sharedTitle' in x.keys()]))
                    possible_nodes.extend(ns_titles_and_refs.keys())
                node_guess = intersect_list_string(possible_nodes, self.raw_ref.rawText)
                if not self.ref and node_guess:
                    try:
                        if ns_titles_and_refs:
                            try:
                                r = Ref(ns_titles_and_refs.get(node_guess, ''))
                                r.normal()
                            except (InputError, AttributeError):
                                r = Ref(node_guess)
                        else:
                            r = Ref(node_guess)
                        if not self.check_for_wrong_ref(r):
                            self.ref_opt.append(r)
                    except InputError:
                        # self.ref_opt.append('')
                        print('the node guess is not a Ref')
            if self.ref_opt:
                if len(self.ref_opt) == 1:
                    r = self.ref_opt[0]
                    #self.ref = r
                    if not r.sections:
                        sections = ' '.join([sect for sect in re.sub('[(,)]', ' ', self.raw_ref.rawText).split() if is_hebrew_number(sect)]) #todo: maybe bad huristic and should wait to do this on the PM level?
                        if sections:
                            try:
                                self.ref = Ref(r.he_normal() + ' ' + sections)
                            except InputError as e:
                                pass
                            return
                    self.ref = r
                else:  # more than one option, we need to choose the better one.
                    he_options = [r.he_normal().replace("ן", "ם") for r in self.ref_opt]
                    try:
                        better = intersect_list_string(he_options, re.sub('[()]', '', self.raw_ref.rawText), ref_opt = True)
                        r = Ref(better)
                        if not r.sections:
                            sections = ' '.join(
                                [sect for sect in re.sub('[(,)]', ' ', self.raw_ref.rawText).split() if
                                 is_hebrew_number(
                                     sect)])  # todo: maybe bad huristic and should wait to do this on the PM level?
                            if sections:
                                try:
                                    self.ref = Ref(r.he_normal() + ' ' + sections)
                                except (AttributeError, InputError):
                                    pass
                                return
                        self.ref = r
                    except InputError:
                        print("more than one option to guess from")


                # elif node_guess:
                #     # then we should check witch is the better option
                #     # maybe using the length of matching words in regards to the titles
                #     ref_opt1 = self.ref.he_normal()
                #     ref_opt2 = node_guess
                #     # sets = strings2sets(ref_opt1, ref_opt2, self.raw_ref.rawText)
                #     if abs(len(set[1]) - len(set[2])) < abs(len(set[0]) - len(set[2])):
                #         self.ref = Ref(node_guess)

    def check_for_wrong_ref(self, r=None):
        wrong_ref = False
        if not r:
            if self.ref:
                r = self.ref
            else:
                return False  # witch is the same as wrong_ref at this point
        if self.author != "תנך"  and r.index.title in library.get_indexes_in_category('Tanakh'):
            wrong_ref = True
        elif self.author != "תלמוד בבלי"  and r.index.title in library.get_indexes_in_category('Bavli'):
            wrong_ref = True
        return wrong_ref

    def wrong_ref_pp(self):
        """
        check for wrong ref parashah perk (pp)
        :return:
        """
        if self.author == 'משך חכמה':
            if self.raw_ref:
                rs = library.get_refs_in_string(self.raw_ref.rawText)
                if not rs:
                    return False  #  (משך חכמה, שם יח ד)
                parashah_str = convert_perk_parasha(rs[0], parser.pp_table)
                parashah_str = re.sub("פרשת ", "", parashah_str)
                self.raw_ref.rawText_old = self.raw_ref.rawText[:]
                self.raw_ref.rawText = parashah_str #Ref(parashah_str).he_normal()
                self.ref = None
                return True  # go thorough the wrongRef path with the new rawRef
        return False

    def set_reduce_indexes(self, reduced_indexes):
        reduced_indexes = filter(lambda x: type(x)==unicode, reduced_indexes)
        return len(reduced_indexes) == 1 or (
                reduced_indexes and all(
            [x == reduced_indexes[-1] or library.get_index(x) == library.get_index(reduced_indexes[-1]) for x in
             reduced_indexes]))

    def get_new_ref_w_look_here(self, look_here, ):
        """

        :param look_here:
        :return:
        """
        new_ref = None
        alt_ref_titles = map(lambda x: x['text'], self.ref.index.schema['titles'])
        look_here_titles = self.get_look_here_titles(look_here)
        # if any(type(book) != Index for book in look_here):
        #     print self.raw_ref
        #     look_here = [book for book in look_here if isinstance(book, Index)]
        look_here_titles_nodes = self.get_look_here_nodes(look_here)
        reduced_indexes = self.reduce_indexes(look_here_titles=look_here_titles,
                                              look_here_titles_nodes=look_here_titles_nodes,
                                              alt_ref_titles=alt_ref_titles)
        if self.set_reduce_indexes(reduced_indexes):
            reduced_indexes = set(reduced_indexes)
            if filter(lambda x: type(x) == tuple, reduced_indexes):
                self.index = filter(lambda x: type(x) == tuple, reduced_indexes)[0]
            else:
                self.index = library.get_index(filter(lambda x: type(x) == unicode, list(reduced_indexes))[0]).title
            try:
                if isinstance(self.index, tuple):
                    index_node_name = self.index[1].title + ', ' + self.index[0]
                    index_node_name = Ref(index_node_name).normal()
                else:
                    index_node_name = self.index
                sections = self.get_sections_from_ref()
                new_refs = library.get_refs_in_string('({} {})'.format(Ref(index_node_name).he_normal(), sections))
                if new_refs:
                    new_ref = new_refs[0]
                else:
                    new_ref = Ref('{} {}'.format(index_node_name, sections)) #re.sub(self.ref.index.title, '', self.ref.normal()).strip()))
                # print "deleting wrong: {} found new Index: {} new ref: {}".format(self.ref, self.index, new_ref)
                self.ref = new_ref
            except exceptions.InputError as e:
                new_ref = None  # so not to have new_ref that failed scrowing with stuff
                # print "inputError for this string {}, extracted from this rawref {}".format(
                #     '{} {}'.format(self.index, re.sub(self.ref.index.title, '', self.ref.normal()).strip()),
                #     self.raw_ref)
        elif not reduced_indexes:  # len(reduced_indexes) == 0
            # couldn't find the title in the books maybe it is in there nodes
            if isinstance(look_here[0], Index):
                if any(type(book) != Index for book in look_here):
                    # print self.raw_ref
                    look_here = [book for book in look_here if isinstance(book, Index)]
                look_here_nodes = reduce(lambda a, b: a + b,
                                         [ind.alt_titles_dict('he').keys() + ind.all_titles('he') for ind in
                                          look_here])  # todo: note: this was ind.alt_titles_dict('he').items() a few lines down the code called node_name = node[0]
                look_here_nodes = filter(lambda x: any(re.search(t, x[0]) or re.search(t, x) for t in alt_ref_titles),
                                         look_here_nodes)
                if len(look_here_nodes) == 1:
                    node = look_here_nodes[0]  # todo: why take the first one?? or move it to be taking the only one
                    node_name = node  # [0]
                    depth = re.search('.*?(\d+):?(\d+)?.*?', self.ref.normal()).groups()
                    for d in depth:
                        if not d:
                            print("break")
                            break
                        try:
                            new_ref = Ref('{} {}'.format(node_name, numToHeb(d)))
                            # print "deleting wrong: {} found new Index: {} new ref: {}".format(self.ref, self.index,
                            #                                                                    new_ref)
                            break
                        except (exceptions.InputError, IndexError) as e:
                            # print "inputError for this string {}, extracted from this rawref {}".format(
                            #     '{} {}'.format(node_name, numToHeb(d)), self.raw_ref.rawText)
                            if "ילקוט שמעוני" in node_name:
                                try:
                                    new_ref = Ref('{}, {}'.format(ind.title, d))
                                except exceptions.InputError:
                                    print("inputError for this string")
                                    # print "inputError for this string {}, extracted from this rawref {}".format(
                                    #     '{} {}'.format(node_name, numToHeb(d)), self.raw_ref.rawText)
                        except IndexError as e:
                            # print 'IndexError {} not sure why...'.format(e)
                            pass
                    self.ref = new_ref
                if len(look_here_nodes) > 1:  # todo: what if there are more than 2 look_here_nodes?
                    # set(look_here_nodes).intersection(self.raw_ref.rawText)
                    # node_ref = self.reduce_indexes(look_here_titles=None, look_here_titles_nodes=look_here_nodes,
                    #                     alt_ref_titles=self.raw_ref.rawText.replace('ו', ''))

                    # [index_t for index_t in look_here_titles_nodes if (set(index_t.split()).intersection(set(alt_ref_titles.split())))]
                    node_ref = intersect_list_string(look_here_nodes, self.raw_ref.rawText)
                    # print 'look at these i took the first: {}'.format(look_here_nodes[0])
                    try:
                        r = Ref(node_ref)
                        self.ref = r
                    except InputError:
                        print("couldn't find ref for") # {}".format(node_ref)
        else:
            depenent_indexes = []
            main_indexes = []
            for ind_title in list(reduced_indexes):
                if isinstance(ind_title, unicode):
                    ind = library.get_index(ind_title)
                elif isinstance(ind_title, Index):
                    ind = ind_title
                elif isinstance(ind_title, tuple):
                    ind = ind_title[1]
                else:
                    ind = None
                if ind and not ind.is_dependant_text():
                    main_indexes.append(ind_title)
                elif ind and ind.is_dependant_text():
                    depenent_indexes.append(ind_title)
            if main_indexes:
                self.index = main_indexes[0]
            elif depenent_indexes:
                self.index = depenent_indexes[0]
            else:
                # print "reduced_indexes: {} deleting wrong ref: {}.".format(reduced_indexes, self.ref.normal())
                self.ref = None

            if self.index:
                try:
                    sections = self.get_sections_from_ref()
                    if isinstance(self.index, tuple):
                        index_node_name = self.index[1].title + ', ' + self.index[0]
                    else:
                        index_node_name = Ref(self.index).he_normal() if is_hebrew(sections) else Ref(self.index).normal()
                    new_ref = Ref('{} {}'.format(index_node_name, sections))
                    # print "deleting wrong: {} found new Index: {} new ref: {}".format(self.ref, self.index, new_ref)
                    self.ref = new_ref
                except exceptions.InputError as e:
                    new_ref = None  # so not to have new_ref that failed scrowing with stuff
                    # try:
                    #     print "inputError for this string {}, extracted from this rawref {}".format(
                    #     '{} {}'.format(self.index.title, re.sub(self.ref.index.title, '', self.ref.normal()).strip()),
                    #     self.raw_ref)
                    # except AttributeError:
                    #     print "inputError for this string {}, extracted from this rawref"

        return new_ref

    def get_sections_from_ref(self):
        if 'Talmud' in self.ref.index.categories:
            he_massechet_title = Ref(self.ref.index.title).he_normal()
            sections = re.sub('(\(|\)|{})'.format(he_massechet_title), '', self.raw_ref.rawText)
        else:
            sections = re.sub(self.ref.index.title, '', self.ref.normal()).strip()
        return sections

    def get_index_options(self, include_dependant=True):
        """
        This function returns a list of indexes that the hope is at least one of them will be in the intersection
        with the original ref catching index (ex. the Tanakh wrong Ref)
        :param include_dependant: regarding the indexes for a giving category should it also list the dependent ones (ex. commentary)
        :return: (list) of indexes
        """
        look_here = self.extract_cat(include_dependant=include_dependant)
        if look_here:
            look_here.extend(self.indexs)
        return look_here

    def get_look_here_nodes(self, look_here):
        """
        nodes (rather then indexes) that there names should be searched
        :param look_here: a list of indexes (Index or str) that can be complex
        :return:
        """
        nodes = []
        for a in look_here:
            if isinstance(a, Index) and a.is_complex():
                nodes += a.nodes.children
        look_here_titles_nodes = [(node.key, node.index) for node in nodes]
        return look_here_titles_nodes

    def reduce_indexes(self, look_here_titles=None, look_here_titles_nodes = [], alt_ref_titles=None):
        """
        Looks for the intersection between the wrong Refs index title (and alt titles) with the optional indexes
        found in "look here", to pin down the correct index and then correct Ref.
        :param look_here_titles: a list of titles and node titles that can fit for part of the index name
        :param alt_ref_titles: a list of titles (including alt titles) of the 'wrong Ref'
        :return: a list of indexes that fall in the intersection of the combination of the lists
        """
        reduced_indexes = []
        if look_here_titles and alt_ref_titles:
            try:
                reduced_indexes = [index_t[0] for index_t in look_here_titles if (
                            (index_t[-1] in alt_ref_titles) or any([t for t in alt_ref_titles if t in index_t[-1]]))]
            except:
                reduced_indexes = []
        reduced_indexes_nodes = [index_t for index_t in look_here_titles_nodes if (index_t[0] in alt_ref_titles)]
        reduced_indexes.extend(reduced_indexes_nodes)

        # self.change_look_here("author", "category", "new_category")
        # reduced_indexes = [Ref(title).index for title in reduced_indexes]

        return reduced_indexes

    def change_look_here(self, author, new_author, category):
        """
        This function tries to run get_ref_step2 functionality if it is an author with a category that we know should be (or
        wish to try) a different author name ex. תרגום יונתן על תהילים is תרגום ארמי על תהילים
        :param author: current (Aspaklaria input) author
        :param new_author: guessed new author
        :param category: problematic category for this author name (כתובים in the previous example)
        :return: changes Source (self.ref, self.index, other things in the get_new_ref_w_look_here process)
        """
        if self.author == author and self.ref.index.title in library.get_indexes_in_category(category):
            self.author = new_author
            new_ref = None
            include_dependant = True
            look_here = self.get_index_options(include_dependant=include_dependant)
            if look_here:
                new_ref = self.get_new_ref_w_look_here(look_here)
            if new_ref:
                self.ref = new_ref
        return

    def intersected_indexes(self, new_index, indexs):
        """

        :param new_index: a index that came form the str but wasn't examed
        :param indexs: the list of indexes found but didn't fit to create a Ref
        :return: a list of indexs in the intersection
        """
        intersect_index = []
        if "Tanakh" in new_index.categories:
            # new_index.categories.pop(new_index.categories.index('Tanakh'))
            if "Torah" in new_index.categories:
                intersect_index = [ind for ind in indexs if re.search("Torah", ind.title)]
            elif "Writings" in new_index.categories or "Prophets" in new_index.categories:
                intersect_index = [ind for ind in indexs if re.search("Nach", ind.title)]
        if self.author == 'משנה תורה':
            title_found = intersect_list_string([x[0] for x in self.get_look_here_titles(indexs)if not re.search('Mishneh', x[0])], Ref(new_index.title).he_normal())
            intersect_index = (library.get_index(title_found), )
        return intersect_index

    def get_ref_clean(self):
        if self.index:
            try:
                try_text = "{}, {}".format(Ref(self.index.title).he_normal(), re.sub("[()]", "", self.text))
                self.ref = Ref(try_text)
            except (InputError, AttributeError, IndexError) as e:
                print("couldn't find it. Error {}. self.index = {}, self.text = {}".format(type(e).__name__, self.index.title, self.text))
                traceback.print_exc()
                self.ref = None
            return self.ref

    def get_author_person(self, author_name):
        person = None
        query = {"names.text": "{}".format(author_name)}
        author_curser = db.person.find(query)
        for doc in author_curser:
            person = doc['key']
        return person

    def get_indexes_docs(self, author_name):
        indexes = []
        person_key = self.get_author_person(author_name)
        if person_key:
            indexes = db.index.find({"authors": "{}".format(person_key)})
        return indexes

    def get_indexes_from_author(self, author_name):
        indexes = []
        curser = self.get_indexes_docs(author_name)
        for doc in curser:
            ind = library.get_index(doc['title'])
            indexes.append(ind)
        return indexes

    def try_from_ls(self):
        """
        try to look for a link to the pasuk from it's link set, since you have a pasuk that is related and an author's name. the authors name need to be extracted via Term
        :return: will return the new guess
        """
        return None

    def pm_match_text(self):
        """
        Use the ParallelMatcher to test and possibly change or precise to segment level the "source.ref"
        :return: the pm_ref (maybe untouched) source.ref
        """
        text_to_match = re.sub('\(.*?\)', '', self.text)
        results = disambiguate_ref_list(self.ref.normal(), [(text_to_match, '0')])
        self.pm_ref = results['0']['A Ref'] if results['0'] else results['0']
        # print "text: {} \n ref: {} \n pm_ref: {}".format(text_to_match, self.ref, self.pm_ref)
        return self.pm_ref

class RawRef(object):

    def __init__(self, st, author):
        self.rawText = st
        self.author = author
        self.book = None
        self.section_level = None
        self.segment_level = None
        self.is_sham = False
        if re.search("^\(שם", self.rawText):
            self.is_sham = True


def write_to_file(text, mode='a'):
    with codecs.open('resolved.txt', mode, encoding='utf-8') as f:
        f.write(text)


def parse_by_topic(topic_file_path):
    # topic_file_path = "009_TET_test/tevila.html"
    t = bs_read(topic_file_path)
    if db_aspaklaria.aspaklaria_source.count_documents({"topic": t.headWord}) > 0:
        print("Already parsed {}. Skipping".format(t.headWord))
        return t
    # parse_refs(t)
    t.parse_refs()
    try:
        t.parse_shams()
    except Exception as e:
        print("Shams Failed on something")
        print(traceback.print_exc())

    cnt = 0
    post_topic_documents(t, cnt)
    return t

def parse2pickle(letter=''):
    topic_le_table = dict()
    with open(ASPAKLARIA_HTML_FILES + '/headwords.csv', 'r') as csvfile:
        file_reader = csv.DictReader(csvfile)
        for i, row in enumerate(file_reader):
            pass
            fieldnames = file_reader.fieldnames
            topic_le_table[row['he']] = row['en']
    all_topics = dict()
    letters = [letter] if letter else os.listdir(ASPAKLARIA_HTML_FILES + '/')
    for letter in letters:
        if not os.path.isdir(ASPAKLARIA_HTML_FILES + '/{}'.format(letter)):
            continue
        i = 0
        topics = dict()
        for file in tqdm(os.listdir(ASPAKLARIA_HTML_FILES + "/{}".format(letter))):
            if '_' in file:
                continue
            # don't read the index file ex: for letter YOD don't read the html file '/Aspaklaria/aspaklaria/www.aspaklaria.info/010_YOD/YOD.html'
            if re.search(re.sub('.html', '', file), letter):
                continue
            t = bs_read(ASPAKLARIA_HTML_FILES + "/{}/{}".format(letter, file))
            i+=1
            topics[i] = t
            # topics[topic_le_table[clean_txt(t.headWord.replace("'", "").replace("-", ""))]] = t
            # topics[transliterator(t.headWord)] = t
        letter_name = re.search(".*_(.*?$)", letter)
        if letter_name:
            letter_name = letter_name.group(1)
            # print '{} headwords in the letter {}'.format(i, letter_name)
        with codecs.open("/home/shanee/www/Sefaria-Data/sources/Aspaklaria/pickle_files/{}.pickle".format(letter_name),"w") as fp:
            # json.dump(topics, fp) #TypeError: <__main__.Topic object at 0x7f5f5bb73790> is not JSON serializable
            pickle.dump(topics, fp, -1)
        all_topics[letter_name] = topics
    return all_topics


def post_topic_documents(t, cnt):
    sources = []
    for authorCit in t.all_a_citations:
        for s in authorCit.sources:
            if s.raw_ref:
                # cnt_sources += 1
                # print s.raw_ref.rawText
                solo_source_text = re.sub(re.escape(s.raw_ref.rawText), '', s.text)
                try:
                    s.ref.normal()
                except AttributeError:
                    s.ref = None
                if s.ref:
                    # if re.search("דרוש ז",s.raw_ref.rawText):
                    #     continue
                    document = {'topic': t.headWord, 'ref': s.ref.normal(), 'text': solo_source_text,
                                'raw_ref': s.raw_ref.rawText if s.raw_ref else None,
                                'index': s.ref.index.title, 'is_sham': s.raw_ref.is_sham, 'author': s.author}
                    if hasattr(s, 'pm_ref'):
                        document['pm_ref'] = s.pm_ref
                    # print s.ref.normal()
                    # cnt_resolved += 1
                else:
                    document = {'topic': t.headWord, 'text': solo_source_text, 'raw_ref': s.raw_ref.rawText,
                                'author': s.author, 'is_sham': s.raw_ref.is_sham}
                    # print s.author  # "None... didn't find the Ref"
                    # add_to = "sham" if s.raw_ref.is_sham else "not_caught"
                    # cnt_sham += 1 if add_to == "sham" else 0
                    # cnt_not_caught += 1 if add_to == "not_caught" else 0
                if s.index:
                    if isinstance(s.index, tuple) or isinstance(s.index, list):
                        s.index = s.index[0] if len(s.index) < 2 else s.index[1]
                    document['index_guess'] = s.index.title if isinstance(s.index, Index) else s.index
                elif s.indexs:
                    document['index_guess'] = ' |'.join([ind.title if isinstance(ind, Index) else ind for ind in s.indexs])

                if s.ref:
                    if s.ref.is_segment_level():
                        document['segment_level'] = True
                    else:
                        document['segment_level'] = False
                document['cnt'] = cnt
                # document['topic_key'] = topic_key
                # db_aspaklaria.aspaklaria_source.insert_one(document)
                db_aspaklaria.aspaklaria_source.update({"topic": document['topic'], "cnt": document['cnt']}, document, upsert=True)
                if 'ref' in document.keys():
                    sources.append(document['ref'])
                cnt += 1
                print('-----------------')
    return sources


def read_sources(letter, with_refs='pickle_files'):
    """

    :param letter: letter to be parsed
    :return: does not return, but rather inserts the data into mongo
    """

    with codecs.open("Aspaklaria/{}/{}.pickle".format(with_refs,letter), "rb") as fp:
        topics = pickle.load(fp)
        print("opend {}".format(letter))
        # cnt_sources = 0
        # cnt_sham = 0
        # cnt_resolved = 0
        # cnt_not_caught = 0
        cnt = 0
        for i, t in tqdm(enumerate(topics.values())):
            print("*******************")
            print(t.headWord)
            # topic_key = post_topic(t)
            sources = post_topic_documents(t, cnt)
            topic_key = post_topic(t, sources)
        print("done")


def shamas_per_leter(he_letter):
    # for file in os.listdir("/home/shanee/www/Sefaria-Data/sources/Aspaklaria/aspaklaria/pickle_files/"):
    # write_to_file('', mode = 'w')
    for file in ['{}.pickle'.format(he_letter)]:
        letter_name = file[0:-7]
        # Source.cnt = 0
        # Source.cnt_sham = 0
        # Source.cnt_resolved = 0
        # Source.cnt_not_found = 0
        with codecs.open("Aspaklaria/pickle_files/{}".format(file), "rb") as fp:
            write_to_file('NEW_Letter: {}\n\n'.format(file.split('.')[0]), mode='a')
            topics = pickle.load(fp)
            for i, t in tqdm(enumerate(topics.values())):
                # parse_refs(t)
                t.parse_refs()
                # print "Before resolved Shams" + str(Source.cnt_sham)
                try:
                    t.parse_shams()
                except:
                    print("Failed on something")
                # print "After resolved Shams" + str(Source.cnt_sham)
                print(i)
            # print "cnt :", Source.cnt
            # print "cnt_sham :", Source.cnt_sham, "precent: ", Source.cnt_sham * 100.0 / Source.cnt * 1.0
            # print "cnt_resolved :", Source.cnt_resolved, "precent: ", Source.cnt_resolved * 100.0 / Source.cnt * 1.0
            # print "cnt_not_found :", Source.cnt_not_found, "precent: ", Source.cnt_not_found * 100.0 / Source.cnt * 1.0
            for missing in parser.missing_authors:
                print(missing)

            with codecs.open(
                    "Aspaklaria/with_refs/{}.pickle".format(letter_name),
                    "w") as fp:
                # json.dump(topics, fp) #TypeError: <__main__.Topic object at 0x7f5f5bb73790> is not JSON serializable
                pickle.dump(topics, fp, -1)
        # print 'done'


def intersect_list_string(title_list, string, ref_opt=False):
    best = ('', -1)
    for title in title_list:
        intersection_size = intersect_2_strings(title, string, combine_single_letters=True)
        if ref_opt and intersection_size == -100:
            intersection_size = 1
        if intersection_size:
            if intersection_size > best[1]:
                best = (title, intersection_size)
            elif intersection_size == best[1] and abs(len(title) - len(string)) < abs(
                    len(best[0]) - len(string)):
                best = (title, intersection_size)
        elif ref_opt and int(best[1]) != best[1]:
            best = (title, intersection_size)
    if best[0] and best[1]:
        best=(best[0], best[1]+1)  # giving the combined version an advantage
    for title in title_list:
        intersection_size = intersect_2_strings(title, string, combine_single_letters=False)
        if intersection_size:
            if intersection_size > best[1]:
                best = (title, intersection_size)
            elif intersection_size == best[1] and abs(len(title)-len(string))<abs(len(best[0])-len(string)):
                best = (title, intersection_size)
        elif ref_opt and int(best[1]) != best[1]:
            best = (title, intersection_size)
    return best[0]

table_he_numbering = {'א' :"ראשון",
                    'ב': "שני",
                    'ג' :"שלישי",
                    'ד' :"רביעי",
                    'ה' :"חמישי",
                    'ו' :"שישי",
                    'ז' :"שביעי",
                    'ח' :"שמיני",
                    'ט' :"תשיעי",
                    'י' :"עשירי",
                      }
def strings2sets(strings, subs=None, combine_single_letters=True):
    sets = []
    single_he_letter_reg = re.compile('([^\s]+)\s+([^\s])(\s+|$)')
    if isinstance(strings, unicode):
        strings = [strings]
    for st in strings:
        # add single letters as numbers to create a "single" word
        if combine_single_letters:
            st = re.sub(single_he_letter_reg, r'\1_\2 ', re.sub('{}'.format(subs), '', st))
        else:
            st = re.sub('{}'.format(subs), '', st)
            # special casing for the Shelah where we refer to the mamarim with hebrew number naming ratehr than hebrew letters.
            if re.search("מאמר", st):
                single_he_letter = re.search(single_he_letter_reg, st)
                if single_he_letter:
                    st = re.sub(single_he_letter.group(2), table_he_numbering[single_he_letter.group(2)], st)
        st_lst = re.split('\s+', st)
        st_lst = [re.sub('_', ' ', x) for x in st_lst if x]
        set_st = set(st_lst)
        sets.append(set_st)
    return sets


def intersect_2_strings(title, raw, combine_single_letters=True):
    # lst_title = re.split(',?\s+', title)
    # lst_raw = re.split('[,]?\s+', re.sub('[()]','', raw))
    # set_title = set(lst_title)
    # set_raw = set(lst_raw)
    set_title, set_raw = strings2sets([title, raw], subs='[,()\']', combine_single_letters=combine_single_letters)
    intersection = set_title.intersection(set_raw)
    # try with using match method from PM
    matches = match_text(list(set_title), list(set_raw), char_threshold=0.27)['matches']
    good_matchs = [x for x in matches if x[0] != -1]
    if intersection:
         return len(intersection)
    elif good_matchs:
        return len(good_matchs)-0.5
    return -100


def sublists(a, b):
    upper = max(len(a), len(b)) + 1
    for i in range(upper):
        for j in range(upper):
            if b == a[j:i] or a == b[j: i]:
                return True
    return False


def clean_see(st):
    """

    :param st:
    :return:
    """
    st = re.sub('(-|\.)', ' ', st)
    st = st.strip()

    return st


def post_topic(t, sources=None):
    """
    postes to collection pairing for the topic words and the appropriate 'see'
    :param t: topic
    :param sources: a list of sources with Refs in Sefaria library as far as we can tell
    :return: posts to collection 'aspaklaria_topics' and returns the mongo obj
    """
    topic_doc = {}
    topic_doc['topic'] = t.headWord
    if t.see:
        topic_doc['see'] = [clean_see(see) for see in t.see]
        found_see = find_see_topics(topic_doc['see'], collection='topics')
        for i, see in enumerate(topic_doc['see']):
            doc = {'topic': t.headWord, 'see': see}
            if see and found_see and found_see[i]:
                doc['found'] = found_see[i]
            db_aspaklaria.pairing.insert_one(doc)
            # db_aspaklaria.pairing.update({"topic": doc['topic'], "cnt": doc['cnt']}, doc,
            #                                        upsert=True)
        if found_see:
            topic_doc['found'] = found_see
    if t.altTitles:
        topic_doc['alt_title'] = t.altTitles
    author_list = [a_cit.author for a_cit in t.all_a_citations]
    number_per_author = [len(a_cit.cit_list) for a_cit in t.all_a_citations]
    number_sources = sum(number_per_author)
    if author_list:
        topic_doc['authors'] = author_list
    topic_doc['sources#'] = number_sources
    topic_doc['sources'] = sources

    res = db_aspaklaria.aspaklaria_topics.insert_one(topic_doc)
    return res


def find_see_topics(see_list, collection): #='topics'
    """
    gets a document representing a topic and returns a list of matching documents for the 'see' field
    :param row: either a doc to be inserted or a doc read from mongo
    :return: list of found topics (as document mongo objects)
    """
    found_see = []
    if see_list:
        if isinstance(see_list, unicode):
            see_list = [see_list]
        for see in see_list:
            see = clean_see(see)
            found = db_aspaklaria.aspaklaria_topics.count_documents({'topic': see})
            if found:
                # for f in found:
                found_see.append(see)
            else:
                found_see.append(None)
    return found_see if any(found_see) else []


def add_found_to_topics(collection): #  = 'topics'
    """
    goes over collection 'aspaklaria_topics' and adds a list see topic objects respectively
    :return: nothing, just updates the docs in the collection
    """
    # topics = db_aspaklaria.aspaklaria_topics.find({})
    topics = db_aspaklaria['{}'.format(collection)].find({})
    for t in topics:
        if 'see' in t.keys():
            found_see = find_see_topics(t['see'], collection)
            if found_see:
                oldid = t['_id']
                new = t.copy()
                new['found'] = found_see[0] if (len(found_see)==1 and collection == 'pairing') else found_see
                del new['_id']
                # db_aspaklaria['{}'.format(collection)].update_one({'_id': '{}'.format(oldid)}, {'$set':{'found':found_see}})
                # db_aspaklaria.aspaklaria_topics.update({'_id': oldid}, t)
                db_aspaklaria['{}'.format(collection)].update({'_id': oldid}, new)


def convert_perk_parasha(ref, table):
    return table[ref]

def parse_html_file(letter_folder=None, num_rand_files=None):
    # letter_folder = letter if letter else random.sample(os.listdir(ASPAKLARIA_HTML_FILES), 1)[0]
    letter_folder_topics = os.listdir(ASPAKLARIA_HTML_FILES + "/{}".format(letter_folder))
    letter_topics = random.sample(letter_folder_topics, num_rand_files) if num_rand_files else letter_folder_topics
    for tf in letter_topics:
        print("/{}/{}".format(letter_folder, tf))
        tfp = ASPAKLARIA_HTML_FILES + "/{}/{}".format(letter_folder, tf)
        try:
            t = parse_by_topic(tfp)
            print(tfp)
        except Exception as e:
            print("ERROR parsing {}".format("/{}/{}".format(letter_folder, tf)).encode('utf-8'))
            traceback.print_exc()

if __name__ == "__main__":
    # he_letter = '010_ALEF'
    # letter = '009_TET'
    # letter = ''  # 020_KAF, 009_TET
    # skip_letters = ['020_KAF']  # ['009_TET','050_NUN', '020_KAF', ]
    # letters = [letter] if letter else os.listdir(ASPAKLARIA_HTML_FILES+
    #     '/')
    # for letter in letters:
    #     if not os.path.isdir(ASPAKLARIA_HTML_FILES+ '/{}'.format(letter)):
    #         continue
    #     if letter == 'test':
    #         continue
    #     if letter in skip_letters:
    #         print 'skipped {}'.format(letter)
    #         continue
    #     match = re.search('(\d*)_(.*)', letter)
    #     he_letter= match.group(2)
    #     letter_gimatria = match.group(1)
    #     print '**HE_LETTER** {}'.format(he_letter)
    #     parse2pickle('{}_{}'.format(letter_gimatria, he_letter))
    #     shamas_per_leter(he_letter)
    #     read_sources('{}'.format(he_letter), with_refs='with_refs')

    args = argparse.ArgumentParser()
    args.add_argument("-l", "--letter", dest="letter", default=None, help="list of letters with the Gimatria number ex: 020_KAF to be parsed and posted to the db, if empty must put in a number of topics to be chosen randomly from all the letters")
    args.add_argument("-r", "--rand", dest="rand", default=None, help="a list of numbers respectively to the letters in the rand numbers of topics that will be chosen from the letter, 0 will parse the whole letter as well as keeping this arg blank")
    args.add_argument("-f", "--file", dest="file", default=None, help="full path of a single topic file to parse and push to the DB")
    user_args = args.parse_args()

    # testing!
    if user_args.file:
        try:
            parse_by_topic(user_args.file)
        except:
            "{} has failed".format(user_args.file)
        sys.exit(1)
    if not user_args.letter and not user_args.rand:
        print("please give at leaset one argument of the fallowing number of topics or list of letters")
        sys.exit(1)
    letter_folders = random.sample(os.listdir(ASPAKLARIA_HTML_FILES), int(user_args.rand)) if not user_args.letter else ["{}_Test".format(l) for l in  user_args.letter.split()] #[None]*int(user_args.rand)
    if not user_args.rand:
        num_rand_files = [None]*len(letter_folders)
    elif not user_args.letter:
        num_rand_files = [1] * len(letter_folders)
    else:
        num_rand_files = [int(num) for num in user_args.rand.split()]

    for letter_folder, num_rand in zip(letter_folders, num_rand_files):
        if not letter_folder:
            for i in range(num_rand):
                parse_html_file(letter_folder, 1)
        else:
            parse_html_file(letter_folder, num_rand)

    # add_found_to_topics(collection='aspaklaria_topics')
    # add_found_to_topics(collection='pairing')
    # cProfile.runctx("g(x)", {'x': '{}_{}'.format(letter_gimatria, he_letter), 'g': parse2pickle}, {}, 'stats')
    # p = pstats.Stats("stats")
    # p.strip_dirs().sort_stats("cumulative").print_stats()

    #create number system for test letters
    # import os
    # letters = [
    #     "001_ALEF",
    #     "002_BET",
    #     "003_GIMEL",
    #     "004_DALET",
    #     "005_HE",
    #     "006_VAV",
    #     "007_ZAYIN",
    #     "008_HET",
    #     "009_TET",
    #     "010_YOD",
    #     "020_KAF",
    #     "030_LAMED",
    #     "040_MEM",
    #     "050_NUN",
    #     "060_SAMEKH",
    #     "070_AYIN",
    #     "080_PE",
    #     "090_TSADI",
    #     "100_QOF",
    #     "200_RESH",
    #     "300_SHIN",
    #     "400_TAV"
    # ]
    # cnt = 0
    # for letter in letters:
    #     new_dir = "Aspaklaria/www.aspaklaria.info/test/{}_Test".format(letter)
    #     command = "mkdir {}".format(new_dir)
    #     os.system(command)
    #     old_dir = "Aspaklaria/www.aspaklaria.info/{}".format(letter)
    #     for file in sorted(os.listdir(old_dir)):
    #         command = "cp '{}/{}' '{}/{}.html'".format(old_dir, file, new_dir, cnt)
    #         os.system(command)
    #         cnt +=1