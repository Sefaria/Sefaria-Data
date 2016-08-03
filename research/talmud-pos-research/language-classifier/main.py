# -*- coding: utf-8 -*-
import sys
import re
import json
import codecs
import cal_tools
import itertools
from hmmlearn import hmm
from sklearn.preprocessing import LabelEncoder
sys.path.append("../hmm")
from sefaria.model import *
from sefaria.utils import hebrew
from sefaria.system.exceptions import InputError

from hmm.discrete.DiscreteHMM import DiscreteHMM

import numpy as np


class Cal_ngram:

    def __init__(self,cal_words,cal_head_words,prev_tagged_words,start_pos,skip_penalty):
        self.cal_words = cal_words
        self.cal_head_words = cal_head_words
        self.prev_tagged_words = prev_tagged_words
        self.matched_indexes = []
        self.num_words_passed = 0
        self.curr_tagged_words = []
        self.score = 0
        self.start_pos = start_pos
        self.skip_penalty = skip_penalty

    def find(self):
        curr_pos = 0
        for i,prev in enumerate(self.prev_tagged_words):
            word = prev["word"]
            classy = prev["class"]
            if classy != "unknown":
                self.curr_tagged_words.append({"word":word,"class":classy})
            else:
                if self.is_match(self.cal_words[curr_pos],self.cal_head_words[curr_pos],word):
                    self.curr_tagged_words.append({"word":word,"class":"talmud"})
                    self.matched_indexes.append(self.start_pos+i)
                    curr_pos += 1
                    if len(self.matched_indexes) == len(self.cal_words):
                        break
                else:
                    self.curr_tagged_words.append({"word":word,"class":"unknown"})
            self.num_words_passed += 1

        self.score = max(self.matched_indexes[:self.skip_penalty+1]) if len(self.matched_indexes) > 0 else self.start_pos + len(self.prev_tagged_words)

    def is_match(self,cw,chw,tw):
        dist = weighted_levenshtein(cw,tw,weighted_levenshtein_cost)
        head_dist = weighted_levenshtein(chw,tw,weighted_levenshtein_cost)
        return dist < 1.4 or head_dist < 1.4

letter_freqs_list = [u'י',u'ו',u'א',u'מ',u'ה',u'ל',u'ר',u'נ',u'ב',u'ש',u'ת',u'ד',u'כ',u'ע',u'ח',u'ק',u'פ',u'ס',u'ט',u'ז',u'ג',u'צ']

sofit_map = {
    u'ך': u'כ',
    u'ם': u'מ',
    u'ן': u'נ',
    u'ף': u'פ',
    u'ץ': u'צ',
}

letter_freqs = {
    u'י': 0.0,
    u'ו': 0.2145,
    u'א': 0.2176,
    u'מ': 0.3555,
    u'ה': 0.4586,
    u'ל': 0.4704,
    u'ר': 0.4930,
    u'נ': 0.5592,
    u'ב': 0.5678,
    u'ש': 0.7007,
    u'ת': 0.7013,
    u'ד': 0.7690,
    u'כ': 0.8038,
    u'ע': 0.8362,
    u'ח': 0.8779,
    u'ק': 0.9124,
    u'פ': 0.9322,
    u'ס': 0.9805,
    u'ט': 0.9924,
    u'ז': 0.9948,
    u'ג': 0.9988,
    u'צ': 1.0
}
def mssl(l):
    best = cur = 0
    curi = starti = besti = 0
    for ind, i in enumerate(l):
        if cur+i > 0:
            cur += i
        else: # reset start position
            cur, curi = 0, ind+1

        if cur > best:
            starti, besti, best = curi, ind+1, cur
    return starti, besti, best

def weighted_levenshtein_cost(c1, c2=None):
    min_cost = 1.0
    c1 = sofit_swap(c1)
    c2 = sofit_swap(c2)
    w1 = letter_freqs[c1] if c1 in letter_freqs else 0.0
    if c2:
        w2 = letter_freqs[c2] if c2 in letter_freqs else 0.0
        return max(w1,w2) + min_cost
    else:
        return w1 + min_cost

