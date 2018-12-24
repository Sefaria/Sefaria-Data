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


class Parser(object):

    def __init__(self):
        self.term_dict = he_term_mapping()

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
        pass



class AuthorCit(object):

    def __init__(self, author):
        self.author = author
        self.cit_list = []
        self.sources = []

    def create_sources(self):
        for cit in self.cit_list:
            s = Source(cit, self.author)
            self.sources.append(s)



class Topic(object):

    def __init__(self, headWord):
        self.headWord = headWord
        self.all_a_citations = [] # list of BookCits
        self.see = None
        self.altTitles = None


class Source(object):
    cnt = 0
    cnt_sham = 0
    cnt_resolved = 0
    cnt_not_found = 0

    def __init__(self, text, author):
        self.text = text
        self.author = author
        self.index = None
        self.cat = None
        self.raw_ref = None
        self.ref = None

        self.extract_raw_ref()
        self.get_ref_from_api()

    def extract_raw_ref(self):
        if re.search(u'(\([^)]*?\)$)', self.text):
            self.raw_ref = RawRef(re.search(u'(\([^)]*?\)$)',self.text).group(1), self.author)
        else:
            pass

    def extract_cat(self):
        # library.get_index(self.author) if library.get_index(self.author) else None # needs to go into a try catch "sefaria.system.exceptions.BookNameError"
        try:
            self.index = library.get_index(self.author.replace(u"", u""))
        except exceptions.BookNameError as e: #sefaria.system.exceptions.
            #todo: check if it is part of an index. maybe a category?
            # found_term = None
            try:
                found_term = parser.term_dict[self.author.replace(u"", u"")]
                if not found_term:
                    found_term = parser.term_dict[(re.sub(u'^[משהוכלב]', u'', self.author.replace(u"", u"")))]
            except KeyError as e:
                for word in self.author.split():
                    found_term = parser.term_dict.get(word.replace(u'"', u""))
                    if not found_term:
                        found_term = parser.term_dict.get(re.sub(u'(^[משהוכלב]|")', u'', word))
            if found_term and found_term in library.get_text_categories():
                self.cat = found_term
            lookhere = library.get_indexes_in_category(self.cat, include_dependant=True, full_records=True).array()
            return lookhere
            #might need to use Terms to make lookup the category in english
            # Term().load({"name": self.author})
            # filter(lambda x: x['lang'] == 'he', t.contents()['titles'])[0]['text']


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
                if len(refs) == 0:
                    print u"how is this possible?", ref_w_author, refs[0], refs[1]
                self.ref = refs[0]
                print self.ref
            else:
                if re.search(u"^\(שם", self.raw_ref.rawText):
                    self.raw_ref.is_sham = True
                    Source.cnt_sham +=1
                else:
                    cleaned = clean_raw(self.raw_ref.rawText)
                    fixed_ref = u"(" + self.author + u", " + re.sub(u"[)(]", u"", cleaned) + u")"
                    print u"*** try new ref, fixed_ref = {}".format(fixed_ref)
                    print library.get_refs_in_string(fixed_ref)
            print self.raw_ref.rawText, u'\n', ref_w_author
            Source.cnt+=1
        else: # there isn't a self.ref means we couldn't find parenthises at the end, probably a conyinuation of the prev source/ cit (in cit_list
            pass

        self.get_ref_step2()



    def get_ref_step2(self):
        """
        after get_ref_from_api() we want to call this function.
        It should discard/change wrongly caught refs, like ones caught bavli instead of Yerushalmi or mishanah instead of Tosefta.
        :return: doesn't return but changes self.ref
        """
        if self.ref and self.ref.index.title in library.get_indexes_in_category(u'Tanakh'): #  probabaly should be calculated once
            if self.author != u"תנך":
                look_here = self.extract_cat()
                if look_here:
                    # than try to get the true title from the cat from look_here
                    look_here_shared_title_word = u'({})'.format(
                        u'|'.join(list(set.intersection(*[set(x.title.split()) for x in look_here]))))
                    alt_ref_titles = map(lambda x: x['text'], self.ref.index.schema['titles'])
                    found_index = [ind for ind in look_here for tanakh_book in alt_ref_titles if
                                   tanakh_book in re.sub(look_here_shared_title_word, u'', ind.title).strip()]
                    if found_index:
                        if len(set(found_index)) > 1:  # assert len(found_index) == 0
                            print "more than one index option" # todo: problem with אלשיך דברים and with books I, II
                            print found_index[0].title, found_index[-1].title
                        self.index = found_index[0]
                        new_ref = Ref(u'{} {}'.format(self.index.title, u' '.join([unicode(x) for x in self.ref.sections])))
                        print u"deleting wrong: {} found new Index: {} new ref: {}".format(self.ref, self.index, new_ref)
                        self.ref = new_ref
                # tanakh is wrong but can't find the index ex: רש"ר הירש
                if not self.index or not new_ref:
                    print u"deleting wrong: {} couldn't find an index".format(self.ref)


                # self.try_from_ls()



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

def he_term_mapping():
    all_terms = TermSet({})
    he_titles = [[(term.get_primary_title(), x['text']) for x in term.title_group.titles if x['lang'] == 'he'] for term
                 in all_terms]
    en, he = zip(*reduce(lambda a,b: a+b, he_titles))
    he = map(lambda x: re.sub(u'"', u"", x), he)
    he_key_term_dict = dict(zip(he, en))
    return he_key_term_dict


if __name__ == "__main__":
    # parse2pickle()

    # a = dict()
    # a[u'שלום'] = 1
    # pass
    parser = Parser() #term_dict = he_term_mapping()
    # for file in os.listdir(u"/home/shanee/www/Sefaria-Data/sources/Aspaklaria/pickle_files/"):
    for file in [u'KAF.pickle', u'BET.pickle']:
        with codecs.open(u"/home/shanee/www/Sefaria-Data/sources/Aspaklaria/pickle_files/{}".format(file), "rb") as fp:
            topics = pickle.load(fp)
            for t in topics.values():
                parse_refs(t)
            print Source.cnt
            print Source.cnt_sham
            print Source.cnt_resolved
            print Source.cnt_not_found
    print u'done'