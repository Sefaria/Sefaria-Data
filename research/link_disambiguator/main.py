# -*- coding: utf-8 -*-
import sys
import os
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
SEFARIA_PROJECT_PATH = "/var/www/readonly"
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"


import re, json, codecs, unicodecsv, heapq, random, regex, math, cProfile, pstats
import django
django.setup()
from sefaria.model import *
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from collections import defaultdict, OrderedDict
from sefaria.system.exceptions import PartialRefInputError, InputError, NoVersionFoundError
from sefaria.utils.hebrew import strip_cantillation
from data_utilities.util import WeightedLevenshtein
from data_utilities.dibur_hamatchil_matcher import ComputeLevenshteinDistanceByWord




def argmax(iterable, n=1):
    if n==1:
        return [max(enumerate(iterable), key=lambda x: x[1])[0]]
    else:
        return heapq.nlargest(n, xrange(len(iterable)), iterable.__getitem__)


class Link_Disambiguator:
    stop_words = [u"ר'", u'רב', u'רבי', u'בן', u'בר', u'בריה', u'אמר', u'כאמר', u'וכאמר', u'דאמר', u'ודאמר', u'כדאמר',
                  u'וכדאמר', u'ואמר', u'כרב',
                  u'ורב', u'כדרב', u'דרב', u'ודרב', u'וכדרב', u'כרבי', u'ורבי', u'כדרבי', u'דרבי', u'ודרבי', u'וכדרבי',
                  u"כר'", u"ור'", u"כדר'",
                  u"דר'", u"ודר'", u"וכדר'", u'א״ר', u'וא״ר', u'כא״ר', u'דא״ר', u'דאמרי', u'משמיה', u'קאמר', u'קאמרי',
                  u'לרב', u'לרבי',
                  u"לר'", u'ברב', u'ברבי', u"בר'", u'הא', u'בהא', u'הך', u'בהך', u'ליה', u'צריכי', u'צריכא', u'וצריכי',
                  u'וצריכא', u'הלל', u'שמאי', u"וגו'", u'וגו׳', u'וגו']
    def __init__(self):
        self.levenshtein = WeightedLevenshtein()
        self.matcher = None
        with codecs.open("word_counts.json", "rb", encoding="utf8") as fin:
            self.word_counts = json.load(fin)

    @staticmethod
    def tokenize_words(base_str):
        base_str = base_str.strip()
        base_str = strip_cantillation(base_str, strip_vowels=True)
        base_str = re.sub(ur"<[^>]+>", u"", base_str)
        for match in re.finditer(ur'\(.*?\)', base_str):
            if len(match.group().split()) <= 5:
                base_str = base_str.replace(match.group(), u"")
                # base_str = re.sub(ur"(?:\(.*?\)|<.*?>)", u"", base_str)
        base_str = re.sub(ur'־', u' ', base_str)
        base_str = re.sub(ur'\[[^\[\]]{1,7}\]', u'', base_str)  # remove kri but dont remove too much to avoid messing with brackets in talmud
        base_str = re.sub(ur'[A-Za-z.,"?!״:׃]', u'', base_str)
        # replace common hashem replacements with the tetragrammaton
        base_str = re.sub(ur"(^|\s)([\u05de\u05e9\u05d5\u05db\u05dc\u05d1]?)(?:\u05d4['\u05f3]|\u05d9\u05d9)($|\s)",
                   ur"\1\2\u05d9\u05d4\u05d5\u05d4\3", base_str)
        # replace common elokim replacement with elokim
        base_str = re.sub(ur"(^|\s)([\u05de\u05e9\u05d5\u05db\u05dc\u05d1]?)(?:\u05d0\u05dc\u05e7\u05d9\u05dd)($|\s)",
                   ur"\1\2\u05d0\u05dc\u05d4\u05d9\u05dd\3", base_str)

        word_list = re.split(ur"\s+", base_str)
        word_list = [w for w in word_list if len(w.strip()) > 0 and w not in Link_Disambiguator.stop_words]
        return word_list

    def word_count_score(self, w):
        max_count = 1358676
        max_score = 1
        wc = self.word_counts.get(w, None)
        score = 1 if wc is None else -math.log10(20*(wc + (max_count/10**max_score))) + math.log10(20*max_count)
        return 3 * score

    def is_stopword(self, w):
        # TODO only if not Tanakh
        if len(w) > 0 and w[0] == u'ו' and self.word_counts.get(w[1:], 0) > 1.8e5:
            # try to strip off leading vav
            return True
        return self.word_counts.get(w, 0) > 1.8e5

    def get_score(self, words_a, words_b):
        # negative because for score higher is better but for leven lower is better
        num_stopwords_a = reduce(lambda a, b: a + (1 if self.is_stopword(b) else 0), words_a, 0)
        num_stopwords_b = reduce(lambda a, b: a + (1 if self.is_stopword(b) else 0), words_b, 0)
        if len(words_a) - num_stopwords_a < 2 or len(words_b) - num_stopwords_b < 2:
            # print "stopwords!"
            # print num_stopwords_a, len(words_a)
            # print num_stopwords_b, len(words_b)
            return -40
        return -ComputeLevenshteinDistanceByWord(u" ".join(words_a), u" ".join(words_b)) + sum([self.word_count_score(w) for w in words_b])

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
        talmud_books = library.get_indexes_in_category("Bavli")
        query = {
            "refs": re.compile(ur'^({}) \d+[ab]?$'.format(u'|'.join(tanakh_books + talmud_books)))
        }
        linkset = LinkSet(query)
        print "Num ambiguous {}".format(linkset.count())
        segment_map = defaultdict(list)
        actual_num = 0
        for l in linkset:
            try:
                segment_map[Ref(l.refs[0]).normal()] += [Ref(l.refs[1]).normal()]
                actual_num += 1
            except PartialRefInputError:
                pass
            except InputError:
                pass
        print "Actual num ambiguous {}".format(actual_num)
        print "Num keys {}".format(len(segment_map))
        objStr = json.dumps(segment_map, indent=4, ensure_ascii=False)
        with open('ambiguous_segments.json', "w") as f:
            f.write(objStr.encode('utf-8'))

    def disambiguate_segment(self, main_tc, tc_list, multiple_ref_map=None):
        """

        :param main_tc: TextChunk that has ambiguous refs
        :param tc_list: list(TextChunk) where each TC is ambiguous
        :param multiple_ref_map: In case two equal ambiguous refs appear in main_tc, dict where keys are normalized refs and values are number of times they appear
        :return: (list, list). first list is good matches. second list is matches that couldn't be disambiguated
        """
        if multiple_ref_map is None:
            multiple_ref_map = {}
        matcher = ParallelMatcher(self.tokenize_words,max_words_between=1, min_words_in_match=3, ngram_size=3,
                                  parallelize=False, calculate_score=self.get_score, all_to_all=False,
                                  verbose=False, min_distance_between_matches=1)
        try:
            match_list = matcher.match(tc_list=[main_tc] + tc_list, return_obj=True)
        except ValueError:
            print "Skipping {}".format(main_tc)
            return [], [] #[[main_tc._oref.normal(), tc_list[i]._oref.normal()] for i in range(len(tc_list))]
        best_list = []
        for tc in tc_list:
            best = None

            filtered_match_list = filter(lambda x: x.b.ref == main_tc._oref and x.a.ref.section_ref() == tc._oref, match_list)
            score_list = [x.score for x in filtered_match_list]
            if len(score_list) == 0:
                continue
            max_scores = argmax(score_list, n=multiple_ref_map.get(tc._oref.normal(), 1))
            best_list += [filtered_match_list[i] for i in max_scores]

        good = [[mm.a.ref.normal(), mm.b.ref.normal(), mm.score] for mm in best_list if not mm is None and mm.score > 0]
        bad = [[main_tc._oref.normal(), tc_list[i]._oref.normal()] for i, mm in enumerate(best_list) if mm is None or mm.score <= 0]
        #print good
        return good, bad

    def disambiguate_segment_by_snippet(self, main_snippet, main_tref, quoted_tc, quote_number):
        """

        :param main_snippet: str with quoted tref inside and a bit of padding
        :param main_tref: tref str for the main_snippet
        :param quoted_tc: TextChunk for quoted ref
        :param quote_number: if the quoted ref appears multiple times in the main ref, this is the index of the quoted ref
        :return: good, bad
        """
        if not self.matcher:
            self.matcher = ParallelMatcher(self.tokenize_words,max_words_between=1, min_words_in_match=3, ngram_size=3,
                                  parallelize=False, calculate_score=self.get_score, all_to_all=False,
                                  verbose=False, min_distance_between_matches=1)
        try:
            match_list = self.matcher.match(tc_list=[(main_snippet, main_tref), quoted_tc], return_obj=True)
        except ValueError:
            print "Skipping {}".format(main_tref)
            return [], []  # [[main_tc._oref.normal(), tc_list[i]._oref.normal()] for i in range(len(tc_list))]

        if len(match_list) == 0:
            return [], [{u"Quoting Ref": main_tref, u"Quoted Ref": None, u"Score": -40, u"Quote Num": 0, u"Snippet": main_snippet}]
        score_list = [x.score for x in match_list]
        max_scores = argmax(score_list, n=1)
        best = match_list[max_scores[0]]
        a_match, b_match = (best.a, best.b) if best.a.mesechta == main_tref else (best.b, best.a)
        # print "snippet"
        # print get_snippet_from_mesorah_item(b_match, self.tokenize_words)
        # print best.score
        ret = [{
            u"Quoting Ref": a_match.mesechta,
            u"Quoted Ref": b_match.ref.normal(),
            u"Score": best.score,
            u"Quote Num": quote_number,
            u"Snippet": main_snippet
        }]
        good, bad = (ret, []) if best.score > -28 else ([], ret)
        return good, bad

    def disambiguate_gra(self):
        gra_segs = OrderedDict()
        matches = []
        with codecs.open("gra2.txt", "rb", encoding="utf8") as fin:
            curr_title = u""
            for iline, line in enumerate(fin):
                line = line.strip()
                if not re.search(ur"^[\u05d0-\u05ea]+:[\u05d0-\u05ea]+$", line) and len(line) > 40:
                    key = u"{}-{}".format(curr_title, iline)
                    gra_segs[key] = line
                elif len(line) > 0:
                    curr_title = line
        ber_tc = TextChunk(Ref("Genesis"), "he")
        ber_word_list = [w for seg in ber_tc.ja().flatten_to_array() for w in self.tokenize_words(seg)]
        all_matches = []
        lengrasegs = len(gra_segs.items())
        for i, (gtitle, gtext) in enumerate(gra_segs.items()):
            print u"{}/{}".format(i, lengrasegs)
            matcher = ParallelMatcher(self.tokenize_words, max_words_between=1, min_words_in_match=4, ngram_size=4,
                                      parallelize=False, calculate_score=self.get_score, all_to_all=False,
                                      verbose=False)
            match_list = matcher.match(tc_list=[(gtext, gtitle), ber_tc], return_obj=True)
            all_matches += [[mm.a.ref.normal(), mm.b.mesechta, mm.a.location, mm.b.location, mm.score] for mm in match_list if not mm is None]
        for m in all_matches:
            text_a = u" ".join(ber_word_list[m[2][0]:m[2][1]+1])
            gra_words = self.tokenize_words(gra_segs[m[1]])
            padding = 4
            start_gra = m[3][0] - padding if m[3][0] - padding >= 0 else 0
            end_gra = m[3][1] + 1 + padding if m[3][1] + 1 + padding <= len(gra_words) else len(gra_words)
            text_b = u" ".join(gra_words[start_gra:m[3][0]]) + u" [[ " + \
                     u" ".join(gra_words[m[3][0]:m[3][1]+1]) + u" ]] " + \
                     u" ".join(gra_words[m[3][1]+1:end_gra])
            matches += [{"Torah Text": text_a, "Gra Text": text_b, "Torah Ref": m[0], "Gra Ref": m[1], "Score": m[4]}]
        matches.sort(key=lambda x: Ref(x["Torah Ref"]).order_id())
        with open("gra_out.csv", "wb") as fout:
            fcsv = unicodecsv.DictWriter(fout, ["Torah Ref", "Gra Ref", "Torah Text", "Gra Text", "Score"])
            fcsv.writeheader()
            fcsv.writerows(matches)

