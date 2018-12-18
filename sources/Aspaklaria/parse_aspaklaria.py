#encoding=utf-8

import django
django.setup()

from sefaria.model import *
from bs4 import BeautifulSoup, element
from sources.functions import *
import string
import unicodecsv as csv
import json
import pickle

def bs_read(fileName):
    with codecs.open(fileName, encoding='utf-8') as f:
        file_content = f.read()

    content = BeautifulSoup(file_content, "lxml")
    headWord = clean_txt(content.findAll('h1')[0].text)
    t = Topic(headWord)
    b = BookCit(u'before')
    wait = True
    for tag in content.findAll():
        if tag.name != 'h1' and wait:
            wait = True
            continue
        wait = False
        if tag.name == 'h2':
            t.citationsBb.append(b)
            b = BookCit(clean_txt(tag.text))
        else:
            txt = clean_txt(tag.text)
            b.cit_list.append(txt)
    t.citationsBb.append(b)

    tanakh = []
    if t.citationsBb[0].author == 'before':
        for ic, c in enumerate(t.citationsBb[0].cit_list):
            if c == t.headWord:
                pass
            elif re.search(u'ראה', c) and re.search(u':', c):
                txt_split = c.split(':')
                see = re.sub(u"[\(\)]", u'', txt_split[1]).split(u',')
                t.see = [re.sub(re.escape(string.punctuation), u'', s) for s in see]
                # t.see = [re.sub(, u'', s) for s in see]
            else:
                tanakh.append(c)
    t.citationsBb.pop(0)
    if tanakh and t.citationsBb:
        t.citationsBb[0] = BookCit(u'Tanakh')
        t.citationsBb[0].cit_list = tanakh

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

    if topic.citationsBb:
        for citbook in topic.citationsBb:
            citbook.create_sources()
            pass
        pass



class BookCit(object):

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
        self.citationsBb = [] # list of BookCits
        self.see = None
        self.altTitles = None


class Source(object):

    def __init__(self, text, author):
        self.text = text
        self.author = author
        # self.index = library.get_index(self.author) if library.get_index(self.author) else None # needs to go into a try catch "sefaria.system.exceptions.BookNameError"
        self.raw_ref = None
        self.ref = None
        self.extract_raw_ref()
        self.get_ref_from_api()

    def extract_raw_ref(self):
        if re.search(u'\(.*?\)$', self.text):
            self.raw_ref = RawRef(re.search(u'(\([^)]*?\)$)',self.text).group(1), self.author)
        else:
            pass

    def get_ref_from_api(self):

        def clean_raw(st):
            he_parashah_array = [u"בראשית", u"נח", u"לך לך", u"וירא", u"חיי שרה", u"תולדות", u"ויצא", u"וישלח", u"וישב", u"מקץ", u"ויגש", u"ויחי", u"שמות", u"וארא", u"בא", u"בשלח", u"יתרו", u"משפטים", u"תרומה", u"תצוה", u"כי תשא", u"ויקהל", u"פקודי", u"ויקרא", u"צו", u"שמיני", u"תזריע", u"מצורע", u"אחרי מות", u"קדושים", u"אמור", u"בהר", u"בחוקתי", u"במדבר", u"נשא", u"בהעלותך", u"שלח", u"קרח", u"חקת", u"בלק", u"פנחס", u"מטות", u"מסעי", u"דברים", u"ואתחנן", u"עקב", u"ראה", u"שופטים", u"כי תצא", u"כי תבוא", u"נצבים", u"וילך", u"האזינו", u"וזאת הברכה"]
            for s in [u"מאמר", u"פרק"]:
                st = re.sub(s, u"", st)
            if self.author == u"משנה תורה":
                st = u" הלכות" + st
            elif self.author == u"ספר החינוך":
                for s in he_parashah_array:
                    st = re.sub(s, u"", st)
                    st = re.sub(u"מצוה", u"", st)
            return st

        if self.raw_ref:
            new_ref = u"(" + self.author + u", " + re.sub(u"[)(]", u"", self.raw_ref.rawText) + u")"
            print self.raw_ref.rawText,'\n', new_ref
            refs = library.get_refs_in_string(new_ref)
            if refs:
                assert len(refs) == 1
                self.ref = refs[0]
                print self.ref
            else:
                if re.search(u"^\(שם", self.raw_ref.rawText):
                    print u"*** is a Sham"
                else:
                    cleaned = clean_raw(new_ref)
                    print u"*** try new ref, new_ref = {}".format(cleaned)
                    print library.get_refs_in_string(new_ref)

class RawRef(object):

    def __init__(self, st, author):
        self.rawText = st
        self.author = author
        self.book = None
        self.section_level = None
        self.segment_level = None


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
    for file in os.listdir(u"/home/shanee/www/Sefaria-Data/sources/Aspaklaria/pickle_files/"):
        with codecs.open(u"/home/shanee/www/Sefaria-Data/sources/Aspaklaria/pickle_files/{}".format(file), "rb") as fp:
            topics = pickle.load(fp)
            for t in topics.values():
                parse_refs(t)
                pass
    print u'done'