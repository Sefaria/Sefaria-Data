# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import os
import re
import sys
import csv

from sources.functions import *
import codecs
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from linking_utilities.dibur_hamatchil_matcher import *

talmud_words = [u'בגמרא', u'גמרא', u'בגמ\'', u'גמ\'', u'במשנה', u'משנה', u'מתניתין', u'מתני\'', u'שם', u'בתר"י',
                u'בהרי"ף', u'ברי"ף', u'בר"ן']
rashi_words = [u'רש\"י ד\"ה', u'ברש\"י', u'רש\"י', u'רד\"ה']
tos_words = [u'תוספות ד\"ה', u'תוס\' ד\"ה', u'תוד\"ה', u'תוס\' ד"ה', u'תוס\'', u'תוספות', u'בתד"ה', u'תד"ה',
             u'בתוס\' ד"ה']

talmud_titles = {}
for tractate_title in library.get_indexes_in_category("Talmud"):
    he_title = library.get_index(tractate_title).get_title("he")
    talmud_titles[he_title] = tractate_title
talmud_titles[u'תלמוד ירושלמי שקלים'] = 'Jerusalem Talmud Shekalim'
talmud_titles[u'משנה עדיות'] = 'Mishnah Eduyot'


def en_name_to_he_name(en_name):
    for key in talmud_titles.keys():
        if talmud_titles[key] in en_name:
            return key


def get_mishnah_seder(mishnah_title):
    if u"Mishnah" not in mishnah_title:
        mishnah_title = "Mishnah " + mishnah_title
    for seder in seders.keys():
        indices = library.get_indexes_in_category(seder)
        if mishnah_title in indices:
            return seder
    return None


def find_tractate_name(s):
    for tn in talmud_titles.keys():
        if tn in s:
            return talmud_titles[tn]
    if u'שקלים' in s:
        return 'Jerusalem Talmud Shekalim'
    if u'עדיות' in s:
        return 'Mishnah Eduyot'


def is_special_case(tractate):
    if u'עדיות' in tractate:
        return True
    if u'ירושלמי' in tractate:
        return True
    return False


def is_continuing(s):
    if re.search(r'^\S*שם', s):
        return True
    if re.search(r'^\S*בא\"ד', s):
        return True
    return False


def exract_daf_ref(s):
    currnent_daf = getGematria(re.search(r'(?<=ף).*(?=ע\")', s).group())
    current_amud = 'b' if u'ע\"ב' in s else 'a'
    return [currnent_daf, current_amud]


def en_ref_to_num(ref_pair):
    if u'a' in ref_pair[1]:
        return ref_pair[0] * 2 - 2
    if u'b' in ref_pair[1]:
        return ref_pair[0] * 2 - 1


def num_to_daf(num):
    daf = int(num / 2) + 1
    if num % 2 == 0:
        return '{}a'.format(daf)
    return '{}b'.format(daf)


def make_talmud_array(book):
    tc = TextChunk(Ref(book), "he")
    return_array = []
    for x in range(len(tc.text)):
        return_array.append([])
    return return_array


def clean_line(s):
    bad_txt = [u'\xd7', u'\xa8', u'\u05b4', u'\u05bc', u'\u05b0', u'\u05b2', u'\u05b7', u'\u05b9', u'\u05b6', u'\u05b8',
               u'\u05bb', u'\u05b3', u'\u05c1', u'\u05c2', u'\u05b5', u'\xa9']
    for txt in bad_txt:
        s = s.replace(txt, u'')
    s = s = s.replace(u' ]', u']')
    # s=re.sub(r'\](?=\S)',u'] ',s)
    s = s.replace(u']', u'] ')
    s = s.replace(u'@B0', u'+').replace(u'@TX', u'&')
    s = re.sub(r'<.*?>', u'', s)
    s = re.sub(r'@[A-Za-z0-9]*', u'', s)
    # s=re.sub(r'[A-Za-z0-9@]',u'',s)
    s = s.replace(u'+', u'<b>').replace(u'&', u'</b>')
    s = re.sub(r'דף \S{1,5} ע\"[אב]', u'', s)
    s = s.replace(u'\n', u'')
    if u'<b>' not in s and u'</b>' in s:
        s = u'<b>' + s
    while u'  ' in s:
        s = s.replace(u'  ', u' ')
    return s


