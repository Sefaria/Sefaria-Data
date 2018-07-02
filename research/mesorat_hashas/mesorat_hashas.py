# -*- coding: utf-8 -*-

import regex as re
import cPickle as pickle
import bisect, csv, codecs, bleach, json, operator, os, subprocess
import time as pytime
from collections import OrderedDict
from copy import deepcopy
import numpy as np
from sefaria.model import *
from sources.functions import post_link
from sefaria.system.exceptions import DuplicateRecordError
from sefaria.system.exceptions import InputError
from sefaria.utils import hebrew
import itertools
from data_utilities.dibur_hamatchil_matcher import get_maximum_subset_dh
import logging, glob


def save_links_dicta(category, mesorat_hashas_name):
    mesorat_hashas = json.load(open(mesorat_hashas_name,'rb'))
    """
    new_mesorat_hashas = []
    for l in mesorat_hashas:
        l[0] = l[0].replace(u'<d>',u'')
        l[1] = l[1].replace(u'<d>', u'')
        lr = [Ref(l[0]),Ref(l[1])]
        if lr[0] == None or lr[1] == None:
            continue
        if lr[0].index.title == 'Bava Batra' or lr[1].index.title == 'Bava Batra':
            new_mesorat_hashas += [l]

    objStr = json.dumps(new_mesorat_hashas, indent=4, ensure_ascii=False)
    with open('bava_batra.json', "w") as f:
        f.write(objStr.encode('utf-8'))
    mesorat_hashas = new_mesorat_hashas
    """

    num_dups = 0
    for link in mesorat_hashas:
        for i,l in enumerate(link):
            link[i] = l.replace(u'<d>',u'')
        link_obj = {"auto": True, "refs": link, "anchorText": "", "generated_by": "mesorat_hashas.cs (Dicta) {}".format(category),
                    "type": "Automatic Mesorat HaShas"}
        try:
            Link(link_obj).save()
        except DuplicateRecordError:
            num_dups += 1
            pass  # poopy

    print "num dups {}".format(num_dups)

def save_links_post_request(category):
    query = {"generated_by": "mesorat_hashas.cs (Dicta) {}".format(category), "auto": True, "type": "Automatic Mesorat HaShas"}
    ls = LinkSet(query)
    links = [l.contents() for l in ls]
    post_link(links)


#stop_words = [w[0] for w in json.load(open("word_counts.json", "rb"), encoding='utf8')[:100]]
stop_words = [u'רב',u'רבי',u'בן',u'בר',u'בריה',u'אמר',u'כאמר',u'וכאמר',u'דאמר',u'ודאמר',u'כדאמר',u'וכדאמר',u'ואמר',u'כרב',
              u'ורב',u'כדרב',u'דרב',u'ודרב',u'וכדרב',u'כרבי',u'ורבי',u'כדרבי',u'דרבי',u'ודרבי',u'וכדרבי',u"כר'",u"ור'",u"כדר'",
              u"דר'",u"ודר'",u"וכדר'",u'א״ר',u'וא״ר',u'כא״ר',u'דא״ר',u'דאמרי',u'משמיה',u'קאמר',u'קאמרי',u'לרב',u'לרבי',
              u"לר'",u'ברב',u'ברבי',u"בר'",u'הא',u'בהא',u'הך',u'בהך',u'ליה',u'צריכי',u'צריכא',u'וצריכי',u'וצריכא',u'הלל',u'שמאי']
stop_phrases = [u'למה הדבר דומה',u'כלל ופרט וכלל',u'אלא כעין הפרט',u'מה הפרט',u'כלל ופרט',u'אין בכלל',u'אלא מה שבפרט']
#stop_words = []
def base_tokenizer(base_str):
    base_str = base_str.strip()
    base_str = bleach.clean(base_str, tags=[], strip=True)
    for match in re.finditer(ur'\(.*?\)', base_str):
        if library.get_titles_in_string(match.group()) and len(match.group().split()) <= 5:
            base_str = base_str.replace(match.group(), u"")
            # base_str = re.sub(ur"(?:\(.*?\)|<.*?>)", u"", base_str)
    base_str = re.sub(ur'־',u' ',base_str)
    base_str = re.sub(ur'[A-Za-z]',u'',base_str)
    for phrase in stop_phrases:
        base_str = base_str.replace(phrase,u'')
    word_list = re.split(ur"\s+", base_str)
    word_list = [re.sub(ur'\P{L}',u'',re.sub(ur'((?<!^)\u05D9)',u'',re.sub(ur'ו',u'',w))) for w in word_list if w not in stop_words] #remove non-leading yuds and all vuvs
    word_list = [w for w in word_list if len(w.strip()) > 0]
    return word_list


