# -*- coding: utf-8 -*-
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import pdb
import os
import sys
import codecs
import re
p = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, p)
sys.path.insert(0, "../")
from local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud
from sefaria.utils.util import replace_using_regex as reg_replace
import base64

gematria = {}
gematria[u'א'] = 1
gematria[u'ב'] = 2
gematria[u'ג'] = 3
gematria[u'ד'] = 4
gematria[u'ה'] = 5
gematria[u'ו'] = 6
gematria[u'ז'] = 7
gematria[u'ח'] = 8
gematria[u'ט'] = 9
gematria[u'י'] = 10
gematria[u'כ'] = 20
gematria[u'ל'] = 30
gematria[u'מ'] = 40
gematria[u'נ'] = 50
gematria[u'ס'] = 60
gematria[u'ע'] = 70
gematria[u'פ'] = 80
gematria[u'צ'] = 90
gematria[u'ק'] = 100
gematria[u'ר'] = 200
gematria[u'ש'] = 300
gematria[u'ת'] = 400


inv_gematria = {}
for key in gematria.keys():
    inv_gematria[gematria[key]] = key

heb_parshiot = [u"בראשית",u"נח", u"לך לך", u"וירא", u"חיי שרה", u"תולדות", u"ויצא", u"וישלח", u"וישב", u"מקץ",
u"ויגש", u"ויחי", u"שמות", u"וארא", u"בא", u"בשלח", u"יתרו", u"משפטים", u"תרומה", u"תצוה", u"כי תשא",
u"ויקהל", u"פקודי", u"ויקרא", u"צו", u"שמיני", u"תזריע", u"מצרע", u"אחרי מות", u"קדשים", u"אמר", u"בהר",
u"בחקתי", u"במדבר", u"נשא", u"בהעלתך", u"שלח לך", u"קרח", u"חקת", u"בלק", u"פינחס", u"מטות",
u"מסעי", u"דברים", u"ואתחנן", u"עקב", u"ראה", u"שפטים", u"כי תצא", u"כי תבוא", u"נצבים",
u"וילך", u"האזינו", u"וזאת הברכה"]

eng_parshiot = ["Bereshit", "Noach", "Lech Lecha", "Vayera", "Chayei Sara", "Toldot", "Vayetzei", "Vayishlach",
"Vayeshev", "Miketz", "Vayigash", "Vayechi", "Shemot", "Vaera", "Bo", "Beshalach", "Yitro",
"Mishpatim", "Terumah", "Tetzaveh", "Ki Tisa", "Vayakhel", "Pekudei", "Vayikra", "Tzav", "Shmini",
"Tazria", "Metzora", "Achrei Mot", "Kedoshim", "Emor", "Behar", "Bechukotai", "Bamidbar", "Nasso",
"Beha'alotcha", "Sh'lach", "Korach", "Chukat", "Balak", "Pinchas", "Matot", "Masei",
"Devarim", "Vaetchanan", "Eikev", "Re'eh", "Shoftim", "Ki Teitzei", "Ki Tavo", "Nitzavim", "Vayeilech", "Ha'Azinu",
"V'Zot HaBerachah"]


def removeExtraSpaces(txt):
    txt = txt.replace("\xc2\xa0", " ") #make sure we only have one kind of space, get rid of unicode space
    while txt.find("  ") >= 0:          #now get rid of all double spaces
        txt = txt.replace("  ", " ")


    '''we want to make sure every end bold tag has one and only one space after it
    right now, we know that all instances have one space or zero.
    this is because we just ran code to get rid of 2 or more spaces
    so first get rid of instances of having a space so we have one case: zero spaces
    then convert all of those cases into having one space in the following line'''
    txt = txt.replace("</b> ", "</b>")
    txt = txt.replace("</b>", "</b> ")

    txt = txt.replace("( ", "(").replace(" )", ")")
    txt = txt.replace("<br> ", "<br>") #paragraphs shouldn't start with a space

    return txt

def ChetAndHey(poss_siman, siman):
    if siman - 4 == poss_siman - 8 and poss_siman % 10 == 8:
        poss_siman = poss_siman - 3
    if siman - 7 == poss_siman - 5 and poss_siman % 10 == 5:
        poss_siman = poss_siman + 3

    return poss_siman