def get_snippet_from_mesorah_item(mesorah_item, tokenizer):
    words = tokenizer(Ref(mesorah_item.mesechta).text("he").ja().flatten_to_string())
    return u" ".join(words[mesorah_item.location[0]:mesorah_item.location[1]+1])


def save_disambiguated_to_file(good, bad, csv_good, csv_bad):
    csv_good.writerows(good)
    csv_bad.writerows(bad)


def disambiguate_all():
    ld = Link_Disambiguator()
    #ld.find_indexes_with_ambiguous_links()
    #ld.get_ambiguous_segments()

    ambig_dict = json.load(open("ambiguous_segments.json",'rb'))
    good = []
    bad = []
    _tc_cache = {}
    def make_tc(tref, oref):
        tc = oref.text('he')
        _tc_cache[tref] = tc
        return tc
    fgood = open('unambiguous_links.json', 'wb')
    fbad = open('still_ambiguous_links.json', 'wb')
    csv_good = unicodecsv.DictWriter(fgood, [u'Quoting Ref', u'Quoted Ref', u'Score', u'Quote Num', u'Snippet'])
    csv_good.writeheader()
    csv_bad = unicodecsv.DictWriter(fbad, [u'Quoting Ref', u'Quoted Ref', u'Score', u'Quote Num', u'Snippet'])
    csv_bad.writeheader()
    for iambig, (main_str, tref_list) in enumerate(ambig_dict.items()):
        if iambig % 50 == 0:
            print "{}/{}".format(iambig, len(ambig_dict))
        try:
            main_ref = Ref(main_str)
            main_tc = _tc_cache.get(main_str, make_tc(main_str, main_ref))
            for quoted_tref in tref_list:
                quoted_oref = Ref(quoted_tref)
                quoted_tc = _tc_cache.get(quoted_tref, make_tc(quoted_tref, quoted_oref))
                temp_good, temp_bad = disambiguate_one(ld, main_ref, main_tc, quoted_oref, quoted_tc)
                good += temp_good
                bad += temp_bad
                if len(good) + len(bad) > 10:
                    save_disambiguated_to_file(good, bad, csv_good, csv_bad)
                    good = []
                    bad = []
        except PartialRefInputError:
            pass
        except InputError as e:
            print e
            pass
        except TypeError as e:
            print e
            pass
    save_disambiguated_to_file(good, bad, csv_good, csv_bad)
    fgood.close()
    fbad.close()


