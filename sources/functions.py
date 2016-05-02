# -*- coding: utf-8 -*-
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json 
import pdb
import os
import sys
import re
p = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, p)
from local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud
from sefaria.utils.util import replace_using_regex as reg_replace


gematria = {}
gematria['א'] = 1
gematria['ב'] = 2
gematria['ג'] = 3
gematria['ד'] = 4
gematria['ה'] = 5
gematria['ו'] = 6
gematria['ז'] = 7
gematria['ח'] = 8
gematria['ט'] = 9
gematria['י'] = 10
gematria['כ'] = 20
gematria['ל'] = 30
gematria['מ'] = 40
gematria['נ'] = 50
gematria['ס'] = 60
gematria['ע'] = 70
gematria['פ'] = 80
gematria['צ'] = 90
gematria['ק'] = 100
gematria['ר'] = 200
gematria['ש'] = 300
gematria['ת'] = 400


inv_gematria = {}
for key in gematria.keys():
    inv_gematria[gematria[key]] = key

heb_parshiot = [u"בראשית",u"נח", u"לך לך", u"וירא", u"חיי שרה", u"תולדות", u"ויצא", u"וישלח", u"וישב", u"מקץ",
u"ויגש", u"ויחי", u"שמות", u"וארא", u"בא", u"בשלח", u"יתרו", u"משפטים", u"תרומה", u"תצוה", u"כי תשא",
u"ויקהל", u"פקודי", u"ויקרא", u"צו", u"שמיני", u"תזריע", u"מצרע", u"אחרי מות", u"קדשים", u"אמר", u"בהר",
u"בחקתי", u"במדבר", u"נשא", u"בהעלתך", u"שלח לך", u"קרח", u"חקת", u"בלק", u"פינחס", u"מטות", 
u"מסעי", u"דברים", u"ואתחנן", u"עקב", u"ראה", u"שפטים", u"כי תצא", u"כי תבוא", u"נצבים",
u"וילך", u"האזינו", u"וזאת הברכה"]

eng_parshiot = ["Bereishit", "Noach", "Lech Lecha", "Vayera", "Chayei Sara", "Toldot", "Vayetzei", "Vayishlach",
"Vayeshev", "Miketz", "Vayigash", "Vayechi", "Shemot", "Vaera", "Bo", "Beshalach", "Yitro",
"Mishpatim", "Terumah", "Tetzaveh", "Ki Tisa", "Vayakhel", "Pekudei", "Vayikra", "Tzav", "Shmini",
"Tazria", "Metzora", "Achrei Mot", "Kedoshim", "Emor", "Behar", "Bechukotai", "Bamidbar", "Nasso",
"Beha'alotcha", "Sh'lach", "Korach", "Chukat", "Balak", "Pinchas", "Matot", "Masei",
"Devarim", "Vaetchanan", "Eikev", "Re'eh", "Shoftim", "Ki Teitzei", "Ki Tavo", "Nitzavim", "Vayeilech", "Ha'Azinu",
"V'Zot HaBerachah"]


def wordHasNekudot(word):
    data = word.decode('utf-8')
    data = data.replace(u"\u05B0", "")
    data = data.replace(u"\u05B1", "")
    data = data.replace(u"\u05B2", "")
    data = data.replace(u"\u05B3", "")
    data = data.replace(u"\u05B4", "")
    data = data.replace(u"\u05B5", "")
    data = data.replace(u"\u05B6", "")
    data = data.replace(u"\u05B7", "")
    data = data.replace(u"\u05B8", "")
    data = data.replace(u"\u05B9", "")
    data = data.replace(u"\u05BB", "")
    data = data.replace(u"\u05BC", "")
    data = data.replace(u"\u05BD", "")
    data = data.replace(u"\u05BF", "")
    data = data.replace(u"\u05C1", "")
    data = data.replace(u"\u05C2", "")
    data = data.replace(u"\u05C3", "")
    data = data.replace(u"\u05C4", "")
    return data != word.decode('utf-8')

def getHebrewParsha(eng_parsha):
    count=0
    eng_parsha = eng_parsha.replace("’", "'")
    for this_parsha in eng_parshiot:
        this_parsha = this_parsha.replace("’", "'")
        if this_parsha==eng_parsha:
            return heb_parshiot[count]
        count+=1