def in_order_caller(file, reg_exp_tag, reg_exp_reset="", dont_count=[], output_file="in_order_output.txt"):
    ##open file, create an array based on reg_exp,
    ##when hit reset_tag, call in_order
    in_order_array = []
    time = 0
    output_file = open(output_file, 'a')
    for line in open(file):
        line = line.replace("\n","")
        if line.find("00") >= 0:
            time+=1
        line = line.decode('utf-8')
        line = line.replace(u"\u202a", "").replace(u"\u202c","")
        if len(line) == 0:
            continue
        if len(reg_exp_reset) > 0:
            reset = re.findall(reg_exp_reset, line)
            if len(reset) > 0:
                result = in_order(in_order_array)
                in_order_array = []
        find_all = re.findall(reg_exp_tag, line)
        if len(find_all) > 0:
          for each_one in find_all:
            in_order_array.append(each_one)
        prev_line = line
    if len(in_order_array) > 0:
        result = in_order(in_order_array)

    if result != "":
        print file
        print result
        print "\n"
        output_file.write(file.encode('utf-8')+"\n")
        output_file.write("חסר פרק "+result.encode('utf-8')+"\n\n\n")
    output_file.close()




def in_order_multiple_segments(line, curr_num, increment_by):
     if len(line) > 0 and line[0] == ' ':
         line = line[1:]
     if len(line) > 0 and line[len(line)-1] == ' ':
         line = line[:-1]
     if len(line.split(" "))>1:
         all = line.split(" ")
         num_list = []
         for i in range(len(all)):
             num_list.append(getGematria(all[i]))
         num_list = sorted(num_list)
         for poss_num in num_list:
             poss_num = fixChetHay(poss_num, curr_num)
             if poss_num < curr_num:
                 return -1
             else:
                 curr_num = poss_num
     return curr_num


def fixChetHay(poss_num, curr_num):
    if poss_num == 8 and curr_num == 4:
        return 5
    elif poss_num == 5 and curr_num == 7:
        return 8
    else:
        return poss_num


def in_order(list_tags, multiple_segments=False, dont_count=[], increment_by=1):
     poss_num = 0
     curr_num = 0
     perfect = True
     for line in list_tags:
         actual_line = line
         for word in dont_count:
            line = line.replace(word, "")
         if multiple_segments == True:
             curr_num = in_order_multiple_segments(line, curr_num, increment_by)
         else:
             poss_num = getGematria(line)
             poss_num = fixChetHay(poss_num, curr_num)
             if increment_by > 0:
                 if poss_num - curr_num != increment_by:
                     perfect = False
             if poss_num < curr_num:
                 perfect = False
             curr_num = poss_num
             if perfect == False:
                 return actual_line
             prev_line = line

     return ""


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


def getHebrewTitle(sefer, SEFARIA_SERVER='http://www.sefaria.org/'):
   sefer = sefer.title() 
   sefer_url = SEFARIA_SERVER+'api/index/'+sefer.replace(" ","_")
   req = urllib2.Request(sefer_url)
   res = urllib2.urlopen(req)
   data = json.load(res)
   return data['heTitle']


