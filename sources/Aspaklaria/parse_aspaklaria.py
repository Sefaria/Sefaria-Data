#encoding=utf-8

import django
django.setup()

from sefaria.model import *
from sefaria.system import exceptions
from bs4 import BeautifulSoup, element
from sources.functions import *
import string
import unicodecsv as csv
import json
import pickle
from data_utilities.util import getGematria, numToHeb
import codecs
from data_utilities.ibid import *

class Parser(object):

    def __init__(self):
        self.term_dict, self.he_term_str = he_term_mapping()
        self.missing_authors = set()

def he_term_mapping():
    all_terms = TermSet({})
    # all_terms += library.get_text_categories()
    he_titles = [[(term.get_primary_title(), x['text']) for x in term.title_group.titles if x['lang'] == 'he'] for term
                 in all_terms]
    en, he = zip(*reduce(lambda a,b: a+b, he_titles))
    he = map(lambda x: re.sub(u'"', u"", x), he)
    he_key_term_dict = dict(zip(he, en))
    he_terms_str = u'|'.join(he)
    he_terms_str = re.sub(re.escape(string.punctuation), u'', he_terms_str)
    return he_key_term_dict, he_terms_str

def bs_read(fileName):
    with codecs.open(fileName, encoding='utf-8') as f:
        file_content = f.read()

    content = BeautifulSoup(file_content, "lxml")
    headWord = clean_txt(content.findAll('h1')[0].text)
    t = Topic(headWord)
    b = AuthorCit(u'before')
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
            elif re.search(u'ראה', c) and re.search(u':', c):
                txt_split = c.split(':')
                see = re.sub(u"[\(\)]", u'', txt_split[1]).split(u',')
                t.see = [re.sub(re.escape(string.punctuation), u'', s) for s in see]
                # t.see = [re.sub(, u'', s) for s in see]
            else:
                tanakh.append(c)
    t.all_a_citations.pop(0)
    if tanakh and t.all_a_citations:
        t.all_a_citations[0] = AuthorCit(u'תנך')
        t.all_a_citations[0].cit_list = tanakh

    return t


def transliterator(hestr):
    trans_table = {u'א': u'a', u'ב': u'b', u'ג': u'g', u'ד': u'd', u'ה': u'h', u'ו': u'v', u'ז': u'z', u'ח': u'ch', u'ט': u't', u'י': u'y', u'כ': u'kh', u'ל': u'l', u'מ': u'm', u'נ': u'n', u'ס': u's', u'ע': u"a'a", u'פ': u'p', u'צ': u'tz', u'ק': u'k', u'ר': u'r', u'ש': u'sh', u'ת': u't', u'ן': u'n', u'ף': u'f', u'ך': u'kh', u'ם': u'm', u'ץ': u'tz'
                   }
    enstr = u''
    for l in hestr:
        enstr+=trans_table[l] if l in trans_table.keys() else l
    return enstr


