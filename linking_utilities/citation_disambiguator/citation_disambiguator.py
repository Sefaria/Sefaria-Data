# -*- coding: utf-8 -*-
import sys, os
import traceback
from tqdm import tqdm
from typing import Dict, List
from functools import reduce, partial
import argparse


import re, json, heapq, random, regex, math, cProfile, pstats, csv
import django
django.setup()
from sefaria.model import *
from sefaria.helper.normalization import NormalizerComposer, RegexNormalizer, ReplaceNormalizer
from linking_utilities.parallel_matcher import ParallelMatcher
from collections import defaultdict, OrderedDict
from sefaria.system.exceptions import PartialRefInputError, InputError, NoVersionFoundError, DuplicateRecordError
from sefaria.utils.hebrew import strip_cantillation
from linking_utilities.weighted_levenshtein import WeightedLevenshtein
from linking_utilities.dibur_hamatchil_matcher import get_maximum_dh, ComputeLevenshteinDistanceByWord

LOWEST_SCORE = -28
DATA_DIR = "data"


class TextChunkFactory:
    """
    Factory class for creating and caching text chunks for speed
    """

    _tc_cache = {}

    @classmethod
    def make(cls, tref, oref, version_title=None):
        if tref is None:
            tref = oref.normal()
        if tref in cls._tc_cache:
            return cls._tc_cache[tref]

        tc = oref.text('he', vtitle=version_title)
        cls._tc_cache[tref] = tc
        if len(cls._tc_cache) > 5000:
            cls._tc_cache = {}
        return tc


def argmax(iterable, n=1):
    if n==1:
        return [max(enumerate(iterable), key=lambda x: x[1])[0]]
    else:
        return heapq.nlargest(n, range(len(iterable)), iterable.__getitem__)


