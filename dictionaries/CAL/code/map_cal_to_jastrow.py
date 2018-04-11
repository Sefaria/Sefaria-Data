# -*- coding: utf-8 -*-

import argparse
import codecs
import bleach
import glob
import json
import re
from collections import defaultdict
from itertools import izip
from xml.etree import ElementTree
import local_settings
from sefaria.model import *


MAP_FILE = "../data/calJastrowMapping.json"


class SokoloffLexicon(object):

    LEXICON_NAME = "Sokoloff"
    DIALECTS_OF_INTEREST = ["00", "53", "71"]
    POS_NAMES = {
        "N": "Noun",
        "X": "Adverb",
        "a": "Adverb",
        "R": "Pronoun",
        "c": "Conjunction",
        "A": "Adjective",
        "p": "Preposition",
        "I": "Interjection",
        "b": "Number",
        "s": "Letter",
        "d": "Divine Name",
        "N01": "Singular absolute or construct form noun",
        "N02": "Singular determined noun",
        "N03": "Plural absolute noun",
        "N04": "Plural construct form noun",
        "N05": "Plural determined noun",
        "V01": "Peal",
        "V02": "Pael",
        "V03": "(H)aphel",
        "V04": "Ethpeel",
        "V05": "Ethpaal",
        "V06": "Ettaphal",
        "V08": "Reduplicated",
        "V09": "Quadrilateral",
        "V10": "Ethpaiel",
        "V11": "Reflexive reduplicate",
        "V12": "Reflexive quadrilateral",
        "A01": "Singular absolute or construct form adjective",
        "A02": "Singular determined adjective",
        "A03": "Plural absolute adjective",
        "A04": "Plural construct form adjective",
        "A05": "Plural determined adjective",
        "n01": "Singular absolute or construct form number",
        "n02": "Singular determined number",
        "n03": "Plural absolute number",
        "n04": "Plural construct number",
        "n05": "Plural determined number",
        "p01": "Independent preposition",
        "p02": "Preposition with pronominal suffix",
        "p03": "Proclitic preposition",
        "GN": "Geographical name",
        "PN": "Proper name",
    }

    @staticmethod
    def create_all():
        SokoloffLexicon.create_lexicon()

        with codecs.open("../data/Cal-Data-Files/dictfull.json", "rb", encoding="utf8") as dict_fp:
            dictfull = json.load(dict_fp, encoding="utf8")
        for hw, v1 in dictfull.items():
            for pos, v2 in v1.items():
                SokoloffLexicon.create_lexicon_entry(hw, pos, v2)

    @staticmethod
    def create_lexicon():
        l = Lexicon().load({"name": SokoloffLexicon.LEXICON_NAME})
        if not l:
            Lexicon({
                "to_language": "eng",
                "name": SokoloffLexicon.LEXICON_NAME,
                "language": "ara.babylonian",
                "source": "Michael Sokoloff's Dictionary of Jewish Babylonian Aramaic",
                "attribution": "Comprehensive Aramaic Lexicon (CAL)",
                "attribution_url": "http://cal1.cn.huc.edu/",
                "text_categories": [
                    'Talmud, Bavli, Seder Zeraim',
                    'Talmud, Bavli, Seder Moed',
                    'Talmud, Bavli, Seder Nashim',
                    'Talmud, Bavli, Seder Nezikin',
                    'Talmud, Bavli, Seder Kodashim',
                    'Talmud, Bavli, Seder Tahorot',
                    'Talmud, Yerushalmi, Seder Zeraim',
                    'Talmud, Yerushalmi, Seder Moed',
                    'Talmud, Yerushalmi, Seder Nashim',
                    'Talmud, Yerushalmi, Seder Nezikin',
                    'Talmud, Yerushalmi, Seder Tahorot'
                ]
            }).save()

    @staticmethod
    def create_lexicon_entry(headword, pos, data):
        """
        :param headword:
        :param data: list of definitions of the form { "dialects": list, "definition": str, "def_num": str }
        :return:
        """
        def traverse(curr_def, sense_stack, last_depth_list):
            curr_depth_list = curr_def["def_num"].split(".")
            first_diff_depth = len(sense_stack)
            for i, (a,b) in enumerate(izip(last_depth_list, curr_depth_list)):
                if a != b:
                    first_diff_depth = i + 1
                    break
            curr_sense = defaultdict(list)
            curr_sense["definition"] = curr_def["definition"]
            while len(sense_stack) > first_diff_depth:
                sense_stack.pop()
            sense_stack[-1]["senses"] += [curr_sense]
            sense_stack.append(curr_sense)
            return curr_depth_list

        # lots of built in python functions.
        # first, filter out definitions that dont have the DIALECTS_OF_INTEREST
        # then, sorted the list so that its in def_num order. reduce just does some fancy math to make the sort work
        data = sorted(filter(lambda x: any([d in SokoloffLexicon.DIALECTS_OF_INTEREST for d in x["dialects"]]), data),
                      key=lambda x: reduce(lambda a, b: a + int(b[1]) ** (5 - b[0]), enumerate(x["def_num"].split(".")), 0))
        le = LexiconEntry().load({"headword": headword, "parent_lexicon": SokoloffLexicon.LEXICON_NAME})
        if not le:
            senses = defaultdict(list)
            sense_stack = [senses]
            last_depth_list = []
            for d in data:
                last_depth_list = traverse(d, sense_stack, last_depth_list)

            dict_entry = {
                'headword': headword,
                'parent_lexicon': SokoloffLexicon.LEXICON_NAME,
                'content': senses
            }

            #LexiconEntry(dict_entry).save()

    @staticmethod
    def create_word_form():
        pass