def fix_colon(s):
    s = s + u':'
    s = s.replace(u'::', u':')
    return s


def not_blank(s):
    while " " in s:
        s = s.replace(u" ", u"")
    return (len(s.replace(u"\n", u"").replace(u"\r", u"").replace(u"\t", u"")) != 0);


def dh_extract_method(some_string):
    some_string = some_string.replace(u'<b>', u'').replace(u'</b>', u'')
    for word in talmud_words:
        some_string = some_string.replace(word, u'')
    for word in tos_words:
        some_string = some_string.replace(word, u'')
    for word in rashi_words:
        some_string = some_string.replace(word, u'')
    if u'וכו\'' in u' '.join(some_string.split(u' ')[:10]):
        return some_string[:some_string.index(u'וכו\'') - 1]
    elif u'.' in some_string:
        if len(some_string.split(u'.')[0].split(u' ')) < 12:
            return some_string.split(u'.')[0]
    return ' '.join(some_string.split(u' ')[:5])


def tos_filter(s):
    s = re.sub(r'^שם ', u'', s)
    for word in tos_words:
        if re.search(r'^\S*' + word, s):
            return True
    return False


def tal_filter(s):
    for word in talmud_words:
        if re.search(r'^\S*' + word, s):
            return True
    return False


def r_filter(s):
    for word in rashi_words:
        if re.search(r'^\S*' + word, s):
            return True
    return False


def remove_extra_space(string):
    while u"  " in string:
        string = string.replace(u"  ", u" ")
    return string


def base_tokenizer(some_string):
    return_s = filter(lambda x: x != u'', remove_extra_space(
        strip_nekud(some_string).replace(u"<b>", u"").replace(u"</b>", u"").replace(".", "").replace(u"\n", u"")).split(
        u" "))
    return bleach.clean(some_string, strip=True).strip()


def post_rashash_link(link1, link2, tractate_name):
    link = (
        {
            "refs": [
                link1,
                link2,
            ],
            "type": "commentary",
            "auto": True,
            "generated_by": "sterling_rashash_" + tractate_name + "_linker"
        })
    print(link["refs"])
    #post_link(link, weak_network=True)


