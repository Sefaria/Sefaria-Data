# -*- coding: utf-8 -*-

import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import requests
import pdb
import os
import sys
import codecs
import re
p = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, p)
sys.path.insert(0, "../")
from local_settings import *
import django
django.setup()
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud
from data_utilities.dibur_hamatchil_matcher import match_ref
from sefaria.utils.util import replace_using_regex as reg_replace
import base64
import enchant
import Levenshtein

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

from lxml.html import fromstring

def create_intro():
    intro = JaggedArrayNode()
    intro.add_structure(["Paragraph"])
    intro.add_shared_term("Introduction")
    intro.key = "intro"
    intro.validate()
    return intro

def any_hebrew_in_str(line):
    '''
    Returns true if there is one Hebrew character in line.
    Useful for when a bad encoding yields nonsense amidst Hebrew text
    or when a segment has both English and Hebrew words.
    :param line:
    :return:
    '''
    is_hebrew = False
    for i in range(len(line)):
        char = line[i: i + 2]
        try:
            char = char.decode('utf-8')
            any_hebrew = re.findall(u"[\u0591-\u05EA]", char)
            is_hebrew = any_hebrew != []
            if is_hebrew:
                return True
        except UnicodeDecodeError:
            pass
    return False

def any_english_in_str(line):
    return re.findall("[a-zA-Z0-9]{1}", line) != []

def is_english_word(line):
    if any_english_in_str(line):
        eng_dictionary = enchant.Dict("en_US")
        return eng_dictionary.check(line)
    return False

def create_simple_index_commentary(en_title, he_title, base_title, categories, type="many_to_one", server=SEFARIA_SERVER):
    '''
    Returns a JSON index object for a simple Index that is a Commentary.
    :param en_title: Name of commentary in English
    :param he_title: Name in Hebrew
    :param base_title: Name of text being commented on.
    :param type: "many_to_one" or "one_to_one".
    :param categories: Array such as ["Tanakh", "Commentary", "Rashi", "Writings", "Psalms"]
    :return:
    '''
    base_index = library.get_index(base_title)
    root = JaggedArrayNode()
    full_title = "{} on {}".format(en_title, base_title)
    he_base_title = base_index.get_title('he')
    he_full_title = u"{} על {}".format(he_title, he_base_title)
    root.add_primary_titles(full_title, he_full_title)
    structure = base_index.nodes.sectionNames #this mimics the structure as "one_to_one"
    if type == "many_to_one":
        structure.append("Comment")
    root.add_structure(structure)

    index = {
        "title": full_title,
        "schema": root.serialize(),
        "collective_title": en_title,
        "categories": categories,
        "dependence": "Commentary",
        "base_text_titles": [base_title],
        "base_text_mapping": type,
    }
    post_index(index, server=server)


def create_complex_index_torah_commentary(en_title, he_title, intro_structure=["Paragraph"], server=SEFARIA_SERVER):
    '''
    Creates a complex index commentary on the Torah.
    :param en_title: English name of commentator
    :param he_title: Hebrew name of commentator
    :param intro_structure: if None, there is no intro.  Otherwise the first JA node is an introduction with section
    names derived from this parameter
    :param server: server to post to
    :return:
    '''
    path = ["Tanakh", "Commentary", en_title]
    root = SchemaNode()
    full_title = "{} on Torah".format(en_title)
    he_full_title = u"{} על תורה".format(he_title)
    root.add_primary_titles(full_title, he_full_title)
    root.key = en_title

    if intro_structure:
        node = JaggedArrayNode()
        node.add_structure(intro_structure)
        node.add_shared_term("Introduction")
        node.key = "intro"
        root.append(node)

    for book in library.get_indexes_in_category("Torah"):
        node = JaggedArrayNode()
        node.add_primary_titles(book, library.get_index(book).get_title('he'))
        node.add_structure(["Chapter", "Paragraph", "Comment"])
        root.append(node)

    root.validate()
    post_index({
        "title": full_title,
        "schema": root.serialize(),
        "categories": path
    }, server=server)





