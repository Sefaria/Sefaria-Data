# -*- coding: utf-8 -*-
import sys
import os
import traceback
from tqdm import tqdm
from functools import reduce
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
SEFARIA_PROJECT_PATH = "/var/www/readonly"
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"


import re, json, codecs, unicodecsv, heapq, random, regex, math, cProfile, pstats, csv
import django
django.setup()
from sefaria.model import *
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from collections import defaultdict, OrderedDict
from sefaria.system.exceptions import PartialRefInputError, InputError, NoVersionFoundError, DuplicateRecordError
from sefaria.utils.hebrew import strip_cantillation
from data_utilities.util import WeightedLevenshtein
from data_utilities.ibid import CitationFinder
from data_utilities.dibur_hamatchil_matcher import get_maximum_dh, ComputeLevenshteinDistanceByWord
from sources.functions import post_text, post_link

LOWEST_SCORE = -28
ROOT = "research/link_disambiguator"
TALMUD_ADDRESS_REG = regex.compile(CitationFinder.create_jan_for_address_type(["Talmud"]).address_regex("he") + "$", regex.VERBOSE)
def argmax(iterable, n=1):
    if n==1:
        return [max(enumerate(iterable), key=lambda x: x[1])[0]]
    else:
        return heapq.nlargest(n, range(len(iterable)), iterable.__getitem__)


