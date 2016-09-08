# -*- coding: utf-8 -*-
import sys
import re
import json
import codecs
import cal_tools
import itertools
#from hmmlearn import hmm
#from sklearn.preprocessing import LabelEncoder

from sefaria.model import *
from sefaria.utils import hebrew
from sefaria.system.exceptions import InputError

#sys.path.append("../hmm")
#from hmm.discrete.DiscreteHMM import DiscreteHMM

import numpy as np

#this class is garbage now...i think
class Cal_ngram:

    def __init__(self,cal_words,prev_tagged_words,start_pos,skip_penalty):
        self.cal_words = cal_words
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
                if self.is_match(self.cal_words[curr_pos],word):
                    self.curr_tagged_words.append({"word":word,"class":"talmud"})
                    self.matched_indexes.append(self.start_pos+i)
                    curr_pos += 1
                    if len(self.matched_indexes) == len(self.cal_words):
                        break
                else:
                    self.curr_tagged_words.append({"word":word,"class":"unknown"})
            self.num_words_passed += 1

        self.score = max(self.matched_indexes[:self.skip_penalty+1]) if len(self.matched_indexes) > 0 else self.start_pos + len(self.prev_tagged_words)

    def is_match(self,cw,tw):
        dist = weighted_levenshtein(cw,tw,weighted_levenshtein_cost)
        return dist < 1.4

letter_freqs_list = [u'י',u'ו',u'א',u'מ',u'ה',u'ל',u'ר',u'נ',u'ב',u'ש',u'ת',u'ד',u'כ',u'ע',u'ח',u'ק',u'פ',u'ס',u'ט',u'ז',u'ג',u'צ']

sofit_map = {
    u'ך': u'כ',
    u'ם': u'מ',
    u'ן': u'נ',
    u'ף': u'פ',
    u'ץ': u'צ',
}

abbrev_map = {
    u"דר'":u"דרב",
    u"ר'":u"רב",
    u"ד'":u"ארבע",
    u"ה'":u"חמש",
    u"אקר'":u"אקרא",
    u"בריש'":u"ברישא",
    u"דילמ'":u"דילמא",
    u"אמתני'":u"אמתניתין",
    u"ש'מ":u"שמע מינה",
    u"ואיבעי'":u"ואיבעית",
    u"אימ'":u"אימא",
    u"קמ'ל":u"קא משמע לן",
    u"והקמ'ל":u"והקא משמע לן",
    u"ת'ש":u"תא שמע",
    u"ת'ר":u"תנו רבנן",
    u"דת'ר":u"דתנו רבנן",
    u"ס'ד":u"סלקא דעתך",
    u"למ'ד":u"למאן דאמר",
    u"מ'ט":u"מאי טעמא",
    u"ומ'ט":u"ומאי טעמא",
    u"ת'ק":u"תנא קמא",
    u"קב'ה":u"קדוש ברוך הוא",
    u"מ'ל":u"מנא לאן"

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

def weighted_levenshtein_cost(c1, c2=None,min_cost=1.0):
    c1 = sofit_swap(c1)
    c2 = sofit_swap(c2)
    w1 = letter_freqs[c1] if c1 in letter_freqs else 0.0
    if c2:
        w2 = letter_freqs[c2] if c2 in letter_freqs else 0.0
        return w1 + min_cost if w1 > w2 else w2 + min_cost
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

def weighted_levenshtein(s1,s2,cost_fn,min_cost=1.0):
    if s1 == s2:
        return 0
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)

    v0 = range(len(s2)+1)
    v1 = [0 for _ in xrange(len(s2)+1)]

    for i in xrange(len(s1)):
        v1[0] = i + 1
        for j in xrange(len(s2)):
            cost_sub = 0.0 if (s1[i] == s2[j]) else cost_fn(s1[i],s2[j],min_cost=min_cost)
            cost_ins = cost_fn(s2[j],min_cost=min_cost)
            cost_del = cost_fn(s1[i],min_cost=min_cost)
            v1[j+1] = min(v1[j]+cost_ins,min(v0[j+1]+cost_del,v0[j]+cost_sub))

        vtemp = v0
        v0 = v1
        v1 = vtemp

    return v0[len(s2)]