def find_almost_identical(str1, array_of_strings, ratio=0.7):
    '''
    Try to find a string in array_of_strings that matches str1 at least as much as ratio.
    Returns the best match that is at least as much as ratio.
    Otherwise, return None
    '''
    best_str = None
    best_match = 0
    matches = []
    for str2 in array_of_strings:
        temp_ratio = Levenshtein.ratio(str1, str2)
        if temp_ratio >= ratio:
            matches.append(str2)
    if len(matches) == 1:
        return matches[0]
    else:
        return matches


def perek_to_number(perek_num):
    '''
    Example: Input is "ראשון" and return is 1
    :param perek_num:
    :return:
    '''
    line = u"""  פרק ראשון   פרק שני   פרק שלישי   פרק רביעי   פרק חמישי   פרק ששי   פרק שביעי   פרק שמיני   פרק תשיעי   פרק עשירי   פרק אחד עשר   פרק שנים עשר   פרק שלשה עשר   פרק ארבעה עשר   פרק חמשה עשר   פרק ששה עשר   פרק שבעה עשר   פרק שמונה עשר   פרק תשעה עשר   פרק עשרים   פרק אחד ועשרים   פרק שנים ועשרים   פרק שלשה ועשרים   פרק ארבעה ועשרים   פרק חמשה ועשרים   פרק ששה ועשרים   פרק שבעה ועשרים   פרק שמונה ועשרים   פרק תשעה ועשרים   פרק שלשים"""
    line = line.replace("\n", "")
    perek_num = perek_num.replace(u"פרק ", u"")
    line = line.split(u" פרק")[1:]
    arr_nums = []
    poss_num = 0
    line = [el[1:-1] for el in line]
    result = find_almost_identical(perek_num, line, ratio=0.85)
    if result:
        return line.index(result) + 1
    else:
        print u"Not supporting {} yet".format(perek_num)
        return u"Not supporting {} yet".format(perek_num)



def removeExtraSpaces(txt, unicode=False):
    txt = txt.replace("\xc2\xa0", " ").replace("\xe2\x80\x83", "")#make sure we only have one kind of space, get rid of unicode space
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
    if poss_siman == 20 and siman == 1:
        return 2

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
    if poss_num == 20 and curr_num == 1:
        return 2
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

def strip_nekud(word):
    data = word.replace(u"\u05B0", "")
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
    return data


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
            count += 1
        else:
            diff = key - count
            while(diff > 0):
                array.append(empty)
                diff -= 1
            array.append(dict[key])
            count = key + 1
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

def remove_numbers(text):
    digit_pattern = re.compile("^\d+\.")
    for count in range(len(text)):
        line = text[count]
        match = digit_pattern.match(line)
        if match:
            match = match.group(0)
            text[count] = text[count].replace(match, "")
            if text[count][0] == " ":
                text[count] = text[count][1:]
        if count == 0 and not match:
            text[0] = text[0].replace("1. ", "")
    text = remove_roman_numerals(text)
    return text


def remove_roman_numerals(text):
    for count, line in enumerate(text):
        matches = re.findall("[IXV]+\.", text[count])
        for match in matches:
            text[count] = text[count].replace(match, "")
            if text[count][0] == " ":
                text[count] = text[count][1:]
    return text


def get_rid_of_numbers(book, version_title, version_source, get_server, post_server, relevant_refs=None):
    sections = library.get_index(book).all_section_refs()
    for section in sections:
        text = get_text(section.normal(), lang="en", versionTitle=version_title, server=get_server)["text"]
        text = remove_numbers(text)
        send_text = {
            "text": text,
            "versionTitle": version_title,
            "versionSource": version_source,
            "language": 'en'
        }
        post_text(section.normal(), send_text, server=post_server)





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

def get_all_non_ascii(text):
    non = filter(lambda x: ord(x) >= 128, text)
    non_ascii_set = set()
    for each_char in non:
        non_ascii_set.add(each_char)
    return non_ascii_set

