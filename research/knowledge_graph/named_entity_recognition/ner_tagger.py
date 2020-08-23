"""
TODO
- nikkud version
- generalize parts of code that assume english

How to update
- To update sperling NEs
    - edit sperling_en_and_he.csv
    - run find_missing_rabbis.convert_final_en_names_to_ner_tagger_input()


inputs
    --taggingParamsFile:
        filepath to JSON of the form
        {
            "namedEntities": [
                {
                    "id": <STRING>,
                    "idIsSlug": <BOOL>,
                    "manualTitles": [
                        {
                            "lang": ["he", "en"],
                            "text": <STRING>
                        }
                    ],
                    "tag": <STRING> (arbitrary tag to associate with this entity),
                    "getLeaves": <BOOL> (if True, include all leaves of this topic),
                }
            ],
            "corpus": [
                {
                    "title": <TITLE>,
                    "type": ["category", "index"],
                    "versions": [
                        {
                            "language": ["en", "he"],
                            "versionTitle": <VTITLE>,
                            "pretaggedFile": <FILEPATH> (OPTIONAL)
                        }
                    ]
                }
            ]
        }
        pretaggedFile is of form
        [
            {
                "start": <START INDEX>,
                "end": <END INDEX>,
                "mention": <MENTION STRING>,
                "id_matches": [<ID>,],
                "ref": <REF>,
                "vtitle": <VTITLE>,
                "lang": <LANG>
            }
        ]
    --outputFile
        file name to save results to

output
    file of the form
    [
        {
            "start": <START INDEX>,
            "end": <END INDEX>,
            "mention": <MENTION STRING>,
            "id_matches": [<ID>,],
            "ref": <REF>,
            "vtitle": <VTITLE>,
            "lang": <LANG>
        }
    ]
"""
import django, json, srsly, csv
django.setup()
import re2 as re
import regex
from tqdm import tqdm
from sefaria.model import *
from collections import defaultdict

class TextNormalizer:
    b_replacements = [' ben ', ' bar ', ', son of ', ', the son of ']
    b_token = ' b. '
    starting_replacements = ['Ben ', 'Bar ', 'The ']
    unidecode_table = {
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
        "“": '"'
    }
    normalizing_reg = r"\s*<[^>]+>\s*"
    normalizing_rep = " "

    @classmethod
    def get_rabbi_regex(cls, rabbi):
        reg = rabbi.replace(cls.b_token, f"(?:{u'|'.join(re.escape(b) for b in cls.b_replacements)})")
        for starter in cls.starting_replacements:
            starter = re.escape(starter)
            reg = re.sub(f'^{starter}', f"(?:{starter.lower()}|{starter})", reg)
        return reg

    @classmethod
    def get_rabbi_expansions(cls, rabbi):
        expansions = [rabbi]
        for starter in cls.starting_replacements:
            if rabbi.startswith(starter):
                expansions += [rabbi[0].lower() + rabbi[1:]]
        for expansion in expansions:
            if cls.b_token in expansion:
                for b_replacement in cls.b_replacements:
                    expansions += [expansion.replace(cls.b_token, b_replacement)]
        return expansions
    
    @classmethod
    def myunidecode(cls, text):
        for k, v in cls.unidecode_table.items():
            text = text.replace(k, v)
        return text

    @classmethod
    def normalize_text(cls, lang, s):
        # text = re.sub('<[^>]+>', ' ', text)
        if lang == 'en':
            s = cls.myunidecode(s)
            s = re.sub(cls.normalizing_reg, cls.normalizing_rep, s)
            # text = unidecode(text)
            # text = re.sub('\([^)]+\)', ' ', text)
            # text = re.sub('\[[^\]]+\]', ' ', text)
        # text = ' '.join(text.split())
        return s

    @classmethod
    def find_text_to_remove(cls, s):
        return [(m, cls.normalizing_rep) for m in re.finditer(cls.normalizing_reg, s)]