def removeAllStrings(array, orig_string):	
    for unwanted_string in array:
        orig_string = orig_string.replace(unwanted_string, "")
    return orig_string

def convertDictToArray(dict, empty=[]):
    array = []
    count = 1
    text_array = []
    sorted_keys = sorted(dict.keys())
    for key in sorted_keys:
        if count == key:
            array.append(dict[key])
            count+=1
        else:
            diff = key - count
            while(diff>0):
                array.append(empty)
                diff-=1
            array.append(dict[key])
            count = key+1
    return array

def compileCommentaryIntoPage(title, daf):
    page = []
    next = title+" "+AddressTalmud.toStr("en", daf)+".1"
    while next is not None and next.find(AddressTalmud.toStr("en", daf)) >= 0:
        text = get_text_plus(next)
        for line in text['he']:
            page.append(line)

        next = text['next']
    return page

def lookForLineInCommentary(title, daf, line_n):
    total_count = 0
    next = title+" "+AddressTalmud.toStr("en", daf)+":1"
    while next.find(AddressTalmud.toStr("en", daf)) >= 0:
        text = get_text_plus(next)
        local_count = 0
        for line in text['he']:
            local_count+=1
            total_count+=1
            if total_count == line_n:
                return next+"."+str(local_count)
        next = text['next']
    return ""

def onlyOne(text, subset):
    if text.find(subset)>=0 and text.find(subset)==text.rfind(subset):
        return True
    return False

def checkLengthsDicts(x_dict, y_dict):
    for daf in x_dict:
        if len(x_dict[daf]) != len(y_dict[daf]):
            print "lengths off"
            pdb.set_trace()

errors = open('errors.html', 'w')
def post_index(index):
    url = SEFARIA_SERVER+'/api/v2/raw/index/' + index["title"].replace(" ", "_")
    indexJSON = json.dumps(index)
    values = {
        'json': indexJSON,
        'apikey': API_KEY
    }
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        print response.read()
    except HTTPError as e:
        errors.write(e.read())
        print "error"


def hasTags(comment):
    num_tag = re.compile('\d+')
    words = comment.split(" ")
    for word in words:
        if num_tag.match(word):
            return True
    return False

def post_link(info):
    url = SEFARIA_SERVER+'/api/links/'
    infoJSON = json.dumps(info)
    values = {
        'json': infoJSON,
        'apikey': API_KEY
    }
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        x= response.read()
        print x
        if x.find("error")>=0 and x.find("Daf")>=0 and x.find("0")>=0:
            return "error"

    except HTTPError, e:
        print 'Error code: ', e.code


def post_link_weak_connection(info, repeat=10):
    url = SEFARIA_SERVER + '/api/links/'
    infoJSON = json.dumps(info)
    values = {
        'json': infoJSON,
        'apikey': API_KEY
    }
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    for i in range(repeat):
        try:
            response = urllib2.urlopen(req, timeout=20)
            x = response.getcode()
            print x

            if x == 200:
                break
        except HTTPError, e:
            errors.write(e.read())
            continue
        except Exception, e:
            print 'Exception {}'.format(i + 1)
            continue
    else:
        print 'too many errors'
        sys.exit(1)

def post_text(ref, text, index_count="off"):
    textJSON = json.dumps(text)
    ref = ref.replace(" ", "_")
    if index_count == "off":
        url = SEFARIA_SERVER+'/api/texts/'+ref
    else:
        url = SEFARIA_SERVER+'/api/texts/'+ref+'?count_after=1'
    values = {'json': textJSON, 'apikey': API_KEY}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req,)
        x = response.read()
        print x
        if x.find("error")>=0 and x.find("Daf")>=0 and x.find("0")>=0:
            return "error"
    except HTTPError, e:
        errors.write(e.read())


def post_text_weak_connection(ref, text, index_count="off", repeat=10):
    """
    use for weak connection. will make multiple (default:10) attempts to make an API call.
    """
    textJSON = json.dumps(text)
    ref = ref.replace(" ", "_")
    if index_count == "off":
        url = SEFARIA_SERVER + '/api/texts/' + ref
    else:
        url = SEFARIA_SERVER + '/api/texts/' + ref + '?count_after=1'
    values = {'json': textJSON, 'apikey': API_KEY}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    for i in range(repeat):
        try:
            response = urllib2.urlopen(req, timeout=15)
            code = response.getcode()
            print code

            if code == 200:
                break
        except HTTPError, e:
            errors.write(e.read())
            continue
        except Exception, e:
            print 'Exception {}'.format(i+1)
            continue
    else:
        print 'too many errors'
        sys.exit(1)