def replaceBadNodeTitlesHelper(title, replaceBadNodeTitles, bad_char, good_char):
    url = SEFARIA_SERVER+'api/index/'+title.replace(" ", "_")
    req = urllib2.Request(url)
    data = json.load(urllib2.urlopen(req))
    replaceBadNodeTitles(bad_char, good_char, data)
    post_index(data)




def checkLengthsDicts(x_dict, y_dict):
    for daf in x_dict:
        if len(x_dict[daf]) != len(y_dict[daf]):
            print "{} by {}".format(daf+1, len(x_dict[daf]) - len(y_dict[daf]))


def weak_connection(func):
    def post_weak_connection(*args, **kwargs):
        result = None
        success = False
        weak_network = kwargs.pop('weak_network', False)
        num_tries = kwargs.pop('num_tries', 3)
        if weak_network:
            for i in range(num_tries-1):
                try:
                    result = func(*args, **kwargs)
                except (HTTPError, URLError) as e:
                    print 'handling weak network'
                else:
                    success = True
                    break
        if not success:
            result = func(*args, **kwargs)
        return result
    return post_weak_connection


def http_request(url, params=None, body=None, json_payload=None, method="GET"):
    if params is None:
        params = {}
    if body is None:
        body = {}
    if json_payload:
        body['json'] = json.dumps(json_payload)  # Adds the json as a url parameter - otherwise json gets lost

    if method == "GET":
        response = requests.get(url)
    elif method == "POST":
        response = requests.post(url, params=params, data=body)
    else:
        raise ValueError("Cannot handle HTTP request method {}".format(method))

    success = True
    try:
        json_response = response.json()
        if isinstance(json_response, dict) and json_response.get("error"):
            success = False
            print u"Error: {}".format(json_response["error"])
    except ValueError:
        success = False
        json_response = ''
        with codecs.open('errors.html', 'w', 'utf-8') as outfile:
            outfile.write(response.text)

    if success:
        print u"\033[92m{} request to {} successful\033[0m".format(method, url)
        return json_response
    else:
        print u"\033[91m{} request to {} failed\033[0m".format(method, url)
        return response.text



def make_title(text):
    '''
    Takes as input a node named 'text' and capitalizes it appropriately
    :param text:
    :return:
    '''
    #first clean up text
    text = text.strip()

    #just make sure there aren't double spaces in the name or code below fails
    text = text.replace("  ", " ")
    stop_words = ["a", "the", "on", "is", "of", "in", "to", "and", "by", "or", "within", "other", "their", "who"]
    roman_letters = ["i", "v", "x", "l"]
    other_starts = ['"', "'", '(', '[']

    #capitalize first letter no matter what so add the first word to new_text because it's fine as it is
    text = text[0].upper() + text[1:].lower()
    new_text = text.split(" ")[0] + " "

    #capitalize non-stopwords
    for word in text.split(" ")[1:]:
        is_roman_numeral = filter(lambda x: x not in roman_letters, word) == ""
        if is_roman_numeral:
            new_text += word.upper() + " "
        elif word not in stop_words:
            if word[0] in other_starts:
                new_text += word[0] + word[1].upper() + word[2:] + " "
            else:
                new_text += word[0].upper() + word[1:] + " "
        else:
            new_text += word + " "

    new_text = new_text.strip()

    return new_text

@weak_connection
def post_index(index, server=SEFARIA_SERVER):
    url = server+'/api/v2/raw/index/' + index["title"].replace(" ", "_")
    return http_request(url, body={'apikey': API_KEY}, json_payload=index, method="POST")
    # indexJSON = json.dumps(index)
    # values = {
    #     'json': indexJSON,
    #     'apikey': API_KEY
    # }
    # data = urllib.urlencode(values)
    # req = urllib2.Request(url, data)
    # try:
    #     response = urllib2.urlopen(req)
    #     print response.read()
    # except HTTPError as e:
    #     with open('errors.html', 'w') as errors:
    #         errors.write(e.read())
    #     print "error"


def hasTags(comment):
    mod_comment = removeAllTags(comment)
    return mod_comment != comment
     
