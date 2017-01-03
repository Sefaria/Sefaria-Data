# -*- coding: utf-8 -*-

"""
algorithm - credit Dicta (dicta.org.il):
- make 484 (=22^2) hashtables
- each hash_table should have a size of 22^6
- go through shas. for every 5 words 5-gram, do:
    - get skip-gram-list for 5-gram
    - for temp-skip-gram in skip-gram-list:
        - append temp-skip-gram to corresponding hashtable with as a tuple of  (mes_name,ref,word number) (is that necessary?)
- for every 5-gram do:
    word_offset <- first gram
    6-letter-rep-list <- the 4 skip grams corresponding to the remaining 4 grams
    match-list <- for every 6-let in 6-letter-rep-list get list of matches from hash-table `word_offset`

    we define a cluster as follows: a set of i or more matching skip-grams with gaps of no more than j words in between
    the skip-grams, stretching across a total of at least k words from the start of the first skip-gram to the end of the
    last one. For this paper, we use the values i=3, j=8, k=20.

"""

import regex as re
import bisect, pickle, csv, codecs, bleach, json, operator
from collections import OrderedDict
from copy import deepcopy
import numpy as np
from sefaria.model import *
from sources.functions import post_link
from sefaria.system.exceptions import DuplicateRecordError
import itertools


min_matching_skip_grams = 2
max_words_between = 8
min_words_in_match = 20



def tokenize_words(str):
    str = str.replace(u"־"," ")
    str = re.sub(r"</?[^>]+>","",str) #get rid of html tags
    str = re.sub(r"\([^\(\)]+\)","",str) #get rid of refs
    str = str.replace('"',"'")
    word_list = filter(bool,re.split(r"[\s\:\-\,\.\;\(\)\[\]\{\}]",str))
    return word_list

class Gemara_Hashtable:

    def __init__(self):
        self.letter_freqs_list = [u'י', u'ו', u'א', u'מ', u'ה', u'ל', u'ר', u'נ', u'ב', u'ש', u'ת', u'ד', u'כ', u'ע', u'ח', u'ק',
                         u'פ', u'ס', u'ט', u'ז', u'ג', u'צ']

        self.sofit_map = {
        u'ך': u'כ',
        u'ם': u'מ',
        u'ן': u'נ',
        u'ף': u'פ',
        u'ץ': u'צ',
        }

        self.letters = [u'א', u'ב', u'ג', u'ד', u'ה',
                        u'ו', u'ז', u'ח', u'ט', u'י',
                        u'כ', u'ל', u'מ', u'נ', u'ס',
                        u'ע', u'פ', u'צ', u'ק', u'ר',
                        u'ש', u'ת', unichr(ord(u'ת')+1)]
        #try:
        #    self.ht_list = pickle.load(open('gemara_chamutz.pkl','rb'))
        #    self.loaded = True
        #except IOError:
        self.ht_list = []
        self.loaded = False
        for i in range(23 ** 2):
            self.ht_list.append({})

    def __setitem__(self,five_gram,value):
        """

        :param five_gram: list of 5 consecutive words
        :param value: MesorahItem
        """
        skip_gram_list = self.get_skip_grams(five_gram)
        ht = self.ht_list[self.w2i(skip_gram_list[0][0])] #should be the same for all four skip grams
        for skip_gram in skip_gram_list:
            index = self.w2i(u''.join(skip_gram[1:]))
            if not index in ht:
                ht[index] = list()
            if len(ht[index]) > 0:
                yo = 45
            if not value in ht[index]:
                ht[index].append(value)

    def __getitem__(self,five_gram):

        skip_gram_list = self.get_skip_grams(five_gram)
        ht = self.ht_list[self.w2i(skip_gram_list[0][0])]  # should be the same for all four skip grams
        results = []
        for skip_gram in skip_gram_list:
            index = self.w2i(u''.join(skip_gram[1:]))
            if not index in ht:
                continue
            for elem in ht[index]:
                if not elem in results:
                    results.append(elem)

        return results


    def get_skip_grams(self,five_gram):
        """

        :param five_gram: list of 5 consecutive words
        :return: list of the 4 skip grams (in 2 letter form)
        """

        two_letter_five_gram = [self.get_two_letter_word(w) for w in five_gram]
        skip_gram_list = []
        for i_skip in range(1,5):
            copy_five_gram = two_letter_five_gram[:]
            del copy_five_gram[i_skip]
            skip_gram_list.append(copy_five_gram)
        return skip_gram_list

    def w2i(self,w):
        """

        :param l: hebrew letters
        :return: corresponding integer
        """
        i = 0
        for ic,c in enumerate(reversed(w)):
            i += 23**ic * self.letters.index(c)

        return i

    def sofit_swap(self,C):
        return self.sofit_map[C] if C in self.sofit_map else C

    def get_two_letter_word(self,word):
        temp_word = u''
        for i, C in enumerate(word):
            temp_word += self.sofit_swap(C)

        temp_word = re.sub(ur'[^א-ת]+',u'',temp_word)
        if len(temp_word) < 2:
            if len(temp_word) == 1:
                return u'{}{}'.format(temp_word,self.letters[-1])
            else: #efes
                return u'{}{}'.format(self.letters[-1],self.letters[-1])

        indices = map(lambda c: self.letter_freqs_list.index(c), temp_word)
        first_max,i_first_max = self.letter_freqs_list[max(indices)],indices.index(max(indices))
        del indices[i_first_max]
        sec_max,i_sec_max     = self.letter_freqs_list[max(indices)],indices.index(max(indices))

        if i_first_max <= i_sec_max:
            return u'{}{}'.format(first_max,sec_max)
        else:
            return u'{}{}'.format(sec_max,first_max)


    def save(self):
        pickle.dump(self.ht_list, open('gemara_chamutz.pkl','wb'))


