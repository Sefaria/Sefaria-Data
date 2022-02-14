import django, regex, srsly, random, re
from os import walk, path
from collections import defaultdict
from tqdm import tqdm
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import InputError
from research.prodigy.prodigy_package.db_manager import MongoProdigyDBManager
from sefaria.helper.normalization import NormalizerComposer


class ProdigyInputWalker:
    def __init__(self, prev_tagged_refs=None):
        self.prodigyInput = []
        self.prodigyInputByVersion = defaultdict(list)
        self.prev_tagged_refs = prev_tagged_refs or []
        self.normalizer = NormalizerComposer(['unidecode', 'html', 'maqaf', 'cantillation', 'double-space'])

    @staticmethod
    def get_refs_with_location(text, lang, citing_only=True):
        unique_titles = set(library.get_titles_in_string(text, lang, citing_only))
        title_node_dict = {title: library.get_schema_node(title,lang) for title in unique_titles}
        titles_regex_str = library.get_multi_title_regex_string(unique_titles, lang)
        titles_regex = regex.compile(titles_regex_str, regex.VERBOSE)
        
        def get_ref_from_match(match, outer_start=0):
            try:
                gs = match.groupdict()
                assert gs.get("title") is not None
                node = title_node_dict[gs.get("title")]
                ref = library._get_ref_from_match(match, node, lang)
                return ref.normal(), match.group(0), match.start(0)+outer_start, match.end(0)+outer_start
            except InputError:
                return None
            except AssertionError:
                return None
            except ValueError:
                return None
            except KeyError:
                return None

        refs_with_loc = []
        if lang == "en":
            refs_with_loc = [get_ref_from_match(m) for m in titles_regex.finditer(text)]
        else:
            outer_regex_str = r"[({\[].+?[)}\]]"
            outer_regex = regex.compile(outer_regex_str, regex.VERBOSE)
            for outer_match in outer_regex.finditer(text):
                refs_with_loc += [get_ref_from_match(m, outer_match.start(0)) for m in titles_regex.finditer(outer_match.group(0))]
        refs_with_loc = list(filter(None, refs_with_loc))
        return refs_with_loc

    def split_text(self, text):
        return text.split('. ')

    def get_input(self, text, en_tref, language):
        text = self.normalizer.normalize(text)
        text_list = text.split('\n')
        temp_input_list = []
        for t in text_list:
            if len(t) <= 20: continue
            refs_with_loc = ProdigyInputWalker.get_refs_with_location(t, language)
            temp_input = {
                "text": t,
                "spans": [
                    {"start": s, "end": e, "label": "source"} for _, _, s, e in refs_with_loc
                ],
                "meta": {
                    "Ref": en_tref
                }
            }
            temp_input_list += [temp_input]
        return temp_input_list
    
    def action(self, text, en_tref, he_tref, version):
        if en_tref in self.prev_tagged_refs:
            print("ignoring", en_tref)
            return
        # text = TextChunk._strip_itags(text)
        temp_input_list = self.get_input(norm_text, en_tref, version.language)
        self.prodigyInputByVersion[(version.versionTitle, version.title, version.language)] += temp_input_list
        
    def make_final_input(self, sample_size):
        import statistics
        lens = []
        for temp_input_list in self.prodigyInputByVersion.values():
            lens += [len(t['text']) for t in temp_input_list]
            self.prodigyInput += random.sample(temp_input_list, min(len(temp_input_list), sample_size))
        print(statistics.mean(lens))
        print(statistics.stdev(lens))
        random.shuffle(self.prodigyInput)


def make_prodigy_input(title_list, vtitle_list, lang_list, prev_tagged_refs):
    walker = ProdigyInputWalker(prev_tagged_refs)
    for title, vtitle, lang in tqdm(zip(title_list, vtitle_list, lang_list), total=len(title_list)):
        if vtitle is None:
            version = VersionSet({"title": title, "language": lang}, sort=[("priority", -1)], limit=1).array()[0]
        else:
            version = Version().load({"title": title, "versionTitle": vtitle, "language": lang})
        version.walk_thru_contents(walker.action)
    walker.make_final_input(400)
    srsly.write_jsonl('data/test_input.jsonl', walker.prodigyInput)


def make_prodigy_input_webpages(n):
    LOC = "/Users/nss/sefaria/datasets/webpages"
    walker = ProdigyInputWalker()
    chosen = 0
    for (dirpath, dirnames, filenames) in walk(path.join(LOC, 'he')):
        for filename in tqdm(filenames, total=2*n):  # total is approximate
            if random.choice([True, False]): continue
            if chosen >= n: break
            chosen += 1
            with open(path.join(dirpath, filename), 'r') as fin:
                url = None
                for iline, line in enumerate(fin):
                    line = " ".join(re.split(r'\s+', line)).strip()

                    if iline == 0: url = line
                    if iline < 2: continue
                    walker.prodigyInput += walker.get_input(line, url, 'he')
    random.shuffle(walker.prodigyInput)
    srsly.write_jsonl('data/test_input.jsonl', walker.prodigyInput)