@weak_connection
def post_category(category_dict, server=SEFARIA_SERVER):
    url = server+'/api/category/'
    return requests.post(url, data={'apikey': API_KEY, 'json': json.dumps(category_dict)})

    
def add_category(en_title, path, he_title=None, server=SEFARIA_SERVER):
    """
    Post a category to the desired server. If a hebrew title is not supplied, this method will attempt to post a category
    using a sharedTerm. This can only work if the corresponding term is present in the local Sefaria.
    This method will attempt to upload parent categories if they are missing on destination server.
    IMPORTANT: It is not assumed that parents exist locally, therefore this method can only post parents that use a
    sharedTerm. All necessary terms must exist locally for this to work.

    :param en_title: Primary English title or sharedTitle
    :param path: path to this category
    :param he_title: Primary Hebrew title. Do not supply if a sharedTerm is to be used.
    :param server: destination server.
    :return:
    """
    # obtain data from server
    '''
    for i in range(len(path)):
        path[i] = path[i].replace(" ", "_")
    en_title = en_title.replace(" ", "_")
    '''
    response = requests.get('{}/api/category/{}'.format(server, '/'.join(path))).json()

    if response.get('error') is None:  # category already exists, exit
        print "Category already exists at {}".format(server)
        return response

    # add missing parents
    closest_parent = response['closest_parent']['lastPath']
    missing_parents = path[path.index(closest_parent)+1:-1]  # grab everything between lastParent and current category
    for parent in missing_parents:
        add_category(parent, path[:path.index(parent)+1], server=server)

    if he_title is None:  # upload using a sharedTerm
        response = requests.get('{}/api/terms/{}'.format(server, en_title)).json()  # check if term exists at destination

        if response.get('error') is not None:
            term = Term().load({'name': en_title})
            if term is None:
                raise ValueError("Attempted to post sharedTitle {} but no such Term exists".format(en_title))
            post_term(term.contents(), server=server)

        category_dict = {
            'path': path,
            'sharedTitle': en_title
        }

    else:
        category_dict = {
            'path': path,
            'titles': [
                {'lang': 'en', 'primary': True, 'text': en_title},
                {'lang': 'he', 'primary': True, 'text': he_title}
            ]
        }
    return requests.post('{}/api/category'.format(server), data={'apikey': API_KEY, 'json': json.dumps(category_dict)})


@weak_connection
def post_link(info, server=SEFARIA_SERVER, VERBOSE = False):
    url = server+'/api/links/'
    result = http_request(url, body={'apikey': API_KEY}, json_payload=info, method="POST")
    if VERBOSE:
        print result
    return result


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



def get_matches_for_dict_and_link(dh_dict, base_text_title, commentary_title, talmud=True, lang='he', word_threshold=0.27, server="", rashi_filter=None, dh_extract_method=lambda x: x):
    def base_tokenizer(str):
        str_list = str.split(" ")
        return [str for str in str_list if len(str) > 0]


    assert len(server) > 0, "Please specify a server"
    results = {}
    links = []
    matched = 0
    total = 0
    for daf in dh_dict:
        print daf
        dhs = dh_dict[daf]
        if talmud:
            base_text_ref = "{} {}".format(base_text_title, AddressTalmud.toStr("en", daf))
            comm_ref = "{} on {} {}".format(commentary_title, base_text_title, AddressTalmud.toStr("en", daf))
        else:
            base_text_ref = "{} {}".format(base_text_title, daf)
            comm_ref = "{} on {} {}".format(commentary_title, base_text_title, daf)
        base_text = TextChunk(Ref(base_text_ref), lang=lang)
        comm_text = TextChunk(Ref(comm_ref), lang=lang)
        results[daf] = match_ref(base_text, comm_text, base_tokenizer=base_tokenizer, word_threshold=word_threshold, rashi_filter=rashi_filter, dh_extract_method=dh_extract_method)["matches"]
        for count, link in enumerate(results[daf]):
            if link:
                base_end = link.normal()
                comm_end = "{} on {} {}:{}".format(commentary_title, base_text_title, AddressTalmud.toStr("en", daf), count+1)
                links.append({
                    "refs": [base_end, comm_end],
                    "auto": True,
                    "type": "commentary",
                    "generated_by": commentary_title+base_text_title
                })
                matched += 1
            total += 1
    print "Matched: {}".format(matched)
    print "Total {}".format(total)
    post_link(links, server=server)

    return results