def sofit_swap(C):
    return sofit_map[C] if C in sofit_map else C


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
    str = str.replace('"',"'")
    word_list = filter(bool,re.split(r"[\s\:\-\,\.\;\(\)\[\]\{\}]",str))
    return word_list


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
    str = u"<html><head><style>.t{color:red}.m{color:blue}.b{color:green}.u{color:grey}.s{color:purple}</style><meta charset='utf-8'></head><body>"
    for word_obj in word_list:
        str += u" <span class='{}'>{}</span>".format(word_obj["class"][0],word_obj["word"])
    str += u"</body></html>"
    fp = codecs.open("{}{}{}".format(test_set_name,'_str','.html'),'w',encoding='utf-8')
    fp.write(str)
    fp.close()

def print_tagged_corpus_to_html_table(text_name,ref_list,num_daf_per_doc,test_set_name="test",test_set_type="init"):
    cal_dh_root = "../../dibur_hamatchil/dh_source_scripts/cal_matcher_output"

    iref = 0
    while iref < len(ref_list):
        str = u"<html><head><style>h1{text-align:center;background:grey}td{text-align:center}table{margin-top:20px;margin-bottom:20px;margin-right:auto;margin-left:auto;width:1200px}.missed{color:white;background:red}.b{color:green}.m{color:blue}.sef{color:black}.cal{color:grey}.good-cal{color:red}.good-jba{background:#eee;color:red}.POS{color:orange}</style><meta charset='utf-8'></head><body>"

        start_daf = ""
        end_daf = ""
        for idaf in xrange(num_daf_per_doc):
            if iref >= len(ref_list): break
            ref = ref_list[iref]
            daf = ref.__str__().replace("{} ".format(text_name),"").encode('utf8')
            str += u"<h1>DAF {}</h1>".format(daf)
            str += u"<table>"
            if idaf == 0: start_daf = daf
            if idaf == num_daf_per_doc-1: end_daf = daf

            test_set = json.load(codecs.open("{}/{}/test_set/{}_{}_{}.json".format(cal_dh_root,text_name,test_set_name, test_set_type,daf), "r", encoding="utf-8"))
            word_list = test_set["words"]
            missed_word_list = test_set["missed_words"]
            missed_dic = {wo["index"]:wo["word"] for wo in missed_word_list}

            sef_count = 0
            cal_count = 0
            while sef_count < len(word_list):
                row_obj = word_list[sef_count:sef_count+10]
                row_sef = u"<tr class='sef'><td>{}</td>".format(u"</td><td>".join([wo["word"] for wo in reversed(row_obj)]))
                row_sef += u"<td>({}-{})</td></tr>".format(sef_count,sef_count+len(row_obj)-1)


                row_cal = u"<tr class='cal'>"
                start_cal_count = cal_count
                for wo in reversed(row_obj):
                    while cal_count in missed_dic:
                        cal_count += 1
                    if "cal_word" in wo:
                        cal_count += 1
                        row_cal += u"<td class='good-cal'>{} <span class='POS'>({})</span></td>".format(wo["cal_word"],wo["POS"])
                    elif "jba_word" in wo:
                        row_cal += u"<td class='good-jba'>{} <span class='POS'>({})</span><br>{}</td>".format(wo["jba_word"],wo["POS"],wo["head_word"])
                    else:
                        row_cal += u"<td class='{}'>{}</td>".format(wo["class"][0],wo["class"][0:3].upper())
                row_cal += u"<td>({}-{})</td>".format(start_cal_count,cal_count-1)
                row_cal += u"</tr>"

                str += row_sef
                str += row_cal
                sef_count += 10
            str += u"</table>"

            str += u"<table>"
            count = 0
            while count < len(missed_word_list):
                row_obj = missed_word_list[count:count+10]
                word_str = [u"{}:{}".format(wo["word"],wo["index"]) for wo in reversed(row_obj)]
                row_missed = u"<tr class='missed'><td>{}</td></tr>".format(u"</td><td>".join(word_str))
                str += row_missed
                count += 10
            str += u"</table>"
            iref += 1
        str += u"</body></html>"
        fp = codecs.open("{}/{}/html_table/{}_{}-{}.html".format(cal_dh_root,text_name,test_set_name,start_daf,end_daf),'w',encoding='utf-8')
        fp.write(str)
        fp.close()

