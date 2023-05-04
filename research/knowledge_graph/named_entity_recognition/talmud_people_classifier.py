from collections import defaultdict
from functools import partial
from tqdm import tqdm
import csv, json, django, random, math, re
from pymongo import MongoClient
import srsly
django.setup()
from sefaria.model import *
from sefaria.helper.normalization import NormalizerByLang, NormalizerComposer
from research.prodigy.functions import wrap_chars_with_overlaps

DATA = "/home/nss/sefaria/datasets/ner/sefaria/ner_output_talmud.json"
NORMALIZER = NormalizerByLang({
    "en": NormalizerComposer(["br-tag", "itag", "unidecode", "html", "parens-plus-contents", "brackets", "double-space"]),
    "he": NormalizerComposer(['unidecode', 'cantillation', 'maqaf']),
})

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
        return NORMALIZER.normalize(random_title, lang=self.language)

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
        snorm = NORMALIZER.normalize(s, lang=self.language)
        norm_map = NORMALIZER.get_mapping_after_normalization(s, lang=self.language, reverse=True)
        mention_indices = NORMALIZER.convert_normalized_indices_to_unnormalized_indices(mention_indices, norm_map, reverse=True)
        chars_to_wrap = []
        for example, (start, end) in zip(examples, mention_indices):
            # just to make sure...
            assert NORMALIZER.normalize(example['mention'], lang=self.language) == snorm[start:end]
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
    b_replacements = sorted([' ben ', ' bar ', ', son of ', ', the son of ', ' son of ', ' the son of ', ' Ben ', ' Bar '], key=lambda x: len(x), reverse=True)
    unique_en = set()
    with open('/home/nss/sefaria/datasets/ner/sefaria/temp/Yerushalmi People Title Matching - yerushalmi_title_possibilities.csv', 'r') as fin:
        cin = csv.DictReader(fin)
        for row in cin:
            en = NORMALIZER.normalize(row['En'], lang='en')
            for brepl in b_replacements:
                en = en.replace(brepl, ' b. ')
            # remove contents of parens and actual square brackets
            en = re.sub(r'\([^)]+\)', ' ', en)
            en = re.sub(r'[\[\]]', '', en)
            en = " ".join(en.split()).strip()
            unique_en.add(en)
    out = [{
        "tag": "PERSON",
        "id": en,
        "gen": None,
        "type": None,
        "idIsSlug": False,
        "manualTitles": [{
            "text": en,
            "lang": "en"
        }]
    } for en in unique_en]
    with open('/home/nss/sefaria/datasets/ner/sefaria/temp/yerushalmi_basic_en_titles.json', 'w') as fout:
        json.dump(out, fout, ensure_ascii=False, indent=2)