#find the lowest wl_dist for str in s in words and return the index and distance
def best_w_levenshtein(s,words,cost_fn):
    best_dist = 1000
    best_ind = -1
    for i,w in enumerate(words):
        dist = weighted_levenshtein(w,s,cost_fn)
        if dist < best_dist:
            best_dist = dist
            best_ind = i
    return best_ind,best_dist

def weighted_levenshtein(s1,s2,cost_fn):
    if s1 == s2:
        return 0
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)

    v0 = range(len(s2)+1)
    v1 = np.zeros(len(s2)+1).tolist()

    for i in range(len(s1)):
        v1[0] = i + 1
        for j in range(len(s2)):
            cost_sub = 0.0 if (s1[i] == s2[j]) else cost_fn(s1[i],s2[j])
            cost_ins = cost_fn(s2[j])
            cost_del = cost_fn(s1[i])
            v1[j+1] = min(v1[j]+cost_ins,min(v0[j+1]+cost_del,v0[j]+cost_sub))

        vtemp = v0
        v0 = v1
        v1 = vtemp

    return v0[len(s2)]

def sofit_swap(C):
    try:
        return sofit_map[C]
    except KeyError:
        return C


def get_two_letter_word(word):
    temp_word = u''
    for i,C in enumerate(word):
        temp_word += sofit_swap(C)
    try:
        indices = np.array(map(lambda c: letter_freqs_list.index(c), temp_word))
        top_indices = (-indices).argsort()[:2]
        return u''.join([temp_word[x] for x in top_indices[top_indices.argsort()]]) #make sure that the letters are in the same order as they were in 'word'
    except ValueError:
        return None

def tokenize_words(str,strip_html=True):
    str = str.replace(u"־"," ")
    if strip_html:
       str = re.sub(r"</?[a-z]+>","",str) #get rid of html tags
    str = re.sub(r"\([^\(\)]+\)","",str) #get rid of refs
    return filter(bool,re.split(r"[\s\:\-\,\.\;\(\)\[\]\{\}]",str))

def make_training_sets(type):
    if type is "biblical":
        tanach_indexes = [library.get_index(ind) for ind in library.get_indexes_in_category("Tanakh") if not ind in ("Daniel","Ezra","Nehemia")]
        tanach_dict = {}
        for ind in tanach_indexes:
            all_secs = ind.all_section_refs()
            for sec in all_secs:
                sec_str = hebrew.strip_cantillation(sec.text('he').as_string(),strip_vowels=True)
                word_list = tokenize_words(sec_str)
                for word in word_list:
                    if word:
                        two_letter = get_two_letter_word(word)
                        if two_letter:
                            temp_list = set(tanach_dict[two_letter]) if two_letter in tanach_dict else set()
                            temp_list.add(word)
                            tanach_dict[two_letter] = list(temp_list)
        fp = codecs.open("biblical_2_letters_training.json","w",encoding='utf-8')
        json.dump(tanach_dict, fp,indent=4, encoding='utf-8', ensure_ascii=False)
    elif type is "mishnaic":
        num_mishnah_per_mesechta = 30000 #effectively all mishnah
        mishnah_indexes = [library.get_index(ind) for ind in library.get_indexes_in_category("Mishnah")]
        mishnah_dict = {}
        for ind in mishnah_indexes:
            mishna_segs = ind.all_section_refs()
            if len(mishna_segs) >= num_mishnah_per_mesechta:
                mishna_segs = mishna_segs[:num_mishnah_per_mesechta]
            for seg in mishna_segs:
                if len(seg.linkset().filter("Tanakh")) > 0:
                    #avoid mishnahs that quote tanakh to not mix languages
                    continue

                first_sec_str = hebrew.strip_cantillation(seg.text('he').as_string(),strip_vowels=True)
                word_list = tokenize_words(first_sec_str)
                for word in word_list:
                    if word:
                        two_letter = get_two_letter_word(word)
                        if two_letter:
                            temp_list = set(mishnah_dict[two_letter]) if two_letter in mishnah_dict else set()
                            temp_list.add(word)
                            mishnah_dict[two_letter] = list(temp_list)
        fp = codecs.open("mishnaic_2_letters_training.json","w",encoding='utf-8')
        json.dump(mishnah_dict, fp,indent=4, encoding='utf-8', ensure_ascii=False)
    elif type is "talmudic":
        talmud_dict = {}
        talmud_dbs = {
            ("caldb.txt",cal_tools.parseCalLine),
            ("jbaforms.txt",cal_tools.parseJBALine)
        }
        for db in talmud_dbs:
            with open(db[0],"r") as caldb:
                for line in caldb:
                    line_obj = db[1](line,True,False)
                    try:
                        word = line_obj["word"]
                    except KeyError:
                        print "continuing"
                        continue
                    if word:
                        two_letter = get_two_letter_word(word)
                        if two_letter:
                            temp_list = set(talmud_dict[two_letter]) if two_letter in talmud_dict else set()
                            temp_list.add(word)
                            talmud_dict[two_letter] = list(temp_list)
                    head_word = line_obj["head_word"]
                    if head_word:
                        two_letter = get_two_letter_word(head_word)
                        if two_letter:
                            temp_list = set(talmud_dict[two_letter]) if two_letter in talmud_dict else set()
                            temp_list.add(head_word)
                            talmud_dict[two_letter] = list(temp_list)

        fp = codecs.open("talmudic_2_letters_training.json", "w", encoding='utf-8')
        json.dump(talmud_dict, fp, indent=4, encoding='utf-8', ensure_ascii=False)