def disambiguate_one(ld, main_oref, main_tc, quoted_oref, quoted_tc):
    good, bad = [], []
    main_snippet_list = get_snippet_by_seg_ref(main_tc, quoted_oref, must_find_snippet=True, snip_size=45, use_indicator_words=True)
    if main_snippet_list:
        for isnip, main_snippet in enumerate(main_snippet_list):
            temp_good, temp_bad = ld.disambiguate_segment_by_snippet(main_snippet, main_oref.normal(), quoted_tc, isnip)
            good += temp_good
            bad += temp_bad
    return good, bad


def get_snippet_by_seg_ref(source_tc, found, must_find_snippet=False, snip_size=100, use_indicator_words=False):
    """
    based off of library.get_wrapped_refs_string
    :param source:
    :param found:
    :param must_find_snippet: bool, True if you only want to return a str if you found a snippet
    :param snip_size int number of chars in snippet on each side
    :param use_indicator_words bool, True if you want to use hard-coded indicator words to determine which side of the ref the quote is on
    :return:
    """
    after_indicators = [u"דכתיב", u"ודכתיב", u"וכתיב", u"וכתוב", u"שכתוב", u"כשכתוב", u"כדכתיב", u"זל", u"ז״ל", u"ז''ל",
                       u"ז\"ל", u"אומרם", u"כאמור", u"ואומר", u"אמר", u"שנאמר", u"בגמ'", u"בגמ׳", u"בפסוק", u"לעיל", u"ולעיל", u"לקמן", u"ולקמן", u"בירושלמי",
                       u"בבבלי", u"שדרשו", u"ששנינו", u"שנינו", u"ושנינו", u"דשנינו", u"כמש״כ", u"כמש\"כ", u"כמ״ש", u"כמ\"ש",
                       u"וכמש״כ", u"וכמ\"ש", u"וכמ״ש", u"וכמש\"כ", u"ע״ה", u"ע\"ה", u"מבואר", u"כמבואר", u"במתני׳",
                       u"במתנ\'", u"דתנן", u"זכרונם לברכה", u"זכר לברכה"]
    after_reg = ur"(?:^|\s)(?:{})\s*[(\[]?$".format(u"|".join(after_indicators))
    after_indicators_far = [u"דבפרק", u"בפרק", u"שבפרק", u"פרק"]
    after_far_reg = ur"(?:^|\s)(?{}:)(?=\s|$)".format(u"|".join(after_indicators_far))
    after_indicators_after = [u"בד״ה", u"בד\"ה", u"ד״ה", u"ד\"ה"]
    after_after_reg = ur"^\s*(?:{})\s".format(u"|".join(after_indicators_after))
    punctuation = [u",", u".", u":", u"?", u"!", u"׃"]
    punctuation_after_reg = ur"^\s*(?:{})\s".format(u"|".join(punctuation))
    punctuation_before_reg = ur"(?:{})\s*$".format(u"|".join(punctuation))
    after_indicators_after_far = [u"וגו׳", u"וגו'", u"וגו", u"וכו׳", u"וכו'", u"וכו"]
    after_after_far_reg = ur"(?:^|\s)(?{}:)(?=\s|$)".format(u"|".join(after_indicators_after_far))
    found_title = found.index.get_title("he")
    found_node = library.get_schema_node(found_title, "he")
    title_nodes = {t: found_node for t in found.index.all_titles("he")}
    all_reg = library.get_multi_title_regex_string(set(found.index.all_titles("he")), "he")
    reg = regex.compile(all_reg, regex.VERBOSE)
    source_text = re.sub(ur"<[^>]+>", u"", strip_cantillation(source_tc.text, strip_vowels=True))

    linkified = library._wrap_all_refs_in_string(title_nodes, reg, source_text, "he")

    snippets = []
    found_normal = found.normal()
    found_section_normal = re.match(ur"^[^:]+", found_normal).group()
    for match in re.finditer(u"(<a [^>]+>)([^<]+)(</a>)", linkified):
        ref = Ref(match.group(2))
        if ref.normal() == found_section_normal or ref.normal() == found_normal:
            start_snip_naive = match.start(1) - snip_size if match.start(1) >= snip_size else 0
            start_snip_space = linkified.rfind(u" ", 0, start_snip_naive)
            start_snip_link = linkified.rfind(u"</a>", 0, match.start(1))
            start_snip = max(start_snip_space, start_snip_link)
            if start_snip == -1:
                start_snip = start_snip_naive
            end_snip_naive = match.end(3) + snip_size if match.end(3) + snip_size <= len(linkified) else len(linkified)
            end_snip_space = linkified.find(u" ", end_snip_naive)
            end_snip_link = linkified.find(u"<a ", match.end(3))
            end_snip = min(end_snip_space, end_snip_link)
            if end_snip == -1:
                end_snip = end_snip_naive

            if use_indicator_words:
                before_snippet = linkified[start_snip:match.start(1)]
                after_snippet = linkified[match.end(3):end_snip]
                if re.search(after_reg, before_snippet) is not None:
                    temp_snip = after_snippet
                    # print before_snippet
                else:
                    temp_snip = linkified[start_snip:end_snip]
            else:
                temp_snip = linkified[start_snip:end_snip]
            snippets += [re.sub(ur"<[^>]+>", u"", temp_snip)]

    if len(snippets) == 0:
        if must_find_snippet:
            return None
        return [source_text]

    return snippets