class FindMissingNames:
    word_breakers = r"|".join(re.escape(breaker) for breaker in ['.', ',', "'", '?', '!', '(', ')', '[', ']', '{', '}', ':', ';', '§', '<', '>', "'s", "׃", "׀", "־", "…"])
    noncapitals_to_remove = {'and'}
    b_replacements = [' ben ', ' bar ', ', son of ', ', the son of ', ' son of ', ' the son of ', ' Ben ', ' Bar ']

    def __init__(self, book_title):
        self.possible_title_continuations = []
        self.normalizer = NormalizerComposer(["br-tag", "itag", "unidecode", "html", "parens-plus-contents", "brackets"])
        self.mentions_by_ref = defaultdict(list)
        with open('/home/nss/sefaria/datasets/ner/sefaria/ner_output_yerushalmi.json', 'r') as fin:
            raw_mentions = json.load(fin)
            for m in raw_mentions:
                self.mentions_by_ref[m['ref']] += [m]
            print(f"{len(raw_mentions)} MENTIONS")
            titles = {self.normalizer.normalize(m['mention']) for m in raw_mentions}
        noncapital_dict = defaultdict(list)
        for title in titles:
            non_capital_matches = re.finditer(r'(?:^|\s)([a-z\s]+)(?=$|[A-Z])', title)
            for match in non_capital_matches:
                noncapital_dict[match.group(1).strip()] += [title]
        noncapitals = list(filter(lambda x: x.strip() not in self.noncapitals_to_remove, noncapital_dict.keys()))
        self.noncapital_reg = fr'(?:^|\s|{self.word_breakers})(?:{"|".join(re.escape(x.strip()) for x in self.b_replacements)})(?=$|\s|{self.word_breakers})'
        self.find_missing_name_continuations_book(book_title)
        self.save_titles()

    def action(self, s, en_tref, he_tref, v):
        from parsing_utilities.util import get_window_around_match
        mentions = self.mentions_by_ref.get(en_tref, [])
        snorm = self.normalizer.normalize(s)
        rm = self.normalizer.get_mapping_after_normalization(s, reverse=True)
        norm_indices = self.normalizer.convert_normalized_indices_to_unnormalized_indices([(m['start'], m['end']) for m in mentions], rm, reverse=True)
        for (start, end), m in zip(norm_indices, mentions):
            assert snorm[start:end] == self.normalizer.normalize(m['mention'])
            before, after = get_window_around_match(start, end, snorm)
            start_match = re.search(self.noncapital_reg + r'$', before.strip())
            end_match = re.search(r'^' + self.noncapital_reg, after.strip())
            before_words = before.split()
            after_words = after.split()
            before_cap = before_words[-1] if re.search(r'^[A-Z]', before_words[-1] if len(before_words) > 0 else '') else None
            if before_cap is not None and re.search(fr'(?:{self.word_breakers})$', before_cap) or before_cap in {'Also', 'Where', 'Were', 'Mishnah', 'Before', 'Do', 'Is', 'Even', 'Since', 'But', 'And', 'Once', 'When', 'Does', 'For', 'If', 'Said', 'As', 'Either', 'Maybe', 'Both', 'Following', 'What', 'In', 'There', 'Which', 'So', 'An', 'Now', 'Then', 'Of', 'He'}:
                before_cap = None
            after_cap = after_words[0] if re.search(r'^[A-Z]', after_words[0] if len(after_words) > 0 else '') else None
            if not (start_match or end_match or before_cap or after_cap): continue
            start_text = start_match.group() if start_match is not None else ''
            end_text = end_match.group() if end_match is not None else ''
            self.possible_title_continuations += [{
                'mention': m["mention"],
                'ref': m['ref'],
                'before': before,
                'after': after,
                'start_match': start_text,
                "end_match": end_text,
            }]

    def find_missing_name_continuations_book(self, title):
        version = Version().load({"title": title, "versionTitle": "Guggenheimer Translation 2.1", "language": "en"})
        version.walk_thru_contents(self.action)

    def save_titles(self):
        with open('/home/nss/sefaria/datasets/ner/sefaria/temp/yerushalmi_title_possibilities_derived.csv', 'w') as fout:
            cout = csv.DictWriter(fout, ['ref', 'before', 'mention', 'after', 'start_match', 'end_match'])
            cout.writeheader()
            cout.writerows(self.possible_title_continuations)

def suggest_people_duplicates():
    from linking_utilities.weighted_levenshtein import WeightedLevenshtein
    norm2peeps = defaultdict(list)
    letter_counts = defaultdict(int)
    with open('/home/nss/sefaria/datasets/ner/sefaria/temp/yerushalmi_basic_en_titles.json', 'r') as fin:
        jin = json.load(fin)
        for person_obj in jin:
            title = person_obj['manualTitles'][0]['text']
            norm_title = title.replace('Rebbi', '').replace('Rav', '').replace('‘', "'").replace('ˋ', "'").replace('`', "'").replace('ї', 'i').replace('ï', 'i').replace('î', 'i').replace('ĩ', 'i').replace('ś', 's').replace('š', 's').replace('Š', 'S').replace('ü', 'u').lower().replace('ẓ', 'z').replace('\u0301', '').replace('\u0308', '')
            norm_title = ' '.join(norm_title.split())
            for char in norm_title:
                letter_counts[char] += 1
            norm2peeps[norm_title] += [title]
    max_letter_count = max(letter_counts.values())
    min_letter_count = min(letter_counts.values())
    letter_freqs = {char: (count-min_letter_count)/(max_letter_count-min_letter_count) for char, count in letter_counts.items()}
    leven = WeightedLevenshtein(letter_freqs)
    clusters = []
    for i, (norm_title, titles) in tqdm(enumerate(norm2peeps.items()), total=len(norm2peeps)):
        found_match = False
        for j, (norm_title2, titles2) in enumerate(list(norm2peeps.items())[i+1:]):
            score = leven.calculate(norm_title, norm_title2)
            if score > 85:
                print('MATCHED\n', norm_title, '\n', norm_title2, '\n', score)
                found_match = True
                norm2peeps[norm_title2] += titles  # merge clusters
                break
        if not found_match:
            clusters += [titles]
    with open('/home/nss/sefaria/datasets/ner/sefaria/temp/yerushalmi_people_duplicates.json', 'w') as fout:
        json.dump(clusters, fout, indent=2, ensure_ascii=False)