def create_payload_and_post_text(ref, text, language, vtitle, vsource, server=SEFARIA_SERVER):
    post_text(ref, {
        "text": text,
        "language": language,
        "versionTitle": vtitle,
        "versionSource": vsource
    }, server=server)


def create_links_many_to_one(comm_ref, base_ref):
    '''
    Creates structural links between a commentary ref and a base ref in the case
    where a commentary is a complex structure and can't be linked via the index commentary linker.
    The commentary ref is assumed to be one level deeper than the base ref
    :param comm_ref: String of comm ref
    :param base_ref: String of base ref
    :return:
    '''
    links = []
    pairs_refs = []
    all_base_refs = Ref(base_ref).all_segment_refs()
    for base_ref in all_base_refs:
        base_ref = base_ref.normal()
        section = base_ref.rsplit(" ", 1)[-1]
        comm_ref_and_section = Ref("{} {}".format(comm_ref, section))
        comm_seg_refs = comm_ref_and_section.all_segment_refs()
        for comm_seg_ref in comm_seg_refs:
            pairs_refs.append([comm_seg_ref.normal(), base_ref])
    return pairs_refs


def first_word_with_period(str):
    for i in range(len(str.split(" "))):
        if str.split(" ")[i].endswith("."):
            return i
    return len(str.split(" "))

@weak_connection
def post_text(ref, text, index_count="off", skip_links=False, server=SEFARIA_SERVER):
    # textJSON = json.dumps(text)
    ref = ref.replace(" ", "_")
    url = server+'/api/texts/'+ref
    params, body = {}, {'apikey': API_KEY}
    if index_count == "on":
        params['count_after'] = 1
    if skip_links:
        params['skip_links'] = True
        # if re.search(r'\?', url):
        #     url += '&skip_links={}'.format(skip_links)
        # else:
        #     url += '?skip_links={}'.format(skip_links)

    return http_request(url, params=params, body=body, json_payload=text, method="POST")
    # values = {'json': textJSON, 'apikey': API_KEY}
    # data = urllib.urlencode(values)
    # req = urllib2.Request(url, data)
    # try:
    #     response = urllib2.urlopen(req)
    #     x= response.read()
    #     print x
    #     if x.find("error")>=0 and x.find("Daf")>=0 and x.find("0")>=0:
    #         return "error"
    # except HTTPError, e:
    #     with open('errors.html', 'w') as errors:
    #         errors.write(e.read())