def generate_dicta_input(category):

    mesechtot_names = get_texts_from_category(category)

    #mesechtot_names = ["Shabbat"]

    for mes in mesechtot_names:
        index = library.get_index(mes)
        vtitle = "Tanach with Text Only" if category == "Tanakh" else None
        mes_tim = index.text_index_map(base_tokenizer,strict=False, lang="he", vtitle=vtitle)

        mes_list = index.nodes.traverse_to_list(lambda n,_: TextChunk(n.ref(), "he", vtitle=vtitle).ja().flatten_to_array() if not n.children else [])
        mes_str_array = [w for seg in mes_list for w in base_tokenizer(seg)]
        mes_str = u" ".join(mes_str_array)

        with codecs.open("dicta_input_{}/{}.txt".format(category.lower(),mes),'wb',encoding='utf8') as f:
            f.write(mes_str)
        pickle.dump(mes_tim, open('dicta_text_index_map/{}.pkl'.format(mes), 'wb'))
        print 'Done with {}'.format(mes)

def generate_dicta_output(category):
    mesechtot_names = get_texts_from_category(category)

    #mesechtot_names = ["Shabbat"]
    mesechtot_names.sort() #put them in alphabetical order

    mesorat_hashas_dicta = {}
    pickle_jar = {}
    for fname in glob.glob("dicta_output/ComparisonResults_*.txt"):
        with codecs.open(fname,'r',encoding='utf8') as f:
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


    for mes in mesechtot_names:
        print mes
        pickle_jar[mes] = pickle.load(open('dicta_text_index_map/{}.pkl'.format(mes)))

    temp_mesorat_hashas = []
    for key in mesorat_hashas_dicta:
        word_indexes = key.split(u'|')
        content = mesorat_hashas_dicta[key].split(u'|')
        match = []
        match_index = []
        is_bad_match = False
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
                try:
                    ref = start_ref.to(end_ref)
                except AssertionError:
                    print start_ref, end_ref, start, end
                    is_bad_match = True
                    break
            match.append(unicode(ref)) # + u' ||| ' + content[iwi])
            match_index.append([start,end])

        if is_bad_match:
            continue

        matchref = [Ref(match[0]),Ref(match[1])]
        temp_mesorat_hashas.append({"match":matchref,"match_index":match_index})

    #remove matches that are subsets
    intersection_map = {}
    for matchobj in temp_mesorat_hashas:
        matchref = matchobj['match']
        for i,m in enumerate(matchref):
            mrange = m.range_list()
            for r in mrange:
                r_str = r.normal()
                if r_str not in intersection_map:
                    intersection_map[r_str] = []
                intersection_map[r_str].append((matchref[i],matchref[int(i == 0)]))


    # filter out all-to-all if you're doing corpus-to-corpus
    if isinstance(category, list) and len(category) >= 2:
        cat1texts = get_texts_from_category(category[0])
        cat2texts = get_texts_from_category(category[1])
        def corp2corp_filter(link):
            link_ref = link['match']
            return (link_ref[0].book in cat1texts and link_ref[1].book in cat2texts) or \
                   (link_ref[0].book in cat2texts and link_ref[1].book in cat1texts)

        temp_mesorat_hashas = filter(corp2corp_filter, temp_mesorat_hashas)

    mesorat_hashas = []
    mesorat_hashas_with_indexes = []
    num_dups = 0
    for matchobj in temp_mesorat_hashas:
        matchref = matchobj['match']
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
            match = [matchref[0].normal().replace("<d>",""),matchref[1].normal().replace("<d>","")]
            mesorat_hashas.append(match)
            mesorat_hashas_with_indexes.append({'match':match,'match_index':matchobj['match_index']})







    category = category if isinstance(category, str) else u'-'.join(category)
    print "Num Subsets: {}".format(num_dups)
    #objStr = json.dumps(mesorat_hashas_dicta, indent=4, ensure_ascii=False)
    #with open('dicta_mesorat_hashas_{}.json'.format(category), "w") as f:
    #    f.write(objStr.encode('utf-8'))
    objStr = json.dumps(mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_{}.json'.format(category), "w") as f:
        f.write(objStr.encode('utf-8'))
    objStr = json.dumps(mesorat_hashas_with_indexes, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_indexes_{}.json'.format(category), "w") as f:
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

def count_matches(mesorat_hashas_name):
    matches = {}
    mesorat_hashas = json.load(open(mesorat_hashas_name, 'rb'))
    for l in mesorat_hashas:
        tup_l = tuple(sorted(l))
        if tup_l not in matches:
            matches[tup_l] = 0
        matches[tup_l] += 1
    print len(matches)

class Mesorah_Match_Ref:

    def __init__(self,a,b):
        """

        :param str a:
        :param str b:
        """
        a = a.replace("<d>","")
        b = b.replace("<d>","")

        yo = sorted((Ref(a),Ref(b)), key=lambda r: r.order_id())
        self.a = yo[0]
        self.b = yo[1]

    def __eq__(self, other):
        return self.a == other.a and self.b == other.b

    def __lt__(self, other):
        if self.a != other.a:
            return self.a.order_id() < other.a.order_id()
        else:
            return self.b.order_id() < other.b.order_id()

    def __gt__(self, other):
        if self.a != other.a:
            return self.a.order_id() > other.a.order_id()
        else:
            return self.b.order_id() > other.b.order_id()

    def normal(self):
        return [self.a.normal(), self.b.normal()]

def compare_mesorat_hashas(compare_a_name, compare_b_name):
    compare_a = json.load(open(compare_a_name,'rb'))
    compare_b = json.load(open(compare_b_name,'rb'))

    def mesorah_match_sort(m1,m2):
        if m1 < m2:
            return -1
        elif m1 > m2:
            return 1
        else:
            return 0

    compare_a_mmr = sorted([Mesorah_Match_Ref(m[0],m[1]) for m in compare_a], cmp=mesorah_match_sort)
    compare_b_mmr = sorted([Mesorah_Match_Ref(m[0],m[1]) for m in compare_b], cmp=mesorah_match_sort)

    inbnota = []
    j = 0
    for i,m in enumerate(compare_b_mmr):
        if i % 1000 == 0:
            print "({}/{})".format(i,len(compare_b))
        while compare_a_mmr[j] < m and j < len(compare_a_mmr) - 1:
            j += 1
        if compare_a_mmr[j] > m:
            inbnota += [m.normal()]
        """

        if m not in compare_a_mmr:
            inbnota.append(compare_b[i])
        """

    print "Num in B not in A: {}".format(len(inbnota))
    objStr = json.dumps(inbnota, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_comparison.json', "w") as f:
        f.write(objStr.encode('utf-8'))


def filter_close_matches(mesorat_hashas_name):
    max_cluster_dist = 20
    filter_only_talmud = False

    mesorat_hashas = json.load(open(mesorat_hashas_name,'rb'))
    new_mesorat_hashas = set()

    seg_map = {}
    all_bad_links = set()
    for l in mesorat_hashas:

        if Ref(l[0]).order_id() < Ref(l[1]).order_id():
            r = l[0]
            ir = 0
        else:
            r = l[1]
            ir = 1


        other_r = Ref(l[int(ir == 0)])

        if r not in seg_map:
            seg_map[r] = set()


        seg_map[r].add((Ref(r),other_r))


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
                    try:
                        dist_mat[i,j] = rray[i][1].distance(rray[j][1])
                    except Exception:
                        dist_mat[i,j] = -1

        clusters = []
        non_clustered = set()
        clustered_indexes = set()
        for i in range(n):
            for j in range(i+1,n):
                if dist_mat[i,j] <= max_cluster_dist and dist_mat[i,j] != -1 and (rray[i][1].type == 'Talmud' or not filter_only_talmud):
                    #we've found an element in a cluster!
                    #figure out if a cluster already exists containing one of these guys
                    found = False
                    for c in clusters:
                        if rray[i][1] in c or rray[j][1] in c:
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


        #if len(clusters) + len(non_clustered) > 5:
        #    print list(non_clustered)[0]

        for c in clusters:
            #add one from each cluster
            other_r = None
            for temp_other_r in c:
                if other_r is None or temp_other_r[1].order_id() < other_r[1].order_id():
                    other_r = temp_other_r

            c.remove(other_r)
            for temp_other_r in c:
                temp_link = tuple(sorted((unicode(temp_other_r[0]), unicode(temp_other_r[1])), key=lambda r: Ref(r).order_id()))
                all_bad_links.add(temp_link)

            temp_link = tuple(sorted((unicode(other_r[0]),unicode(other_r[1])),key=lambda r: Ref(r).order_id()))

            # make sure temp_link isn't within max_dist of itself
            try:
                ref_obj1 = Ref(temp_link[0])
                ref_obj2 = Ref(temp_link[1])
                if (ref_obj1.type == 'Talmud' and ref_obj2.type == 'Talmud') or not filter_only_talmud:
                    temp_dist = ref_obj1.distance(ref_obj2,max_cluster_dist)
                else:
                    temp_dist = -1
            except Exception:
                temp_dist = -1
            if temp_dist == -1: # they're far away from each other
                new_mesorat_hashas.add(temp_link)

        for other_r in non_clustered:
            temp_link = tuple(sorted((unicode(other_r[0]),unicode(other_r[1])),key=lambda r: Ref(r).order_id()))

            # make sure temp_link isn't within max_dist of itself
            try:
                ref_obj1 = Ref(temp_link[0])
                ref_obj2 = Ref(temp_link[1])
                if (ref_obj1.type == 'Talmud' and ref_obj2.type == 'Talmud') or not filter_only_talmud:
                    temp_dist = ref_obj1.distance(ref_obj2,max_cluster_dist)
                else:
                    temp_dist = -1
            except Exception:
                temp_dist = -1
            if temp_dist == -1: # they're far away from each other
                new_mesorat_hashas.add(temp_link)


    filtered_mesorat_hashas = []
    for l in new_mesorat_hashas:
        if l not in all_bad_links:
            lray = list(l)
            filtered_mesorat_hashas += [lray]
        else:
            print l



    print "Old: {} New: {} Difference: {}".format(len(mesorat_hashas),len(new_mesorat_hashas),len(mesorat_hashas)-len(new_mesorat_hashas))
    objStr = json.dumps(filtered_mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_clustered_9_words.json', "w") as f:
        f.write(objStr.encode('utf-8'))

def filter_pasuk_matches(category, mesorat_hashas_name):

    def bible_tokenizer(s):

        words = re.split(ur'\s+',re.sub(u'\u05be', u' ',s))
        words = filter(lambda w: not (u'[' in w and u']' in w) and w != u'',words) # strip out kri
        return words

    def talmud_tokenizer(s):
        for match in re.finditer(ur'\(.*?\)', s):
            if library.get_titles_in_string(match.group()) and len(match.group().split()) <= 5:
                s = s.replace(match.group(), u"")
        for phrase in stop_phrases:
            s = s.replace(phrase, u'')
        words = [w for w in re.split(ur'\s+',s) if w not in stop_words and w != u'']
        return words


    num_nonpasuk_match_words = 4
    mesorat_hashas = json.load(open(mesorat_hashas_name, 'rb'))

    mesechtot_names = get_texts_from_category(category)

    pickle_jar = {}
    for mes in mesechtot_names:
        pickle_jar[mes] = pickle.load(open('dicta_text_index_map/{}.pkl'.format(mes)))

    matches = {}
    for l in mesorat_hashas:
        tup_l = tuple(sorted(l['match']))
        if tup_l not in matches:
            try:
                matches[tup_l] = (Ref(tup_l[0]), Ref(tup_l[1]),l['match_index'])
            except InputError:
                pass
    #mesorat_hashas = [{'match':['Berakhot 4a:1-3','Berakhot 5a:1-3'],'match_index':[[1,2],[3,4]]}]


    bible_set_cache = {}
    text_array_cache = {}
    bible_array_cache = {}

    new_mesorat_hashas = []
    bad_mesorat_hashas = []
    for ildict, (match_str_tup, (ref1, ref2, inds)) in enumerate(matches.items()):
        if ildict % 100 == 0:
            print "{}/{}--------------------------------------------".format(ildict,len(mesorat_hashas))
        bad_match = False
        m = ref1.index.title
        ind_list = pickle_jar[m][0]
        for ir,rr in enumerate([ref1,ref2]):
            try:
                str_r = str(rr)
            except UnicodeEncodeError:
                continue

            if str_r not in text_array_cache:
                tt = talmud_tokenizer(rr.text("he").ja().flatten_to_string())
                text_array_cache[str_r] = tt
                biblset = rr.linkset().filter("Tanakh")
                bible_set_cache[str_r] = biblset
            else:
                tt = text_array_cache[str_r]
                biblset = bible_set_cache[str_r]



            s = ind_list[bisect.bisect_right(ind_list, inds[ir][0]) - 1]
            os = inds[ir][0] - s
            oe = inds[ir][1] - s
            match_len = oe-os + 1

            tb = {yo: 0 for yo in xrange(os,oe+1)}
            tt_slice = tt[os:oe+1]

            for bl in biblset:
                try:
                    if not Ref(bl.refs[1]).is_segment_level():
                        #print bl.refs[1]
                        continue
                    bt = bible_tokenizer(Ref(bl.refs[1]).text('he','Tanach with Text Only').as_string()) if bl.refs[1] not in bible_array_cache else bible_array_cache[bl.refs[1]]
                except InputError as e:
                    print e
                    print u"This ref is problematic {} on this Talmud ref {}".format(bl.refs[1],unicode(rr))
                    continue
                bs,be = get_maximum_subset_dh(tt_slice,bt,threshold=85)
                if bs != -1 and be != -1:
                    for ib in xrange(bs+os,be+os):
                        tb[ib] = 1


            #e = bisect.bisect_right(ind_list, inds[ir][1])-1


            num_pasuk  = sum(tb.values())
            if match_len - num_pasuk < num_nonpasuk_match_words:
                bad_match = True
                break

        if not bad_match:
            new_mesorat_hashas.append(list(match_str_tup))
        else:
            bad_mesorat_hashas.append(list(match_str_tup))

    print bad_mesorat_hashas
    print "Old: {} New: {} Difference: {}".format(len(mesorat_hashas), len(new_mesorat_hashas),
                                                  len(mesorat_hashas) - len(new_mesorat_hashas))

    objStr = json.dumps(bad_mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_pasuk_filtered_bad.json', "w") as f:
        f.write(objStr.encode('utf-8'))
    objStr = json.dumps(new_mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_pasuk_filtered.json', "w") as f:
        f.write(objStr.encode('utf-8'))

def remove_mishnah_talmud_dups(mesorat_hashas_name):
    mesorat_hashas = json.load(open(mesorat_hashas_name, 'rb'))
    mishnah_set = LinkSet({'type': 'mishnah in talmud'}).array()
    mishnah_set = [(Ref(ms.refs[0]),Ref(ms.refs[1])) for ms in mishnah_set]


    new_mesorat_hashas = []
    for l in mesorat_hashas:
        is_bad_link = False
        try:
            lr = sorted([Ref(l[0]),Ref(l[1])], key=lambda x: x.order_id())
        except InputError:
            continue
        if lr[0] is None or lr[1] is None:
            continue
        if lr[0].type == 'Mishnah' and lr[1].type == 'Talmud':
            for mish_link in mishnah_set:
                if lr[0].overlaps(mish_link[0]) and lr[1].overlaps(mish_link[1]):
                    is_bad_link = True
                    break

        if not is_bad_link:
            new_mesorat_hashas += [l]



    print "Old: {} New: {} Difference: {}".format(len(mesorat_hashas), len(new_mesorat_hashas),
                                                  len(mesorat_hashas) - len(new_mesorat_hashas))
    objStr = json.dumps(new_mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_mishnah_filtered.json', "w") as f:
        f.write(objStr.encode('utf-8'))

def dicta_all_to_all(base_path, comp_path, aaa, min_thresh, char_inds):
    os.chdir('dicta_output/')
    for f in glob.glob("*.txt"):
       os.remove(f)
    cmd = "mono FindAllSimilarPassages.exe -basepath=../{} -comppath=../{} -allagainstall={} -minthreshold={} -charindicies={}".format(base_path, comp_path, aaa, min_thresh, char_inds)
    process = subprocess.Popen(cmd.split(), stdin=subprocess.PIPE)
    output, error = process.communicate("")
    #print output
    os.chdir('../')

def get_texts_from_category(category):
    if isinstance(category,str):
        categories = [category]
    else:
        categories = category

    text_names = []
    for cat in categories:
        if cat == "Talmud":
            text_names += [name for name in library.get_indexes_in_category("Talmud") if
                           not "Jerusalem " in name and not "Ritva " in name and not "Rif " in name]

        elif cat == "Mishnah" or cat == "Tosefta" or cat == "Tanakh":
            text_names += library.get_indexes_in_category(cat)
        elif cat == "All":
            cats = ['Bavli','Mishnah', 'Tosefta','Midrash Rabbah']
            text_names += ["Mekhilta d'Rabbi Yishmael", 'Seder Olam Rabbah','Sifra' ,'Mekhilta DeRabbi Shimon Bar Yochai','Sifrei Bamidbar','Megillat Taanit','Otzar Midrashim','Pirkei DeRabbi Eliezer','Pesikta D\'Rav Kahanna','Tanna Debei Eliyahu Rabbah','Tanna debei Eliyahu Zuta','Pesikta Rabbati']
            for c in cats:
                text_names += library.get_indexes_in_category(c)
        elif cat == "Debug":
            text_names += ["Berakhot"]

        else:
            text_names += []

    return text_names

def filter_pasuk_matches2(cat1, cat2):
    class TanakhLink:

        def __init__(self, tref, to_ref, tref_index):
            self.tref = tref
            self.oref = Ref(tref)
            self.original_to_ref = to_ref
            self.to_ref_map = {
                to_ref: tref_index
            }

        def __eq__(self, other):
            return self.__hash__() == other.__hash__()

        def __hash__(self):
            return self.oref.order_id().__hash__()

    cat1 = cat1 if isinstance(cat1, str) else u'-'.join(cat1)
    cat2 = cat2 if isinstance(cat2, str) else u'-'.join(cat2)
    mes_shas1 = json.load(open('mesorat_hashas_indexes_{}.json'.format(cat1), 'rb'))
    mes_shas2 = json.load(open('mesorat_hashas_indexes_{}.json'.format(cat2), 'rb'))


    def get_tanakh_links(r1, r2):
        tan1 = {}
        tan2 = {}
        for m in mes_shas2:
            if m['match'][0] == r1:
                tan1[m['match'][1]] = TanakhLink(m['match'][1], r1, m['match_index'][0])
            elif m['match'][1] == r1:
                tan1[m['match'][0]] = TanakhLink(m['match'][0], r1, m['match_index'][1])

            if m['match'][0] == r2:
                tan2[m['match'][1]] = TanakhLink(m['match'][1], r2, m['match_index'][0])
            elif m['match'][1] == r2:
                tan2[m['match'][0]] = TanakhLink(m['match'][0], r2, m['match_index'][1])

        inter_keys = set(tan1.keys()).intersection(set(tan2.keys()))
        inter = []

        if len(inter_keys) == 0:
            for temp_tan in tan1.values():
                temp_map = temp_tan.to_ref_map[temp_tan.original_to_ref]
                if temp_map[1] - temp_map[0] + 1 > 6:
                    inter += [temp_tan]
            for temp_tan in tan2.values():
                temp_map = temp_tan.to_ref_map[temp_tan.original_to_ref]
                if temp_map[1] - temp_map[0] + 1 > 6:
                    inter += [temp_tan]
        else:
            for temp_int in inter_keys:
                temp_tan1 = tan1[temp_int]
                temp_tan2 = tan2[temp_int]

                temp_tan1.to_ref_map[temp_tan2.original_to_ref] = temp_tan2.to_ref_map[temp_tan2.original_to_ref]
                inter += [temp_tan1]

        return inter

    def inner_pasuk_filter(m):
        tan_links = get_tanakh_links(m['match'][0], m['match'][1])


        is_bad_match = False
        for i, r in enumerate(m['match']):
            ind_dict = {ind: 0 for ind in xrange(m['match_index'][i][0],m['match_index'][i][1] + 1)}
            for temp_tan in tan_links:
                try:
                    temp_map = temp_tan.to_ref_map[r]
                except KeyError:
                    continue

                for j in xrange(temp_map[0],temp_map[1]+1):
                    try:
                        ind_dict[j] = 1
                    except KeyError:
                        pass

            num_in_pasuk = sum([v for k, v in ind_dict.items()])
            num_in_match = m['match_index'][i][1] - m['match_index'][i][0] + 1

            if num_in_match - num_in_pasuk < 4:
                is_bad_match = True
                break

        return not is_bad_match

    new_mesorat_hashas = []
    bad_mesorat_hashas = []
    for i, m in enumerate(mes_shas1):
        if i % 1000 == 0:
            print "{}/{}".format(i,len(mes_shas1))

        if inner_pasuk_filter(m):
            new_mesorat_hashas += [m['match']]
        else:
            bad_mesorat_hashas += [m['match']]

    print bad_mesorat_hashas
    print "Old: {} New: {} Difference: {}".format(len(mes_shas1), len(new_mesorat_hashas),
                                                  len(mes_shas1) - len(new_mesorat_hashas))

    objStr = json.dumps(bad_mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_pasuk_filtered_bad2.json', "w") as f:
        f.write(objStr.encode('utf-8'))
    objStr = json.dumps(new_mesorat_hashas, indent=4, ensure_ascii=False)
    with open('mesorat_hashas_pasuk_filtered2.json', "w") as f:
        f.write(objStr.encode('utf-8'))

def sort_n_save(mesorat_hashas_name):
    mesorat_hashas = json.load(open(mesorat_hashas_name, 'rb'))
    def mesorah_match_sort(m1,m2):
        if m1 < m2:
            return -1
        elif m1 > m2:
            return 1
        else:
            return 0

    sorted_match_refs = sorted([Mesorah_Match_Ref(m[0],m[1]) for m in mesorat_hashas], cmp=mesorah_match_sort)
    sorted_mh = [[mmr.a.normal(), mmr.b.normal()] for mmr in sorted_match_refs]
    objStr = json.dumps(sorted_mh, indent=4, ensure_ascii=False)
    with open(mesorat_hashas_name, "wb") as f:
        f.write(objStr.encode('utf-8'))

#make_mesorat_hashas()
#minify_mesorat_hashas()
#find_most_quoted()
#save_links()

#clean_mesorat_hashas()
#find_bad_bad_gemaras()


#generate_dicta_input("Debug")
#dicta_all_to_all('dicta_input_debug/', '', True, 9, False)
#generate_dicta_output(["Debug"])
#filter_pasuk_matches2("Talmud", ["Tanakh", "Talmud"])
#filter_pasuk_matches('Debug','mesorat_hashas_indexes_Debug.json')
#filter_close_matches('mesorat_hashas_pasuk_filtered.json')
#remove_mishnah_talmud_dups('mesorat_hashas_clustered_9_words.json')
#save_links_dicta("All", 'mesorat_hashas_mishnah_filtered_ALL_READY_FOR_PROD.json')
compare_mesorat_hashas('mesorat_hashas_clustered_DICTA.json', 'mesorat_hashas_clustered_SEFARIA.json')
#save_links_post_request("All")
#count_matches('mesorat_hashas_mishnah_filtered.json')

#sort_n_save('mesorat_hashas_clustered_SEFARIA.json')
#sort_n_save('mesorat_hashas_clustered_DICTA.json')