class Tractate:
    def __init__(self, tractate_name, tractate_text):
        
        "DOING", tractate_name
        self.en_name = tractate_name
        self.he_name = en_name_to_he_name(tractate_name)
        self.text = tractate_text
        self.is_special = is_special_case(self.he_name)

    def _tract(self):
        for dindex, daf in enumerate(self.text):
            for cindex, comment in enumerate(daf):
                
                self.en_name, num_to_daf(dindex), cindex, comment

    def rashash_post_index(self):
        en_title = self.en_name
        he_title = self.he_name
        record = JaggedArrayNode()
        record.add_title('Rashash on ' + en_title, 'en', primary=True)
        record.add_title(u'רש\"ש על' + u" " + he_title, 'he', primary=True)
        record.key = 'Rashash on ' + en_title
        record.depth = 2
        record.addressTypes = ['Talmud', 'Integer']
        record.sectionNames = ['Daf', 'Comment']
        record.validate()

        index = {
            "title": 'Rashash on ' + en_title,
            "base_text_titles": [
                en_title
            ],
            "collective_title": "Rashash",
            "dependence": "Commentary",
            "categories": ["Talmud", "Bavli", "Commentary", "Rashash", get_mishnah_seder(self.en_name)],
            "schema": record.serialize()
        }
        post_index(index, weak_network=True)

    def post_rashash_text(self):
        version = {
            'versionTitle': 'Vilna Edition',
            'versionSource': 'https://www.nli.org.il/he/books/NNL_ALEPH001300957/NLI',
            'language': 'he',
            'text': self.text
        }
        post_text('Rashash on ' + self.en_name, version)

    def link_rashash(self):
        for dindex, daf in enumerate(self.text):
            if len(daf) > 0:
                
                '{} {}'.format(self.en_name, num_to_daf(dindex))
                tractate_ref = Ref('{} {}'.format(self.en_name, num_to_daf(dindex)))
                tractate_chunk = TextChunk(tractate_ref, 'he', vtitle="William Davidson Edition - Aramaic")
                if len(tractate_chunk.text) > 0:
                    match_set = match_ref(tractate_chunk, daf, base_tokenizer, dh_extract_method=dh_extract_method,
                                          verbose=False)
                    for index, base in enumerate(match_set['matches']):
                        comment = daf[index]
                        if base and (tal_filter(comment) or (
                                not tos_filter(comment) and not r_filter(comment) and index == 0)):
                            post_rashash_link(base.normal(),
                                              'Rashash on {} {}.{}'.format(self.en_name, num_to_daf(dindex), index + 1),
                                              self.en_name)

                rashi_ref = Ref('Rashi on {} {}'.format(self.en_name, num_to_daf(dindex)))
                rashi_chunk = TextChunk(rashi_ref, "he")
                last_base = False
                if len(rashi_chunk.text) > 0:
                    match_set = match_ref(rashi_chunk, daf, base_tokenizer, dh_extract_method=dh_extract_method,
                                          verbose=False)
                    for index, base in enumerate(match_set['matches']):
                        if index < len(daf):
                            comment = daf[index]
                            if r_filter(comment) and base:
                                post_rashash_link(base.normal(),
                                                  'Rashash on {} {}.{}'.format(self.en_name, num_to_daf(dindex),
                                                                               index + 1), self.en_name)
                                last_base = base
                                talmud_link = re.search(r'.*\d+[ab]:\d+', base.normal()).group().replace(u'Rashi on ',
                                                                                                          u'')
                                post_rashash_link(talmud_link,
                                                  'Rashash on {} {}.{}'.format(self.en_name, num_to_daf(dindex),
                                                                               index + 1), self.en_name)
                            elif is_continuing(daf[index]) and last_base:
                                post_rashash_link(last_base.normal(),
                                                  'Rashash on {} {}.{}'.format(self.en_name, num_to_daf(dindex),
                                                                               index + 1), self.en_name)
                                talmud_link = re.search(r'.*\d+[ab]:\d+', last_base.normal()).group().replace(
                                    u'Rashi on ', u'')
                                post_rashash_link(talmud_link,
                                                  'Rashash on {} {}.{}'.format(self.en_name, num_to_daf(dindex),
                                                                               index + 1), self.en_name)
                            else:
                                last_base = False

                tos_ref = Ref('Tosafot on {} {}'.format(self.en_name, num_to_daf(dindex)))
                tos_chunk = TextChunk(tos_ref, "he")
                last_base = False
                if len(tos_chunk.text) > 0:
                    match_set = match_ref(tos_chunk, daf, base_tokenizer, dh_extract_method=dh_extract_method,
                                          verbose=False)
                for index, base in enumerate(match_set['matches']):
                    if index < len(daf):
                        comment = daf[index]
                        if tos_filter(comment) and base:
                            post_rashash_link(base.normal(),
                                              'Rashash on {} {}.{}'.format(self.en_name, num_to_daf(dindex), index + 1),
                                              self.en_name)
                            last_base = base
                            # get additional link to daf:
                            talmud_link = re.search(r'.*\d+[ab]:\d+', last_base.normal()).group().replace(
                                u'Tosafot on ', u'')
                            post_rashash_link(talmud_link,
                                              'Rashash on {} {}.{}'.format(self.en_name, num_to_daf(dindex), index + 1),
                                              self.en_name)
                        elif is_continuing(daf[index]) and last_base:
                            post_rashash_link(last_base.normal(),
                                              'Rashash on {} {}.{}'.format(self.en_name, num_to_daf(dindex), index + 1),
                                              self.en_name)
                            talmud_link = re.search(r'.*\d+[ab]:\d+', last_base.normal()).group().replace(
                                u'Tosafot on ', u'')
                            post_rashash_link(talmud_link,
                                              'Rashash on {} {}.{}'.format(self.en_name, num_to_daf(dindex), index + 1),
                                              self.en_name)
                        else:
                            last_base = False


seders = {'Seder Zeraim': u'סדר זרעים', 'Seder Moed': u'סדר מועד', 'Seder Nashim': u'סדר נשים',
          'Seder Nezikin': u'סדר נזיקין', 'Seder Kodashim': u'סדר קדשים', 'Seder Tahorot': u'סדר טהרות'}


def post_talmud_categories():
    add_category('Rashash', ["Talmud", "Bavli", "Commentary", 'Rashash'], u'רש\"ש')
    for seder in seders.keys():
        add_category(seder, ["Talmud", "Bavli", "Commentary", 'Rashash', seder], seders[seder])
        
        "ADDED ", seder