class Mesorah_Item:

    def __init__(self,mesechta,location,ref,num_skip_grams=1):
        self.mesechta = mesechta
        self.location = location
        self.ref = ref

        self.num_skip_grams = num_skip_grams


    def __iadd__(self, other):
        if other.mesechta == self.mesechta:
            temp_loc = (self.location[0],other.location[1])
            temp_ref = self.ref.starting_ref().to(other.ref.ending_ref())
            temp_num_skip_grams = self.num_skip_grams + 1
            return Mesorah_Item(self.mesechta,temp_loc,temp_ref,temp_num_skip_grams)
        else:
            raise ValueError("Mesechtot need to be the same")

    def __str__(self):
        return "{} - {} - {}".format(self.mesechta,self.location,self.ref)

    def __len__(self):
        return self.location[1] - self.location[0] + 1

    def __sub__(self, other):
        """
        distance. negative means that self ends after other starts
        :param other:
        :return:
        """
        if self.mesechta != other.mesechta:
            return None
        else:
            return other.location[0] - self.location[1]

    def __eq__(self, other):
        return self.mesechta == other.mesechta and self.location == other.location

    def contains(self,other):
        return self.mesechta == other.mesechta and \
               ((self.location[0] < other.location[0] and self.location[1] >= other.location[1]) or \
               (self.location[0] <= other.location[0] and self.location[1] > other.location[1]))


class Mesorah_Match:

    def __init__(self,a,b):
        self.a = a
        self.b = b

    def __str__(self):
        return "{} <===> {}".format(self.a,self.b)

    def __eq__(self, other):
       return self.__hash__() == other.__hash__()

    def __hash__(self):
        return hash(self.a.mesechta + str(self.a.location) + self.b.mesechta + str(self.b.location))

    def valid(self):
        return self.a.num_skip_grams >= min_matching_skip_grams and self.b.num_skip_grams >= min_matching_skip_grams and \
            len(self.a) >= min_words_in_match and len(self.b) >= min_words_in_match

class Mesorah_Match_Ref:

    def __init__(self,a,b):
        self.a = a
        self.b = b

    def __eq__(self, other):
        return (self.a == other.a and self.b == other.b) or (self.a == other.b and self.b == other.a)


def mesechta_index_map(mesechat_name):
    mes = library.get_index(mesechat_name)
    mes_sec_ref_list = mes.all_section_refs()

    #mes_sec_ref_list = Ref('Taanit 23a-26a').starting_refs_of_span() if mesechat_name == "Taanit" else Ref("Bava Batra 80b-81a").starting_refs_of_span()
    mes_word_list = []
    mes_ind_list = []
    mes_seg_ref_list = []
    index_offset = 0
    for sec_ref in mes_sec_ref_list:
        sec_tc = TextChunk(sec_ref,"he")
        temp_ind_list,temp_ref_list = sec_tc.text_index_map(tokenize_words)
        #TODO this is a temporary fix
        if len(temp_ind_list) != len(temp_ref_list):
            temp_ref_list = temp_ref_list[:len(temp_ind_list)]
        temp_word_list = []
        for seg in sec_tc.text:
            temp_word_list += tokenize_words(seg)

        mes_word_list += temp_word_list
        mes_ind_list += [i+index_offset for i in temp_ind_list]
        mes_seg_ref_list += temp_ref_list

        index_offset += len(temp_word_list)


    return mes_word_list,mes_ind_list,mes_seg_ref_list