class Mention:

    def __init__(self, start=None, end=None, mention=None, id_matches=None, ref=None, versionTitle=None, language=None):
        self.start = start
        self.end = end
        self.mention = mention
        self.id_matches = id_matches
        self.ref = ref
        self.versionTitle = versionTitle
        self.language = language


    def add_metadata(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self

    def serialize(self):
        return {
            "start": self.start,
            "end": self.end,
            "mention": self.mention,
            "id_matches": self.id_matches,
            "ref": self.ref,
            "versionTitle": self.versionTitle,
            "language": self.language
        }

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        id_hash = "|".join(sorted(self.id_matches))
        return hash(f"{self.start}|{self.end}|{self.mention}|{self.ref}|{self.versionTitle}|{self.language}|{id_hash}")

class AbstractNamedEntityRecognizer:
    """
    Generic NER classifier
    Subclasses implement specific ner strategies
    """
    def __init__(self, named_entities, **kwargs):
        raise Exception("AbstractNamedEntityRecognizer should not be instantiated. Instantiate a subclass.")

    def fit(self):
        pass

    def predict(self, text):
        """
        Tags `text` with named entities
        Returns list of `Mentions`
        """
        pass

class NaiveNamedEntityRecognizer(AbstractNamedEntityRecognizer):

    def __init__(self, named_entities, **kwargs):
        self.named_entities = named_entities
        self.named_entity_regex = None

    def fit(self):
        title_regs = []
        for ne in tqdm(self.named_entities, desc="fit ner"):
            for title in ne.get_titles(lang="en", with_disambiguation=False):
                title_regs += [re.escape(expansion) for expansion in TextNormalizer.get_rabbi_expansions(title)]
        title_regs.sort(key=lambda x: len(x), reverse=True)
        word_breakers = r"|".join(re.escape(breaker) for breaker in ['.', ',', '"', '?', '!', '(', ')', '[', ']', '{', '}', ':', ';', '§', '<', '>', "'s"])

        self.named_entity_regex = re.compile(fr"(?:^|\s|{word_breakers})({'|'.join(title_regs)})(?:\s|{word_breakers}|$)")

    @staticmethod
    def filter_already_found_mentions(mentions, text, lang):
        text = text.replace('\xa0', ' ')  # strange character
        unique_titles = set(library.get_titles_in_string(text, lang, True))
        all_reg = library.get_multi_title_regex_string(unique_titles, lang)
        reg = regex.compile(all_reg, regex.VERBOSE)

        link_indexes = set()
        for match in reg.finditer(text):
            link_indexes |= {i for i in range(match.start(), match.end())}
        return list(filter(lambda m: len(link_indexes & set(range(m.start, m.end))) == 0, mentions))

    def predict_segment(self, corpus_segment):
        from data_utilities.util import get_mapping_after_normalization, convert_normalized_indices_to_unnormalized_indices

        norm_text = TextNormalizer.normalize_text(corpus_segment.language, corpus_segment.text)
        mentions = []
        for match in re.finditer(self.named_entity_regex, norm_text):
            mentions += [Mention(match.start(1), match.end(1), match.group(1), ref=corpus_segment.ref, versionTitle=corpus_segment.versionTitle, language=corpus_segment.language)]
        mention_indices = [(mention.start, mention.end) for mention in mentions]
        norm_map = get_mapping_after_normalization(corpus_segment.text, TextNormalizer.find_text_to_remove)
        mention_indices = convert_normalized_indices_to_unnormalized_indices(mention_indices, norm_map)
        for mention, (unnorm_start, unnorm_end) in zip(mentions, mention_indices):
            mention.add_metadata(start=unnorm_start, end=unnorm_end)
        mentions = self.filter_already_found_mentions(mentions, corpus_segment.text, corpus_segment.language)
        return mentions

    def predict(self, corpus_segments):
        mentions = []
        for corpus_segment in tqdm(corpus_segments, desc="ner predict"):
            mentions += self.predict_segment(corpus_segment)
        return mentions

class AbstractEntityLinker:
    """
    Generic Entity Linker
    Subclasses implement specific el strategies
    """
    def __init__(self, named_entities, **kwargs):
        raise Exception("AbstractEntityLinker should not be instantiated. Instantiate a subclass.")

    def fit(self):
        pass

    def predict(self, text, mentions):
        """
        Links mentions in `text` to named entities
        Returns list of `Mentions` with id_matches
        """
        pass

class NaiveEntityLinker(AbstractEntityLinker):

    def __init__(self, named_entities):
        self.named_entities = named_entities
        self.named_entity_table = defaultdict(dict)

    def fit(self):
        for ne in tqdm(self.named_entities, desc="fit el"):
            for title in ne.get_titles(lang="en", with_disambiguation=False):
                title_expansions = TextNormalizer.get_rabbi_expansions(title)
                for expansion in title_expansions:
                    self.named_entity_table[expansion][ne.slug] = ne
        for key, ne_dict in self.named_entity_table.items():
            self.named_entity_table[key] = sorted(ne_dict.values(), key=lambda x: getattr(x, 'numSources', 0), reverse=True)

    def predict(self, corpus_segments, mentions):
        for mention in tqdm(mentions, desc="el predict"):
            ne_list = self.named_entity_table.get(mention.mention, None)
            if ne_list is None:
                print(f"No named entity matches '{mention.mention}'")
                continue
            mention.add_metadata(id_matches=[ne.slug for ne in ne_list])
        return mentions

class CorpusSegment:

    def __init__(self, text, language, versionTitle, ref):
        self.text = text
        self.language = language
        self.versionTitle = versionTitle
        self.ref = ref

class CorpusManager:

    def __init__(self, tagging_params_file, mentions_output_file, mentions_html_folder):
        self.mentions_output_file = mentions_output_file
        self.mentions_html_folder = mentions_html_folder
        self.ner = None
        self.el = None
        self.mentions = []
        self.corpus_version_queries = []
        self.corpus_segments = []
        self.read_tagging_params_file(tagging_params_file)

    def read_tagging_params_file(self, tagging_params_file):
        with open(tagging_params_file, "r") as fin:
            tagging_params = json.load(fin)
        named_entities = self.create_named_entities(tagging_params["namedEntities"])
        self.ner = NaiveNamedEntityRecognizer(named_entities)
        self.el = NaiveEntityLinker(named_entities)
        self.ner.fit()
        self.el.fit()
        self.corpus_version_queries = self.create_corpus_version_queries(tagging_params["corpus"])

    def tag_corpus(self):
        for version_query in tqdm(self.corpus_version_queries, desc="load corpus"):
            pretagged_file = version_query.get("pretaggedFile", None)
            if pretagged_file is not None:
                with open(pretagged_file, "r") as fin:
                    pretagged_mentions = json.load(fin)
                    for mention in pretagged_mentions:
                        self.mentions += [Mention().add_metadata(versionTitle=version_query['versionTitle'], language=version_query['language'], **mention)]
            else:
                version = Version().load(version_query)
                version.walk_thru_contents(self.recognize_named_entities_in_segment)
        ner_mentions = self.ner.predict(self.corpus_segments)
        self.mentions += self.el.predict(self.corpus_segments, ner_mentions)

    def save_mentions(self):
        out = [mention.serialize() for mention in tqdm(self.mentions, desc="save mentions")]
        with open(self.mentions_output_file, "w") as fout:
            json.dump(out, fout, ensure_ascii=False, indent=2)

    def recognize_named_entities_in_segment(self, segment_text, en_tref, he_tref, version):
        self.corpus_segments += [CorpusSegment(segment_text, version.language, version.versionTitle, en_tref)]

    @staticmethod
    def create_named_entities(raw_named_entities):               
        named_entities = []
        for ne in raw_named_entities:
            if ne.get("idIsSlug", False):
                topic = Topic.init(ne["id"])
                if ne.get("getLeaves", False):
                    named_entities += topic.topics_by_link_type_recursively(only_leaves=True)
                else:
                    named_entities += [topic]
            else:
                if ne.get("namedEntityFile", False):
                    with open(ne["namedEntityFile"], "r") as fin:
                        manual_named_entities = json.load(fin)
                else:
                    manual_named_entities = [ne]
                for temp_ne in manual_named_entities:
                    topic = Topic({
                        "slug": temp_ne["id"],
                        "titles": temp_ne["manualTitles"]
                    })
                    named_entities += [topic]
        return named_entities

    @staticmethod
    def create_corpus_version_queries(raw_corpus):
        version_queries = []
        for item in raw_corpus:
            title_list = [item["title"]] if item["type"] == "index" else library.get_indexes_in_category(item["title"])
            for title in title_list:
                for temp_version_query in item["versions"]:
                    version_query_copy = temp_version_query.copy()
                    version_query_copy["title"] = title
                    version_queries += [version_query_copy]
        return version_queries

    @staticmethod
    def add_html_links(mentions, text):
        linked_text = ""
        mentions.sort(key=lambda x: x.start)
        dummy_char = "$"
        char_list = list(text)
        rabbi_dict = {}
        for m in mentions:
            if m.id_matches is None:
                continue
            rabbi_dict[m.start] = (text[m.start:m.end], m.id_matches)
            char_list[m.start:m.end] = list(dummy_char*(m.end-m.start))
        dummy_text = "".join(char_list)
        
        # assert len(dummy_text) == len(text), f"DUMMY {dummy_text}\nREAL {text}"

        def repl(match):
            try:
                mention, slugs = rabbi_dict[match.start()]
            except KeyError:
                print("KEYERROR", match.group())
                return match.group()
            # TODO find better way to determine if slug is in topics collection
            slug = slugs[0]
            other_slugs = slugs[1:]
            link = f"""<a href="https://www.sefaria.org/topics/{slug}" class="{"missing" if ':' in slug else "found"}">{mention}</a>"""
            if len(other_slugs) > 0:
                link += f'''<sup>{", ".join([f"""<a href="https://www.sefaria.org/topics/{temp_slug}" class="{"missing" if ':' in temp_slug else "found"}">[{i+1}]</a>""" for i, temp_slug in enumerate(other_slugs)])}</sup>'''
            return link
        linked_text = re.sub(r"\$+", repl, dummy_text)
        return linked_text
    
    def generate_html_file(self):
        mentions_by_ref = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for mention in tqdm(self.mentions, desc="html group by ref"):
            mentions_by_ref[Ref(mention.ref).index.title][mention.ref][f"{mention.versionTitle}|||{mention.language}"] += [mention]
        for book, ref_dict in tqdm(mentions_by_ref.items(), desc="make html"):
            refs_in_order = sorted(ref_dict.keys(), key=lambda x: Ref(x).order_id())
            html = """
            <html>
                <head>
                    <style>
                        body {
                            width: 700px;
                            margin-right: auto;
                            margin-bottom: 50px;
                            margin-top: 50px;
                            margin-left: auto;
                        }
                        .he {
                            direction: rtl;
                        }
                        .missing {
                            color: red;
                        }
                        .found {
                            color: green;
                        }
                    </style>
                </head>
                <body>
            """
            for ref in refs_in_order:
                oref = Ref(ref)
                versions = ref_dict[ref]
                html += f"""
                    <p><a href="https://www.sefaria.org/{oref.url()}">{ref}</a></p>
                """
                sorted_versions = sorted(versions.items(), key=lambda x: x[0])
                for version_lang, temp_mentions in sorted_versions:
                    vtitle, lang = version_lang.split('|||')
                    segment_text = oref.text(lang, vtitle=vtitle).text
                    linked_text = self.add_html_links(temp_mentions, segment_text)
                    html += f"""
                        <p class="{lang}">{linked_text}</p>
                    """
            html += """
                </body>
            </html>
            """
            with open(self.mentions_html_folder + f'/{book}.html', "w") as fout:
                fout.write(html)

    @staticmethod
    def get_snippet(text, mention, padding=30, delim='~'):
        start = text[mention.start-padding:mention.start] if mention.start - padding >= 0 else text[:mention.start]
        end = text[mention.end:mention.end+padding]
        return f"{start}{delim}{mention.mention}{delim}{end}"

    def cross_validate_mentions_by_lang(self, output_file, common_mistakes_output_file):
        from functools import reduce
        ps = PassageSet()
        ref_passage_map = {
            r: p.full_ref for p in ps for r in p.ref_list
        }
        common_mistakes = defaultdict(lambda: {"count": 0, "rowIds": []})
        mentions_by_passage = defaultdict(lambda: defaultdict(set))
        for mention in tqdm(self.mentions, desc="group by passage"):
            passage_ref = ref_passage_map.get(mention.ref, mention.ref)
            mentions_by_passage[passage_ref][(mention.versionTitle,mention.language)].add(mention)
        rows = []
        cached_text = {}
        for passage, version_dict in tqdm(mentions_by_passage.items(), desc="cross validate"):
            unique_ids_by_version = {}
            for version_lang, temp_mentions in version_dict.items():
                temp_unique_ids = {}
                for temp_mention in temp_mentions:
                    if temp_mention.id_matches is None:
                        continue
                    temp_unique_ids['|'.join(sorted(temp_mention.id_matches))] = set(temp_mention.id_matches)
                unique_ids_by_version[version_lang] = {
                    "ids": temp_unique_ids,
                    "mentions": temp_mentions
                }
            if len(unique_ids_by_version) == 1:
                continue
            for version_lang, temp_mentions_dict in unique_ids_by_version.items():
                versionTitle, language = version_lang
                temp_unique_ids = temp_mentions_dict["ids"]
                temp_mentions = temp_mentions_dict["mentions"]

                other_unique_ids = reduce(lambda a, b: a | b, reduce(lambda a, b: a + b, [list(value["ids"].values()) for key, value in unique_ids_by_version.items() if key != version_lang], []), set())
                for temp_id_key, temp_id_set in temp_unique_ids.items():
                    _type = "matched" if len(temp_id_set & other_unique_ids) > 0 else "extra"
                    ambiguous = len(temp_id_set) > 1
                    if _type == "matched" and not ambiguous:
                        continue
                    mentions_for_id = {m.mention:m for m in temp_mentions if '|'.join(sorted(set(getattr(m, 'id_matches', [])))) == temp_id_key}
                    example_mention = list(mentions_for_id.values())[0]
                    example_ref = example_mention.ref
                    text_key = f"{version_lang}|||{example_ref}"
                    try:
                        temp_text = cached_text[text_key]
                    except KeyError:
                        temp_text = Ref(example_ref).text(language, vtitle=versionTitle).text
                        cached_text[text_key] = temp_text
                    common_key = (
                        versionTitle,
                        language,
                        temp_id_key,
                        _type,
                        ambiguous
                    )
                    common_mistakes[common_key]['count'] += 1
                    common_mistakes[common_key]['rowIds'] += [len(rows)+1]
                    rows += [{
                        "rowId": len(rows)+1,
                        "versionTitle": versionTitle,
                        "language": language,
                        "passage": passage,
                        "mentions": " | ".join(mentions_for_id.keys()),
                        "example snippet": self.get_snippet(temp_text, example_mention),
                        "id": temp_id_key,
                        "type": _type,
                        "ambiguous": ambiguous
                    }]
                if len(unique_ids_by_version) > 2:
                    you_not_me = other_unique_ids.difference(temp_unique_ids)
                    # missing only adds info when there are more than two versions being compared
                    for you in you_not_me:
                        rows += [{
                            "versionTitle": versionTitle,
                            "language": language,
                            "passage": passage,
                            "id": you,
                            "type": "missing"
                        }]
            if len(rows) > 0 and rows[-1]["versionTitle"] != "---":
                rows += [{
                    "versionTitle": "---"
                }]
        common_rows = []
        for (versionTitle, language, id_key, _type, ambiguous), temp_dict in sorted(common_mistakes.items(), key=lambda x: x[1]['count'], reverse=True):
            common_rows += [{
                "versionTitle": versionTitle,
                "language": language,
                "id": id_key,
                "type": _type,
                "ambiguous": ambiguous,
                "count": temp_dict['count'],
                "rowIds": ", ".join(str(rowId) for rowId in temp_dict['rowIds'])
            }]
        with open(output_file, "w") as fout:
            c = csv.DictWriter(fout, ["rowId","versionTitle", "language", "id", "type", "ambiguous", "passage", "mentions", "example snippet"])
            c.writeheader()
            c.writerows(rows)
        with open(common_mistakes_output_file, "w") as fout:
            c = csv.DictWriter(fout, ["versionTitle", "language", "id", "type", "ambiguous", "count", "rowIds"])
            c.writeheader()
            c.writerows(common_rows)

    def load_mentions(self):
        with open(self.mentions_output_file, "r") as fin:
            print("Loading mentions...")
            mentions = json.load(fin)
            print("Done")
            self.mentions = [Mention().add_metadata(**m) for m in tqdm(mentions, desc="load mentions")]

if __name__ == "__main__":
    corpus_manager = CorpusManager(
        "research/knowledge_graph/named_entity_recognition/ner_tagger_input.json",
        "/home/nss/sefaria/datasets/ner/sefaria/ner_output.json",
        "/home/nss/sefaria/datasets/ner/sefaria/html"
    )
    corpus_manager.tag_corpus()
    corpus_manager.save_mentions()
    corpus_manager.generate_html_file()

    # corpus_manager.load_mentions()
    corpus_manager.cross_validate_mentions_by_lang("/home/nss/sefaria/datasets/ner/sefaria/cross_validated_by_language.csv", "/home/nss/sefaria/datasets/ner/sefaria/cross_validated_by_language_common_mistakes.csv")


"""
x-validation algo

for each sugya
    en_ids = set(ids in en mentions)
    he_ids = set(ids in he mentions)

"""

