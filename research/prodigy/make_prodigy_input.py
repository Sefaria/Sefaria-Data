import django, regex, srsly, random
from collections import defaultdict
from tqdm import tqdm
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import InputError

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
        refs_with_loc = ProdigyInputWalker.get_refs_with_location(text, language)
        temp_input = {
            "text": text,
            "spans": [
                {"start": s, "end": e, "label": "פשוט"} for _, _, s, e in refs_with_loc
            ],
            "meta": {
                "Ref": en_tref
            }
        }
        return temp_input
    
    def action(self, text, en_tref, he_tref, version):
        norm_text = self.normalize(text)
        temp_input = self.get_input(norm_text, en_tref, version.language)
        self.prodigyInputByVersion[(version.versionTitle, version.title, version.language)] += [temp_input]
        
    def make_final_input(self, sample_size):
        for temp_input_list in self.prodigyInputByVersion.values():
            self.prodigyInput += random.sample(temp_input_list, sample_size)


def make_prodigy_input(title_list, vtitle_list, lang_list):
    walker = ProdigyInputWalker()
    for title, vtitle, lang in tqdm(zip(title_list, vtitle_list, lang_list), total=len(title_list)):
        if vtitle is None:
            version = VersionSet({"title": title, "language": lang}, sort=[("priority", -1)], limit=1).array()[0]
        else:
            version = Version().load({"title": title, "versionTitle": vtitle, "language": lang})
        version.walk_thru_contents(walker.action)
    walker.make_final_input(200)
    srsly.write_jsonl('research/prodigy/data/test_input.jsonl', walker.prodigyInput)

if __name__ == "__main__":
    title_list = ['Rashba on Eruvin', 'Responsa Benei Banim', 'Magen Avraham', 'Beit Yosef', 'Be\'er HaGolah', 'Havot Yair', 'Peninei Halakhah, Festivals', 'Pele Yoetz', 'Teshuvot HaRadbaz Volume 1']
    make_prodigy_input(title_list, [None]*len(title_list), ['he']*len(title_list))