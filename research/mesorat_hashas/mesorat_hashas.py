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

import re, bisect, pickle, csv, codecs
from collections import OrderedDict
from copy import deepcopy
from sefaria.model import *
from sources.functions import post_link
from sefaria.system.exceptions import DuplicateRecordError

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

def save_links_post_request():
    query = {"generated_by": "mesorat_hashas.py", "auto": True, "type": "Automatic Mesorat HaShas"}
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




make_mesorat_hashas()
#minify_mesorat_hashas()
#find_most_quoted()
#save_links()
#save_links_post_request()
#clean_mesorat_hashas()
#find_bad_bad_gemaras()