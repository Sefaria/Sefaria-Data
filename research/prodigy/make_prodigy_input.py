import django, regex, srsly, random
from collections import defaultdict
from tqdm import tqdm
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import InputError
from research.prodigy.db_manager import MongoProdigyDBManager

class ProdigyInputWalker:
    def __init__(self):
        self.prodigyInput = []
        self.prodigyInputByVersion = defaultdict(list)
    
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

    def normalize(self, text):
        return regex.sub(r"\s*<[^>]+>\s*", " ", text)

    def split_text(self, text):
        return text.split('. ')

    def get_input(self, text, en_tref, language):
        text_list = text.split('\n')
        temp_input_list = []
        for t in text_list:
            if len(t) <= 20: continue
            refs_with_loc = ProdigyInputWalker.get_refs_with_location(t, language)
            temp_input = {
                "text": t,
                "spans": [
                    {"start": s, "end": e, "label": "מקור"} for _, _, s, e in refs_with_loc
                ],
                "meta": {
                    "Ref": en_tref
                }
            }
            temp_input_list += [temp_input]
        return temp_input_list
    
    def action(self, text, en_tref, he_tref, version):
        norm_text = self.normalize(text)
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


def make_prodigy_input(title_list, vtitle_list, lang_list):
    walker = ProdigyInputWalker()
    for title, vtitle, lang in tqdm(zip(title_list, vtitle_list, lang_list), total=len(title_list)):
        if vtitle is None:
            version = VersionSet({"title": title, "language": lang}, sort=[("priority", -1)], limit=1).array()[0]
        else:
            version = Version().load({"title": title, "versionTitle": vtitle, "language": lang})
        version.walk_thru_contents(walker.action)
    walker.make_final_input(400)
    srsly.write_jsonl('research/prodigy/data/test_input.jsonl', walker.prodigyInput)

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



if __name__ == "__main__":
    # title_list = [
    #     'Rashba on Eruvin', 'Chiddushei Ramban on Avodah Zarah', 'Ben Yehoyada on Beitzah',
    #     'Tosafot on Shabbat', 'Chidushei Agadot on Rosh Hashanah', 'Chidushei Halachot on Taanit', 'Rabbeinu Gershom on Chullin',
    #     'Maharam Shif on Gittin', 'Maadaney Yom Tov on Menachot', 'Rashbam on Bava Batra', 'Penei Yehoshua on Bava Metzia',
    #     'Ran on Nedarim', 'Tosafot Shantz on Sotah', 'Yad Ramah on Bava Batra', 'Shita Mekubetzet on Berakhot'
    # ]
    # make_prodigy_input(title_list, [None]*len(title_list), ['he']*len(title_list))
    combine_all_sentences_to_paragraphs()