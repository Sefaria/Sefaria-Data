from collections import defaultdict
import csv, json, django, random, math, re
from pymongo import MongoClient
import srsly
django.setup()
from sefaria.model import *
from data_utilities.util import get_mapping_after_normalization, convert_normalized_indices_to_unnormalized_indices
from research.knowledge_graph.named_entity_recognition.ner_tagger import TextNormalizer
from research.prodigy.functions import wrap_chars_with_overlaps

DATA = "/home/nss/sefaria/datasets/ner/sefaria/ner_output_talmud.json"

class TalmudTrainingGenerator:

    def __init__(self, raw_training_file, vtitle, language, category, db_host='localhost', db_port=27017, randomize_titles=False) -> None:
        self.randomize_titles = randomize_titles
        self.client = MongoClient(db_host, db_port)
        self.db_name = "prodigy"
        self.db = getattr(self.client, self.db_name)
        self.vtitle = vtitle
        self.language = language
        self.category = category
        self.raw_training_examples_by_ref = defaultdict(list)
        self.spacy_training_examples = []
        self.topic_map = {t.slug: t for t in TopicSet()}
        with open(raw_training_file, 'r') as fin:
            jin = json.load(fin)
            for example in jin:
                if example['language'] != language or example['versionTitle'] != vtitle: continue
                self.raw_training_examples_by_ref[example['ref']] += [example]

    def generate_spacy_training(self):
        for title in library.get_indexes_in_category(self.category):
            self.generate_spacy_training_for_book(title)

    def get_random_title(self, slugs):
        random_slug = random.choice(slugs)
        random_topic = self.topic_map.get(random_slug)
        if random_topic is None: return
        random_title = random.choice(random_topic.get_titles(self.language, False))
        return TextNormalizer.normalize_text(self.language, random_title)

    def get_wrapped_text(self, mention, metadata):
        return metadata['new_title'], (len(metadata['new_title']) - len(mention)), 0

    def remove_subsets(self, chars_to_wrap):
        index_set_list = [set(range(start, end)) for start, end, _ in chars_to_wrap]
        new_chars_to_wrap = []
        for i, (temp_char_to_wrap, index_set) in enumerate(zip(chars_to_wrap, index_set_list)):
            is_subset = False
            for j, other_index_set in enumerate(index_set_list):
                if i == j: continue
                if index_set.issubset(other_index_set):
                    is_subset = True
                    break
            if not is_subset:
                new_chars_to_wrap += [temp_char_to_wrap]
        return new_chars_to_wrap

    def walker_action(self, s, en_tref, he_tref, version):
        examples = self.raw_training_examples_by_ref[en_tref]
        mention_indices = [(x['start'], x['end']) for x in examples]
        snorm = TextNormalizer.normalize_text(self.language, s)
        norm_map = get_mapping_after_normalization(s, TextNormalizer.get_find_text_to_remove(self.language), reverse=True)
        mention_indices = convert_normalized_indices_to_unnormalized_indices(mention_indices, norm_map, reverse=True)
        chars_to_wrap = []
        for example, (start, end) in zip(examples, mention_indices):
            # just to make sure...
            assert TextNormalizer.normalize_text(self.language, example['mention']) == snorm[start:end]
            new_title = self.get_random_title(example['id_matches'])
            if new_title is None: continue
            chars_to_wrap += [(start, end, {"new_title": new_title})]
        if self.randomize_titles:
            snorm, chars_to_wrap = wrap_chars_with_overlaps(snorm, chars_to_wrap, self.get_wrapped_text, return_chars_to_wrap=True)

        chars_to_wrap = self.remove_subsets(chars_to_wrap)
        self.spacy_training_examples += [{
            "text": snorm,
            "meta": {
                "Ref": en_tref
            },
            "answer": "accept",
            "spans": [{
                "start": start,
                "end": end,
                "label": "Person"
            } for start, end, _ in chars_to_wrap]
        }]

    def generate_spacy_training_for_book(self, title):
        version = Version().load({"title": title, "versionTitle": self.vtitle, "language": self.language})
        if version is None: return
        version.walk_thru_contents(self.walker_action)

    def save_training_to_db(self, collection_name):
        collection = getattr(self.db, collection_name)
        collection.delete_many({})
        collection.insert_many(self.spacy_training_examples)