def make_mesorat_hashas():
    ght = Gemara_Hashtable()
    mesechtot_names = [name for name in library.get_indexes_in_category("Talmud") if not "Jerusalem " in name and not "Ritva " in name and not "Rif " in name]
    mesechtot_names = ["Taanit"]
    mesechtot_data = {}
    for mes in mesechtot_names:
        mes_wl,mes_il,mes_rl = mesechta_index_map(mes)
        mesechtot_data[mes] = (mes_wl,mes_il,mes_rl)

        for i_word in range(len(mes_wl)-4):
            start_ref = mes_rl[bisect.bisect_right(mes_il, i_word) - 1]
            end_ref = mes_rl[bisect.bisect_right(mes_il, i_word+4) - 1]
            if start_ref == end_ref:
                matched_ref = start_ref
            else:
                matched_ref = start_ref.to(end_ref)
            ght[mes_wl[i_word:i_word+5]] = Mesorah_Item(mes,(i_word,i_word+4),matched_ref)
    #ght.save()

    mesorat_hashas = list()

    for mes in mesechtot_data:
        (mes_wl,mes_il,mes_rl) = mesechtot_data[mes]

        for i_word in range(len(mes_wl)-4):
            if i_word % 4000 == 0:
                print "{}\t{}%\tNum Found: {}".format(mes,round(100.0*i_word/len(mes_wl),2),len(mesorat_hashas))

            start_ref = mes_rl[bisect.bisect_right(mes_il, i_word) - 1]
            end_ref = mes_rl[bisect.bisect_right(mes_il, i_word+4) - 1]
            if start_ref == end_ref:
                matched_ref = start_ref
            else:
                matched_ref = start_ref.to(end_ref)

            a = Mesorah_Item(mes, (i_word, i_word + 4), matched_ref)
            skip_matches = ght[mes_wl[i_word:i_word+5]]
            skip_matches.remove(a) #remove the skip match that we're inspecting

            mes_matches = [Mesorah_Match(Mesorah_Item(mes,(i_word,i_word+4),matched_ref),b) for b in skip_matches]

            for j_word in range(i_word+1,len(mes_wl)-4):
                if len(mes_matches) == 0:
                    break
                temp_start_ref = mes_rl[bisect.bisect_right(mes_il, j_word) - 1]
                temp_end_ref = mes_rl[bisect.bisect_right(mes_il, j_word + 4) - 1]
                if temp_start_ref == temp_end_ref:
                    temp_matched_ref = temp_start_ref
                else:
                    temp_matched_ref = temp_start_ref.to(temp_end_ref)

                temp_a = Mesorah_Item(mes,(j_word,j_word+4),temp_matched_ref)
                temp_skip_matches = ght[mes_wl[j_word:j_word + 5]]
                temp_skip_matches.remove(temp_a)

                for temp_mes_match in reversed(mes_matches):
                    if temp_mes_match.a - temp_a > max_words_between:
                        #before removing, check if this is a valid mesorat hashas match
                        if temp_mes_match.valid():
                            mesorat_hashas.append(temp_mes_match)

                        mes_matches.remove(temp_mes_match)

                        continue

                    found = False #TODO right now I'm just choosing the first match. maybe choose closest?
                    for temp_skip_gram in temp_skip_matches:
                        if found: break
                        dist =  temp_mes_match.b - temp_skip_gram
                        if not dist is None and 0 < dist <= max_words_between:
                            found = True
                            temp_mes_match.a += temp_a
                            temp_mes_match.b += temp_skip_gram



    #final pass through matches to remove duplicates

    temp_mesorat_hashas = []
    bad_mesorat_hashas = []
    list_mesorat_hashas = list(mesorat_hashas)
    for i,a in enumerate(list_mesorat_hashas):
        bad_match = False

        if a.a.ref.section_ref().contains(a.b.ref.section_ref()) or a.b.ref.section_ref().contains(a.a.ref.section_ref()) or\
                   (a.b.ref.prev_section_ref() and (a.a.ref.section_ref().contains(a.b.ref.prev_section_ref()) or a.b.ref.prev_section_ref().contains(a.a.ref.section_ref()))) or \
                   (a.a.ref.prev_section_ref() and (a.b.ref.section_ref().contains(a.a.ref.prev_section_ref()) or a.a.ref.prev_section_ref().contains(a.b.ref.section_ref()))):
            bad_match = True

        if not bad_match:
            for j in range(0,len(list_mesorat_hashas)):
                if i == j: continue
                b = list_mesorat_hashas[j]
                if (b.a.contains(a.a) and b.b.contains(a.b)) or \
                        (b.a.contains(a.b) and b.b.contains(a.a)):
                    bad_match = True
                    break

        if not bad_match:
            for b in temp_mesorat_hashas:
                if (a.a == b.a and a.b == b.b) or \
                        (a.b == b.a and a.a == b.b):
                    bad_match = True
                    break
        if not bad_match:
            temp_mesorat_hashas.append(a)
        else:
            bad_mesorat_hashas.append(a)

    #mesorat_hashas = temp_mesorat_hashas
    print len(temp_mesorat_hashas)
    mesorat_hashas = temp_mesorat_hashas + bad_mesorat_hashas
    f = codecs.open('mesorat_hashas_test.csv','wb',encoding='utf8')
    f.write(u','.join([u'Ref A',u'Ref B',u'Text A',u'Text B',u'Location A',u'Location B']) + u'\n')
    for match in mesorat_hashas:
        f.write(u','.join([str(match.a.ref),str(match.b.ref),u' '.join(mesechtot_data[match.a.mesechta][0][match.a.location[0]:match.a.location[1]+1]),u' '.join(mesechtot_data[match.b.mesechta][0][match.b.location[0]:match.b.location[1]+1]),str(match.a.location).replace(u',',u'-'),str(match.b.location).replace(u',',u'-')]) + u'\n')
    f.close()