def clean_txt(text):
    cleaned = u' '.join(text.split())
    if cleaned and cleaned[-1] == u':':
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
        tanakh_books =library.get_indexes_in_category(u'Tanakh')
        comp_tanakh_comm = re.compile(u'(?P<commentator>^.*?(on|,)\s+).*$')
        for cit in self.all_a_citations:
            for source in cit.sources:
                ref_d = self.ref_dict(source)
                if ref_d:
                    topic_table.append(self.ref_dict(source))
                    BT.registerRef(source.ref)
                if source.ref and u'Tanakh'in source.ref.index.categories and source.ref.index.title not in tanakh_books:
                    match = re.search(comp_tanakh_comm, source.ref.normal())
                    tanakh_ref = Ref(re.sub(match.group(u'commentator'), u'', source.ref.normal()))
                    BT.registerRef(tanakh_ref)
                if source.raw_ref and source.raw_ref.is_sham:
                    print u'Sham Ref {}'.format(source.raw_ref.rawText)
                    if topic_table[-1]['author'] == source.raw_ref.author:
                        source.ref = BT.resolve(topic_table[-1]['index'].title, match_str= source.author + source.raw_ref.rawText) # assuming the index is definatly the same as the last one is not neccesary. and should check if there is a source.index frist?
                        print source.ref
                        BT.registerRef(source.ref)
                    elif u'Tanakh' in topic_table[-1]['index'].categories:
                        tanakh_book = tanakh_ref.index.title
                        # if topic_table[-1]['index'].is_complex():
                        #     tanakh_book = tanakh_ref.index.title
                        # else:
                        #     tanakh_book = topic_table[-1]['index'].base_text_titles[0]
                        # this_he_title = u'{} על {}'.format(source.raw_ref.author, Ref(tanakh_book).he_normal())
                        library.get_index(tanakh_book)
                        match_str = Ref(tanakh_book).he_normal() + re.sub(u'שם ', u'', source.raw_ref.rawText, count=1) #re.sub(u'(\(|\))', u'', this_he_title + re.sub(u'שם', u'', u'(שם שם כג)', count=1))
                        try:
                            try_ref = BT.resolve(tanakh_book, match_str=match_str)  # sections=[topic_table[-1]['section'],topic_table[-1]['segment']])
                            source.ref = Ref(cit.author + u' על ' + try_ref.he_normal())
                            BT.registerRef(source.ref)
                            print source.ref
                        except (InputError, IbidRefException) as e:
                            source.ref = None
                            cnt+=1
                            print cnt
                            print u'{}'.format(e)


                    pass

    def ref_dict(self, source):
        d = {}
        if source.ref:
            if hasattr(source.ref.index.schema, 'addressTypes') and u'Talmud' in source.ref.index.schema['addressTypes']:
                d['section'] = source.ref.sections[0]%2
            d['author'] = source.author
            d['index'] = source.ref.index
            d['section'] = source.ref.sections[0]
            d['segment'] = source.ref.sections[1] if len(source.ref.sections) > 1 else None
        if d:
            return d