def re_split_line(line, pattern):
    '''
    this function splits a string based on a regular expression pattern so that the resultant array of strings
    still has the pattern at the front of every string in the array
    :param line: the string to be split
    :param pattern: the reg exp pattern
    :return: array of strings
    '''

    #first make sure pattern is surrounded by parenthesis so that re.split will give us an array like:
    # 0: pattern
    # 1: text
    # 2: pattern
    # 3: text
    # Then make an array half the size made up of [pattern + text, pattern + text]
    if pattern[0] != '(':
        pattern = '(' + pattern
    if pattern[-1] != ')':
        pattern += ')'

    fix_pos_in_arr = 0
    lines = re.split(pattern, line)
    assert len(lines) % 2 == 1

    if lines[0] == "":
        lines = lines[1:]
        text = [""] * (len(lines) / 2)
    else:
        text = [""] * (len(lines) / 2)
        text.insert(0, lines[0])
        lines = lines[1:]
        fix_pos_in_arr = 1

    for i, line in enumerate(lines):
        pos_in_arr = int(i/2) + fix_pos_in_arr
        text[pos_in_arr] += line
    return text



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
def post_flags(version, flags, server=SEFARIA_SERVER):
    """
    Update flags of a specific version.

    :param version: Dictionary with fields: ref, lang(en or he), vtitle(version title)
    :param flags: Dictionary with flags set as key: value pairs.
    :param server: url of destination server
    """
    textJSON = json.dumps(flags)
    version['ref'] = version['ref'].replace(' ', '_')
    url = server+'/api/version/flags/{}/{}/{}'.format(
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
def post_term(term_dict, server=SEFARIA_SERVER, update=False):
    name = term_dict['name']
    # term_JSON = json.dumps(term_dict)
    url = '{}/api/terms/{}'.format(server, urllib.quote(name))
    if update:
        url += "?update=1"
    return http_request(url, body={'apikey': API_KEY}, json_payload=term_dict, method="POST")
    # values = {'json': term_JSON, 'apikey': API_KEY}
    # data = urllib.urlencode(values)
    # req = urllib2.Request(url, data)
    # try:
    #     response = urllib2.urlopen(req)
    #     x = response.read()
    #     print x
    # except (HTTPError, URLError) as e:
    #     print e


def add_term(en_title, he_title, scheme='toc_categories', server=SEFARIA_SERVER):
    term_dict = {
    'name': en_title,
    'scheme': scheme,
    'titles': [{'lang': 'en', 'text': en_title, 'primary': True}, {'lang': 'he', 'text': he_title, 'primary': True}]
    }
    post_term(term_dict, server)


def add_title_existing_term(name, title, lang="en", server=SEFARIA_SERVER):
    '''
    Used to add titles to existing terms.  TODO: flag to set new titles as primary
    :param name: Name of existing term
    :param title: Title to add to term
    :parem lang: Language of title
    :param server:
    :return:
    '''
    url = server+"/api/terms/"+name
    term = http_request(url)
    new_title = {'lang': lang, 'text': title}
    term["titles"].append(new_title)
    post_term(term, server=server, update=True)


def get_index_api(ref, server='http://www.sefaria.org'):
    ref = ref.replace(" ", "_")
    url = server+'/api/v2/raw/index/'+ref
    # req = urllib2.Request(url)
    # response = urllib2.urlopen(req)
    # data = json.load(response)
    return http_request(url)

def get_links(ref, server="http://www.sefaria.org"):
    ref = ref.replace(" ", "_")
    url = server+'/api/links/'+ref
    return http_request(url)

def get_text(ref, lang="", versionTitle="", server="http://draft.sefaria.org"):
    ref = ref.replace(" ", "_")
    versionTitle = versionTitle.replace(" ", "_")
    url = '{}/api/texts/{}'.format(server, ref)
    if lang and versionTitle:
        url += "/{}/{}".format(lang, versionTitle)
    req = urllib2.Request(url)
    try:
        response = urllib2.urlopen(req)
        data = json.load(response)
        return data
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

import csv, codecs, cStringIO

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class WordsToNumbers():
    """A class that can translate strings of common English words that
    describe a number into the number described
    """
    # a mapping of digits to their names when they appear in the
    # relative "ones" place (this list includes the 'teens' because
    # they are an odd case where numbers that might otherwise be called
    # 'ten one', 'ten two', etc. actually have their own names as single
    # digits do)
    __ones__ = {'one': 1, 'eleven': 11,
                'two': 2, 'twelve': 12,
                'three': 3, 'thirteen': 13,
                'four': 4, 'fourteen': 14,
                'five': 5, 'fifteen': 15,
                'six': 6, 'sixteen': 16,
                'seven': 7, 'seventeen': 17,
                'eight': 8, 'eighteen': 18,
                'nine': 9, 'nineteen': 19}

    # a mapping of digits to their names when they appear in the 'tens'
    # place within a number group
    __tens__ = {'ten': 10,
                'twenty': 20,
                'thirty': 30,
                'forty': 40,
                'fifty': 50,
                'sixty': 60,
                'seventy': 70,
                'eighty': 80,
                'ninety': 90}

    # an ordered list of the names assigned to number groups
    __groups__ = {'thousand': 1000,
                  'million': 1000000,
                  'billion': 1000000000,
                  'trillion': 1000000000000}

    # a regular expression that looks for number group names and captures:
    #     1-the string that preceeds the group name, and
    #     2-the group name (or an empty string if the
    #       captured value is simply the end of the string
    #       indicating the 'ones' group, which is typically
    #       not expressed)
    __groups_re__ = re.compile(
        r'\s?([\w\s]+?)(?:\s((?:%s))|$)' %
        ('|'.join(__groups__))
    )

    # a regular expression that looks within a single number group for
    # 'n hundred' and captures:
    #    1-the string that preceeds the 'hundred', and
    #    2-the string that follows the 'hundred' which can
    #      be considered to be the number indicating the
    #      group's tens- and ones-place value
    __hundreds_re__ = re.compile(r'([\w\s]+)\shundred(?:\s(.*)|$)')

    # a regular expression that looks within a single number
    # group that has already had its 'hundreds' value extracted
    # for a 'tens ones' pattern (ie. 'forty two') and captures:
    #    1-the tens
    #    2-the ones
    __tens_and_ones_re__ = re.compile(
        r'((?:%s))(?:\s(.*)|$)' %
        ('|'.join(__tens__.keys()))
    )

    def parse(self, words):
        """Parses words to the number they describe"""
        # to avoid case mismatch, everything is reduced to the lower
        # case
        words = words.lower()
        # create a list to hold the number groups as we find them within
        # the word string
        groups = {}
        # create the variable to hold the number that shall eventually
        # return to the caller
        num = 0
        # using the 'groups' expression, find all of the number group
        # an loop through them
        for group in WordsToNumbers.__groups_re__.findall(words):
            ## determine the position of this number group
            ## within the entire number
            # assume that the group index is the first/ones group
            # until it is determined that it's a higher group
            group_multiplier = 1
            if group[1] in WordsToNumbers.__groups__:
                group_multiplier = WordsToNumbers.__groups__[group[1]]
            ## determine the value of this number group
            # create the variable to hold this number group's value
            group_num = 0
            # get the hundreds for this group
            hundreds_match = WordsToNumbers.__hundreds_re__.match(group[0])
            # and create a variable to hold what's left when the
            # "hundreds" are removed (ie. the tens- and ones-place values)
            tens_and_ones = None
            # if there is a string in this group matching the 'n hundred'
            # pattern
            if hundreds_match is not None and hundreds_match.group(1) is not None:
                # multiply the 'n' value by 100 and increment this group's
                # running tally
                group_num = group_num + \
                            (WordsToNumbers.__ones__[hundreds_match.group(1)] * 100)
                # the tens- and ones-place value is whatever is left
                tens_and_ones = hundreds_match.group(2)
            else:
                # if there was no string matching the 'n hundred' pattern,
                # assume that the entire string contains only tens- and ones-
                # place values
                tens_and_ones = group[0]
            # if the 'tens and ones' string is empty, it is time to
            # move along to the next group
            if tens_and_ones is None:
                # increment the total number by the current group number, times
                # its multiplier
                num = num + (group_num * group_multiplier)
                continue
            # look for the tens and ones ('tn1' to shorten the code a bit)
            tn1_match = WordsToNumbers.__tens_and_ones_re__.match(tens_and_ones)
            # if the pattern is matched, there is a 'tens' place value
            if tn1_match is not None:
                # add the tens
                group_num = group_num + WordsToNumbers.__tens__[tn1_match.group(1)]
                # add the ones
                if tn1_match.group(2) is not None:
                    group_num = group_num + WordsToNumbers.__ones__[tn1_match.group(2)]
            else:
                # assume that the 'tens and ones' actually contained only the ones-
                # place values
                group_num = group_num + WordsToNumbers.__ones__[tens_and_ones]
            # increment the total number by the current group number, times
            # its multiplier
            num = num + (group_num * group_multiplier)
        # the loop is complete, return the result
        return num