def clean_mesorat_hashas():
    mesechtot_names = [name for name in library.get_indexes_in_category("Talmud") if not "Jerusalem " in name and not "Ritva " in name and not "Rif " in name]
    seg_map = OrderedDict()
    for name in mesechtot_names:
        mes = library.get_index(name)
        for seg in mes.all_segment_refs():
            seg_map[str(seg)] = None
    with codecs.open('mesorat_hashas_refs.csv','rb',encoding='utf8') as meshas:
        isfirstline = True
        for line in meshas:
            if isfirstline:
                isfirstline = False
                continue
            line_array = line.split(u',')[0:2]
            line_array.sort(key=lambda r: Ref(r).order_id())
            seg_map[str(line_array[0])] = str(line_array[1])



    """temp_mesorat_hashas = []

    list_mesorat_hashas = list(mesorat_hashas)
    for i,a in enumerate(list_mesorat_hashas):
        bad_match = False

        if a.a.ref == a.b.ref or a.a.ref.section_ref() == a.b.ref.section_ref() or \
                   (a.b.ref.prev_section_ref() and a.a.ref.section_ref() == a.b.ref.prev_section_ref()) or \
                   (a.a.ref.prev_section_ref() and a.b.ref.section_ref() == a.a.ref.prev_section_ref()):
            bad_match = True

        if not bad_match:
            for j in range(0,len(list_mesorat_hashas)):
                b = list_mesorat_hashas[j]
                if (b.a.ref.contains(a.a.ref) and b.b.ref.contains(a.b.ref)) or \
                        (b.a.ref.contains(a.b.ref) and b.b.ref.contains(a.a.ref)):
                    bad_match = True
                    break
        if not bad_match:
            temp_mesorat_hashas.append(a)

    mesorat_hashas = temp_mesorat_hashas

    f = codecs.open('mesorat_hashas.csv','wb',encoding='utf8')
    for match in mesorat_hashas:
        f.write(u','.join([str(match.a.ref),str(match.b.ref),u' '.join(mesechtot_data[match.a.mesechta][0][match.a.location[0]:match.a.location[1]+1]),u' '.join(mesechtot_data[match.b.mesechta][0][match.b.location[0]:match.b.location[1]+1])]) + u'\n')
    f.close()"""