def find_low_confidence_talmud():
    with open("unambiguous_links.json", "rb") as fin:
        jin = json.load(fin)
    low_conf = []
    high_conf = []
    for r1, r2, conf in jin:
        is_talmud = Ref(r1).primary_category == "Talmud"
        if conf < 40 and is_talmud:
            low_conf += [[r1, r2, conf]]
        else:
            high_conf += [[r1, r2, conf]]

    tanakh = random.sample(filter(lambda x: Ref(x[0]).primary_category == "Tanakh", high_conf), 250)
    talmud = random.sample(filter(lambda x: Ref(x[0]).primary_category == "Talmud", high_conf), 250)
    qa_rows = [
        {
            u"Found Text": Ref(x[0]).text("he").ja().flatten_to_string(),
            u"Source Text": u"...".join(get_snippet_by_seg_ref(Ref(x[1]).text('he'), Ref(x[0]))),
            u"Source Ref URL": u"https://sefaria.org/{}".format(Ref(x[1]).url()),
            u"Found Ref URL": u"https://sefaria.org/{}".format(Ref(x[0]).url()),
            u"Wrong segment (seg) / Wrong link (link)": u""
        }
        for x in (tanakh + talmud)]

    print len(low_conf)
    print len(high_conf)
    with open("low_conf_links.json", "wb") as fout:
        json.dump(low_conf, fout, indent=2)
    with open("high_conf_links.json", "wb") as fout:
        json.dump(high_conf, fout, indent=2)
    with open("QA Section Links.csv", "wb") as fout:
        csv = unicodecsv.DictWriter(fout, [u"Source Text", u"Found Text", u"Source Ref URL", u"Found Ref URL", u"Wrong segment (seg) / Wrong link (link)"])
        csv.writeheader()
        csv.writerows(qa_rows)

