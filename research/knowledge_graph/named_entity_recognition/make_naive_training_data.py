import django, re, csv, json, srsly
from tqdm import tqdm
import spacy
from unidecode import unidecode
from functools import partial, reduce
from collections import defaultdict
from bisect import bisect_right
django.setup()
from sefaria.model import *
from linking_utilities.dibur_hamatchil_matcher import match_text

DATA_LOC = "/home/nss/sefaria/datasets/ner/michael-sperling"

def myunidecode(text):
    # 'ăǎġḥḤḫḳḲŏṭżūŻāīēḗîìi̧'
    table = {
        "ḥ": "h",
        "Ḥ": "H",
        "ă": "a",
        "ǎ": "a",
        "ġ": "g",
        "ḫ": "h",
        "ḳ": "k",
        "Ḳ": "K",
        "ŏ": "o",
        "ṭ": "t",
        "ż": "z",
        "Ż": "Z" ,
        "’": "'",
        '\u05f3': "'",
        "\u05f4": '"',
        "”": '"',
    }
    for k, v in table.items():
        text = text.replace(k, v)
    return text

NORMALIZING_REG = r"\s*<[^>]+>\s*"
NORMALIZING_REP = " "

def normalize_text(lang, s):
    # text = re.sub('<[^>]+>', ' ', text)
    if lang == 'en':
        s = myunidecode(s)
        s = re.sub(NORMALIZING_REG, NORMALIZING_REP, s)
        # text = unidecode(text)
        # text = re.sub('\([^)]+\)', ' ', text)
        # text = re.sub('\[[^\]]+\]', ' ', text)
    # text = ' '.join(text.split())
    return s

def find_text_to_remove(s):
    return [(m, NORMALIZING_REP) for m in re.finditer(NORMALIZING_REG, s)]
        
