import django, re, csv, json, srsly
from tqdm import tqdm
import spacy
from unidecode import unidecode
from functools import partial, reduce
from collections import defaultdict
from bisect import bisect_right
django.setup()
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import match_text


class Row(object):

    def __init__(self, d):
        self.masechet = None
        self.begin_offset = None
        self.end_offset = None
        self.amud = None
        self.snippet = None
        self.seg_ref = None
        self.rid = None
        for k, v in d.items():
            if k == ' Amud':
                v = v.lower()
            if k == ' Masechet':
                v = Ref(v).normal()
            if k == ' Rabbi ID after Link':
                k = 'rid'
                v = int(v)
            setattr(self, k.strip().lower().replace(' ', '_'), v)

    def index_of(self, search_text: str) -> int:
        """
        Return index of start of `self.snippet`
        :param str search_text: search text
        :return: index of start of `self.snippet`. None if doesn't exist
        """
        try:
            return search_text.index(self.text)
        except ValueError:
            return None

    def get_text(self):
        return self.snippet.replace('~', '')

    def get_ref(self):
        return Ref("{} {}".format(self.masechet, self.amud))

    def get_name_pos(self):
        start = self.snippet.index('~')
        end = self.snippet.index('~', start+1) - 1
        return start, end

    def get_name_word_pos(self):
        start, end = None, None
        for i, w in enumerate(self.snippet.split()):
            if w.startswith('~') and start is None:
                start = i
            elif w.endswith('~') and end is None:
                end = i+1
        return start, end

    def get_name(self):
        start, end = self.name_pos
        return self.text[start:end]

    ref = property(get_ref)
    text = property(get_text)
    name_pos = property(get_name_pos)
    name_word_pos = property(get_name_word_pos)
    name = property(get_name)


class Amud(object):

    def __init__(self, book_name, amud_name, rows):
        self.ref = Ref("{} {}".format(book_name, amud_name))
        self.he = self.init_text('he')
        self.en = self.init_text('en')
        self.rows = rows

    def init_text(self, lang):
        vtitle = None if lang == 'en' else 'William Davidson Edition - Aramaic'
        return self.normalize_text(lang, self.ref.text(lang, vtitle=vtitle).as_string())

    def find_names(self):
        ind_list, ref_list, total_len, text_list = self.ref.text('he', 'William Davidson Edition - Aramaic').text_index_map(lambda x: self.normalize_text('he', x).split(), ret_ja=True)
        matches = match_text(self.he.split(), [r.text for r in self.rows], with_num_abbrevs=False)
        for (m_start, m_end), m_text, row in zip(matches['matches'], matches['match_text'], self.rows):
            if m_start == -1:
                continue
            try:
                letter_ind = m_text[0].index(row.name)  # assumes name only appears once in row...
            except ValueError:
                print(row.name, 'not found in', m_text[0])
                continue
            word_lens = reduce(lambda a, b: a + [a[-1] + len(b) + 1], m_text[0].split(' '), [0])
            word_ind = bisect_right(word_lens, letter_ind) - 1
            full_word_ind = word_ind + m_start
            ref_ind = bisect_right(ind_list, full_word_ind) - 1
            ref = ref_list[ref_ind]
            setattr(row, 'seg_ref', ref)

    @staticmethod
    def normalize_text(lang, text):
        text = re.sub('<[^>]+>', ' ', text)
        if lang == 'en':
            text = unidecode(text)
            text = re.sub('\([^)]+\)', ' ', text)
            text = re.sub('\[[^\]]+\]', ' ', text)
        text = ' '.join(text.split())
        return text


class Book(object):

    def __init__(self, name, rows):
        self.name = name
        rows.sort(key=lambda x: int(x.begin_offset))
        amud_dict = defaultdict(list)
        for r in rows:
            amud_dict[r.amud] += [r]
        self.amuds = [Amud(self.name, k, v) for k, v in amud_dict.items()]


class Rav(object):

    def __init__(self):
        pass


class TonORabanan(object):

    def __init__(self, rows):
        self.bon_sef_map = {}
        rabbi_topics = {t.fromTopic for t in IntraTopicLinkSet({'linkType': 'is-a', '$or': [{'toTopic': 'mishnaic-people'}, {'toTopic': 'talmudic-people'}]})}
        with open('sefaria_bonayich_reconciliation - Sheet1.csv', 'r') as fin:
            c = csv.DictReader(fin)
            for cc in tqdm(list(c)):
                if cc['bonayich'] == 'null':
                    continue
                query = {'slug': cc['sefaria_key'][1:]} if cc['sefaria_key'].startswith('#') else {"titles.text": cc['sefaria_key']}
                topic_set = [t for t in TopicSet(query) if t.slug in rabbi_topics]
                if len(topic_set) > 1 or len(topic_set) == 0:
                    # print('Len', len(topic_set), cc['sefaria_key'])
                    continue
                self.bon_sef_map[int(cc['bonayich'])] = topic_set[0]
        count = 0
        for r in rows:
            if r.rid in self.bon_sef_map:
                count += 1
        print('Percent matched', count, len(rows), count/len(rows))

    def __getitem__(self, item):
        return self.bon_sef_map.get(item, None)