def get_ref_list(text_name,start_ref=None,end_ref=None):
    mesechta = library.get_index(text_name)
    if start_ref is None:
        start_ref = mesechta.all_section_refs()[0]
    if end_ref is None:
        end_ref = mesechta.all_section_refs()[-1]

    ref_list = []
    curr_ref = start_ref
    finished_yet = False
    while not finished_yet and not curr_ref is None:
        finished_yet = curr_ref == end_ref
        ref_list.append(curr_ref)
        curr_ref = curr_ref.next_section_ref()

    return ref_list

def get_test_set(text_name, ref_list, strip_html=True, get_bib_links=False):
    mesechta = library.get_index(text_name)

    all_seg_str_list = []
    bib_links = []
    for ref in ref_list:
        temp_seg_str_list = []
        temp_bib_links = []
        for seg in ref.all_subrefs():
            temp_seg_str_list.append(tokenize_words(seg.text("he").as_string(), strip_html))
            if get_bib_links:
                temp_bib_links.append(seg.linkset().filter("Tanakh"))
        all_seg_str_list.append(temp_seg_str_list)
        if get_bib_links:
            bib_links.append(temp_bib_links)



    #i like array comprehensions...
    lens = [[len(word_list) for word_list in word_list_list] for word_list_list in all_seg_str_list]
    return [[word for word_list in word_list_list for word in word_list] for word_list_list in all_seg_str_list ],lens,bib_links

#return start and end indices of best subsequence from sub_seg which matches main_seg

def match_segments(sub_seg, main_seg,threshold=1.4):
    wl_tuple_list = [best_w_levenshtein(tword,main_seg,weighted_levenshtein_cost) for tword in sub_seg]
    dist_list = [-temp_tup[1]+threshold for temp_tup in wl_tuple_list]
    start,end,cost = mssl(dist_list)
    return start,end

def match_segments_without_order(sub_seg, main_seg,threshold=1.4):
    '''
    right now, for a match returned from the dibur hamatchil matcher.
    :param sub_seg: list(str)
    :param main_seg: list(str)
    :param threshold: levenshtein score above which the word is no longer considered matching
    :return: gives me the indexes relative to the words in sub_seg of where words from sub_seg match in main_seg
    -1 if the corresponding sub_seg word has no match
    '''

    #writing this a bit more verbosely to make it a bit clearer
    wl_tuple_list = [best_w_levenshtein(w,sub_seg,weighted_levenshtein_cost) for w in main_seg]
    dist_list = [-temp_tup[1]+threshold for temp_tup in wl_tuple_list]
    index_list = [temp_tup[0] for temp_tup in wl_tuple_list]
    index_list = [index_list[i] if dist_list[i] >= 0 else -1 for i in range(len(wl_tuple_list))]

    return index_list