class NaiveNERTagger(object):

    word_breakers = {' ', '.', ',', '"', '?', '!', '(', ')', '[', ']', '{', '}', ':', ';', '§', '<', '>'}

    def __init__(self):
        self.search_terms = self.generate_search_terms()
        self.unique_uncaught_rabbis = defaultdict(int)
        self.sefaria_to_bonayich = self.init_sefaria_bonayich_map()

    def init_sefaria_bonayich_map(self):
        with open("research/knowledge_graph/named_entity_recognition/sefaria_bonayich_reconciliation - Sheet2.csv", "r") as fin:
            rows = list(csv.DictReader(fin))
        return {
            r["Slug"]: int(r["bonayich"]) if r["bonayich"] != "null" else None for r in rows
        }

    def tag_segment(self, text):
        entities = []
        tagged_indexes = set()
        for term, matches in self.search_terms:
            term_start_ind = 0
            term_end_ind = 0
            while term_start_ind > -1:
                term_start_ind = text.find(term, term_end_ind)
                if term_start_ind == -1:
                    continue
                if not (term_start_ind == 0 or text[term_start_ind - 1] in self.word_breakers):
                    term_end_ind = term_start_ind + 1
                    continue  # must be beginning of word
                term_end_ind = term_start_ind + len(term)
                if not (term_end_ind == len(text) or text[term_end_ind] in self.word_breakers or text[
                                                                                            term_end_ind:term_end_ind + 2] == "'s"):
                    continue  # also must be end of word
                temp_tagged_indexes = set(range(term_start_ind, term_end_ind))
                if len(temp_tagged_indexes & tagged_indexes) > 0:
                    # cant double tag
                    continue
                # successful tag!
                if text[term_end_ind:term_end_ind + 5] == ' bar ' and matches[0][1] == "PERSON":
                    continue
                    # print('Son of a...', matches[0][0], term, text[term_end_ind:term_end_ind + 15])
                tagged_indexes |= temp_tagged_indexes
                entities += [[term_start_ind, term_end_ind, matches[0][1], matches[0][0], self.sefaria_to_bonayich.get(matches[0][0], None)]]  # only use most popular term
        return entities

    @staticmethod
    def generate_search_terms():
        def rabbi_extra_keys(title):
            return ([re.sub(' b\. ', replac, title) for replac in b_replacements]) if ' b. ' in title else []  #  + [title[:title.find(' b. ')]]

        def halachic_role_extra_keys(title):
            return [title.lower()]

        b_replacements = [' ben ', ' bar ', ', son of ', ', the son of ']
        starting_replacements = ['Ben', 'Bar', 'The']
        # search_types = [
        #     ('people', 'PERSON', rabbi_extra_keys),
        #     ("geography", 'GPE', None),
        #     ('history', 'EVENT', lambda x: [x.lower()]),
        #     ('halachic-role-of-inanimate-object', 'PRODUCT', halachic_role_extra_keys),
        #     ('halachic-role-of-person', 'PERSON', halachic_role_extra_keys),
        #     ("halachic-quality", 'PRODUCT', halachic_role_extra_keys),
        #     ('halachic-process', 'EVENT', halachic_role_extra_keys),
        #     ('angels', 'PERSON', None),
        #     ('holidays', 'DATE', None),
        #     ('months', 'DATE', None),
        #     ('texts', 'WORK_OF_ART', None),
        #     ('group-of-people', 'NORP', None),
        #     # topics to add
        #     (['god', 'talmid-chacham'], 'PERSON', None),
        #     (['gan-eden'], 'LOC', None),
        #     (['tumah'], 'PRODUCT', halachic_role_extra_keys),
        #     (['shemitah', 'jubilee', 'eve-of-shabbat', "the-conclusion-of-shabbat", "the-ten-days-of-repentance", "yom-tov", 'passover', 'shabbat'], 'DATE', halachic_role_extra_keys),
        #     (["exile-of-the-jewish-people", "the-messianic-era", "egyptian-exile", "greek-exile", "babylonian-exile", "building-of-the-second-temple", "period-of-the-judges", "second-temple", "the-first-temple"], 'EVENT', halachic_role_extra_keys),
        #     (["aron-habrit", 'mishkan','ohel-moed','beit-hamikdash', 'beer-lachai-roi', 'beit-midrash', 'the-lebanon-forest-house', 'synagogues', 'houses-of-a-walled-city', 'cemeteries', 'altars', 'chuppah', 'courtyards', 'cities-of-refuge', 'ramp-of-the-altar', 'altar', 'mikvah', 'tabernacle-courtyard', 'the-tabernacle-in-shiloh', 'the-gate-of-nikanor', 'sukkah', 'the-courtyard', 'walled-cities', 'town-squares', 'arks'], 'FAC', halachic_role_extra_keys),
        #     # strings to add
        #     ({
        #          'Bar Hamdakh',
        #          'Sekhavta',
        #         'Mata Mehasya',
        #      }, 'GPE', None),
        #     ({
        #         'Burnitz River',
        #         'Bedita River',
        #         'Shanvata',
        #     }, 'LOC', None),
        #     ({'Baraita', 'Seder Olam', 'Psalms'}, 'WORK_OF_ART', halachic_role_extra_keys),
        #     ({'Torah law', 'rabbinic law'}, 'LAW', None),
        #     ({'Aramaic', 'Greek'}, 'LANGUAGE', None),
        #     ({'Ammonite', 'Moabite', 'Babylonian', 'Samaritan', 'Beit Hillel', 'Beit Shammai'}, 'NORP', None),
        # ]
        topics_to_skip = {'on-the-son-of-pelet', 'will', 'groups', 'entourages', 'peoplehood', 'nations', 'groupings',
                          'generations', 'earlier-generations', 'groups-(אשישי)', 'the-early-pious-people', 'magicians',
                          'craftsmen-and-guards', 'mules', 'land', "earth-(ארקא)", 'earth', 'fifth', 'killing',
                          'hanging', "human-rights", 'mixtures', 'get'}
        with open(f"{DATA_LOC}/sperling_en_and_he.csv", "r") as fin:
            sperling_rabbis = {}
            sperling_norps = {}
            c = csv.DictReader(fin)
            for row in c:
                en1 = row["En 1"].strip()
                if len(en1) == 0 or en1 == "N/A" or en1 == "MM":
                    continue
                bid = row['Bonayich ID']
                titles = []
                for i in range(3):
                    temp_en = row[f'En {i+1}']
                    if len(temp_en) == 0:
                        continue
                    titles += [temp_en]
                if len(row["Is Group"]) > 0:
                    sperling_norps[bid] = titles
                else:
                    sperling_rabbis[bid] = titles
        search_types = [
            ('talmudic-people', 'PERSON', rabbi_extra_keys),
            ('mishnaic-people', 'PERSON', rabbi_extra_keys),
       ({
                'Rav Samma b. Rav Asi',
                'Rabbi Yitzhak b. Rav Ya\'akov b.Rav Tahlifa b. Avudimi Giyyorei',
                'Rav Hiyya b. Avin',
                'Rabbi Hiyya b. Avin',
                'Rabbi Hanin',
                'Rav Natan b. Ami',
                'Yehuda b. Mareimar',
                'Rav Yeimar the Elder',
                'Rav Yeimar',
                'Rav Hiyya b. Ami',
                'Rav Hoshaya',
                'Rav Shemaya',
                'Rav Huna b. Yehuda',
                'Rabba b. Livai',
                'Ben Azzai',
                'Rav Hinnana b. Rav Ika',
                'Rav Hinnana',
                'Rav Hanina',
                'Rav Yirmeya',
                'Rabbi Zeira b. Hanina',
                'Rabbi Ila',
                'Rabbi Ela',
                'Mar Shmuel',
                'Rav Shemen b. Abba',
                'Rabbi Ami',
                'Rav Yitzhak b. Ya\'akov b. Giyorei',
                'Bar Hedya',
                'Rav Nehemya b. Rav Yehoshua',
                'Rav Nehemya',
                'Rav Yehoshua',
                'Rav Haviva',
                'Rabbi Levi b. Hayyata',
                'Abba b. Hayyata',
                'Rabbi Tanhum b. Hiyya',
                'Rabbi Elyashiv',
                'Rabbi Yitzhak b. Ami',
                'Rav Hanan b. Hisda',
                'Rav Giddel b. Menashya',
                'Ravin b. Adda',
                'Rabbi Yosei b. Avin',
                'Ravina b. Sheila',
                'Rav Aha b. Pinehas',
                'Rabbi Yosei b. Hanina',
                'Rabbi Yosei b. Yehuda',
                'Rabbi Yitzhak b. Avdimi',
                'Rav Yitzhak b. Ami',
                'Rav Yitzhak b. Abba',
                'Daniel b. Ketina',
                'Rav b. Shaba',
                'Rav Yeimar b. Shelamya',
                'Rava b. Yishmael',
                'Rav Yehuda b. Ami',
                'Rav Yehoshua b. Abba',
                'Rabbi Abba b. Memel',
                'Rabba b. Yirmeya',
                'Rabba b. Shmuel',
                'Rabba b. Ashabi',
                'Rabba b. Mari',
                'Rabbi Abba b. Hiyya',
                'Rav Yirmeya b. Ami',
                'Rav Hagga',
                'bar Kippok',
                'Rav Tahlifa b. Avimi',
                'Rav Tahlifa b. Shaul',
                'Rav Tahlifa',
                'Yosef the Priest',
                'Adda Mari',
                'Eliphaz the Temanite',
                'Rabbi Ile\'a',
                'Rabbi Parnakh',
                'Hizkiyya',
                'Rav Yehiel',
                'Rav Shapir',
                'Adda the fisherman',
                'Maryon b. Ravin',
                'Mar b. Rav Aha b. Rava',
                'Mar b. Rav Aha',
                'Rabbi Elazar b. Hisma',
                'Ravin b. Rav Adda',
                'Rava b. Rabba',
                'Rav Hama b. Ukva',
                'Rabba b. Rav Nahman',
                'Rabba b. Rava',
                'Rav Hananya',
                'Rabbi Abba b. Kahana',
                'Rabbi Natan b. Oshaya',
                'Rava b. Ittai',
                'Rav Hinnana b. Sheilat',
                'Rav Yosef b. Minyumi'
                'Rav Huna b. Tahlifa',
                'Rabbi Ya\'akov bar Abba',
                'Mar bar Isak',  # probs should have been written Mari bar Isak
                'Rav Shmuel bar Aha',
                'Rabba bar Memel',
                'Rabbi Yitzhak b. Abba',
                'Mar Zutra b. Toviyya',
                'Rav Hinnana b. Pappa',
                'Rav Aha b. Adda',
                'Rava b. Mari',
                'Ravin b. Rav Nahman',
                'Rabba b. Ulla',
                'Rav Haviva b. Surmakei',
                'Rabba b. Rav Sheila',
                'Rav Sheila',
                'Rabba b. b. Hanan',
                'Rav Hanan b. Ami',
                'Rav Nahman b. Pappa',
                'Rabbi Shmuel b. Hiyya',
                'Rav Huna b. Manoah',
                'Rav b. Shabba',
                'Rav Natan b. Abba',
                'Rabbi Abba b. Zavda',
                'Efrayim the scribe',
                'Rabbi Idi',
                'Rav Idi',
                'Rav Shemaya b. Ze\'eira',
                'Rabbi Yirmeya b. Abba',
                'Rav Hilkiya b. Tovi',
                'Rav Hiyya b. Abba',
                'Rabbi Yehuda b. Lakish',
                'Rabbi Tanhum b. Hanilai',
                'Rabbi Menahem b. Yosei',
                'Rav Ika',
                'Rav Zutra',
                'Rav Hillel',
                'Rav Natan b. Oshaya',
                'Rav Zutra b. Toviya',
                'Rabbi Yitzhak b. Yosef',
                'Rav Yitzhak b. Avdimi',
                'Rabbi Meyasha',
                'Rav Menashya',
                'Rav Menashya b. Gadda',
                "Rav Ya'akov",
                "Rav Ami",
                "Rav Shmuel b. Rav",
                'Rabbi Simai',
                'Rav Hiyya from Yostiniyya',
                'Rabbi Shmuel b. Rav', #NA
                'Rav Nahman b. Rav', # NA
                'Rav Shimi', # NA
                'Rabbi Elazar b. Perata', # NA
                'Rabbi Dostai', # NA
                'Rabbi Elazar b. Rabbi', # NA
                'Rabbi Yosei b. Rabbi', # NA
                'Rabbi Yehuda b. Teima', # NA
             }, 'PERSON', rabbi_extra_keys),
             (sperling_rabbis, 'PERSON', rabbi_extra_keys),
             (sperling_norps, 'NORP', rabbi_extra_keys),
             (['beit-hillel', 'beit-shammai'], 'NORP', None),
            
        ]
        search_terms = defaultdict(list)
        for slug, tag, extra_keys in tqdm(search_types, desc='init'):
            if isinstance(slug, list):
                topics = []
                for temp_slug in slug:
                    temp_topic = Topic.init(temp_slug)
                    if temp_topic is None:
                        print("Topic is None:", temp_slug)
                        continue
                    topics += [temp_topic]
            elif isinstance(slug, set):
                topics = [Topic({'slug': 'N/A', 'titles': [{'text': title, 'lang': 'en'}]}) for title in slug]
            elif isinstance(slug, dict):
                topics = [Topic({'slug': f'ID:{bid}', 'titles': [{'text': title, 'lang': 'en'} for title in titles]}) for bid, titles in slug.items()]
            else:
                topics = Topic.init(slug).topics_by_link_type_recursively(only_leaves=True)
            for topic in topics:
                if topic.slug in topics_to_skip:
                    continue
                value = (topic.slug, tag, getattr(topic, 'numSources', 0), True)
                inexact_value = list(value)
                inexact_value[-1] = False
                inexact_value = tuple(inexact_value)
                for title in topic.titles:
                    if title['lang'] == 'en':
                        search_terms[title['text']] += [value]
                        if extra_keys is not None:
                            for extra in extra_keys(title['text']):
                                # print('Extra', extra, title['text'])
                                search_terms[extra] += [inexact_value]
                        for starting_replacement in starting_replacements:
                            if title['text'].startswith(f'{starting_replacement} '):
                                uncapitalized = title['text'][0].lower() + title['text'][1:]
                                search_terms[uncapitalized] += [value]                   
                    
        search_terms = sorted(list(search_terms.items()), key=lambda x: len(x[0]), reverse=True)
        for term, matches in search_terms:
            matches.sort(key=lambda x: int(x[3])*1e7+x[2], reverse=True)
        return search_terms

    def check_for_missing_entities(self, string, entities):
        tagged_index_set = {i for start, end, tag in entities for i in range(start, end)}
        rabbi_re = r'^[A-Z][a-z\']+(?: (?:bar|ben|, son of) [A-Z][a-z\']+)?(?=\W|$)'
        for match in re.finditer('(?:Rabbi|Rav) ', string):
            temp_match = re.search(rabbi_re, string[match.end():])
            if not temp_match:
                continue
            has_untagged = any([i not in tagged_index_set for i in range(temp_match.start(), temp_match.end()-1)])
            if match.start() in tagged_index_set and (match.end()) < len(string) and has_untagged:
                uncaught_rabbi = string[match.start():match.end() + temp_match.end()]
                uncaught_rabbi = re.sub("'s$", '', uncaught_rabbi)
                self.unique_uncaught_rabbis[uncaught_rabbi] += 1

    def tag_index(self, index):
        from parsing_utilities.util import get_mapping_after_normalization, convert_normalized_indices_to_unnormalized_indices
        training = []
        mentions = []
        for seg in tqdm(index.all_segment_refs(), desc='Segs'):
            unnorm_text = seg.text('en').text
            norm_text = normalize_text('en', unnorm_text)

            entities = self.tag_segment(norm_text)
            ent_indices = [(ent[0], ent[1]) for ent in entities]
            norm_map = get_mapping_after_normalization(unnorm_text, find_text_to_remove)
            ent_indices = convert_normalized_indices_to_unnormalized_indices(ent_indices, norm_map)
            for ent, unnorm_index in zip(entities, ent_indices):
                ent[0] = unnorm_index[0]
                ent[1] = unnorm_index[1]
            spacy_entities = [e[:3] for e in entities]
            self.check_for_missing_entities(unnorm_text, spacy_entities)
            for ent in entities:
                mentions += [{
                    "Book": index.title,
                    "Ref": seg.normal(),
                    "Bonayich ID": ent[4],
                    "Slug": ent[3],
                    "Start": ent[0],
                    "End": ent[1],
                    "Mention": unnorm_text[ent[0]:ent[1]]
                }]
            training += [[unnorm_text, {"entities": spacy_entities}]]
        return training, mentions

    def tag_all(self, start=0, end=None, category='Bavli'):
        talmud = library.get_indexes_in_category(category, full_records=True)
        training = []
        mentions = []
        for mes in tqdm(talmud[start:end], desc='Books'):
            temp_training, temp_mentions = self.tag_index(mes)
            training += temp_training
            mentions += temp_mentions
        srsly.write_jsonl('/home/nss/sefaria/datasets/ner/michael-sperling/en_training.jsonl', training)
        srsly.write_jsonl('/home/nss/sefaria/datasets/ner/michael-sperling/en_mentions.jsonl', mentions)