word_counter = defaultdict(int)

def count_words():
    global word_counter
    index_set = library.all_index_records()
    for ii, i in enumerate(index_set):
        print u"{}/{}".format(ii, len(index_set))
        count_words_map(i)
    with codecs.open('word_counts.json', 'wb', encoding='utf8') as fout:
        json.dump(word_counter, fout)


def count_words_map(index):
    global word_counter
    try:
        seg_list = index.nodes.traverse_to_list(
            lambda n, _: TextChunk(n.ref(), "he").ja().flatten_to_array() if not n.children else [])
        for seg in seg_list:
            for w in Link_Disambiguator.tokenize_words(seg):
                word_counter[w] += 1
    except InputError:
        pass

def run():
    ld = Link_Disambiguator()
    ld.get_ambiguous_segments()
    disambiguate_all()
    #find_low_confidence_talmud()
    # ld = Link_Disambiguator()
    # ld.disambiguate_gra()
    #count_words()

if __name__ == '__main__':
    profiling = False
    if profiling:
        print "Profiling...\n"
        cProfile.run("run()", "stats")
        p = pstats.Stats("stats")
        sys.stdout = sys.__stdout__
        p.strip_dirs().sort_stats("cumtime").print_stats()
    else:
        run()


    # tc_list = [Ref("Zohar 1:70b:7").text("he"), Ref("Song of Songs 1").text("he")] #{'match_index': [[5, 7], [11, 13]], 'score': 81, 'match': [u'Zohar 1:70b:7', u'Song of Songs 1:3']}
    # tc_list = [Ref("Zohar 1:70b:9").text("he"), Ref("Genesis 1").text("he")] #{'match_index': [[27, 32], [106, 111]], 'score': 96, 'match': [u'Genesis 1:4', u'Zohar 1:70b:9']}

# TODO: find the right length of match. best way to score? limit matches to one side of ref

u""