def post_text_burp(ref, text, index_count="off"):
    """
    Use to debug with burp suite
    """
    proxy = urllib2.ProxyHandler({'http': '127.0.0.1:8080'})
    opener = urllib2.build_opener(proxy)

    textJSON = json.dumps(text)
    ref = ref.replace(" ", "_")
    if index_count == "off":
        url = SEFARIA_SERVER + '/api/texts/' + ref
    else:
        url = SEFARIA_SERVER + '/api/texts/' + ref + '?count_after=1'
    values = {'json': textJSON, 'apikey': API_KEY}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = opener.open(req)
        x = response.read()
        print x
        if x.find("error") >= 0 and x.find("Daf") >= 0 and x.find("0") >= 0:
            return "error"
    except HTTPError, e:
        errors.write(e.read())

def post_flags(version, flags):
    """
    Update flags of a specific version.

    :param version: Dictionary with fields: ref, lang(en or he), vtitle(version title)
    :param flags: Dictionary with flags set as key: value pairs.
    """
    textJSON = json.dumps(flags)
    version['ref'] = version['ref'].replace(' ', '_')
    url = SEFARIA_SERVER+'/api/version/flags/{}/{}/{}'.format(
        urllib.quote(version['ref']), urllib.quote(version['lang']), urllib.quote(version['vtitle'])
    )
    values = {'json': textJSON, 'apikey': API_KEY}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        x = response.read()
        print x
        if x.find("error") >= 0 and x.find("Daf") >= 0 and x.find("0") >= 0:
            return "error"
    except HTTPError, e:
        errors.write(e.read())

def get_text(ref):
    ref = ref.replace(" ", "_")
    url = 'http://www.sefaria.org/api/texts/'+ref
    req = urllib2.Request(url)
    try:
        response = urllib2.urlopen(req)
        data = json.load(response)
        for i, temp_text in enumerate(data['he']):      
            data['he'][i] = data['he'][i].replace(u"\u05B0", "")
            data['he'][i] = data['he'][i].replace(u"\u05B1", "")
            data['he'][i] = data['he'][i].replace(u"\u05B2", "")
            data['he'][i] = data['he'][i].replace(u"\u05B3", "")
            data['he'][i] = data['he'][i].replace(u"\u05B4", "")
            data['he'][i] = data['he'][i].replace(u"\u05B5", "")
            data['he'][i] = data['he'][i].replace(u"\u05B6", "")
            data['he'][i] = data['he'][i].replace(u"\u05B7", "")
            data['he'][i] = data['he'][i].replace(u"\u05B8", "")
            data['he'][i] = data['he'][i].replace(u"\u05B9", "")
            data['he'][i] = data['he'][i].replace(u"\u05BB", "")
            data['he'][i] = data['he'][i].replace(u"\u05BC", "")
            data['he'][i] = data['he'][i].replace(u"\u05BD", "")
            data['he'][i] = data['he'][i].replace(u"\u05BF", "")
            data['he'][i] = data['he'][i].replace(u"\u05C1", "")
            data['he'][i] = data['he'][i].replace(u"\u05C2", "")
            data['he'][i] = data['he'][i].replace(u"\u05C3", "")
            data['he'][i] = data['he'][i].replace(u"\u05C4", "")
        return data['he']
    except:
        print 'Error'

