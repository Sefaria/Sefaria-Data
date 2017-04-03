# -*- coding: utf-8 -*-
import re, bleach, json
from sefaria.model import *
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from collections import defaultdict
from sefaria.system.exceptions import PartialRefInputError, InputError
from sefaria.utils.hebrew import strip_cantillation
from data_utilities.util import WeightedLevenshtein

class Link_Disambiguator:
    def __init__(self):
        self.stop_words = []
        self.levenshtein = WeightedLevenshtein()


    def tokenize_words(self, base_str):
        base_str = base_str.strip()
        base_str = strip_cantillation(base_str, strip_vowels=True)
        base_str = bleach.clean(base_str, tags=[], strip=True)
        for match in re.finditer(ur'\(.*?\)', base_str):
            if library.get_titles_in_string(match.group()) and len(match.group().split()) <= 5:
                base_str = base_str.replace(match.group(), u"")
                # base_str = re.sub(ur"(?:\(.*?\)|<.*?>)", u"", base_str)
        base_str = re.sub(ur'־', u' ', base_str)
        base_str = re.sub(ur'[A-Za-z.]', u'', base_str)
        word_list = re.split(ur"\s+", base_str)
        word_list = [w for w in word_list if len(w.strip()) > 0 and w not in self.stop_words]
        return word_list

    def get_score(self, words_a, words_b):
        normalizingFactor = 100
        smoothingFactor = 1
        ImaginaryContenderPerWord = 22

        dist = self.levenshtein.calculate(u" ".join(words_a), u" ".join(words_b),normalize=False)
        score = 1.0 * (dist + smoothingFactor) / (len(words_a) + smoothingFactor) * normalizingFactor

        dumb_score = (ImaginaryContenderPerWord * len(words_a)) - score
        return dumb_score
        #return 1.0 * (len(words_a) + len(words_b)) / 2

    def find_indexes_with_ambiguous_links(self):
        tanakh_books = library.get_indexes_in_category("Tanakh")
        query = {
            "refs": re.compile(ur'^({}) \d+$'.format(u'|'.join(tanakh_books)))
        }
        linkset = LinkSet(query)
        index_dict = defaultdict(int)
        for l in linkset:
            try:
                index_dict[Ref(l.refs[0]).index.title] += 1
            except PartialRefInputError:
                pass
            except InputError:
                pass

        items = sorted(index_dict.items(), key=lambda x: x[1])
        for i in items:
            print i

    def get_ambiguous_segments(self):
        tanakh_books = library.get_indexes_in_category("Tanakh")
        query = {
            "refs": re.compile(ur'^({}) \d+$'.format(u'|'.join(tanakh_books)))
        }
        linkset = LinkSet(query)
        segment_map = defaultdict(list)
        for l in linkset:
            try:
                segment_map[Ref(l.refs[0]).normal()] += [Ref(l.refs[1]).normal()]
            except PartialRefInputError:
                pass
            except InputError:
                pass

        objStr = json.dumps(segment_map, indent=4, ensure_ascii=False)
        with open('ambiguous_segments.json', "w") as f:
            f.write(objStr.encode('utf-8'))


    def disambiguate_segment(self, main_tc, tc_list):
        matcher = ParallelMatcher(self.tokenize_words,max_words_between=1, min_words_in_match=3, ngram_size=3,
                                       parallelize=False, calculate_score=self.get_score, all_to_all=False, verbose=False)
        try:
            match_list = matcher.match(tc_list=[main_tc] + tc_list, return_obj=True)
        except ValueError:
            print "Skipping {}".format(main_tc)
            return [], [] #[[main_tc._oref.normal(), tc_list[i]._oref.normal()] for i in range(len(tc_list))]
        best_list = []
        for tc in tc_list:
            best = None
            best_score = 0
            for match in match_list:
                #print match
                if match.score > best_score and match.b.ref == main_tc._oref and match.a.ref.section_ref() == tc._oref:
                    best = match
                    best_score = match.score

            best_list += [best]

        good = [[mm.a.ref.normal(), mm.b.ref.normal()] for mm in best_list if not mm is None]
        bad = [[main_tc._oref.normal(), tc_list[i]._oref.normal()] for i, mm in enumerate(best_list) if mm is None]
        #print good
        return good, bad

ld = Link_Disambiguator()
#ld.find_indexes_with_ambiguous_links()
#ld.get_ambiguous_segments()

ambig_dict = json.load(open("ambiguous_segments.json",'rb'))
good = []
bad = []
for iambig, (main_str, tref_list) in enumerate(ambig_dict.items()[:100]):
    if iambig % 50 == 0:
        print "{}/{}".format(iambig, len(ambig_dict))
    main_tc = Ref(main_str).text("he")
    tc_list = [Ref(tref).text("he") for tref in tref_list]
    temp_good, temp_bad = ld.disambiguate_segment(main_tc, tc_list)
    good += temp_good
    bad += temp_bad

objStr = json.dumps(good, indent=4, ensure_ascii=False)
with open('unambiguous_links.json', "w") as f:
    f.write(objStr.encode('utf-8'))

objStr = json.dumps(bad, indent=4, ensure_ascii=False)
with open('still_ambiguous_links.json', "w") as f:
    f.write(objStr.encode('utf-8'))


#tc_list = [Ref("Zohar 1:70b:7").text("he"), Ref("Song of Songs 1").text("he")] #{'match_index': [[5, 7], [11, 13]], 'score': 81, 'match': [u'Zohar 1:70b:7', u'Song of Songs 1:3']}
#tc_list = [Ref("Zohar 1:70b:9").text("he"), Ref("Genesis 1").text("he")] #{'match_index': [[27, 32], [106, 111]], 'score': 96, 'match': [u'Genesis 1:4', u'Zohar 1:70b:9']}