def minify_mesorat_hashas():
    out = codecs.open('mesorat_hashas_refs.csv','wb',encoding='utf8')
    with codecs.open('mesorat_hashas.csv','rb',encoding='utf8') as inn:
        for line in inn:
            line_array = line.split(u',')
            out.write(u','.join(line_array[0:2]) + u'\n')
    out.close()

def find_most_quoted():
    mesechtot_names = [name for name in library.get_indexes_in_category("Talmud") if not "Jerusalem " in name and not "Ritva " in name and not "Rif " in name]
    seg_map = OrderedDict()
    for name in mesechtot_names:
        mes = library.get_index(name)
        for seg in mes.all_segment_refs():
            seg_map[str(seg)] = 0
    with codecs.open('mesorat_hashas_refs.csv','rb',encoding='utf8') as meshas:
        isfirstline = True
        for line in meshas:
            if isfirstline:
                isfirstline = False
                continue
            line_array = line.split(u',')
            for ref in line_array:
                ref_list = Ref(ref).range_list()
                for rref in ref_list:
                    seg_map[str(rref)] += 1

    most_quoted = ''
    num = 0
    with open('gemara_popularity.csv','wb') as pop:
        for seg,count in seg_map.items():
            if count > num:
                most_quoted = seg
                num = count
            pop.write('{},{}\n'.format(seg,count))

    print "the most quoted gemara is:",most_quoted,num,'times'

def save_links():
    with open("mesorat_hashas_refs.csv","rb") as f:
        r = csv.reader(f)
        isfirstline = True
        for row in r:
            if isfirstline:
                isfirstline = False
                continue
            link_obj = {"auto":True,"refs":row,"anchorText":"","generated_by":"mesorat_hashas.py","type":"Automatic Mesorat HaShas"}
            try:
                Link(link_obj).save()
            except DuplicateRecordError:
                pass #poopy

def save_links_dicta(category):
    mesorat_hashas = json.load(open("mesorat_hashas2_{}.json".format(category),'rb'))
    for link in mesorat_hashas:
        link_obj = {"auto": True, "refs": link, "anchorText": "", "generated_by": "mesorat_hashas.cs (Dicta) {}".format(category),
                    "type": "Automatic Mesorat HaShas"}
        try:
            Link(link_obj).save()
        except DuplicateRecordError:
            pass  # poopy

def save_links_post_request(category):
    query = {"generated_by": "mesorat_hashas.cs (Dicta) {}".format(category), "auto": True, "type": "Automatic Mesorat HaShas"}
    ls = LinkSet(query)
    links = [l.contents() for l in ls]
    post_link(links)

def find_bad_bad_gemaras():
    mesechtot_names = [name for name in library.get_indexes_in_category("Talmud") if
                       not "Jerusalem " in name and not "Ritva " in name and not "Rif " in name]
    for mesechta in mesechtot_names:
        wl,il,rl = mesechta_index_map(mesechta)

def merge_matches(mesorat_hashas):
    pass
    """
    make dictionary where each key is mesechta name and value is array for every word
    populate arrays so that each word is an array of all matches which include that word
    mesorah_dict = {old_mesorah_match : merged_mesorah_match}

    updated = False
    for every mesechta
        for every word
            close_matches = matches that are close to each other
            temp_merged = merge(matches)
            for match in matches
                mesorah_dict[match] = max(mesorah_dict[match],match)
                if you did something:
                    updated = True

    new_mesorah = set(all matches in mesorah_dict)
    if updated
        return merge_matches(new_mesorh)
    """
    mesechtot_names = [name for name in library.get_indexes_in_category("Talmud") if
                       not "Jerusalem " in name and not "Ritva " in name and not "Rif " in name]

    mesechta_dict = {}
    for mesechta in mesechtot_names:
        wl,il,rl = mesechta_index_map(mesechta)
        mesechta_dict[mesechta] = [set() for _ in wl]