class Source(object):
    cnt = 0
    cnt_sham = 0
    cnt_resolved = 0
    cnt_not_found = 0
    global parser
    parser = Parser() #term_dict = he_term_mapping()
    indexSet_dict = dict()
    found_term_dict = dict()

    def __init__(self, text, author):
        self.text = text
        self.author = author
        self.index = None
        self.indexs = None
        self.cat = None
        self.raw_ref = None
        self.ref = None

        self.extract_raw_ref()
        self.get_ref_from_api()

        if self.raw_ref:
            Source.cnt+=1
            if self.raw_ref.is_sham:
                Source.cnt_sham += 1
            elif self.ref:  # found ref (presumably a correct ref :) )
                Source.cnt_resolved += 1
                res_text = u'{}, {}\n{}\n\n'.format(self.raw_ref.author, self.raw_ref.rawText, self.ref.normal())
                write_to_file(res_text)
            else:
                Source.cnt_not_found += 1

    def extract_raw_ref(self):
        """
        looks for the ref in the end of the text in parentheses
        :return: does not return but creates a RawRef obj if the parentheses are found
        """
        if re.search(u'(\([^)]*?\)$)', self.text):
            self.raw_ref = RawRef(re.search(u'(\([^)]*?\)$)',self.text).group(1), self.author)
        # else:
        #     pass

    def extract_cat(self, include_dependant):
        # library.get_index(self.author) if library.get_index(self.author) else None # needs to go into a try catch "sefaria.system.exceptions.BookNameError"
        author = re.sub(u'[{}]'.format(re.escape(string.punctuation)), u'', self.author)
        try:
            self.index = library.get_index(author)
        except exceptions.BookNameError as e: #sefaria.system.exceptions.
            found_term = self.extract_term()
            if found_term:
                found_term = [found_term] if not isinstance(found_term, list) else filter(lambda x: x, found_term)
                cat_terms = filter(lambda term: term in library.get_text_categories(), found_term)
                self.cat = cat_terms  # found_term
                if self.cat:
                    look_here = reduce(lambda a,b: [x for x in b for y in a if x==y], [library.get_indexes_in_category(cat, include_dependant=include_dependant, full_records=True).array() for cat in self.cat])
                    return look_here
            #might need to use Terms to make lookup the category in english
            # Term().load({"name": self.author})
            # filter(lambda x: x['lang'] == 'he', t.contents()['titles'])[0]['text']

    def extract_term(self):
        # text_categories = library.get_text_categories()
        found_term = []
        author = re.sub(u'[{}]'.format(re.escape(string.punctuation)), u'', self.author)
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
                match = re.search(u"\|([^|]*{}(\s[^|]*?\||\|))".format(term_string), parser.he_term_str)
                if match:
                    found_term = parser.term_dict.get(match.group(1).replace(u"|", u""), [])
                    Source.found_term_dict[term_string] = found_term
                    return found_term
                elif prefixes:
                    return try_to_find(re.sub(u'^[משהוכלב]', u'', term_string), False)
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
        #     found_he = re.search(u"\|(.*?{}.*?)\|".format(author), parser.he_term_str).group(1)
        #     found_term = parser.term_dict.get(found_he, [])
        # if not found_term:
        #     found_term = parser.term_dict.get(re.sub(u'^[משהוכלב]', u'', author), [])
        # if not found_term:
        #     for word in author.split():
        #         found = parser.term_dict.get(word.replace(u'"', u""), [])
        #         if found:
        #             found_term.append(found)
        #         else:
        #             found_term.append(parser.term_dict.get(re.sub(u'(^[משהוכלב]|")', u'', word), []))
        # return found_term if isinstance(found_term, list) else [found_term]

    def extract_indx(self):
        author = re.sub(u'[{}]'.format(re.escape(string.punctuation)), u'', self.author)
        try:
            self.index = library.get_index(author)
            if self.index.title == u'Yalkut Shimoni on Torah':
                raise exceptions.BookNameError
        except exceptions.BookNameError as e:
            term_list = self.extract_term()
            if term_list:
                # term_list = map(lambda x: unicode.lower(x), term_list)
                inds_via_term = []
                for term in term_list:
                    indexset = Source.indexSet_dict.get(term, None)
                    if indexset is None:
                        indexset = IndexSet({u"title": {u"$regex": u".*(?i){}.*".format(term)}}).array()
                        Source.indexSet_dict[term] = indexset
                    inds_via_term += indexset
                # for title in [x['text'] for ind in inds_from_term for x in ind.schema['titles'] if x['lang'] == 'he']:
                #     print title
                inds_via_cats = reduce(lambda a,b : a and b, [library.get_indexes_in_category(term) for term in term_list])
                if bool(inds_via_cats) != bool(inds_via_term): # only one of the index groups was filled
                    self.indexs = inds_via_term if inds_via_term else inds_via_cats
                elif bool(inds_via_cats) and bool(inds_via_term):
                    if self.author == u'תלמוד בבלי':
                        self.indexs = inds_via_cats
                    elif self.author == u'משנה תורה':
                        self.indexs = inds_via_cats
                    elif self.author == u'ירושלמי':
                        self.indexs = library.get_indexes_in_category(u'Yerushalmi')
                    else:
                        self.indexs = inds_via_term
                else:  # both are empty
                    pass
                    print "done"

    def get_ref_from_api(self):

        def clean_raw(st):
            st = re.sub(u'[)(]', u'', st) # incase we put those parantheses on before to try and catch it with get_ref_in_string
            he_parashah_array = [u"בראשית", u"נח", u"לך לך", u"וירא", u"חיי שרה", u"תולדות", u"ויצא", u"וישלח", u"וישב", u"מקץ", u"ויגש", u"ויחי", u"שמות", u"וארא", u"בא", u"בשלח", u"יתרו", u"משפטים", u"תרומה", u"תצוה", u"כי תשא", u"ויקהל", u"פקודי", u"ויקרא", u"צו", u"שמיני", u"תזריע", u"מצורע", u"אחרי מות", u"קדושים", u"אמור", u"בהר", u"בחוקתי", u"במדבר", u"נשא", u"בהעלותך", u"שלח", u"קרח", u"חקת", u"בלק", u"פנחס", u"מטות", u"מסעי", u"דברים", u"ואתחנן", u"עקב", u"ראה", u"שופטים", u"כי תצא", u"כי תבוא", u"נצבים", u"וילך", u"האזינו", u"וזאת הברכה"]
            for s in [u"מאמר", u"פרק"]:
                st = re.sub(s, u"", st)
            if self.author == u"משנה תורה":
                st = u"הלכות " + st
            elif self.author == u"ספר החינוך":
                for s in he_parashah_array:
                    st = re.sub(s, u"", st)
                    st = re.sub(u"מצוה", u"", st)
            return st

        if self.raw_ref:
            ref_w_author = u"(" + self.author + u", " + re.sub(u"[)(]", u"", self.raw_ref.rawText) + u")"
            refs = library.get_refs_in_string(ref_w_author)
            if refs:
                # assert len(refs) == 1
                self.ref = refs[0]
                print self.ref
            else:  # straight forward didn't find, so might be a sham. Or might need special casing.
                if re.search(u"^\(שם", self.raw_ref.rawText):
                    self.raw_ref.is_sham = True
                else:
                    cleaned = clean_raw(self.raw_ref.rawText)
                    fixed_ref = u"(" + self.author + u", " + re.sub(u"[)(]", u"", cleaned) + u")"
                    print u"*** try new ref, fixed_ref = {}".format(fixed_ref)
                    refs = library.get_refs_in_string(fixed_ref)
                    if refs:
                        self.ref = refs[0]
                        print self.ref
            print self.raw_ref.rawText, u'\n', ref_w_author
        else: # there isn't a self.ref means we couldn't find parenthises at the end, probably a conyinuation of the prev source/ cit (in cit_list
            pass
        self.extract_indx()
        self.get_ref_step2()


    def get_look_here_titles(self, look_here):
        look_here_titles = [index.title for index in look_here] if isinstance(look_here[0], Index) else look_here
        shared_word_in_titles = u'({})'.format(u'|'.join(list(set.intersection(*[set(x.split()) for x in look_here_titles]))))
        if shared_word_in_titles:
            look_here_titles = map(lambda x: (x, re.sub(shared_word_in_titles, u'', x).strip()), look_here_titles)
        else:
            look_here_titles = map(lambda x: tuple(x), look_here_titles)
        return look_here_titles


    def get_ref_step2(self):
        """
        after get_ref_from_api() we want to call this function.
        It should discard/change wrongly caught refs, like ones caught bavli instead of Yerushalmi or mishanah instead of Tosefta.
        :return: doesn't return but changes self.ref
        """
        wrong_ref = False

        if self.ref:  # probabaly should be calculated once
            if self.author != u"תנך"  and self.ref.index.title in library.get_indexes_in_category(u'Tanakh'):
                include_dependant = True
                wrong_ref = True
            elif self.author != u"תלמוד בבלי"  and self.ref.index.title in library.get_indexes_in_category(u'Bavli'):
                include_dependant = False
                wrong_ref = True

        if self.ref:
            if wrong_ref:  # or (self.raw_ref and not self.ref and not self.raw_ref.is_sham):
                new_ref = None
                include_dependant = True
                # look_here = self.extract_cat(include_dependant=include_dependant)
                look_here = self.indexs
                if look_here:
                    if wrong_ref:
                        current_title = self.ref.index.title
                        alt_ref_titles = map(lambda x: x['text'], self.ref.index.schema['titles'])
                        look_here_titles = self.get_look_here_titles(look_here)
                        reduced_indexes = [index_t[0] for index_t in look_here_titles if ((index_t[-1] in alt_ref_titles) or any([t for t in alt_ref_titles if t in index_t[-1]]))]
                        if len(reduced_indexes) == 1:
                            self.index = reduced_indexes[0]
                            try:
                                new_ref = Ref(u'{} {}'.format(self.index, re.sub(self.ref.index.title, u'', self.ref.normal()).strip()))
                                print u"deleting wrong: {} found new Index: {} new ref: {}".format(self.ref, self.index, new_ref)
                                self.ref = new_ref
                            except exceptions.InputError as e:
                                new_ref = None # so not to have new_ref that failed scrowing with stuff
                                print u"inputError for this string {}, extracted from this rawref {}".format(u'{} {}'.format(self.index.title, re.sub(self.ref.index.title, u'', self.ref.normal()).strip()), self.raw_ref)
                        elif not reduced_indexes: #  len(reduced_indexes) == 0
                            # couldn't find the title in the books maybe it is in there nodes
                            if isinstance(look_here[0], Index):
                                look_here_nodes = reduce(lambda a,b: a+b, [ind.alt_titles_dict('he').items() for ind in look_here])
                                look_here_nodes = filter(lambda x: any(re.search(t, x[0]) for t in alt_ref_titles), look_here_nodes)
                                if len(look_here_nodes) >= 1:
                                    node = look_here_nodes[0]
                                    node_name = node[0]
                                    depth = re.search(u'.*?(\d+):?(\d+)?.*?', self.ref.normal()).groups()
                                    for d in depth:
                                        if not d:
                                            print "break"
                                            break
                                        try:
                                            new_ref = Ref(u'{} {}'.format(node_name, numToHeb(d)))
                                            print u"deleting wrong: {} found new Index: {} new ref: {}".format(self.ref, self.index, new_ref)
                                            break
                                        except exceptions.InputError as e:
                                            print u"inputError for this string {}, extracted from this rawref {}".format(u'{} {}'.format(node_name, numToHeb(d)), self.raw_ref.rawText)
                                            if u"ילקוט שמעוני" in node_name:
                                                try:
                                                    new_ref = Ref(u'{}, {}'.format(ind.title, d))
                                                except exceptions.InputError:
                                                    print u"inputError for this string {}, extracted from this rawref {}".format(
                                                        u'{} {}'.format(node_name, numToHeb(d)), self.raw_ref.rawText)
                                        except IndexError as e:
                                            print u'IndexError {} not sure why...'.format(e)
                                    self.ref = new_ref
                                if len(look_here_nodes) > 1:  #todo: what if there are more than 2 look_here_nodes?
                                    print u'look at these i took the first: {}'.format(look_here_nodes[0])
                        else:
                            print u"reduced_indexes: {} deleting wrong ref: {}.".format(reduced_indexes, self.ref.normal())
                            self.ref = None
                else: #couldn't find a indexs for this author
                    parser.missing_authors.add(self.author)
                # if look_here and (self.index or wrong_ref):
                #     # than try to get the true title from the cat from look_here
                #     look_here_shared_title_word = u'({})'.format(
                #         u'|'.join(list(set.intersection(*[set(x.title.split()) for x in look_here]))))
                #     alt_ref_titles = map(lambda x: x['text'], self.ref.index.schema['titles'])
                #     found_index = [ind for ind in look_here for tanakh_book in alt_ref_titles if
                #                    tanakh_book in re.sub(look_here_shared_title_word, u'', ind.title).strip()]
                #     if found_index:
                #         if len(set(found_index)) > 1:  # assert len(found_index) == 0
                #             print "more than one index option"  # todo: problem with אלשיך דברים and with books I, II
                #             print found_index[0].title, found_index[-1].title
                #         self.index = found_index[0]
                #         try:
                #             new_ref = Ref(u'{} {}'.format(self.index.title, re.sub(self.ref.index.title, u'', self.ref.normal()).strip()))
                #             print u"deleting wrong: {} found new Index: {} new ref: {}".format(self.ref, self.index, new_ref)
                #             self.ref = new_ref
                #         except exceptions.InputError as e:
                #             print u"inputError for this string {}, extracted from this rawref {}".format(u'{} {}'.format(self.index.title, re.sub(self.ref.index.title, u'', self.ref.normal()).strip()), self.raw_ref)
                # tanakh is wrong but can't find the index ex: רש"ר הירש
                if self.index and not self.ref:
                    ind = self.index
                    #todo: look into the original catching see why it is not catching kalla. also see how to copy the intresting parts to here
                    self.raw_ref.book = ind.title
                    split_raw_text = re.sub(u'[\(\)]', u'', self.raw_ref.rawText).split()
                    self.raw_ref.section_level = split_raw_text

                    pass
                if not self.index or not new_ref:
                    print u"deleting wrong: {} couldn't find an index".format(self.ref)
                    self.ref = None
            else:  # not wrong_ref. and found a ref, might just be a correct ref. todo: how to test it is correct?
                pass
        # where can we look at nodes names when we are not testing giving wrong Ref?


    def try_from_ls(self):
        """
        try to look for a link to the pasuk from it's link set, since you have a pasuk that is related and an author's name. the aouthers name need to be exctracted via Term
        :return: will return the new guess
        """
        return None