class CitationDisambiguator:
    """
    Currently limited to disambiguating citations to Tanakh and Bavli
    """

    stop_words = ["ר'", 'רב', 'רבי', 'בן', 'בר', 'בריה', 'אמר', 'כאמר', 'וכאמר', 'דאמר', 'ודאמר', 'כדאמר',
                  'וכדאמר', 'ואמר', 'כרב',
                  'ורב', 'כדרב', 'דרב', 'ודרב', 'וכדרב', 'כרבי', 'ורבי', 'כדרבי', 'דרבי', 'ודרבי', 'וכדרבי',
                  "כר'", "ור'", "כדר'",
                  "דר'", "ודר'", "וכדר'", 'א״ר', 'וא״ר', 'כא״ר', 'דא״ר', 'דאמרי', 'משמיה', 'קאמר', 'קאמרי',
                  'לרב', 'לרבי',
                  "לר'", 'ברב', 'ברבי', "בר'", 'הא', 'בהא', 'הך', 'בהך', 'ליה', 'צריכי', 'צריכא', 'וצריכי',
                  'וצריכא', 'הלל', 'שמאי', "וגו'", 'וגו׳', 'וגו']

    def __init__(self, lang, title=None, version_title=None):
        self.title = title
        self.version_title = version_title
        self.levenshtein = WeightedLevenshtein()
        self.matcher = None
        # self.normalizer = NormalizerComposer(step_keys=['cantillation', 'html', 'parens-plus-contents', 'maqaf', 'kri-ktiv', 'hasehm', 'elokim'])
        try:
            print("Loading word counts...")
            with open(DATA_DIR + f"/word_counts_{lang}.json", "r") as fin:
                self.word_counts = json.load(fin)
        except IOError:
            raise Exception("Couldn't find word counts file. Please run count_words().")

        self.segments_to_disambiguate: Dict[str, List[Ref]] = None

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
                   "\\1\\2\u05d9\u05d4\u05d5\u05d4\\3", base_str)
        # replace common elokim replacement with elokim
        base_str = re.sub(r"(^|\s)([\u05de\u05e9\u05d5\u05db\u05dc\u05d1]?)(?:\u05d0\u05dc\u05e7\u05d9\u05dd)($|\s)",
                   "\\1\\2\u05d0\u05dc\u05d4\u05d9\u05dd\\3", base_str)

        word_list = re.split(r"\s+", base_str)
        word_list = [w for w in word_list if len(w.strip()) > 0 and w not in CitationDisambiguator.stop_words]
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

    def get_ambiguous_segments(self):
        tanakh_books = library.get_indexes_in_corpus("Tanakh")
        talmud_books = library.get_indexes_in_corpus("Bavli")
        tan_tal_books = set(tanakh_books + talmud_books)
        query = {
            "refs": re.compile(r'^({}) \d+[ab]?$'.format('|'.join(tanakh_books + talmud_books)))
        }
        linkset = LinkSet(query)
        segment_map = defaultdict(list)
        total = 0
        for link in tqdm(linkset, total=linkset.count(), desc="validate ambiguous refs"):
            try:
                orefs = [Ref(tref) for tref in link.refs]
                quoter_oref, quoted_oref = orefs if orefs[1].index.title in tan_tal_books else reversed(orefs)
                if self.title and quoter_oref.index.title != self.title:
                    continue
                segment_map[quoter_oref.normal()] += [quoted_oref]
                total += 1
            except PartialRefInputError:
                pass
            except InputError:
                pass
        print(f"Total num ambiguous {total}")
        print(f"Num unique refs with ambiguous citations {len(segment_map.keys())}")

        self.segments_to_disambiguate = segment_map

    def disambiguate_all(self):
        good = []
        bad = []
        fgood = open(DATA_DIR +'/unambiguous_links.csv', 'w')
        fbad = open(DATA_DIR + '/still_ambiguous_links.csv', 'w')
        csv_good = csv.DictWriter(fgood, ['Quoting Ref', 'Quoted Ref', 'Score', 'Quote Num', 'Snippet', 'Quoting Version Title'])
        csv_good.writeheader()
        csv_bad = csv.DictWriter(fbad, ['Quoting Ref', 'Quoted Ref', 'Score', 'Quote Num', 'Snippet', 'Quoting Version Title'])
        csv_bad.writeheader()
        for iambig, (main_str, quoted_orefs) in tqdm(enumerate(self.segments_to_disambiguate.items()), total=len(self.segments_to_disambiguate), desc="disambiguate all"):
            try:
                main_ref = Ref(main_str)
                main_tc = TextChunkFactory.make(main_str, main_ref, self.version_title)
                for quoted_oref in quoted_orefs:
                    temp_good, temp_bad = self.disambiguate_one(main_ref, main_tc, quoted_oref)
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

    def disambiguate_one(self, main_oref, main_tc, quoted_oref, snip_only_before=False):
        good, bad = [], []
        try:
            main_snippet_list = get_snippet_by_seg_ref(main_tc.text, quoted_oref, must_find_snippet=True, snip_size=65, use_indicator_words=True, snip_only_before=snip_only_before)
        except InputError:
            return good, bad
        except UnicodeEncodeError:
            return good, bad
        if main_snippet_list:
            for isnip, main_snippet in enumerate(main_snippet_list):
                quoted_tref = quoted_oref.normal()
                results = self.disambiguate_segment_by_snippet(quoted_tref, [(main_snippet, main_oref.normal())])
                for k, v in list(results.items()):
                    is_bad = v is None
                    temp = {
                        "Quote Num": isnip,
                        "Snippet": main_snippet,
                        "Quoting Version Title": main_tc.vtitle,
                        "Quoted Ref": v["A Ref"] if not is_bad else quoted_oref.normal(),
                        "Quoting Ref": v["B Ref"] if not is_bad else k,
                        "Score": v["Score"] if not is_bad else LOWEST_SCORE
                    }
                    if is_bad:
                        bad += [temp]
                    else:
                        good += [temp]
        return good, bad

    def disambiguate_segment_by_snippet(self, main_tref, tref_list, lowest_score_threshold=LOWEST_SCORE, max_words_between=1, min_words_in_match=2, ngram_size=3, verbose=False, with_match_text=False):
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

    def delete_irrelevant_disambiguator_links(self, dryrun=True):
        """
        After a while, disambiguator links can break if segmentation changes
        Check that for each existing disambiguator link, there still exists an inline citation to back it
        """
        def normalize(s):
            return re.sub(r"<[^>]+>", "", strip_cantillation(s, strip_vowels=True))
        irrelevant_links = []
        ls = LinkSet({"generated_by": "link_disambiguator", "auto": True})
        for link in tqdm(ls, total=ls.count()):
            source_tref, quoted_tref = link.refs if Ref(link.refs[1]).primary_category == 'Talmud' else reversed(link.refs)
            source_oref = Ref(source_tref)
            quoted_oref= Ref(quoted_tref)
            if quoted_oref.primary_category != 'Talmud': continue
            source_tc = TextChunkFactory.make(source_tref, source_oref, self.version_title)
            if len(source_tc.text) == 0 or isinstance(source_tc.text, list):
                snippets = None
            else:
                snippets = get_snippet_by_seg_ref(source_tc.text, quoted_oref.section_ref(), must_find_snippet=True)
            if snippets is None:
                irrelevant_links += [{"ID": link._id, "Source": source_tref, "Quoted": quoted_tref, "Source Text": normalize(source_tc.ja().flatten_to_string())}]

        with open(DATA_DIR + '/irrelevant_links.csv', 'w') as fout:
            c = csv.DictWriter(fout, ['ID', 'Source', 'Quoted', 'Source Text'])
            c.writeheader()
            c.writerows(irrelevant_links)
        if not dryrun:
            from sefaria.system.database import db
            from pymongo import DeleteOne
            db.links.bulk_write([DeleteOne({"_id": _id}) for _id in irrelevant_links])