def combine_sentences_to_paragraph(sentences):
    if len(sentences) == 0: return
    full_text = ""
    full_spans = []
    curr_tokens = 0
    already_seen_text = set()
    for s in sentences:
        if s['text'] in already_seen_text: continue
        already_seen_text.add(s['text'])
        if len(full_text) > 0: full_text += " "
        full_spans += [{
            "start": span['start'] + len(full_text),
            "end": span['end'] + len(full_text),
            "token_start": span['token_start'] + curr_tokens,
            "token_end": span['token_end'] + curr_tokens,
            "label": span['label']
        } for span in s['spans']]
        curr_tokens += len(s['tokens'])
        full_text += s['text']
    return {
        'text': full_text,
        'spans': full_spans,
        'meta': sentences[0]['meta']
    }

def combine_all_sentences_to_paragraphs():
    my_db = MongoProdigyDBManager('localhost', 27017)
    examples = my_db.db.examples
    combined_examples = []
    examples_by_ref = defaultdict(list)
    for example in examples.find({}):
        examples_by_ref[example['meta']['Ref']] += [example]
    combined_examples = [combine_sentences_to_paragraph(sentences) for sentences in examples_by_ref.values()]
    my_db.db.examples1_input.delete_many({})
    my_db.db.examples1_input.insert_many(combined_examples)

def make_prodigy_input_by_refs(ref_list, lang, vtitle):
    walker = ProdigyInputWalker([])
    input_list = []
    for tref in ref_list:
        oref = Ref(tref)
        text = walker.normalizer.normalize(oref.text(lang, vtitle=vtitle).text)
        temp_input_list = walker.get_input(text, tref, lang)
        input_list += temp_input_list
    srsly.write_jsonl('data/test_input.jsonl', input_list)

def make_prodigy_input_sub_citation(citation_collection, output_collection):
    my_db = MongoProdigyDBManager('blah', 'localhost', 27017)
    getattr(my_db.db, output_collection).delete_many({})
    for doc in getattr(my_db.db, citation_collection).find({}):
        for span in doc['spans']:
            span_text = doc['text'][span['start']:span['end']]
            getattr(my_db.db, output_collection).insert_one({"text": span_text, "spans": [], "meta": {"Ref": doc['meta']['Ref'], "Start": span['start'], "End": span['end']}})

def get_prev_tagged_refs(collection):
    my_db = MongoProdigyDBManager(collection,'localhost', 27017)
    return set(my_db.output_collection.find({}).distinct('meta.Ref'))

if __name__ == "__main__":
    # title_list = [
    #     'Rashba on Chullin', 'Chiddushei Ramban on Beitzah',
    #     'Tosafot on Shevuot', 'Rabbeinu Gershom on Meilah',
    #     'Rashbam on Menachot',
    #     'Yad Ramah on Sanhedrin', 'Rashi on Taanit', "Chidushei HaRa'ah on Berakhot",
    #     "Commentary of the Rosh on Nedarim", "Mefaresh on Tamid", "Meiri on Bava Kamma",
    #     "Mordechai on Bava Batra", "Rav Nissim Gaon on Shabbat", "Rosh on Kiddushin", "Tosafot Chad Mikamei on Yevamot",
    #     "Tosafot HaRosh on Horayot", "Tosafot Rid on Avodah Zarah Third Recension", "Tosafot Shantz on Sotah",
    #     "Tosafot Yeshanim on Keritot", "HaMaor HaKatan on Eruvin", "Nimukei Yosef on Bava Metzia"
    # ]
    title_list = [
        "Ein HaTekhelet", "Shev Shmat'ta", "Havot Yair", "Responsa Chatam Sofer", "Netivot Olam", "Mei HaShiloach", "Pri Tzadik", "Sefer HeArukh"
    ]
    prev_tagged_refs = get_prev_tagged_refs('gold_output_full')
    # title_list = [i.title for i in IndexSet({"title": re.compile(r'Gilyon HaShas on')})]
    # print(title_list)
    #make_prodigy_input(title_list, [None]*len(title_list), ['en']*len(title_list), prev_tagged_refs)
    make_prodigy_input_webpages(3000)
    # combine_all_sentences_to_paragraphs()
    # make_prodigy_input_sub_citation('yerushalmi_output2', 'yerushalmi_sub_citation_input2')