class RawRef(object):

    def __init__(self, st, author):
        self.rawText = st
        self.author = author
        self.book = None
        self.section_level = None
        self.segment_level = None
        self.is_sham = False


def write_to_file(text, mode='a'):
    with codecs.open(u'resolved.txt', mode, encoding='utf-8') as f:
        f.write(text)



def parse2pickle():
    topic_le_table = dict()
    with open(u'/home/shanee/www/Sefaria-Data/sources/Aspaklaria/headwords.csv', 'r') as csvfile:
        file_reader = csv.DictReader(csvfile)
        for i, row in enumerate(file_reader):
            pass
            fieldnames = file_reader.fieldnames
            topic_le_table[row[u'he']] = row[u'en']
    all_topics = dict()
    for letter in os.listdir(u'/home/shanee/www/Sefaria-Data/sources/Aspaklaria/www.aspaklaria.info/'):
        if not os.path.isdir(u'/home/shanee/www/Sefaria-Data/sources/Aspaklaria/www.aspaklaria.info/{}'.format(letter)):
            continue
        i = 0
        topics = dict()
        for file in os.listdir(u"/home/shanee/www/Sefaria-Data/sources/Aspaklaria/www.aspaklaria.info/{}".format(letter)):
            if u'_' in file:
                continue
            if file[:-5].isalpha():
                continue
            t = bs_read(u"/home/shanee/www/Sefaria-Data/sources/Aspaklaria/www.aspaklaria.info/{}/{}".format(letter, file))
            i+=1
            topics[i] = t
            # topics[topic_le_table[clean_txt(t.headWord.replace(u"'", u"").replace(u"-", u""))]] = t
            # topics[transliterator(t.headWord)] = t
        letter_name = re.search(u".*_(.*?$)", letter)
        if letter_name:
            letter_name = letter_name.group(1)
            print u'{} headwords in the letter {}'.format(i, letter_name)
        with codecs.open(u"/home/shanee/www/Sefaria-Data/sources/Aspaklaria/pickle_files/{}.pickle".format(letter_name), "w") as fp:
            # json.dump(topics, fp) #TypeError: <__main__.Topic object at 0x7f5f5bb73790> is not JSON serializable
            pickle.dump(topics, fp, -1)
        all_topics[letter_name] = topics