def make_csv_for_deduping():
    with open('/home/nss/sefaria/datasets/ner/sefaria/temp/yerushalmi_people_duplicates.json', 'r') as fin:
        clusters = json.load(fin)
    with open('/home/nss/sefaria/datasets/ner/sefaria/ner_output_yerushalmi.json', 'r') as fin:
        mentions = json.load(fin)
    mentions_by_title = defaultdict(list)
    for m in mentions:
        for _id in m['id_matches']:
            mentions_by_title[_id] += [m]
    rows = []
    clusters.sort(key=lambda x: min(*x, key=lambda y: len(y)))
    for cluster in clusters:
        for title in cluster:
            temp_mentions = mentions_by_title[title]
            row = {
                "En Title": title,
                "He Title": "",
                "Slug or Bonayich ID": "",
            }
            for i, m in enumerate(temp_mentions[:5]):
                row[f'Ref {i+1}'] = m['ref']
            rows += [row]
        rows += [{}]
    with open('/home/nss/sefaria/datasets/ner/sefaria/temp/yerushalmi_people_dudupe.csv', 'w') as fout:
        cout = csv.DictWriter(fout, ['En Title', 'He Title', 'Slug or Bonayich ID'] + [f'Ref {i+1}' for i in range(5)])
        cout.writeheader()
        cout.writerows(rows)

def output_existing_people():
    from research.knowledge_graph.named_entity_recognition.ner_tagger import CorpusManager
    raw_named_entities = [
        {
            "id": "talmudic-people",
            "idIsSlug": True,
            "getLeaves": True
        },
        {
            "id": "mishnaic-people",
            "idIsSlug": True,
            "getLeaves": True
        },
        {
            "id": "group-of-talmudic-people",
            "idIsSlug": True,
            "getLeaves": True
        },
        {
            "id": "group-of-mishnaic-people",
            "idIsSlug": True,
            "getLeaves": True
        },
        {
            "id": "biblical-figures",
            "idIsSlug": True,
            "getLeaves": True
        },
        {
            "id": "jewish-people",
            "idIsSlug": True
        },
        {
            "id": "israel",
            "idIsSlug": True
        },
        {
            "id": "jesus",
            "idIsSlug": True
        },
        {
            "namedEntityFile": "sperling_named_entities.json"
        }
    ]
    named_entities = CorpusManager.create_named_entities(raw_named_entities)
    rows = []
    for ne in named_entities:
        assert isinstance(ne, Topic)
        other_titles = [title_obj['text'] for title_obj in ne.titles if not title_obj.get('primary', False)]
        rows += [{
            "Slug": ne.slug,
            "En": ne.get_primary_title('en'),
            "He": ne.get_primary_title('he'),
            "Description": getattr(ne, 'description', {}).get('en', ''),
            "Other Titles": " | ".join(other_titles)
        }]
    with open('/home/nss/sefaria/datasets/ner/sefaria/temp/existing_topics.csv', 'w') as fout:
        cout = csv.DictWriter(fout, ['Slug', 'En', 'He', 'Description', 'Other Titles'])
        cout.writeheader()
        cout.writerows(rows)

if __name__ == "__main__":
    # ttg = TalmudTrainingGenerator(DATA, 'William Davidson Edition - Aramaic', 'he', 'Bavli')
    # ttg.generate_spacy_training()
    # ttg.save_training_to_db('talmud_ner_he')
    # guess_most_likely_transliteration()
    # make_en_named_entities_file()
    # FindMissingNames('JTmock Niddah')
    # suggest_people_duplicates()
    # make_csv_for_deduping()
    output_existing_people()
"""
python -m spacy pretrain ./research/prodigy/configs/talmud_ner.cfg ./research/prodigy/output/pretrain_talmud_ner --code ./research/prodigy/functions.py --gpu-id 0

python -m spacy train ./research/prodigy/configs/talmud_ner.cfg --output ./research/prodigy/output/talmud_ner --code ./research/prodigy/functions.py --gpu-id 0
"""