def convert_training_to_displacy(jsonl_loc):
    out = []
    for text, tags in srsly.read_jsonl(jsonl_loc):
        out += [{
            'text': text,
            'ents': sorted([{'start': s, 'end': e, 'label': l} for s, e, l in tags['entities']], key=lambda x: x['start'])
        }]
    srsly.write_jsonl(jsonl_loc + '.displacy', out)


def display_displacy(jsonl_loc):
    jsonl_data = list(filter(lambda x: len(x['text']) > 0, srsly.read_jsonl(jsonl_loc)))
    spacy.displacy.serve(jsonl_data, style='ent', manual=True)


if __name__ == '__main__':
    tagger = NaiveNERTagger()
    tagger.tag_all(category='Bavli', start=18, end=19)
    # with open('best_rabbis.csv', 'w') as fout:
    #     c = csv.DictWriter(fout, ['Rabbi', 'Count'])
    #     c.writeheader()
    #     rows = [{'Rabbi': r, 'Count': i} for r, i in tagger.unique_uncaught_rabbis.items()]
    #     c.writerows(rows)
    convert_training_to_displacy('/home/nss/sefaria/datasets/ner/michael-sperling/en_training.jsonl')
    display_displacy('/home/nss/sefaria/datasets/ner/michael-sperling/en_training.jsonl.displacy')
    # with open('AllNameReferences.xlsx - Sheet1.csv', 'r') as fin:
    #     c = csv.DictReader(fin)
    #     rows = [Row(r) for r in c]
    # tonorabanan = TonORabanan(rows)
    # book_dict = defaultdict(list)
    # for r in rows:
    #     book_dict[r.masechet] += [r]
    #
    # books = [Book(k, v) for k, v in list(book_dict.items())[:1]]
    # books[0].amuds[0].find_names()
    # for r in books[0].amuds[0].rows:
    #     print(r.seg_ref, r.name)

"""
TODO: add amora'im, amora, tanna etc.
TODO: watch out for 'earth'
TODO: REMOVE GET, intentional, pulling, interest, damage
TODO: how do we catch halitza?
TODO: add Yavne, intermediate days of a Festival, Hol HaMoed, Tabernacle, Evel Rabbati, Amida prayer, Shema
TODO: deal with things that are not leaf nodes (e.g. passover, shabbat)
"""