all_tracts = {}
with open('RashashShas.txt') as myFile:
    lines = list(map(lambda x: x, myFile.readlines()))
    current_tractate = None
    currnet_daf = None
supersting = u''
for line in lines:
    #  line
    if u'<CH A>' in line:
        current_tractate = find_tractate_name(line)
        
        if current_tractate not in all_tracts.keys():
            if is_special_case(current_tractate):
                all_tracts[current_tractate] = []
            else:
                all_tracts[current_tractate] = make_talmud_array(current_tractate)
                currnet_daf_pair = [2, 'a']

    else:
        if u'<CH B>ד' in line:
            currnet_daf_pair = exract_daf_ref(re.search(r'(?<=<CH B>ד)[^<]+', line).group())
            #  currnet_daf_pair
        if u'@PR' in line:
            if u'דף' in line:
                currnet_daf_pair = exract_daf_ref(re.search(r'(?<=ד)ף[^<]+', line).group())
        elif not_blank(clean_line(line)) and len(line.split(u' ')) > 2:
            if is_special_case(current_tractate):
                all_tracts[current_tractate].append(clean_line(line))
            else:
                # bracketed_line=line.replace(u'@B0<FT51>',u'@B0<FT51>[').replace(u'@B1<FT51>',u'@B1<FT51>]')
                for snippet in re.split(r'(?<=(..:|ע\"[אב]))[^א-ת]*@B0', line):
                    cleaned_line = clean_line(snippet)
                    if u' ]' in cleaned_line:
                        cleaned_line = cleaned_line.replace(u' ]', u']')
                    if not_blank(cleaned_line) and len(cleaned_line.split(u' ')) > 2:
                        # supersting+=cleaned_line
                        all_tracts[current_tractate][en_ref_to_num(currnet_daf_pair)].append(cleaned_line)
theset = set(supersting)
for thing in theset:
    
    repr(thing)


def post_rashash_term():
    term_obj = {
        "name": 'Rashash',
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": 'Rashash',
                "primary": True
            },
            {
                "lang": "he",
                "text": u'רש\"ש',
                "primary": True
            }
        ]
    }
    post_term(term_obj)


# post_rashash_term()
# post_talmud_categories()
posting_index = True
posting_text = True
linking_text = True
ing_text = False
in_the_yes = False
admin_links = []
site_links = []
for tract in all_tracts.keys():
    tractate_object = Tractate(tract, all_tracts[tract])
    
    'pasring {}...'.format(tractate_object.en_name)
    if not tractate_object.is_special:
        admin_links.append(SEFARIA_SERVER + "/admin/reset/Rashash_on_" + tractate_object.en_name.replace(u" ", u"_"))
        site_links.append(SEFARIA_SERVER + "/Rashash_on_" + tractate_object.en_name.replace(u" ", u"_"))
        if ing_text:
            tractate_object._tract()
        assert tract == tractate_object.en_name
        if "Rashash on "+tract in ['Rashash on Arakhin',
                     'Rashash on Bava Batra',
                     'Rashash on Bava Kamma',
                     'Rashash on Beitzah',
                     'Rashash on Bekhorot',
                     'Rashash on Berakhot',
                     'Rashash on Chagigah',
                     'Rashash on Chullin',
                     'Rashash on Eruvin',
                     'Rashash on Gittin',
                     'Rashash on Horayot',
                     'Rashash on Keritot',
                     'Rashash on Makkot',
                     'Rashash on Megillah',
                     'Rashash on Meilah',
                     'Rashash on Nazir',
                     'Rashash on Nedarim',
                     'Rashash on Niddah',
                     'Rashash on Pesachim',
                     'Rashash on Pirkei Avot',
                     'Rashash on Rosh Hashanah',
                     'Rashash on Sanhedrin',
                     'Rashash on Shabbat',
                     'Rashash on Shevuot',
                     'Rashash on Sotah',
                     'Rashash on Taanit',
                     'Rashash on Temurah',
                     'Rashash on Yevamot',
                     'Rashash on Yoma',
                     'Rashash on Zevachim']:
            pass
        print(tract)
        # if posting_index:
        #     tractate_object.rashash_post_index()
        if posting_text:
            tractate_object.post_rashash_text()
        # if linking_text:
        #    tractate_object.link_rashash()

"Admin Links:"
for link in admin_links:
    
    link

"Site Links:"
for link in site_links:
    
    link