def removeAllTags(orig_string, array = ['@', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0']):
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
    ref = Ref(title+" "+AddressTalmud.toStr("en", daf)+".1")
    while ref is not None and ref.normal().find(AddressTalmud.toStr("en", daf)) >= 0:
        text = ref.text('he').text
        for line in text:
            page.append(line)
        ref = ref.next_section_ref() if ref.next_section_ref() != ref else None
    return page


def lookForLineInCommentary(title, daf, line_n):
    total_count = 0
    ref = Ref(title+" "+AddressTalmud.toStr("en", daf)+":1")
    while ref is not None and ref.normal().find(AddressTalmud.toStr("en", daf)) >= 0:
        text = ref.text('he').text
        local_count = 0
        for line in text:
            local_count+=1
            total_count+=1
            if total_count == line_n:
                return ref.normal()+"."+str(local_count)
        ref = ref.next_section_ref() if ref.next_section_ref() != ref else None
    return ""


def onlyOne(text, subset):
    if text.find(subset)>=0 and text.find(subset)==text.rfind(subset):
        return True
    return False



def replaceBadNodeTitlesHelper(title, replaceBadNodeTitles, bad_char, good_char):
    url = SEFARIA_SERVER+'api/index/'+title.replace(" ", "_")
    req = urllib2.Request(url)
    data = json.load(urllib2.urlopen(req))
    replaceBadNodeTitles(bad_char, good_char, data)
    post_index(data)


def checkLengthsDicts(x_dict, y_dict):
    for daf in x_dict:
        if len(x_dict[daf]) != len(y_dict[daf]):
            print "lengths off"
            pdb.set_trace()


def weak_connection(func):
    def post_weak_connection(*args, **kwargs):
        success = False
        weak_network = kwargs.pop('weak_network', False)
        num_tries = kwargs.pop('num_tries', 3)
        if weak_network:
            for i in range(num_tries-1):
                try:
                    func(*args, **kwargs)
                except (HTTPError, URLError) as e:
                    print 'handling weak network'
                else:
                    success = True
                    break
        if not success:
            func(*args, **kwargs)
    return post_weak_connection


@weak_connection
def post_index(index, server=SEFARIA_SERVER):
    url = server+'/api/v2/raw/index/' + index["title"].replace(" ", "_")
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
        with open('errors.html', 'w') as errors:
            errors.write(e.read())
        print "error"


def hasTags(comment):
    mod_comment = removeAllStrings(comment)
    return mod_comment != comment 


@weak_connection
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
            with open('errors.html', 'w') as errors:
                errors.write(e.read())
            continue
        except Exception, e:
            print 'Exception {}'.format(i + 1)
            continue
    else:
        print 'too many errors'
        sys.exit(1)


@weak_connection
def post_text(ref, text, index_count="off", skip_links=False, server=SEFARIA_SERVER):
    textJSON = json.dumps(text)
    ref = ref.replace(" ", "_")
    if index_count == "off":
        url = server+'/api/texts/'+ref
    else:
        url = server+'/api/texts/'+ref+'?count_after=1'
    if skip_links:
        url += '&skip_links={}'.format(skip_links)
    values = {'json': textJSON, 'apikey': API_KEY}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        x= response.read()
        print x
        if x.find("error")>=0 and x.find("Daf")>=0 and x.find("0")>=0:
            return "error"
    except HTTPError, e:
        with open('errors.html', 'w') as errors:
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
            with open('errors.html', 'w') as errors:
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
        with open('errors.html', 'w') as errors:
            errors.write(e.read())


@weak_connection
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
        with open('errors.html', 'w') as errors:
            errors.write(e.read())


@weak_connection
def post_term(term_dict, server=SEFARIA_SERVER):
    name = term_dict['name']
    term_JSON = json.dumps(term_dict)
    url = '{}/api/terms/{}'.format(server, urllib.quote(name))
    values = {'json': term_JSON, 'apikey': API_KEY}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        x = response.read()
        print x
    except (HTTPError, URLError) as e:
        print e

def get_index(ref, server='http://www.sefaria.org'):
    ref = ref.replace(" ", "_")
    url = server+'/api/v2/raw/index/'+ref
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    data = json.load(response)
    return data


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

def get_text_plus(ref, SERVER='www'):
    #ref = Ref(ref).url()
    url = 'http://'+SERVER+'.sefaria.org/api/texts/'+ref.replace(" ","_")+'?commentary=0&context=0&pad=0'
    req = urllib2.Request(url)
    try:
        response = urllib2.urlopen(req)
        data = json.load(response)
        return data
    except HTTPError as e:
        pdb.set_trace()

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
    if not isinstance(txt, unicode):
        txt = txt.decode('utf-8')
    txt = txt.replace(u"ך", u"כ").replace(u"ץ", u"צ")
    index=0
    sum=0
    while index <= len(txt)-1:
        if txt[index:index+1] in gematria:
            sum += gematria[txt[index:index+1]]

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
            url = SEFARIA_SERVER + '/api/texts/' + book + '.' + \
                str(start_chapter) + '/' + language + '/' + version_title

        else:
            url = SEFARIA_SERVER + '/api/texts/' + book + '.1/' + language + '/' + version_title


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
                url = SEFARIA_SERVER+'/api/texts/'+next_chapter+'/'+language+'/'+version_title

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