def tag_testing_init(word_list_in,test_set_lens,test_set_name="test"):
    print "tag_testing_init"
    doc = {}
    word_list_out = []
    suffix = "_2_letters_training.json"
    classes = ("talmudic","mishnaic","biblical")
    class_dicts = [json.load(codecs.open("{}{}".format(clas,suffix),"r",encoding='utf-8')) for clas in classes]

    prev_class = ""
    for j,word in enumerate(word_list_in):
        if not word:
            continue
        two_letter = get_two_letter_word(word)
        scores = np.empty((len(classes)))

        for i,dict in enumerate(class_dicts):
            best_class_score = 1000
            close_words = dict[two_letter] if two_letter in dict else []
            for close in close_words:
                temp_score = weighted_levenshtein(close,word,weighted_levenshtein_cost)
                best_class_score = temp_score if temp_score < best_class_score else best_class_score
            scores[i] = best_class_score

        max_score = np.max(scores)
        scores = 1 - (scores / max_score) if max_score != 0 else 1 - scores
        tied_classes = [classes[i] for i in np.where(np.abs(np.max(scores)-scores) < 0.05)[0]]
        if prev_class in tied_classes:
            best_class = prev_class
            if np.max(scores) < 0.3: #in case we know nothing about this word except context, give that class a boost
                ind = classes.index(best_class)
                scores[ind] += 0.3
        else:
            best_class = classes[np.argmax(scores)]
        scores[scores < 0.7] = 0
        #give best_class


        word_list_out.append({"word":word,"class":best_class,"scores":scores.tolist()})
        prev_class = best_class
        if j % 100 == 0:
            print "{}/{}".format(j,len(word_list_in))

    '''
    visible_states = []
    for dict in class_dicts:
        for k in dict:
            visible_states += dict[k]
    '''

    visible_states = list(set(word_list_in))
    doc["words"] = word_list_out
    doc["num_visible_states"] = len(visible_states)
    doc["num_hidden_states"] = len(classes)
    doc["hidden_states"] = list(classes)
    doc["visible_states"] = visible_states
    doc["observations"] = [visible_states.index(obs) for obs in word_list_in]
    doc["segment_lengths"] = test_set_lens
    fp = codecs.open("{}{}{}".format(test_set_name,"_init", ".json"), "w", encoding='utf-8')
    json.dump(doc, fp, indent=4, encoding='utf-8', ensure_ascii=False)