class NaiveNERTagger(object):

    word_breakers = {' ', '.', ',', '"', '?', '!', '(', ')', '[', ']', '{', '}', ':', ';', '§'}

    def __init__(self):
        self.search_terms = self.generate_search_terms()
        self.unique_uncaught_rabbis = defaultdict(int)

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
                    pass
                    print('Son of a...', matches[0][0], term, text[term_end_ind:term_end_ind + 15])
                tagged_indexes |= temp_tagged_indexes
                entities += [[term_start_ind, term_end_ind, matches[0][1]]]  # only use most popular term
        return entities

    @staticmethod
    def generate_search_terms():
        def rabbi_extra_keys(title):
            return ([re.sub(' b\. ', replac, title) for replac in b_replacements] + [
                title[:title.find(' b. ')]]) if ' b. ' in title else []

        def halachic_role_extra_keys(title):
            return [title.lower()]

        b_replacements = [' ben ', ' bar ', ', son of ', ', the son of ']
        search_types = [
            ('people', 'PERSON', rabbi_extra_keys),
            ("geography", 'GPE', None),
            ('history', 'EVENT', lambda x: [x.lower()]),
            ('halachic-role-of-inanimate-object', 'PRODUCT', halachic_role_extra_keys),
            ('halachic-role-of-person', 'PERSON', halachic_role_extra_keys),
            ("halachic-quality", 'PRODUCT', halachic_role_extra_keys),
            ('halachic-process', 'EVENT', halachic_role_extra_keys),
            ('angels', 'PERSON', None),
            ('holidays', 'DATE', None),
            ('months', 'DATE', None),
            ('texts', 'WORK_OF_ART', None),
            ('group-of-people', 'NORP', None),
            # topics to add
            (['god', 'talmid-chacham'], 'PERSON', None),
            (['gan-eden'], 'LOC', None),
            (['tumah'], 'PRODUCT', halachic_role_extra_keys),
            (['shemitah', 'jubilee', 'eve-of-shabbat', "the-conclusion-of-shabbat", "the-ten-days-of-repentance", "yom-tov", 'passover', 'shabbat'], 'DATE', halachic_role_extra_keys),
            (["exile-of-the-jewish-people", "the-messianic-era", "egyptian-exile", "greek-exile", "babylonian-exile", "building-of-the-second-temple", "period-of-the-judges", "second-temple", "the-first-temple"], 'EVENT', halachic_role_extra_keys),
            (["aron-habrit", 'mishkan','ohel-moed','beit-hamikdash', 'beer-lachai-roi', 'beit-midrash', 'the-lebanon-forest-house', 'synagogues', 'houses-of-a-walled-city', 'cemeteries', 'altars', 'chuppah', 'courtyards', 'cities-of-refuge', 'ramp-of-the-altar', 'altar', 'mikvah', 'tabernacle-courtyard', 'the-tabernacle-in-shiloh', 'the-gate-of-nikanor', 'sukkah', 'the-courtyard', 'walled-cities', 'town-squares', 'arks'], 'FAC', halachic_role_extra_keys),
            # strings to add
            ({
                'Rav Eina',
                'Rav Sama b. Rav Mari',
                'Rav Samma b. Rav Yirmeya',
                'Rav Samma b. Rav Asi',
                'Rav Zevid of Neharde\'a',
                'Rav Yosef Tzidoni',
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
                'Rav Ḥiyya from Yostiniyya',
                'Rav Pinehas',
                'Rabbi Aha b. Hanina',
                'Rav Yitzhak b. Shmuel',
                'Rabbi Shimon b. Yehotzadak',
                'Rav Aha b. Rav',
                'Rav Shimi b. Hiyya',
                'Rabbi Shmuel b. Rav',
                'Rav Sherevya',
                'Rabbi Mani',
                'Rav Nahman b. Rav',
                'Rabbi Hiyya b. Ashi',
                'Rav Shimi',
                'Rabbi Binyamin b. Yefet',
                'Rabbi Elazar b. Perata',
                'Rabbi Dostai',
                'Rav Sheizevi',
                'Rav Sheizvi',
                'Rabbi Zekharya',
                'Rabbi Ahai',
                'Rav Aha b. Huna',
                'Rabbi Elazar b. Rabbi',
                'Zunin',
                'Rabbi Yosei b. Rabbi',
                'Rabbi Yosei b. Shaul',
                'Rabbi Yehuda b. Teima',
                'Rav Yitzhak b. Avudimi',
                'Rabbi Menahem',
                'Rabbi Yosef',
                'Rabbi Yehuda b. Agra',
                'Rabbi Yirmeya b. Elazar',
                'Rav Beruna',
                'Rabbi Hananya b. Gamliel',
                'Rabbi Hananya',
                'Rabbi Yosei b. Zimra',
                'Rabbi Ahiyya',
                'Rabbi Hanan',
                'Rabbi Hiyya b. Ami',
             }, 'PERSON', rabbi_extra_keys),
            ({
                 'Bar Hamdakh',
                 'Sekhavta',
                'Mata Mehasya',
             }, 'GPE', None),
            ({
                'Burnitz River',
                'Bedita River',
                'Shanvata',
            }, 'LOC', None),
            ({'Baraita', 'Seder Olam', 'Psalms'}, 'WORK_OF_ART', halachic_role_extra_keys),
            ({'Torah law', 'rabbinic law'}, 'LAW', None),
            ({'Aramaic', 'Greek'}, 'LANGUAGE', None),
            ({'Ammonite', 'Moabite', 'Babylonian', 'Samaritan', 'Beit Hillel', 'Beit Shammai'}, 'NORP', None),
        ]
        topics_to_skip = {'on-the-son-of-pelet', 'will', 'groups', 'entourages', 'peoplehood', 'nations', 'groupings',
                          'generations', 'earlier-generations', 'groups-(אשישי)', 'the-early-pious-people', 'magicians',
                          'craftsmen-and-guards', 'mules', 'land', "earth-(ארקא)", 'earth', 'fifth', 'killing',
                          'hanging', "human-rights", 'mixtures', 'get'}
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
            else:
                topics = Topic.init(slug).get_leaf_nodes('is-a')
            for topic in topics:
                if topic.slug in topics_to_skip:
                    continue
                value = (topic.slug, tag, getattr(topic, 'numSources', 0))
                for title in topic.titles:
                    if title['lang'] == 'en':
                        search_terms[title['text']] += [value]
                        if extra_keys is not None:
                            for extra in extra_keys(title['text']):
                                # print('Extra', extra, title['text'])
                                search_terms[extra] += [value]
                        if title['text'].startswith('The '):
                            search_terms[re.sub('^The ', 'the ', title['text'])] += [value]
        search_terms = sorted(list(search_terms.items()), key=lambda x: len(x[0]), reverse=True)
        for term, matches in search_terms:
            matches.sort(key=lambda x: x[2], reverse=True)
        return search_terms

    def check_for_missing_entities(self, text, entities):
        tagged_index_set = {i for start, end, tag in entities for i in range(start, end)}
        rabbi_re = r'^[A-Z][a-z\']+(?: (?:bar|ben|, son of) [A-Z][a-z\']+)?(?=\W|$)'
        for match in re.finditer('(?:Rabbi|Rav) ', text):
            temp_match = re.search(rabbi_re, text[match.end():])
            if not temp_match:
                continue
            has_untagged = any([i not in tagged_index_set for i in range(temp_match.start(), temp_match.end()-1)])
            if match.start() in tagged_index_set and (match.end()) < len(text) and has_untagged:
                uncaught_rabbi = text[match.start():match.end() + temp_match.end()]
                uncaught_rabbi = re.sub("'s$", '', uncaught_rabbi)
                self.unique_uncaught_rabbis[uncaught_rabbi] += 1

    def tag_index(self, index):
        training = []
        for seg in tqdm(index.all_segment_refs(), desc='Segs'):
            text = Amud.normalize_text('en', seg.text('en').text)
            entities = self.tag_segment(text)
            self.check_for_missing_entities(text, entities)
            training += [[text, {"entities": entities}]]
        return training

    def tag_all(self, start=0, end=None, category='Bavli'):
        talmud = library.get_indexes_in_category(category, full_records=True)
        training = []
        for mes in tqdm(talmud[start:end], desc='Books'):
            training += self.tag_index(mes)
        srsly.write_jsonl('training/naive_training.jsonl', training)


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
    tagger.tag_all(start=0, end=1, category='Tanakh')
    # with open('best_rabbis.csv', 'w') as fout:
    #     c = csv.DictWriter(fout, ['Rabbi', 'Count'])
    #     c.writeheader()
    #     rows = [{'Rabbi': r, 'Count': i} for r, i in tagger.unique_uncaught_rabbis.items()]
    #     c.writerows(rows)
    convert_training_to_displacy('training/naive_training.jsonl')
    display_displacy('training/naive_training.jsonl.displacy')
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