def guess_most_likely_transliteration():
    """
    Creates a CSV mapping spellings of rabbis in English to most common spellings in Hebrew
    """
    prefixes = "בכ|וב|וה|וכ|ול|ומ|וש|כב|ככ|כל|כמ|כש|לכ|מב|מה|מכ|מל|מש|שב|שה|שכ|של|שמ|ב|כ|ל|מ|ש|ה|ו|ד".split('|')
    en_ents = srsly.read_jsonl('./research/prodigy/output/evaluation_results/talmud_en.jsonl')
    he_segs_by_ref = {ent['ref']: ent for ent in srsly.read_jsonl('./research/prodigy/output/evaluation_results/talmud_he.jsonl')}
    en_to_he_spellings = defaultdict(lambda: defaultdict(int))
    en_to_refs = defaultdict(list)
    for en_seg in en_ents:
        for start, end, _ in en_seg['tp']:
            en_mention = en_seg['text'][start:end]
            en_to_refs[en_mention] += [en_seg['ref']]
            he_seg = he_segs_by_ref[en_seg['ref']]
            for he_start, he_end, _ in he_seg['tp']:
                he_mention = he_seg['text'][he_start:he_end]
                en_to_he_spellings[en_mention][he_mention] += 1
    out_rows = []
    max_he = 0

    # reptitious but I'm lazy. calculate total he count first
    total_he_count = defaultdict(int)
    for en_mention, he_mention_count in en_to_he_spellings.items():
        for he_mention, count in he_mention_count.items():
            total_he_count[he_mention] += count
            for prefix in prefixes:
                if he_mention.startswith(prefix):
                    total_he_count[he_mention[len(prefix):]] += count
    # then use it to normalize counts
    for en_mention, he_mention_count in en_to_he_spellings.items():
        sans_prefix_count = defaultdict(int)
        for he_mention, count in he_mention_count.items():
            sans_prefix_count[he_mention] += count
            for prefix in prefixes:
                if he_mention.startswith(prefix):
                    sans_prefix_count[he_mention[len(prefix):]] += count
        for he_mention, count in sans_prefix_count.items():
            sans_prefix_count[he_mention] = math.log(count) - math.log(total_he_count[he_mention])
        best_hebrew = sorted(sans_prefix_count.items(), key=lambda x: x[1], reverse=True)[:5]
        out_row = {
            "En": en_mention,
            "Example Refs": " | ".join(en_to_refs[en_mention][:10])
        }
        for i, (he, count) in enumerate(best_hebrew):
            out_row[f"He {i+1}"] = he
            if i > max_he:
                max_he = i
        out_rows += [out_row]
    with open('/home/nss/sefaria/datasets/ner/sefaria/yerushalmi_title_possibilities.csv', 'w') as fout:
        cout = csv.DictWriter(fout, ['En', 'Example Refs'] + [f'He {i+1}' for i in range(max_he+1)])
        cout.writeheader()
        cout.writerows(out_rows)

def make_en_named_entities_file():
    b_replacements = [' ben ', ' bar ', ', son of ', ', the son of ', ' son of ', ' the son of ', ' Ben ', ' Bar ']
    unique_en = set()
    with open('/home/nss/sefaria/datasets/ner/sefaria/yerushalmi_title_possibilities2.csv', 'r') as fin:
        cin = csv.DictReader(fin)
        for row in cin:
            en = TextNormalizer.normalize_text('en', row['En'])
            for brepl in b_replacements:
                en = en.replace(brepl, ' b. ')
            # remove contents of parens and actual square brackets
            en = re.sub(r'\([^)]+\)', ' ', en)
            en = re.sub(r'[\[\]]', '', en)
            en = " ".join(en.split()).strip()
            unique_en.add(en)
    out = [{
        "tag": "PERSON",
        "id": "N/A",
        "gen": None,
        "type": None,
        "idIsSlug": False,
        "manualTitles": [{
            "text": en,
            "lang": "en"
        }]
    } for en in unique_en]
    with open('/home/nss/sefaria/datasets/ner/sefaria/yerushalmi_basic_en_titles.json', 'w') as fout:
        json.dump(out, fout)

if __name__ == "__main__":
    # ttg = TalmudTrainingGenerator(DATA, 'William Davidson Edition - Aramaic', 'he', 'Bavli')
    # ttg.generate_spacy_training()
    # ttg.save_training_to_db('talmud_ner_he')
    # guess_most_likely_transliteration()
    make_en_named_entities_file()

"""
python -m spacy pretrain ./research/prodigy/configs/talmud_ner.cfg ./research/prodigy/output/pretrain_talmud_ner --code ./research/prodigy/functions.py --gpu-id 0

python -m spacy train ./research/prodigy/configs/talmud_ner.cfg --output ./research/prodigy/output/talmud_ner --code ./research/prodigy/functions.py --gpu-id 0
"""