if __name__ == "__main__":
    # parse2pickle()

    # a = dict()
    # a[u'שלום'] = 1
    # name=u'מיכאל'
    # pass
    # for file in os.listdir(u"/home/shanee/www/Sefaria-Data/sources/Aspaklaria/pickle_files/"):
    write_to_file(u'', mode = 'w')
    for file in [u'BET.pickle']:
        letter_name = file[0:-7]
        Source.cnt = 0
        Source.cnt_sham = 0
        Source.cnt_resolved = 0
        Source.cnt_not_found = 0
        with codecs.open(u"/home/shanee/www/Sefaria-Data/sources/Aspaklaria/pickle_files/{}".format(file), "rb") as fp:
            write_to_file(u'NEW_Letter: {}\n\n'.format(file.split(u'.')[0]), mode='a')
            topics = pickle.load(fp)
            for i, t in enumerate(topics.values()):
                parse_refs(t)
                t.parse_shams()
                print i
            print u"cnt :", Source.cnt
            print u"cnt_sham :", Source.cnt_sham, u"precent: ", Source.cnt_sham*100.0/Source.cnt*1.0
            print u"cnt_resolved :", Source.cnt_resolved, u"precent: ", Source.cnt_resolved*100.0/Source.cnt*1.0
            print u"cnt_not_found :", Source.cnt_not_found, u"precent: ", Source.cnt_not_found*100.0/Source.cnt*1.0
            for missing in parser.missing_authors:
                print missing

        with codecs.open(u"/home/shanee/www/Sefaria-Data/sources/Aspaklaria/with_refs/{}.pickle".format(letter_name),
                         "w") as fp:
            # json.dump(topics, fp) #TypeError: <__main__.Topic object at 0x7f5f5bb73790> is not JSON serializable
            pickle.dump(topics, fp, -1)
    print u'done'