#stop_words = [w[0] for w in json.load(open("word_counts.json", "rb"), encoding='utf8')[:100]]
#stop_words = [u'רב',u'רבי',u'בן',u'בר',u'בריה',u'אמר',u'כאמר',u'וכאמר',u'דאמר',u'ודאמר',u'כדאמר',u'וכדאמר',u'ואמר',u'כרב',
#              u'ורב',u'כדרב',u'דרב',u'ודרב',u'וכדרב',u'כרבי',u'ורבי',u'כדרבי',u'דרבי',u'ודרבי',u'וכדרבי',u"כר'",u"ור'",u"כדר'",
#              u"דר'",u"ודר'",u"וכדר'",u'א״ר',u'וא״ר',u'כא״ר',u'דא״ר',u'דאמרי',u'משמיה',u'קאמר',u'קאמרי',u'לרב',u'לרבי',
#              u"לר'",u'ברב',u'ברבי',u"בר'",u'ביה',u'הא',u'ליה']
stop_words = []
def base_tokenizer(base_str):
    base_str = base_str.strip()
    base_str = bleach.clean(base_str, tags=[], strip=True)
    for match in re.finditer(ur'\(.*?\)', base_str):
        if library.get_titles_in_string(match.group()) and len(match.group().split()) <= 5:
            base_str = base_str.replace(match.group(), u"")
            # base_str = re.sub(ur"(?:\(.*?\)|<.*?>)", u"", base_str)
    base_str = re.sub(ur'[A-Za-z]',u'',base_str)
    word_list = re.split(ur"\s+", base_str)
    word_list = [re.sub(ur'\P{L}',u'',re.sub(ur'((?<!^)\u05D9)',u'',re.sub(ur'ו',u'',w))) for w in word_list if w not in stop_words] #remove non-leading yuds and all vuvs
    word_list = [w for w in word_list if len(w.strip()) > 0]
    return word_list

def generate_dicta_input(category):

    if category == "Talmud":
        mesechtot_names = [name for name in library.get_indexes_in_category("Talmud") if
                       not "Jerusalem " in name and not "Ritva " in name and not "Rif " in name]

    elif category == "Mishnah" or category == "Tosefta":
        mesechtot_names = library.get_indexes_in_category(category)
    else:
        mesechtot_names = []

    #mesechtot_names = ["Shabbat"]

    for mes in mesechtot_names:
        mes_tc = Ref(mes).text("he")
        mes_tim = mes_tc.text_index_map(base_tokenizer,strict=False)
        mes_str_array = [w for seg in mes_tc.ja().flatten_to_array() for w in base_tokenizer(seg)]
        mes_str = u" ".join(mes_str_array)

        #mes_str_array2 = mes_str.strip().split(u' ')

        #random_num = 5000
        #print u"BEFORE", mes_tim[1][random_num].text("he").text, mes_tim[1][random_num].text("he")
        #print u"AFTER",u" ".join(mes_str_array2[mes_tim[0][random_num]:mes_tim[0][random_num+1]])

        with codecs.open("dicta_input_{}/{}.txt".format(category.lower(),mes),'wb',encoding='utf8') as f:
            f.write(mes_str)
        pickle.dump(mes_tim, open('dicta_text_index_map/{}.pkl'.format(mes), 'wb'))
        print 'Done with {}'.format(mes)