def tag_testing_final(decoded_states,logprob,test_set_name="test"):
    print "tag_testing_final"
    test_set_init = json.load(codecs.open("{}{}{}".format(test_set_name,'_init','.json'),"r",encoding="utf-8"))
    visible_states = test_set_init["visible_states"]
    hidden_states = test_set_init["hidden_states"]
    word_list_in = test_set_init["words"]
    word_list_out = [{"word":word_list_in[i]["word"],"class":hidden_states[x],"old_class":word_list_in[i]["class"] } for i,x in enumerate(decoded_states)]
    test_set_final = test_set_init
    test_set_final["words"] = word_list_out
    test_set_final["logprob"] = logprob

    fp = codecs.open("{}{}{}".format(test_set_name, "_final", ".json"), "w", encoding='utf-8')
    json.dump(test_set_final, fp, indent=4, encoding='utf-8', ensure_ascii=False)


def get_hmm_initial_state(test_set_name="test",hmm_init_state_name="hmm_initial_state"):
    print "get_hmm_initial_state"
    test_set_init = json.load(codecs.open("{}{}{}".format(test_set_name,'_init','.json'),"r",encoding="utf-8"))
    visible_states = test_set_init["visible_states"]
    hidden_states = test_set_init["hidden_states"]
    word_list = test_set_init["words"]
    observations = test_set_init["observations"]
    N = test_set_init["num_hidden_states"]
    K = test_set_init["num_visible_states"]
    A = np.ones(shape=(N,N))
    pi = np.ones(shape=(N))
    B = np.ones(shape=(N,K))

    prev_hs_ind = -1
    for i,word_obj in enumerate(word_list):
        scores = 10*np.array(word_obj["scores"])
        hs_ind = hidden_states.index(word_obj["class"])
        vs_ind = visible_states.index(word_obj["word"])
        pi[:] += scores
        B[:,vs_ind] += scores
        if i > 0:
            A[prev_hs_ind,:] += scores
        prev_hs_ind = hs_ind

    """
    row_sums = A.sum(axis=1)
    A = A / row_sums[:, np.newaxis]

    row_sums = B.sum(axis=1)
    B = B / row_sums[:, np.newaxis]

    pi = pi / pi.sum()
    """

    print A
    print B
    print pi

    fp = open("{}{}".format(hmm_init_state_name,'.npz'),"w")
    np.savez(fp,A=A,pi=pi,B=B,obs=np.array(observations))
    fp.close()

def run_baum_welch(test_set_name="test",hmm_init_state_name="hmm_initial_state"):
    print "run_baum_welch"
    fp = open("{}{}".format(hmm_init_state_name,'.npz'),"r")
    hmm_init_state = np.load(fp)
    A = hmm_init_state['A']
    pi = hmm_init_state['pi']
    B = hmm_init_state['B']
    obs = np.array([hmm_init_state['obs']]).T

    test_set_init = json.load(codecs.open("{}{}{}".format(test_set_name, '_init', '.json'), "r", encoding="utf-8"))
    lens = np.array(test_set_init['segment_lengths'])
    lens = lens[lens != 0]
    """
    num_per_sec = 1
    num_secs = round(obs.shape[1]/num_per_sec)
    new_len = num_secs*num_per_sec
    obs = obs[0,0:new_len]
    #obs = np.atleast_2d(obs).T
    #lens = np.zeros(num_secs)+num_per_sec
    obs_reshaped = np.reshape(obs,(num_secs,num_per_sec))

    for i in range(obs_reshaped.shape[0]):
        obs_reshaped[i,:] = LabelEncoder().fit_transform(obs_reshaped[i,:])
    print obs_reshaped.shape
    """
    nmm = hmm.MultinomialHMM(pi.shape[0],pi,A,algorithm='viterbi',n_iter=100,verbose=True)
    nmm.emissionprob_ = B
    nmm = nmm.fit(obs,lens)
    logprob,decoded_states = nmm.decode(obs,algorithm='viterbi')
    tag_testing_final(decoded_states,logprob,test_set_name=test_set_name)
    #hmm2 = DiscreteHMM(pi.shape[0], B.shape[1], A, B, pi, init_type='user', precision=np.double, verbose=True)
    #hmm2.train(obs, 100)
    #print "Pi", hmm2.pi
    #print "A", hmm2.A
    #print "B", hmm2.B