class Link_Disambiguator:
    stop_words = ["ר'", 'רב', 'רבי', 'בן', 'בר', 'בריה', 'אמר', 'כאמר', 'וכאמר', 'דאמר', 'ודאמר', 'כדאמר',
                  'וכדאמר', 'ואמר', 'כרב',
                  'ורב', 'כדרב', 'דרב', 'ודרב', 'וכדרב', 'כרבי', 'ורבי', 'כדרבי', 'דרבי', 'ודרבי', 'וכדרבי',
                  "כר'", "ור'", "כדר'",
                  "דר'", "ודר'", "וכדר'", 'א״ר', 'וא״ר', 'כא״ר', 'דא״ר', 'דאמרי', 'משמיה', 'קאמר', 'קאמרי',
                  'לרב', 'לרבי',
                  "לר'", 'ברב', 'ברבי', "בר'", 'הא', 'בהא', 'הך', 'בהך', 'ליה', 'צריכי', 'צריכא', 'וצריכי',
                  'וצריכא', 'הלל', 'שמאי', "וגו'", 'וגו׳', 'וגו']
    def __init__(self):
        self.levenshtein = WeightedLevenshtein()
        self.matcher = None
        try:
            with codecs.open(ROOT + "/word_counts.json", "rb", encoding="utf8") as fin:
                self.word_counts = json.load(fin)
        except IOError:
            self.word_counts = {}

    @staticmethod
    def tokenize_words(base_str):
        base_str = base_str.strip()
        base_str = strip_cantillation(base_str, strip_vowels=True)
        base_str = re.sub(r"<[^>]+>", "", base_str)
        for match in re.finditer(r'\(.*?\)', base_str):
            if len(match.group().split()) <= 5:
                base_str = base_str.replace(match.group(), "")
                # base_str = re.sub(ur"(?:\(.*?\)|<.*?>)", u"", base_str)
        base_str = re.sub(r'־', ' ', base_str)
        base_str = re.sub(r'\[[^\[\]]{1,7}\]', '', base_str)  # remove kri but dont remove too much to avoid messing with brackets in talmud
        base_str = re.sub(r'[A-Za-z.,"?!״:׃]', '', base_str)
        # replace common hashem replacements with the tetragrammaton
        base_str = re.sub(r"(^|\s)([\u05de\u05e9\u05d5\u05db\u05dc\u05d1]?)(?:\u05d4['\u05f3]|\u05d9\u05d9)($|\s)",
                   "\1\2\u05d9\u05d4\u05d5\u05d4\3", base_str)
        # replace common elokim replacement with elokim
        base_str = re.sub(r"(^|\s)([\u05de\u05e9\u05d5\u05db\u05dc\u05d1]?)(?:\u05d0\u05dc\u05e7\u05d9\u05dd)($|\s)",
                   "\1\2\u05d0\u05dc\u05d4\u05d9\u05dd\3", base_str)

        word_list = re.split(r"\s+", base_str)
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
        if len(w) > 0 and w[0] == 'ו' and self.word_counts.get(w[1:], 0) > 1.8e5:
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
        lazy_tfidf = sum([self.word_count_score(w) for w in words_b])
        best_match = get_maximum_dh(words_a, words_b,min_dh_len=len(words_b)-1, max_dh_len=len(words_b))
        if best_match:
            return -best_match.score + lazy_tfidf
        else:
            return -ComputeLevenshteinDistanceByWord(" ".join(words_a), " ".join(words_b)) + lazy_tfidf

    def find_indexes_with_ambiguous_links(self):
        tanakh_books = library.get_indexes_in_category("Tanakh")
        query = {
            "refs": re.compile(r'^({}) \d+$'.format('|'.join(tanakh_books)))
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

        items = sorted(list(index_dict.items()), key=lambda x: x[1])
        for i in items:
            print(i)

    def get_ambiguous_segments(self):
        tanakh_books = library.get_indexes_in_category("Tanakh")
        talmud_books = list(set(library.get_indexes_in_category("Bavli")) - set(library.get_indexes_in_category("Minor Tractates")))
        tan_tal_books = set(tanakh_books + talmud_books)
        query = {
            "refs": re.compile(r'^({}) \d+[ab]?$'.format('|'.join(tanakh_books + talmud_books)))
        }
        linkset = LinkSet(query)
        print("Num ambiguous {}".format(linkset.count()))
        segment_map = defaultdict(list)
        actual_num = 0
        for l in linkset:
            quoter, quoted = l.refs if Ref(l.refs[1]).index.title in tan_tal_books else reversed(l.refs)
            try:
                segment_map[Ref(quoter).normal()] += [Ref(quoted).normal()]
                actual_num += 1
            except PartialRefInputError:
                pass
            except InputError:
                pass
        print("Actual num ambiguous {}".format(actual_num))
        print("Num keys {}".format(len(segment_map)))
        objStr = json.dumps(segment_map, indent=2, ensure_ascii=False)
        with open(ROOT + '/ambiguous_segments.json', "w") as f:
            f.write(objStr)

    def disambiguate_segment_by_snippet(self, main_tref, tref_list, lowest_score_threshold=LOWEST_SCORE, max_words_between=1, min_words_in_match=3, ngram_size=3, verbose=False, with_match_text=False):
        """

        :param main_tref: Must be a text ref
        :param tref_list: List of text refs. Can have tuples of the form (text, tref)
        :param lowest_score_threshold: matches below this score will be considered 'bad'
        :return: two lists, `good` and `bad`. Each list has matches
        """
        if not self.matcher:
            self.matcher = ParallelMatcher(self.tokenize_words,max_words_between=max_words_between, min_words_in_match=min_words_in_match, ngram_size=ngram_size,
                                  parallelize=False, calculate_score=self.get_score, all_to_all=False,
                                  verbose=verbose, min_distance_between_matches=0, only_match_first=True)
        try:
            match_list = self.matcher.match([main_tref] + tref_list, return_obj=True)
        except ValueError:
            print("Skipping {}".format(main_tref))
            final_result_dict = {}
            for other_tref in tref_list:
                is_tuple = isinstance(other_tref, tuple)
                parallel_item_key = other_tref[1] if is_tuple else other_tref
                final_result_dict[parallel_item_key] = None
            return final_result_dict # [[main_tc._oref.normal(), tc_list[i]._oref.normal()] for i in range(len(tc_list))]

        final_result_dict = {}
        for other_tref in tref_list:
            is_tuple = isinstance(other_tref, tuple)
            parallel_item_key = other_tref[1] if is_tuple else other_tref
            parallel_matches = [x for x in match_list if x.a.mesechta == parallel_item_key or x.b.mesechta == parallel_item_key]
            if len(parallel_matches) == 0:
                final_result_dict[parallel_item_key] = None
                continue
            score_list = [x.score for x in parallel_matches]
            max_scores = argmax(score_list, n=1)
            best = parallel_matches[max_scores[0]]
            a_match, b_match = (best.a, best.b) if best.a.mesechta == main_tref else (best.b, best.a)
            if best.score > lowest_score_threshold:
                result = {
                    "A Ref": a_match.ref.normal(),
                    "B Ref": b_match.mesechta if is_tuple else b_match.ref.normal(),
                    "Score": best.score,
                }
                if with_match_text:
                    result["Match Text A"] = get_snippet_from_mesorah_item(a_match, self.matcher)
                    result["Match Text B"] = get_snippet_from_mesorah_item(b_match, self.matcher)

            else:
                result = None
            final_result_dict[parallel_item_key] = result
        return final_result_dict

    def disambiguate_gra(self):
        gra_segs = OrderedDict()
        matches = []
        with codecs.open("gra2.txt", "rb", encoding="utf8") as fin:
            curr_title = ""
            for iline, line in enumerate(fin):
                line = line.strip()
                if not re.search(r"^[\u05d0-\u05ea]+:[\u05d0-\u05ea]+$", line) and len(line) > 40:
                    key = "{}-{}".format(curr_title, iline)
                    gra_segs[key] = line
                elif len(line) > 0:
                    curr_title = line
        ber_tc = TextChunk(Ref("Genesis"), "he")
        ber_word_list = [w for seg in ber_tc.ja().flatten_to_array() for w in self.tokenize_words(seg)]
        all_matches = []
        lengrasegs = len(list(gra_segs.items()))
        for i, (gtitle, gtext) in enumerate(gra_segs.items()):
            print("{}/{}".format(i, lengrasegs))
            matcher = ParallelMatcher(self.tokenize_words, max_words_between=1, min_words_in_match=4, ngram_size=4,
                                      parallelize=False, calculate_score=self.get_score, all_to_all=False,
                                      verbose=False)
            match_list = matcher.match(tref_list=[(gtext, gtitle), ber_tc], return_obj=True)
            all_matches += [[mm.a.ref.normal(), mm.b.mesechta, mm.a.location, mm.b.location, mm.score] for mm in match_list if not mm is None]
        for m in all_matches:
            text_a = " ".join(ber_word_list[m[2][0]:m[2][1]+1])
            gra_words = self.tokenize_words(gra_segs[m[1]])
            padding = 4
            start_gra = m[3][0] - padding if m[3][0] - padding >= 0 else 0
            end_gra = m[3][1] + 1 + padding if m[3][1] + 1 + padding <= len(gra_words) else len(gra_words)
            text_b = " ".join(gra_words[start_gra:m[3][0]]) + " [[ " + \
                     " ".join(gra_words[m[3][0]:m[3][1]+1]) + " ]] " + \
                     " ".join(gra_words[m[3][1]+1:end_gra])
            matches += [{"Torah Text": text_a, "Gra Text": text_b, "Torah Ref": m[0], "Gra Ref": m[1], "Score": m[4]}]
        matches.sort(key=lambda x: Ref(x["Torah Ref"]).order_id())
        with open("gra_out.csv", "wb") as fout:
            fcsv = unicodecsv.DictWriter(fout, ["Torah Ref", "Gra Ref", "Torah Text", "Gra Text", "Score"])
            fcsv.writeheader()
            fcsv.writerows(matches)


def get_snippet_from_mesorah_item(mesorah_item, pm):
    words = pm.word_list_map[mesorah_item.mesechta]
    return " ".join(words[mesorah_item.location[0]:mesorah_item.location[1]+1])


def save_disambiguated_to_file(good, bad, csv_good, csv_bad):
    csv_good.writerows(good)
    csv_bad.writerows(bad)

_tc_cache = {}
def disambiguate_all():
    ld = Link_Disambiguator()
    #ld.find_indexes_with_ambiguous_links()
    #ld.get_ambiguous_segments()

    ambig_dict = json.load(open(ROOT + "/ambiguous_segments.json",'r'))
    good = []
    bad = []
    def make_tc(tref, oref):
        global _tc_cache
        tc = oref.text('he')
        _tc_cache[tref] = tc
        if len(_tc_cache) > 5000:
            _tc_cache = {}
        return tc
    fgood = open(ROOT +'/unambiguous_links.csv', 'wb')
    fbad = open(ROOT + '/still_ambiguous_links.csv', 'wb')
    csv_good = unicodecsv.DictWriter(fgood, ['Quoting Ref', 'Quoted Ref', 'Score', 'Quote Num', 'Snippet'])
    csv_good.writeheader()
    csv_bad = unicodecsv.DictWriter(fbad, ['Quoting Ref', 'Quoted Ref', 'Score', 'Quote Num', 'Snippet'])
    csv_bad.writeheader()
    for iambig, (main_str, tref_list) in enumerate(ambig_dict.items()):
        if iambig % 50 == 0:
            print("{}/{}".format(iambig, len(ambig_dict)))
        try:
            main_ref = Ref(main_str)
            main_tc = _tc_cache.get(main_str, make_tc(main_str, main_ref))
            for quoted_tref in tref_list:
                quoted_oref = Ref(quoted_tref)
                quoted_tc = _tc_cache.get(quoted_tref, make_tc(quoted_tref, quoted_oref))
                temp_good, temp_bad = disambiguate_one(ld, main_ref, main_tc, quoted_oref, quoted_tc)
                good += temp_good
                bad += temp_bad
                if len(good) + len(bad) > 1000:
                    save_disambiguated_to_file(good, bad, csv_good, csv_bad)
                    good = []
                    bad = []
        except PartialRefInputError:
            pass
        except InputError as e:
            traceback.print_exc(file=sys.stdout)
            pass
        except TypeError as e:
            traceback.print_exc(file=sys.stdout)
            pass
    save_disambiguated_to_file(good, bad, csv_good, csv_bad)
    fgood.close()
    fbad.close()


def disambiguate_one(ld, main_oref, main_tc, quoted_oref, quoted_tc):
    good, bad = [], []
    try:
        main_snippet_list = get_snippet_by_seg_ref(main_tc, quoted_oref, must_find_snippet=True, snip_size=65, use_indicator_words=True)
    except InputError:
        return good, bad
    except UnicodeEncodeError:
        return good, bad
    if main_snippet_list:
        for isnip, main_snippet in enumerate(main_snippet_list):
            quoted_tref = quoted_oref.normal()
            # if is_ref_to_daf and quoted_tref[-1] == "a":
            #     quoted_tref += "-b"  # make ref to full daf
            #     quoted_tref = Ref(quoted_tref).normal()  # renormalize
            results = ld.disambiguate_segment_by_snippet(quoted_tref, [(main_snippet, main_oref.normal())])
            temp_good, temp_bad = [], []
            for k, v in list(results.items()):
                is_bad = v is None
                temp = {
                    "Quote Num": isnip,
                    "Snippet": main_snippet,
                    "Quoted Ref": v["A Ref"] if not is_bad else quoted_oref.normal(),
                    "Quoting Ref": v["B Ref"] if not is_bad else k,
                    "Score": v["Score"] if not is_bad else LOWEST_SCORE
                }
                # if is_ref_to_daf:
                #     print("ref to daf!")
                #     print(temp)
                if is_bad:
                    bad += [temp]
                else:
                    good += [temp]
    return good, bad


def get_snippet_by_seg_ref(source_tc, found, must_find_snippet=False, snip_size=100, use_indicator_words=False, return_matches=False):
    """
    based off of library.get_wrapped_refs_string
    :param source:
    :param found:
    :param must_find_snippet: bool, True if you only want to return a str if you found a snippet
    :param snip_size int number of chars in snippet on each side
    :param use_indicator_words bool, True if you want to use hard-coded indicator words to determine which side of the ref the quote is on
    :return:
    """
    after_indicators = ["דכתיב", "ודכתיב", "וכתיב", "וכתוב", "שכתוב", "כשכתוב", "כדכתיב", "זל", "ז״ל", "ז''ל",
                       "ז\"ל", "אומרם", "כאמור", "ואומר", "אמר", "שנאמר", "בגמ'", "בגמ׳", "בפסוק", "לעיל", "ולעיל", "לקמן", "ולקמן", "בירושלמי",
                       "בבבלי", "שדרשו", "ששנינו", "שנינו", "ושנינו", "דשנינו", "כמש״כ", "כמש\"כ", "כמ״ש", "כמ\"ש",
                       "וכמש״כ", "וכמ\"ש", "וכמ״ש", "וכמש\"כ", "ע״ה", "ע\"ה", "מבואר", "כמבואר", "במתני׳",
                       "במתנ\'", "דתנן", "זכרונם לברכה", "זכר לברכה"]
    after_reg = r"(?:^|\s)(?:{})\s*[(\[]?$".format("|".join(after_indicators))
    after_indicators_far = ["דבפרק", "בפרק", "שבפרק", "פרק"]
    after_far_reg = r"(?:^|\s)(?{}:)(?=\s|$)".format("|".join(after_indicators_far))
    after_indicators_after = ["בד״ה", "בד\"ה", "ד״ה", "ד\"ה"]
    after_after_reg = r"^\s*(?:{})\s".format("|".join(after_indicators_after))
    punctuation = [",", ".", ":", "?", "!", "׃"]
    punctuation_after_reg = r"^\s*(?:{})\s".format("|".join(punctuation))
    punctuation_before_reg = r"(?:{})\s*$".format("|".join(punctuation))
    after_indicators_after_far = ["וגו׳", "וגו'", "וגו", "וכו׳", "וכו'", "וכו"]
    after_after_far_reg = r"(?:^|\s)(?{}:)(?=\s|$)".format("|".join(after_indicators_after_far))
    found_title = found.index.get_title("he")
    found_node = library.get_schema_node(found_title, "he")
    title_nodes = {t: found_node for t in found.index.all_titles("he")}
    all_reg = library.get_multi_title_regex_string(set(found.index.all_titles("he")), "he")
    reg = regex.compile(all_reg, regex.VERBOSE)
    if len(source_tc.text) == 0 or not isinstance(source_tc.text, str):
        print(source_tc._oref)
    source_text = re.sub(r"<[^>]+>", "", strip_cantillation(source_tc.text, strip_vowels=True))
    linkified = library._wrap_all_refs_in_string(title_nodes, reg, source_text, "he")

    snippets = []
    found_normal = found.normal()
    found_section_normal = re.match(r"^[^:]+", found_normal).group()
    for match in re.finditer("(<a [^>]+>)([^<]+)(</a>)", linkified):
        ref = Ref(match.group(2))
        # use split_spanning_ref in case where talmud ref is amudless. It's essentially a ranged ref across two amudim
        if len({found_section_normal, found_normal} & {temp_ref.normal() for temp_ref in ref.split_spanning_ref()}) > 0 or ref.normal() == found_normal or ref.normal() == found_section_normal:
            if return_matches:
                snippets += [(match, linkified)]
            else:
                start_snip_naive = match.start(1) - snip_size if match.start(1) >= snip_size else 0
                start_snip_space = linkified.rfind(" ", 0, start_snip_naive)
                start_snip_link = linkified.rfind("</a>", 0, match.start(1))
                start_snip = max(start_snip_space, start_snip_link)
                if start_snip == -1:
                    start_snip = start_snip_naive
                end_snip_naive = match.end(3) + snip_size if match.end(3) + snip_size <= len(linkified) else len(linkified)
                end_snip_space = linkified.find(" ", end_snip_naive)
                end_snip_link = linkified.find("<a ", match.end(3))
                end_snip = min(end_snip_space, end_snip_link)
                if end_snip == -1:
                    end_snip = end_snip_naive

                if use_indicator_words:
                    before_snippet = linkified[start_snip:match.start(1)]
                    if "ירושלמי" in before_snippet[-20:] and (len(ref.index.categories) < 2 or ref.index.categories[1] != 'Yerushalmi'):
                        # this guys not a yerushalmi but very likely should be
                        continue
                    after_snippet = linkified[match.end(3):end_snip]
                    if re.search(after_reg, before_snippet) is not None:
                        temp_snip = after_snippet
                        # print before_snippet
                    else:
                        temp_snip = linkified[start_snip:end_snip]
                else:
                    temp_snip = linkified[start_snip:end_snip]
                snippets += [re.sub(r"<[^>]+>", "", temp_snip)]

    if len(snippets) == 0:
        if must_find_snippet:
            return None
        return [source_text]

    return snippets


def get_qa_csv():
    with open(ROOT +"/unambiguous_links.json", "rb") as fin:
        cin = unicodecsv.DictReader(fin)
        rows = [row for row in cin]
    def normalize(s):
        return re.sub(r"<[^>]+>", "", strip_cantillation(s, strip_vowels=True))

    tanakh = random.sample([x for x in rows if Ref(x['Quoted Ref']).primary_category == "Tanakh" and Ref(x['Quoting Ref']).is_segment_level()], 250)
    talmud = random.sample([x for x in rows if Ref(x['Quoted Ref']).primary_category == "Talmud" and Ref(x['Quoting Ref']).is_segment_level()], 250)
    qa_rows = [
        {
            "Found Text": normalize(Ref(x['Quoted Ref']).text("he").ja().flatten_to_string()),
            "Source Text": "...".join(get_snippet_by_seg_ref(Ref(x['Quoting Ref']).text('he'), Ref(x['Quoted Ref']))),
            "URL": "https://sefaria.org/{}?p2={}".format(Ref(x['Quoting Ref']).url(), Ref(x['Quoted Ref']).url()),
            "Wrong segment (seg) / Wrong link (link)": ""
        }
        for x in (tanakh + talmud)]

    with open(ROOT +"/QA Section Links.csv", "wb") as fout:
        csv = unicodecsv.DictWriter(fout, ["Source Text", "Found Text", "URL", "Wrong segment (seg) / Wrong link (link)"])
        csv.writeheader()
        csv.writerows(qa_rows)


def filter_books_from_output(books, cats):
    with open(ROOT + "/still_ambiguous_links.json", "rb") as fin:
        cin = unicodecsv.DictReader(fin)
        out_rows = []
        for row in cin:
            r = Ref(row['Quoting Ref'])
            if r.index.title in books or r.index.get_primary_category() in cats:
                row['Quoting Book'] = r.index.title
                try:
                    s = Ref(row['Quoted Ref'])
                    row['Quoted Book'] = s.index.title if s else ''
                except AttributeError:
                    row['Quoted Book'] = ''
                row['Quoted Ref'] = ''
                row['id'] = r.order_id()
                del row['Quote Num']
                del row['Score']
                out_rows += [row]
    out_rows.sort(key=lambda x: x['id'])
    for r in out_rows:
        del r['id']
    with open(ROOT + "/qa_books.csv", "wb") as fout:
        cout = unicodecsv.DictWriter(fout, ["Quoting Book", "Quoting Ref", "Quoted Book", "Quoted Ref", "Snippet"])
        cout.writeheader()
        cout.writerows(out_rows)


word_counter = defaultdict(int)

def count_words():
    global word_counter
    index_set = library.all_index_records()
    for ii, i in enumerate(index_set):
        print("{}/{}".format(ii, len(index_set)))
        count_words_map(i)
    with codecs.open(ROOT + '/word_counts.json', 'wb', encoding='utf8') as fout:
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
    except AttributeError:
        pass


def post_unambiguous_links(post=False):
    links = []
    with open(ROOT + "/unambiguous_links.csv", "r") as fin:
        cin = csv.DictReader(fin)
        for row in cin:
            link = {"generated_by": "link_disambiguator", "auto": True,
                     "type": "", "refs": [row["Quoting Ref"], row["Quoted Ref"]]}
            links += [link]
    print("Total Links: {}".format(len(links)))
    if post:
        i = 0
        batch_size = 50
        while i < len(links):
            print("Posting [{}:{}]".format(i, i + batch_size - 1))
            print(post_link(links[i:i + batch_size]))
            i += batch_size
    else:
        for link_obj in tqdm(links):
            try:
                Link(link_obj).save()
            except DuplicateRecordError:
                pass  # poopy


def calc_stats():
    books = defaultdict(int)
    cats = defaultdict(int)
    with open("research/link_disambiguator/unambiguous_links.json", "r") as fin:
        cin = csv.DictReader(fin)
        for row in cin:
            try:
                quoting = Ref(row["Quoting Ref"])
                key = quoting.index.collective_title if hasattr(quoting.index, "collective_title") else quoting.index.title
                books[key] += 1
                cats[quoting.primary_category] += 1
            except InputError:
                print(row["Quoting Ref"])
    with open("research/link_disambiguator/unambiguous_books.json", "w") as fout:
        books = [list(x) for x in sorted(list(books.items()), key=lambda x: x[1], reverse=True)]
        json.dump({"books": books, "cats": cats}, fout, ensure_ascii=False, indent=2)


def delete_irrelevant_disambiguator_links(dryrun=True):
    """
    After a while, disambiguator links can break if segmentation changes
    Check that for each existing disambiguator link, there still exists an inline citation to back it
    """
    def make_tc(tref, oref):
        global _tc_cache
        tc = oref.text('he')
        _tc_cache[tref] = tc
        if len(_tc_cache) > 5000:
            _tc_cache = {}
        return tc
    def normalize(s):
        return re.sub(r"<[^>]+>", "", strip_cantillation(s, strip_vowels=True))
    irrelevant_links = []
    ls = LinkSet({"generated_by": "link_disambiguator", "auto": True})
    for link in tqdm(ls, total=ls.count()):
        source_tref, quoted_tref = link.refs if Ref(link.refs[1]).primary_category == 'Talmud' else reversed(link.refs)
        source_oref = Ref(source_tref)
        quoted_oref= Ref(quoted_tref)
        if quoted_oref.primary_category != 'Talmud': continue
        source_tc = _tc_cache.get(source_tref, make_tc(source_tref, source_oref))
        if len(source_tc.text) == 0 or isinstance(source_tc.text, list):
            snippets = None
        else:
            snippets = get_snippet_by_seg_ref(source_tc, quoted_oref.section_ref(), must_find_snippet=True)
        if snippets is None:
            irrelevant_links += [{"ID": link._id, "Source": source_tref, "Quoted": quoted_tref, "Source Text": normalize(source_tc.ja().flatten_to_string())}]

    with open(ROOT + '/irrelevant_links.csv', 'w') as fout:
        c = csv.DictWriter(fout, ['ID', 'Source', 'Quoted', 'Source Text'])
        c.writeheader()
        c.writerows(irrelevant_links)
    if not dryrun:    
        from sefaria.system.database import db
        from pymongo import DeleteOne
        db.links.bulk_write([DeleteOne({"_id": _id}) for _id in irrelevant_links])


def run():
    delete_irrelevant_disambiguator_links(False)  # run before disambiguate_all() to clear out irrelevant links first
    # ld = Link_Disambiguator()
    # ld.get_ambiguous_segments()
    # disambiguate_all()
    # get_qa_csv()
    # ld = Link_Disambiguator()
    # ld.disambiguate_gra()
    # count_words()
    #post_unambiguous_links(post=True)
    # calc_stats()
    #filter_books_from_output({u'Akeidat Yitzchak', u'HaKtav VeHaKabalah'}, {u'Responsa'})
    #filter_books_from_output({u'Alshich on Torah', u'Meshech Hochma', u'Messilat Yesharim', u'Gevurot Hashem', u'Kedushat Levi', u'Mei HaShiloach'}, set())

if __name__ == '__main__':
    profiling = False
    if profiling:
        print("Profiling...\n")
        cProfile.run("run()", "stats")
        p = pstats.Stats("stats")
        sys.stdout = sys.__stdout__
        p.strip_dirs().sort_stats("cumtime").print_stats()
    else:
        run()


    # tc_list = [Ref("Zohar 1:70b:7").text("he"), Ref("Song of Songs 1").text("he")] #{'match_index': [[5, 7], [11, 13]], 'score': 81, 'match': [u'Zohar 1:70b:7', u'Song of Songs 1:3']}
    # tc_list = [Ref("Zohar 1:70b:9").text("he"), Ref("Genesis 1").text("he")] #{'match_index': [[27, 32], [106, 111]], 'score': 96, 'match': [u'Genesis 1:4', u'Zohar 1:70b:9']}

# TODO: find the right length of match. best way to score? limit matches to one side of ref

""