def generate_dicta_output(category):
    if category == "Talmud":
        mesechtot_names = [name for name in library.get_indexes_in_category("Talmud") if
                       not "Jerusalem " in name and not "Ritva " in name and not "Rif " in name]

    elif category == "Mishnah" or category == "Tosefta":
        mesechtot_names = library.get_indexes_in_category(category)
    else:
        mesechtot_names = []

    #mesechtot_names = ["Shabbat"]

    mesorat_hashas_dicta = {}
    pickle_jar = {}
    for mes in mesechtot_names:
        with codecs.open("dicta_output/ComparisonResults_{}Output.txt".format(mes),'r',encoding='utf8') as f:
            curr_match = []
            curr_match_content = []
            for line in f:
                if u"***" in line:
                    curr_match = []
                    curr_match_content = []
                elif len(line.strip()) == 0 or (len(line.strip()) == 1 and line.strip()[0] == u'\uFEFF'):
                    combos = list(itertools.combinations(zip(curr_match,curr_match_content),2))
                    for combo in combos:

                        combo = sorted(combo,key=lambda x: x[0])
                        combo_mes = [c[0] for c in combo]
                        combo_content = [c[1] for c in combo]
                        mesorah_key = u'|'.join(combo_mes)
                        mesorah_value = u'|'.join(combo_content)
                        if mesorah_key not in mesorat_hashas_dicta:
                            mesorat_hashas_dicta[mesorah_key] = u''
                        mesorat_hashas_dicta[mesorah_key] = mesorah_value
                else:
                    temp_match = line.split(u':')[0]
                    temp_match_content = line.split(u':')[1]
                    curr_match.append(temp_match)
                    curr_match_content.append(temp_match_content)
        pickle_jar[mes] = pickle.load(open('dicta_text_index_map/{}.pkl'.format(mes)))

    temp_mesorat_hashas = []
    for key in mesorat_hashas_dicta:
        word_indexes = key.split(u'|')
        content = mesorat_hashas_dicta[key].split(u'|')
        match = []
        for iwi,wi in enumerate(word_indexes):
            mes = wi.split(u'  ')[0]
            temp_word_index = wi.split(u'  ')[1]
            start = int(temp_word_index.split(u'-')[0][1:]) #get rid of brackets
            end = int(temp_word_index.split(u'-')[1][:-1])

            #print "ORIG:{}MES:{}S:{}E:{}--".format(wi,mes,start,end)

            mes_ref_list = pickle_jar[mes][1]
            mes_ind_list = pickle_jar[mes][0]

            start_ref = mes_ref_list[bisect.bisect_right(mes_ind_list, start)-1]
            end_ref = mes_ref_list[bisect.bisect_right(mes_ind_list, end)-1]

            if start_ref == end_ref:
                ref = start_ref
            else:
                ref = start_ref.to(end_ref)
            match.append(str(ref)) # + u' ||| ' + content[iwi])

        matchref = [Ref(match[0]),Ref(match[1])]
        temp_mesorat_hashas.append(matchref)

    #remove matches that are subsets
    intersection_map = {}
    for matchref in temp_mesorat_hashas:
        for i,m in enumerate(matchref):
            mrange = m.range_list()
            for r in mrange:
                r_str = r.normal()
                if r_str not in intersection_map:
                    intersection_map[r_str] = []
                intersection_map[r_str].append((matchref[i],matchref[int(i == 0)]))

    mesorat_hashas = []
    num_dups = 0
    for matchref in temp_mesorat_hashas:
        is_subset = False
        intersected2 = []
        intersected1 = intersection_map[matchref[0].starting_ref().normal()]
        for m_inter in intersected1:
            if not (m_inter[0] == matchref[0] and m_inter[1] == matchref[1]) and m_inter[0].contains(matchref[0]):
                intersected2.append(m_inter[1])

        for m_inter in intersected2:
            if m_inter.contains(matchref[1]):
                is_subset = True
                num_dups += 1
                break

        if not is_subset:
            match = [matchref[0].normal(),matchref[1].normal()]
            mesorat_hashas.append(match)




    print "Num Subsets: {}".format(num_dups)
    objStr = json.dumps(mesorat_hashas_dicta, indent=4, ensure_ascii=False)
    with open('dicta_mesorat_hashas_{}.json'.format(category), "w") as f:
        f.write(objStr.encode('utf-8'))
    objStr = json.dumps(mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas2_{}.json'.format(category), "w") as f:
        f.write(objStr.encode('utf-8'))

def find_extra_spaces():
    mesechta_names = ["Berakhot"]
    for mes in mesechta_names:
        segs = library.get_index(mes).all_segment_refs()
        for seg in segs:
            text = seg.text("he").text
            if text != text.strip():
                print seg, text


def find_gemara_stopwords():
    mesechtot_names = [name for name in library.get_indexes_in_category("Talmud") if
                       not "Jerusalem " in name and not "Ritva " in name and not "Rif " in name]

    word_counts = {}
    for mes in mesechtot_names:
        mes_tc = Ref(mes).text("he")
        mes_str = mes_tc.ja().flatten_to_string()
        mes_str_array = mes_str.split()
        for w in mes_str_array:
            if w not in word_counts:
                word_counts[w] = 0
            word_counts[w] += 1

    sorted_wc = sorted(word_counts.items(), key=operator.itemgetter(1))

    objStr = json.dumps(sorted_wc[-1:-1000:-1], indent=4, ensure_ascii=False)
    with open('word_counts.json', "wb") as f:
        f.write(objStr.encode('utf-8'))

def count_matches():
    matches = {}
    mesorat_hashas = json.load(open("mesorat_hashas-10words.json", 'rb'))
    for l in mesorat_hashas:
        tup_l = tuple(sorted(l))
        if tup_l not in matches:
            matches[tup_l] = 0
        matches[tup_l] += 1
    print len(matches)

def compare_mesorat_hashas():
    compare_a_name = 'mesorat_hashas-10words.json'
    compare_b_name = 'mesorat_hashas2.json'

    compare_a = json.load(open(compare_a_name,'rb'))
    compare_b = json.load(open(compare_b_name,'rb'))

    compare_a_mmr = [Mesorah_Match_Ref(m[0],m[1]) for m in compare_a]
    compare_b_mmr = [Mesorah_Match_Ref(m[0],m[1]) for m in compare_b]

    inbnota = []
    for i,m in enumerate(compare_b_mmr):
        if i % 1000 == 0:
            print "({}/{})".format(i,len(compare_b))
        if m not in compare_a_mmr:
            inbnota.append(compare_b[i])

    print "Num in B not in A: {}".format(len(inbnota))
    objStr = json.dumps(inbnota, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_comparison.json', "w") as f:
        f.write(objStr.encode('utf-8'))

def filter_close_matches():
    max_cluster_dist = 20
    mesorat_hashas = json.load(open('mesorat_hashas2_Talmud.json','rb'))
    new_mesorat_hashas = set()

    mesechtot_names = [name for name in library.get_indexes_in_category("Talmud") if not "Jerusalem " in name and not "Ritva " in name and not "Rif " in name]
    seg_map = {}
    """
    for name in mesechtot_names:
        mes = library.get_index(name)
        for seg in mes.all_segment_refs():
            seg_map[str(seg)] = []
    """
    for l in mesorat_hashas:
        for ir,r in enumerate(l):
            if r not in seg_map:
                seg_map[r] = set()
            seg_map[r].add(Ref(l[int(ir == 0)]))


    m = len(seg_map.items())
    for iseg, (strr, rset) in enumerate(seg_map.items()):
        rray = list(rset)
        if iseg % 100 == 0:
            print "{}/{}".format(iseg,m)
        n = len(rray)
        dist_mat = np.zeros((n,n))
        for i in range(n):
            for j in range(i+1,n):
                if i == j:
                    dist_mat[i,j] = 0
                else:
                    dist_mat[i,j] = rray[i].distance(rray[j])

        clusters = []
        non_clustered = set()
        clustered_indexes = set()
        for i in range(n):
            for j in range(i+1,n):
                if dist_mat[i,j] <= max_cluster_dist and dist_mat[i,j] != -1:
                    #we've found an element in a cluster!
                    #figure out if a cluster already exists containing one of these guys
                    found = False
                    for c in clusters:
                        if rray[i] in c or rray[j] in c:
                            c.add(rray[i])
                            c.add(rray[j])
                            clustered_indexes.add(i)
                            clustered_indexes.add(j)
                            found = True
                            break
                    if not found:
                        c = set()
                        c.add(rray[i])
                        c.add(rray[j])
                        clustered_indexes.add(i)
                        clustered_indexes.add(j)
                        clusters += [c]

        for ir, r in enumerate(rray):
            if ir not in clustered_indexes:
                non_clustered.add(r)


        if len(clusters) + len(non_clustered) > 5:
            print list(non_clustered)[0]

        for c in clusters:
            #add one from each cluster
            other_r = None
            for temp_other_r in c:
                if other_r is None or temp_other_r.order_id() < other_r.order_id():
                    other_r = temp_other_r

            new_mesorat_hashas.add(tuple(sorted((strr,str(other_r)),key=lambda r: Ref(r).order_id())))

        for r in non_clustered:
            new_mesorat_hashas.add(tuple(sorted((strr, str(r)), key=lambda r: Ref(r).order_id())))

    filtered_mesorat_hashas = []
    for l in new_mesorat_hashas:
        lray = list(l)
        filtered_mesorat_hashas += [lray]



    print "Old: {} New: {} Difference: {}".format(len(mesorat_hashas),len(new_mesorat_hashas),len(mesorat_hashas)-len(new_mesorat_hashas))
    objStr = json.dumps(filtered_mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_clustered.json', "w") as f:
        f.write(objStr.encode('utf-8'))






#make_mesorat_hashas()
#minify_mesorat_hashas()
#find_most_quoted()
#save_links()
#save_links_post_request("Talmud")
#clean_mesorat_hashas()
#find_bad_bad_gemaras()
#generate_dicta_input("Talmud")
#generate_dicta_output("Talmud")
#find_extra_spaces()
save_links_dicta("Talmud")
#find_gemara_stopwords()
#count_matches()
#compare_mesorat_hashas()
#filter_close_matches()