def tag_testing_naive(text_name,bib_links,seg_len_list,word_list_in,ref_list,test_set_name="test"):
    cal_dh_root = "../../dibur_hamatchil/dh_source_scripts/cal_matcher_output"
    jba_count = 0
    curr_state = "" #state should be retained, even b/w dafs
    #caldb_words = json.load(codecs.open("caldb_words_{}.json".format(text_name), "r", encoding="utf-8"))
    for iref,ref in enumerate(ref_list):
        curr_seg_len_list = seg_len_list[iref]
        curr_bib_links = bib_links[iref]
        curr_word_list_in = word_list_in[iref]

        daf = ref.__str__().replace("{} ".format(text_name),"").encode('utf8')

        try:
            cal_pre_tagged_words = \
            json.load(codecs.open("{}/{}/lang_naive_talmud/lang_naive_talmud_{}.json".format(cal_dh_root,text_name,daf), "r", encoding="utf8"))
        except IOError:
            cal_pre_tagged_words = None

        jbaforms = json.load(codecs.open("JBAHashtable.json","rb",encoding='utf8'))

        word_list_out = []
        count = 0
        main_i = 0

        while main_i < len(curr_seg_len_list):
            seg_len = curr_seg_len_list[main_i]
            bib_linkset = curr_bib_links[main_i]
            seg = curr_word_list_in[count:count+seg_len]
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

                cal_obj = None
                if b_start != -1 and b_end != -1 and i in xrange(b_start,b_end):
                    lang = "biblical"
                elif curr_state == "talmudic":
                    #lang = cal_pre_tagged_words[count-seg_len+i]["class"]
                    if not cal_pre_tagged_words is None:
                        try:
                            cal_obj = cal_pre_tagged_words["words"][count-seg_len+i]
                            if cal_obj["class"] == "unknown":
                                if word in jbaforms and len(jbaforms[word]) == 1 and False:
                                    temp_cal_obj = jbaforms[word][0].copy()
                                    if temp_cal_obj["word"][-1] != "'" and temp_cal_obj["head_word"][-1] != "_":
                                        cal_obj = temp_cal_obj
                                        cal_obj["jba_word"] = cal_obj["word"]
                                        cal_obj["word"] = word
                                        cal_obj["class"] = "talmud"
                                        jba_count += 1
                        except IndexError:
                            break
                elif curr_state == "mishnaic":
                    lang = "mishnaic"
                else:
                    lang = "unknown"

                if cal_obj:
                    word_list_out.append(cal_obj)
                else:
                    word_list_out.append({"word":word,"class":lang})
            main_i += 1
        missed_words = [] if cal_pre_tagged_words is None else cal_pre_tagged_words["missed_words"]
        doc = {"words":word_list_out,"missed_words":missed_words}
        fp = codecs.open("{}/{}/test_set/{}_naive_{}.json".format(cal_dh_root,text_name,test_set_name,daf), "w", encoding='utf-8')
        json.dump(doc, fp, indent=4, encoding='utf-8', ensure_ascii=False)

    print "NUM JBA WORDS: {}".format(jba_count)


def make_cal_db_word_list(text_name):
    word_list_out = []
    line_len_list = []
    curr_line = -1
    num_words_on_line = 0
    with open("caldb_{}.txt".format(text_name), "r") as caldb:
        for line in caldb:
            line_obj = cal_tools.parseCalLine(line,True,False)
            word = abbrev_map[line_obj["word"]] if line_obj["word"] in abbrev_map else line_obj["word"]
            word_list = word.split(" ")
            if curr_line == -1:
                curr_line = line_obj["line_num"]
            if curr_line != line_obj["line_num"]:
                line_len_list.append(num_words_on_line)
                num_words_on_line = len(word_list)
                curr_line = line_obj["line_num"]
            else:
                num_words_on_line += len(word_list)
            for w in word_list:
                word_list_out.append(w)
            #unabbrev_list_out.append(abbrev_map[line_obj["word"]] if line_obj["word"] in abbrev_map else "")
            prefix_list = [pre.replace("_","") for pre in line_obj["prefix"]] if "prefix" in line_obj else []
            #hword_list_out.append("".join(prefix_list) + line_obj["head_word"])
    line_len_list.append(num_words_on_line) #for the last line
    doc = {"words":word_list_out,"line_lens":line_len_list}
    fp = codecs.open("caldb_words_{}.json".format(text_name), "w", encoding='utf-8')
    json.dump(doc, fp, indent=4, encoding='utf-8', ensure_ascii=False)