class CalJastrowLink(object):
    """
    represents a link between CAL forms / headwords and Jastrow headwords that all share a common spelling (without nikkud)
    """
    def __init__(self):
        self.jhw_id_set = set()
        self.jastrow = []
        self.cal = defaultdict(list)

    def add_jastrow(self, jheadword, jid):
        jheadword = CalJastrowLink.clean_hw(jheadword)
        if (jheadword, jid) in self.jhw_id_set:
            print u"Already have jid {}, jheadword {}".format(jid, jheadword)
            return
        self.jastrow.append({
            "jheadword": jheadword,
            "jid": jid,
        })
        self.jhw_id_set.add((jheadword, jid))

    def add_cal(self, cheadword, cform, pos, word_num):
        self.cal[cheadword] += [{'w': cform, 'p': pos, 'n': word_num}]

    @staticmethod
    def clean_hw(hw):
        return re.sub(ur"[,.;]", u"", hw.strip())

    def to_json(self):
        return {
            "jastrow": self.jastrow,
            "cal": {
                k: list(v) for k, v in self.cal.items()
            }
        }


def clean_jheadword(jhw):
    return re.sub(ur"[^א-ת]", u"", jhw)


def clean_cheadword(chw):
    sofit_map = {
        u"מ": u"ם",
        u"כ": u"ך",
        u"נ": u"ן",
        u"פ": u"ף",
        u"צ": u"ץ"
    }
    if chw[-1] in sofit_map:
        return chw[:-1] + sofit_map[chw[-1]]
    else:
        return chw


def input_jastrow():
    tree = ElementTree.parse('../../Jastrow/data/01-Merged XML/Jastrow-full.xml')
    root = tree.getroot()
    chapters = root.find("body").findall("chapter")

    bad_hws = 0
    dup_hws = 0
    total_hws = 0
    for i, chapter in enumerate(chapters):
        raw_entries = chapter.findall("entry")
        for e in raw_entries:
            id = e.attrib["id"]
            headwords = [el.text for el in e.findall("head-word")]

            for hw in headwords:
                total_hws += 1
                if not hw:
                    bad_hws += 1
                    continue
                hw_clean = clean_jheadword(hw)
                if len(hw_clean) == 0:
                    bad_hws += 1
                    continue
                if hw_clean not in CalJastrowMapping:
                    cjl = CalJastrowLink()
                    CalJastrowMapping[hw_clean] = cjl
                else:
                    dup_hws += 1
                    cjl = CalJastrowMapping[hw_clean]
                cjl.add_jastrow(hw, id)

    print bad_hws, dup_hws, total_hws