def get_text_plus(ref):
    ref = Ref(ref).url()
    url = 'http://www.sefaria.org/api/texts/'+ref
    req = urllib2.Request(url)
    try:
        response = urllib2.urlopen(req)
        data = json.load(response)
        for i, temp_text in enumerate(data['he']):      
            data['he'][i] = data['he'][i].replace(u"\u05B0", "")
            data['he'][i] = data['he'][i].replace(u"\u05B1", "")
            data['he'][i] = data['he'][i].replace(u"\u05B2", "")
            data['he'][i] = data['he'][i].replace(u"\u05B3", "")
            data['he'][i] = data['he'][i].replace(u"\u05B4", "")
            data['he'][i] = data['he'][i].replace(u"\u05B5", "")
            data['he'][i] = data['he'][i].replace(u"\u05B6", "")
            data['he'][i] = data['he'][i].replace(u"\u05B7", "")
            data['he'][i] = data['he'][i].replace(u"\u05B8", "")
            data['he'][i] = data['he'][i].replace(u"\u05B9", "")
            data['he'][i] = data['he'][i].replace(u"\u05BB", "")
            data['he'][i] = data['he'][i].replace(u"\u05BC", "")
            data['he'][i] = data['he'][i].replace(u"\u05BD", "")
            data['he'][i] = data['he'][i].replace(u"\u05BF", "")
            data['he'][i] = data['he'][i].replace(u"\u05C1", "")
            data['he'][i] = data['he'][i].replace(u"\u05C2", "")
            data['he'][i] = data['he'][i].replace(u"\u05C3", "")
            data['he'][i] = data['he'][i].replace(u"\u05C4", "")
        return data
    except:
        print 'Error'


def isGematria(txt):
    txt = txt.replace('.','')
    if txt.find("ך")>=0:
        txt = txt.replace("ך", "כ")
    if txt.find("ם")>=0:
        txt = txt.replace("ם", "מ")
    if txt.find("ף")>=0:
        txt = txt.replace("ף", "פ")
    if txt.find("ץ")>=0:
        txt = txt.replace("ץ", "צ")
    if txt.find("טו")>=0:
        txt = txt.replace("טו", "יה")
    if txt.find("טז")>=0:
        txt = txt.replace("טז", "יו")
    if len(txt) == 2:
        letter_count = 0
        for i in range(9):
            if inv_gematria[i+1]==txt[letter_count:2+letter_count]:
                return True
            if inv_gematria[(i+1)*10]==txt[letter_count:2+letter_count]:
                return True
        for i in range(4):
            if inv_gematria[(i+1)*100]==txt[letter_count:2+letter_count]:
                return True
    elif len(txt) == 4:
      first_letter_is = ""
      for letter_count in range(2):
        letter_count *= 2
        for i in range(9):
            if inv_gematria[i+1]==txt[letter_count:2+letter_count]:
                if letter_count == 0:
                    #print "single false"
                    return False
                else:
                    first_letter_is = "singles"
            if inv_gematria[(i+1)*10]==txt[letter_count:2+letter_count]:
                if letter_count == 0:
                    first_letter_is = "tens"
                elif letter_count == 2:
                    if first_letter_is != "hundred":
                        #print "tens false"
                        return False
        for i in range(4):
            if inv_gematria[(i+1)*100]==txt[letter_count:2+letter_count]:
                if letter_count == 0:
                    first_letter_is = "hundred"
                elif letter_count == 2:
                    if txt[0:2] != 'ת':
                        #print "hundreds false, no taf"
                        return False
    elif len(txt) == 6:
        #rules: first and second letter can't be singles
        #first letter must be hundreds
        #second letter can be hundreds or tens
        #third letter must be singles
        for letter_count in range(3):
            letter_count *= 2
            for i in range(9):
                if inv_gematria[i+1]==txt[letter_count:2+letter_count]:
                    if letter_count != 4:
                    #	print "3 length singles false"
                        return False
                    if letter_count == 0:
                        first_letter_is = "singles"
                if inv_gematria[(i+1)*10]==txt[letter_count:2+letter_count]:
                    if letter_count == 0:
                        #print "3 length tens false, can't be first"
                        return False
                    elif letter_count == 2:
                        if first_letter_is != "hundred":
                        #	print "3 length tens false because first letter not 100s"
                            return False
                    elif letter_count == 4:
                        #print "3 length tens false, can't be last"
                        return False
            for i in range(4):
                if inv_gematria[(i+1)*100]==txt[letter_count:2+letter_count]:
                    if letter_count == 0:
                        first_letter_is = "hundred"
                    elif letter_count == 2:
                        if txt[0:2] != 'ת':
                            #print "3 length hundreds false, no taf"
                            return False
    else:
        print "length of gematria is off"
        print txt
        return False
    return True

def getGematria(txt):
    index=0
    sum=0
    while index <= len(txt)-1:
        if txt[index:index+2] in gematria:
            sum += gematria[txt[index:index+2]]
        index+=1
    return sum