def print_tagged_corpus(test_set_name="test"):
    print "print_tagged_corpus"
    test_set_init = json.load(codecs.open("{}{}{}".format(test_set_name, '_final', '.json'), "r", encoding="utf-8"))
    word_list = test_set_init["words"]

    str = u" ".join([u"{} ({}/{})".format(w["word"],w["old_class"][0],w["class"][0]) for w in word_list])
    fp = codecs.open("{}{}{}".format(test_set_name,'_str','.txt'),'w',encoding='utf-8')
    fp.write(str)
    fp.close()

def print_tagged_corpus_to_html(test_set_name="test",test_set_type="init"):
    test_set = json.load(codecs.open("{}_{}.json".format(test_set_name, test_set_type), "r", encoding="utf-8"))
    word_list = test_set["words"]
    str = u"<html><head><style>.t{color:red}.m{color:blue}.b{color:green}.u{color:grey}</style><meta charset='utf-8'></head><body>"
    for word_obj in word_list:
        str += u" <span class='{}'>{}</span>".format(word_obj["class"][0],word_obj["word"])
    str += u"</body></html>"
    fp = codecs.open("{}{}{}".format(test_set_name,'_str','.html'),'w',encoding='utf-8')
    fp.write(str)
    fp.close()


def get_test_set(text_name, limit=-1, strip_html=True, get_bib_links=False):
    mesechta = library.get_index(text_name)
    if limit == -1:
        all_segs = mesechta.all_section_refs()
    else:
        all_segs = mesechta.all_segment_refs()[:limit]
    all_seg_str_list = []
    bib_links = []
    for seg in all_segs:
        all_seg_str_list.append(tokenize_words(seg.text("he").as_string(), strip_html))
        if get_bib_links:
            bib_links.append(seg.linkset().filter("Tanakh"))

    lens = [len(word_list) for word_list in all_seg_str_list]
    return [word for word_list in all_seg_str_list for word in word_list],lens,bib_links

#return start and end indices of best subsequence from sub_seg which matches main_seg

def match_segments(sub_seg, main_seg,with_order=False):
    wl_tuple_list = [best_w_levenshtein(tword,main_seg,weighted_levenshtein_cost) for tword in sub_seg]
    dist_list = [-temp_tup[1]+1.4 for temp_tup in wl_tuple_list]
    start,end,cost = mssl(dist_list)
    if with_order:
        pass #TODO should i take into account order?
    return start,end