def input_cal():
    cal_matches = 0
    cal_mismatches = 0
    num_files = 0
    mismatched = []
    used_word_instead = defaultdict(list)
    # prefix_map = defaultdict(set)
    for file in glob.glob("../data/Cal-Matched-to-Sefaria/*/*.json"):
        if num_files % 100 == 0:
            print file
        num_files += 1
        with codecs.open(file, 'rb', encoding='utf8') as fin:
            cal_json = json.load(fin, encoding='utf8')
            for iw, w in enumerate(cal_json['words']):
                if 'head_word' in w:
                    cheadword = clean_cheadword(w['head_word'])
                    if cheadword in CalJastrowMapping:
                        cal_matches += 1
                        cjl = CalJastrowMapping[cheadword]
                        cjl.add_cal(cheadword, w['word'], w['POS'], iw)
                    elif w['word'] in CalJastrowMapping and len(w['word'].split()) == len(cheadword.split()) and u"'" not in cheadword:
                        used_word_instead[w['word']] += [[w['word'], cheadword]]
                        cal_matches += 1
                        cjl = CalJastrowMapping[w['word']]
                        cjl.add_cal(cheadword, w['word'], w['POS'], iw)
                    else:
                        if cheadword[-1] == u'_' or u"'" in cheadword or len(cheadword.split()) > 1:
                            continue
                        cal_mismatches += 1
                        mismatched += [{"head_word": cheadword, "word": w['word']}]
                    # if 'prefix' in w:
                    #     for p in w['prefix']:
                    #         prefix_map[w['POS'][0]].add(p)
    # with codecs.open('mismatched_cal.json', 'wb', encoding='utf8') as fout:
    #     json.dump(mismatched, fout, ensure_ascii=False, indent=4)
    print "Cal Matches: {}".format(cal_matches)
    print "Cal Mismatches: {}".format(cal_mismatches)
    # with codecs.open('../data/prefixes.json', 'wb', encoding='utf8') as prefix_f:
    #     json.dump({k: list(v) for k, v in prefix_map.items()}, prefix_f, ensure_ascii=False, indent=4, encoding='utf8')


def input_prefixed_cal():
    """
    putting this func on hold because I think it'll add too much error to mapping
    :return:
    """
    with codecs.open("../data/prefixes.json", 'rb', encoding='utf8') as pref:
        prefix_map = json.load(pref, encoding='utf8')
    for jhw, v1 in CalJastrowMapping.items():
        for chw, v2 in v1["cal"].items():
            pass


def save_mapping():
    with codecs.open(MAP_FILE, "wb", encoding='utf8') as fout:
        out = {
            k: v.to_json() for k, v in CalJastrowMapping.items()
        }
        json.dump(out, fout, ensure_ascii=False, indent=4)


def tokenizer(s):
    s = bleach.clean(s.strip(), tags=[], strip=True)
    word_list = s.split()
    word_list = [w for w in word_list if len(w.strip()) > 0]
    return word_list

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", help="One of [map, dryrun]")
    user_args = parser.parse_args()

    if user_args.action == "map":
        CalJastrowMapping = {}
        input_jastrow()
        input_cal()
        save_mapping()
    elif user_args.action == "dryrun":
        with codecs.open(MAP_FILE, 'rb', encoding='utf8') as fin:
            map_json = json.load(fin, encoding='utf8')
            word_set = set()
            for jhw, v in map_json.items():
                word_set.add(jhw)
                for cw in v['cal']:
                    word_set.add(cw)
        indexes = library.get_indexes_in_category("Bavli", full_records=True)
        vtitle = 'William Davidson Edition - Aramaic'

        words_seen = 0
        words_matched = 0
        for index in indexes:
            print index.title
            unit_list_temp = index.nodes.traverse_to_list(
                lambda n, _: TextChunk(n.ref(), "he", vtitle=vtitle).ja().flatten_to_array() if not n.children else [])
            unit_wl = [w for seg in unit_list_temp for w in tokenizer(seg)]
            for w in unit_wl:
                words_seen += 1
                if w in word_set:
                    words_matched += 1
        print words_matched, words_seen, 100.0*words_matched/words_seen
    elif user_args.action == "create-lexicon":
        SokoloffLexicon.create_all()
    else:
        print "no action"