def numToHeb(engnum=""):
    engnum = str(engnum)
    numdig = len(engnum)
    hebnum = ""
    letters = [["" for i in range(3)] for j in range(10)]
    letters[0]=["", "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט"]
    letters[1]=["", "י", "כ", "ל", "מ", "נ", "ס", "ע", "פ", "צ"]
    letters[2]=["", "ק", "ר", "ש", "ת", "תק", "תר", "תש", "תת", "תתק"]
    if (numdig > 3):
        print "We currently can't handle numbers larger than 999"
        exit()
    for count in range(numdig):
        hebnum += letters[numdig-count-1][int(engnum[count])]
    hebnum = re.sub('יה', 'טו', hebnum)
    hebnum = re.sub('יו', 'טז', hebnum)
    hebnum = hebnum.decode('utf-8')
    return hebnum


def multiple_replace(old_string, replacement_dictionary):
    """
    Use a dictionary to make multiple replacements to a single string

    :param old_string: String to which replacements will be made
    :param replacement_dictionary: a dictionary with keys being the substrings
    to be replaced, values what they should be replaced with.
    :return: String with replacements made.
    """

    for keys, value in replacement_dictionary.iteritems():
        old_string = old_string.replace(keys, value)

    return old_string


def find_discrepancies(book_list, version_title, file_buffer, language, middle=False):
    """
    Prints all cases in which the number of verses in a text version doesn't match the
    number in the canonical version.

    *** Only works for Tanach, can be modified to work for any level 2 text***

    :param book_list: list of books
    :param version_title: Version title to be examined
    :param file_buffer: Buffer for file to print results
    :param language: 'en' or 'he' accordingly
    :param middle: set to True to manually start scanning a book from the middle.
    If middle is set to True, user will be prompted for the beginning chapter.
    """

    # loop through each book
    for book in book_list:

        # print book to give user update on progress
        print book
        book = book.replace(' ', '_')
        book = book.replace('\n', '')

        if middle:

            print "Start {0} at chapter: ".format(book)
            start_chapter = input()
            url = SEFARIA_SERVER + 'api/texts/' + book + '.' + \
                str(start_chapter) + '/' + language + '/' + version_title

        else:
            url = SEFARIA_SERVER + 'api/texts/' + book + '.1/' + language + '/' + version_title

        try:
            # get first chapter in book
            response = urllib2.urlopen(url)
            version_text = json.load(response)

            # loop through chapters
            chapters = Ref(book).all_subrefs()

            # check for correct number of chapters
            if len(chapters) != version_text['lengths'][0]:
                file_buffer.write('Chapter Problem in'+book+'\n')

            for index, chapter in enumerate(chapters):

                # if starting in the middle skip to appropriate chapter
                if middle:
                    if index+1 != start_chapter:
                        continue

                    else:
                        # set middle back to false
                        middle = False

                print index+1,

                # get canonical number of verses
                canon = len(TextChunk(chapter, vtitle=u'Tanach with Text Only', lang='he').text)

                # get number of verses in version
                verses = len(version_text['text'])
                if verses != canon:
                    file_buffer.write(chapter.normal() + '\n')

                # get next chapter
                next_chapter = reg_replace(' \d', version_text['next'], ' ', '.')
                next_chapter = next_chapter.replace(' ', '_')
                url = SEFARIA_SERVER+'api/texts/'+next_chapter+'/'+language+'/'+version_title
                response = urllib2.urlopen(url)
                version_text = json.load(response)

        except (URLError, HTTPError, KeyboardInterrupt, KeyError, ValueError) as e:
            print e
            print url
            file_buffer.close()
            sys.exit(1)


def get_daf(num):
    """
    Get the daf given the page number (i.e. num = 1, return ב_א)
    :param num: page number
    :return: string <daf>_<ammud>
    """

    if num % 2 == 1:
        num = num / 2 + 2
        return u'{}_א'.format(numToHeb(num))

    else:
        num = num / 2 + 1
        return u'{}_ב'.format(numToHeb(num))


def get_page(daf, amud):
    """
    Inverse of get_daf, enter a daf, gets page number
    :param daf: Daf number
    :param amud: a or b
    :return: Page number (i.e. get_page(2, a) = 1)
    """

    if amud == 'a':
        return 2*daf - 3
    elif amud == 'b':
        return 2*daf - 2
    else:
        print 'invalid daf number'
        return 0