def tag_testing_naive(text_name,bib_links,seg_len_list,word_list_in,test_set_name="test"):
    curr_state = ""
    caldb_words = json.load(codecs.open("caldb_words_{}.json".format(text_name), "r", encoding="utf-8"))
    cal_words = caldb_words["words"]
    cal_head_words = caldb_words["head_words"]
    word_list_out = []
    count = 0

    main_i = 0
    while main_i < len(seg_len_list):
        seg_len = seg_len_list[main_i]
        bib_linkset = bib_links[main_i]
        seg = word_list_in[count:count+seg_len]
        count += seg_len

        b_start = -1; b_end = -1
        if len(bib_linkset) > 0:
            for bib_link in bib_linkset:
                #there is an assumption here that the links to Tanakh are always 1
                try:
                    bib_seg = tokenize_words(hebrew.strip_cantillation(Ref(bib_link.refs[1]).text('he').as_string(),strip_vowels=True),strip_html=True)
                    b_start,b_end = match_segments(seg, bib_seg)
                except InputError:
                    continue
        for i,word in enumerate(seg):
            state_switch_pat = re.compile(r"\<big\>\<strong\>[^\<\>]+\</strong\>\</big\>")
            if re.match(state_switch_pat,word):
                if curr_state == "mishnaic":
                    curr_state = "talmudic"
                elif curr_state == "talmudic" or curr_state == "":
                    curr_state = "mishnaic"
            if b_start != -1 and b_end != -1 and i in xrange(b_start,b_end):
                lang = "biblical"
            elif curr_state == "talmudic":
                lang = "unknown"

            elif curr_state == "mishnaic":
                lang = "mishnaic"
            else:
                lang = "unknown"
            word_list_out.append({"word":word,"class":lang})
        main_i += 1

    curr_state = ""
    cal_count = 0
    main_i = 0
    num_rounds_without_matches = 0
    last_match_i = 0
    in_backtrack = False
    while main_i < len(word_list_out) and cal_count + 4 < len(cal_words):
        if num_rounds_without_matches > 15:
            if in_backtrack:
                cal_count -= 4
                in_backtrack = False
            else:
                main_i = last_match_i
                cal_count += 4
                in_backtrack = True
            num_rounds_without_matches = 0
            print "back track!"
        yo = 34
        if cal_count == 12:
            yo += 3432443
        temp_tal_words = word_list_out[main_i:main_i+10]
        cal_ngram_list = []
        for inner_cal_count in range(4):
            temp_ngram = Cal_ngram(cal_words[cal_count+inner_cal_count:cal_count+inner_cal_count+4],cal_head_words[cal_count+inner_cal_count:cal_count+inner_cal_count+4],temp_tal_words,main_i,skip_penalty=min(inner_cal_count,1))
            temp_ngram.find()
            cal_ngram_list.append(temp_ngram)
        best_ngram_score = -1
        best_ngram = None
        best_ngram_index = -1
        for i,cng in enumerate(cal_ngram_list):
            if cng.score < best_ngram_score or best_ngram_score == -1:
                best_ngram_score = cng.score
                best_ngram = cng
                best_ngram_index = i
        if len(best_ngram.matched_indexes) == 0:
            temp_tags = best_ngram.curr_tagged_words
            start_match_pos = best_ngram.start_pos
            num_rounds_without_matches += 1
        else:
            in_backtrack = False
            num_rounds_without_matches = 0
            last_match_i = main_i+len(temp_tags)
            cal_count += (best_ngram_index+1)
            start_match_pos = best_ngram.start_pos
            temp_tags = best_ngram.curr_tagged_words[:best_ngram.matched_indexes[0]-start_match_pos+1]
        word_list_out[start_match_pos:start_match_pos+len(temp_tags)] = temp_tags
        main_i += len(temp_tags)

    doc = {}
    doc["words"] = word_list_out
    fp = codecs.open("{}_naive.json".format(test_set_name), "w", encoding='utf-8')
    json.dump(doc, fp, indent=4, encoding='utf-8', ensure_ascii=False)

def make_cal_db_word_list(text_name):
    word_list_out = []
    hword_list_out = []
    with open("caldb_{}.txt".format(text_name), "r") as caldb:
        for line in caldb:
            line_obj = cal_tools.parseCalLine(line,True,False)
            word_list_out.append(line_obj["word"])
            prefix_list = [pre.replace("_","") for pre in line_obj["prefix"]] if "prefix" in line_obj else []
            hword_list_out.append("".join(prefix_list) + line_obj["head_word"])
    doc = {"words":word_list_out,"head_words":hword_list_out}
    fp = codecs.open("caldb_words_{}.json".format(text_name), "w", encoding='utf-8')
    json.dump(doc, fp, indent=4, encoding='utf-8', ensure_ascii=False)

word1 = u'וימן'
word2 = u'יאמר'
print weighted_levenshtein(word1, word2, weighted_levenshtein_cost)
print get_two_letter_word(word1)

test_set_name = "test_set_5_daf"
text_name = "Shabbat"
#test_discrete()
#make_training_sets("talmudic")
make_cal_db_word_list(text_name)
#print "done making training"
word_list_in,test_set_lens,bib_links = get_test_set(text_name,700,strip_html=False,get_bib_links=True)
tag_testing_naive(text_name,bib_links,test_set_lens,word_list_in,test_set_name)
#tag_testing_init(word_list_in,test_set_lens,test_set_name=test_set_name)
#get_hmm_initial_state(test_set_name=test_set_name)
#run_baum_welch(test_set_name=test_set_name)
#print_tagged_corpus(test_set_name=test_set_name)
print_tagged_corpus_to_html(test_set_name,"naive")