def get_snippet_from_mesorah_item(mesorah_item, pm):
    words = pm.word_list_map[mesorah_item.mesechta]
    return " ".join(words[mesorah_item.location[0]:mesorah_item.location[1]+1])


def save_disambiguated_to_file(good, bad, csv_good, csv_bad):
    csv_good.writerows(good)
    csv_bad.writerows(bad)

def get_snippet_by_seg_ref(source_text, found, must_find_snippet=False, snip_size=100, use_indicator_words=False, return_matches=False, snip_only_before=False):
    """
    based off of library.get_wrapped_refs_string
    :param source_text:
    :param found:
    :param must_find_snippet: bool, True if you only want to return a str if you found a snippet
    :param snip_size int number of chars in snippet on each side
    :param use_indicator_words bool, True if you want to use hard-coded indicator words to determine which side of the ref the quote is on
    :param snip_only_before bool, True if you want the snippet to take words only before the citation
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
    if len(source_text) == 0 or not isinstance(source_text, str):
        print(f"Invalid source text with value '{source_text}'")
    source_text = re.sub(r"<[^>]+>", "", strip_cantillation(source_text, strip_vowels=True))
    linkified = library.get_wrapped_refs_string(source_text, "he", citing_only=False, reg=reg, title_nodes=title_nodes)

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
                snip_after_size = 0 if snip_only_before else snip_size
                end_snip_naive = match.end(3) + snip_after_size if match.end(3) + snip_after_size <= len(linkified) else len(linkified)
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
    with open(DATA_DIR +"/unambiguous_links.json", "r") as fin:
        cin = csv.DictReader(fin)
        rows = [row for row in cin]

    def normalize(s):
        return re.sub(r"<[^>]+>", "", strip_cantillation(s, strip_vowels=True))

    tanakh = random.sample([x for x in rows if Ref(x['Quoted Ref']).primary_category == "Tanakh" and Ref(x['Quoting Ref']).is_segment_level()], 250)
    talmud = random.sample([x for x in rows if Ref(x['Quoted Ref']).primary_category == "Talmud" and Ref(x['Quoting Ref']).is_segment_level()], 250)
    qa_rows = [
        {
            "Found Text": normalize(Ref(x['Quoted Ref']).text("he").ja().flatten_to_string()),
            "Source Text": "...".join(get_snippet_by_seg_ref(Ref(x['Quoting Ref']).text('he').text, Ref(x['Quoted Ref']))),
            "URL": "https://sefaria.org/{}?p2={}".format(Ref(x['Quoting Ref']).url(), Ref(x['Quoted Ref']).url()),
            "Wrong segment (seg) / Wrong link (link)": ""
        }
        for x in (tanakh + talmud)]

    with open(DATA_DIR + "/QA Section Links.csv", "w") as fout:
        cin = csv.DictWriter(fout, ["Source Text", "Found Text", "URL", "Wrong segment (seg) / Wrong link (link)"])
        cin.writeheader()
        cin.writerows(qa_rows)


def filter_books_from_output(books, cats):
    with open(DATA_DIR + "/still_ambiguous_links.json", "r") as fin:
        cin = csv.DictReader(fin)
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
    with open(DATA_DIR + "/qa_books.csv", "w") as fout:
        cout = csv.DictWriter(fout, ["Quoting Book", "Quoting Ref", "Quoted Book", "Quoted Ref", "Snippet"])
        cout.writeheader()
        cout.writerows(out_rows)


def count_words(lang, force):
    if lang is None:
        raise Exception("Error: No language passed. Use -l to specify a language")

    file_path = DATA_DIR + f'/word_counts_{lang}.json'
    if not force:
        if os.path.exists(file_path):
            return
        else:
            print(f"Running word counts because {file_path} does not exist.")

    word_counter = defaultdict(int)

    version_set = VersionSet({"language": lang})
    for version in tqdm(version_set, total=version_set.count()):
        try:
            version.walk_thru_contents(partial(count_words_in_segment, word_counter))
        except InputError:
            pass

    with open(file_path, 'w') as fout:
        json.dump(word_counter, fout, ensure_ascii=False)


def count_words_in_segment(word_counter, segment_str, en_tref, he_tref, version):
    for w in CitationDisambiguator.tokenize_words(segment_str):
        word_counter[w] += 1


def post_unambiguous_links(post=False):
    from sources.functions import post_link

    links = []
    with open(DATA_DIR + "/unambiguous_links.csv", "r") as fin:
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
    with open(DATA_DIR + "/unambiguous_links.json", "r") as fin:
        cin = csv.DictReader(fin)
        for row in cin:
            try:
                quoting = Ref(row["Quoting Ref"])
                key = quoting.index.collective_title if hasattr(quoting.index, "collective_title") else quoting.index.title
                books[key] += 1
                cats[quoting.primary_category] += 1
            except InputError:
                print(row["Quoting Ref"])
    with open(DATA_DIR + "/unambiguous_books.json", "w") as fout:
        books = [list(x) for x in sorted(list(books.items()), key=lambda x: x[1], reverse=True)]
        json.dump({"books": books, "cats": cats}, fout, ensure_ascii=False, indent=2)
        



def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--lang', dest='lang', help='')
    parser.add_argument('-c', '--force-word-count', action='store_true', dest="force_word_count", help="Force a word count")
    parser.add_argument('-d', '--delete-old-links', action='store_true', dest="delete_old_links", help="Delete old link disambiguator links")
    parser.add_argument('-t', '--title', dest='title', help='Optional title. If passed, will only disambiguate citations in title. Otherwise, disambiguates on all texts.')
    parser.add_argument('--version-title', dest='version_title')
    return parser.parse_args()


def run():
    args = get_args()
    count_words(args.lang, args.force_word_count)
    if not args.title:
        print("No title passed. Disambiguating all citations throughout the library. Sit tight...")
    cd = CitationDisambiguator(args.lang, args.title, args.version_title)
    if args.delete_old_links:
        cd.delete_irrelevant_disambiguator_links(False)
    cd.get_ambiguous_segments()
    cd.disambiguate_all()
    # get_qa_csv()
    # post_unambiguous_links(post=True)
    # calc_stats()
    # filter_books_from_output({u'Akeidat Yitzchak', u'HaKtav VeHaKabalah'}, {u'Responsa'})


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

