"""
TODO
- combination algorithm
    - ideally only limit to same sugya, not same segment
- nikkud version
- generalize parts of code that assume english

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
        for ne in self.named_entities:
            for title in ne.get_titles(lang="en", with_disambiguation=False):
                title_regs += [re.escape(expansion) for expansion in TextNormalizer.get_rabbi_expansions(title)]
        title_regs.sort(key=lambda x: len(x), reverse=True)
        word_breakers = r"|".join(re.escape(breaker) for breaker in ['.', ',', '"', '?', '!', '(', ')', '[', ']', '{', '}', ':', ';', '§', '<', '>', "'s"])

        self.named_entity_regex = re.compile(fr"(?:\s|{word_breakers})({'|'.join(title_regs)})(?:\s|{word_breakers})")

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

    def predict(self, text, lang):
        from data_utilities.util import get_mapping_after_normalization, convert_normalized_indices_to_unnormalized_indices

        norm_text = TextNormalizer.normalize_text('en', text)
        mentions = []
        for match in re.finditer(self.named_entity_regex, norm_text):
            mentions += [Mention(match.start(1), match.end(1), match.group(1))]
        mention_indices = [(mention.start, mention.end) for mention in mentions]
        norm_map = get_mapping_after_normalization(text, TextNormalizer.find_text_to_remove)
        mention_indices = convert_normalized_indices_to_unnormalized_indices(mention_indices, norm_map)
        for mention, (unnorm_start, unnorm_end) in zip(mentions, mention_indices):
            mention.add_metadata(start=unnorm_start, end=unnorm_end)
        if "Samuel 5:21" in text:
            print("yo")
        mentions = self.filter_already_found_mentions(mentions, text, lang)
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
        for ne in self.named_entities:
            for title in ne.get_titles(lang="en", with_disambiguation=False):
                title_expansions = TextNormalizer.get_rabbi_expansions(title)
                for expansion in title_expansions:
                    self.named_entity_table[expansion][ne.slug] = ne
        for key, ne_dict in self.named_entity_table.items():
            self.named_entity_table[key] = sorted(ne_dict.values(), key=lambda x: getattr(x, 'numSources', 0), reverse=True)

    def predict(self, text, mentions):
        for mention in mentions:
            ne_list = self.named_entity_table.get(mention.mention, None)
            if ne_list is None:
                print(f"No named entity matches '{mention.mention}'")
                continue
            mention.add_metadata(id_matches=[ne.slug for ne in ne_list])
        return mentions


class CorpusManager:

    def __init__(self, tagging_params_file, mentions_output_file, mentions_html_folder):
        self.mentions_output_file = mentions_output_file
        self.mentions_html_folder = mentions_html_folder
        self.ner = None
        self.el = None
        self.mentions = []
        self.corpus_version_queries = []
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
        for version_query in tqdm(self.corpus_version_queries, desc="tag corpus"):
            pretagged_file = version_query.get("pretaggedFile", None)
            if pretagged_file is not None:
                with open(pretagged_file, "r") as fin:
                    pretagged_mentions = json.load(fin)
                    for mention in pretagged_mentions:
                        self.mentions += [Mention().add_metadata(versionTitle=version_query['versionTitle'], language=version_query['language'], **mention)]
            else:
                version = Version().load(version_query)
                version.walk_thru_contents(self.recognize_named_entities_in_segment)

    def save_mentions(self):
        out = [mention.serialize() for mention in self.mentions]
        with open(self.mentions_output_file, "w") as fout:
            json.dump(out, fout, ensure_ascii=False, indent=2)

    def recognize_named_entities_in_segment(self, segment_text, en_tref, he_tref, version):
        mentions = self.ner.predict(segment_text, version.language)
        for ment in mentions:
            ment.add_metadata(ref=en_tref, versionTitle=version.versionTitle, language=version.language)
        mentions = self.el.predict(segment_text, mentions)
        self.mentions += mentions

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
            rabbi_dict[m.start] = (text[m.start:m.end], m.id_matches[0])
            char_list[m.start:m.end] = list(dummy_char*(m.end-m.start))
        dummy_text = "".join(char_list)
        
        # assert len(dummy_text) == len(text), f"DUMMY {dummy_text}\nREAL {text}"

        def repl(match):
            try:
                mention, slug = rabbi_dict[match.start()]
            except KeyError:
                print("KEYERROR", match.group())
                return match.group()
            # TODO find better way to determine if slug is in topics collection
            return f"""<a href="https://www.sefaria.org/topics/{slug}" class="{"missing" if ':' in slug else "found"}">{mention}</a>"""
        linked_text = re.sub(r"\$+", repl, dummy_text)
        return linked_text
    
    def generate_html_file(self):
        mentions_by_ref = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        for mention in self.mentions:
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

    def cross_validate_mentions_by_lang(self, output_file):
        from functools import reduce
        ps = PassageSet()
        ref_passage_map = {
            r: p.full_ref for p in ps for r in p.ref_list
        }
        mentions_by_passage = defaultdict(lambda: defaultdict(list))
        for mention in self.mentions:
            passage_ref = ref_passage_map.get(mention.ref, mention.ref)
            mentions_by_passage[passage_ref][f"{mention.versionTitle}|||{mention.language}"] += [mention]
        rows = []
        for passage, version_dict in tqdm(mentions_by_passage.items(), desc="cross validate"):
            unique_ids_by_version = defaultdict(set)
            for version_lang, temp_mentions in version_dict.items():
                temp_unique_ids = set()
                for temp_mention in temp_mentions:
                    if temp_mention.id_matches is None:
                        continue
                    temp_unique_ids |= set(temp_mention.id_matches)
                unique_ids_by_version[version_lang] = {
                    "ids": temp_unique_ids,
                    "mentions": temp_mentions
                }
            if len(unique_ids_by_version) == 1:
                continue
            for version_lang, temp_mentions_dict in unique_ids_by_version.items():
                versionTitle, language = version_lang.split('|||')
                temp_unique_ids = temp_mentions_dict["ids"]
                temp_mentions = temp_mentions_dict["mentions"]
                other_unique_ids = reduce(lambda a, b: a | b, [value["ids"] for key, value in unique_ids_by_version.items() if key != version_lang], set())
                me_not_you = temp_unique_ids.difference(other_unique_ids)
                you_not_me = other_unique_ids.difference(temp_unique_ids)
                for me in me_not_you:
                    mentions_for_id = {m.mention for m in temp_mentions if me in getattr(m, 'id_matches', [])}
                    rows += [{
                        "versionTitle": versionTitle,
                        "language": language,
                        "passage": passage,
                        "mentions": " | ".join(mentions_for_id),
                        "id": me,
                        "type": "extra"
                    }]
                for you in you_not_me:
                    rows += [{
                        "versionTitle": versionTitle,
                        "language": language,
                        "passage": passage,
                        "id": you,
                        "type": "missing"
                    }]
        with open(output_file, "w") as fout:
            c = csv.DictWriter(fout, ["versionTitle", "language", "passage", "id", "type", "mentions"])
            c.writeheader()
            c.writerows(rows)

    def load_mentions(self):
        with open(self.mentions_output_file, "r") as fin:
            mentions = json.load(fin)
            self.mentions = [Mention().add_metadata(**m) for m in mentions]

if __name__ == "__main__":
    corpus_manager = CorpusManager(
        "research/knowledge_graph/named_entity_recognition/ner_tagger_input.json",
        "/home/nss/sefaria/datasets/ner/sefaria/ner_output.json",
        "/home/nss/sefaria/datasets/ner/sefaria/html"
    )
    # corpus_manager.tag_corpus()
    # corpus_manager.save_mentions()
    # corpus_manager.generate_html_file()

    corpus_manager.load_mentions()
    corpus_manager.cross_validate_mentions_by_lang("/home/nss/sefaria/datasets/ner/sefaria/cross_validated_by_language.csv")


"""
x-validation algo

for each sugya
    en_ids = set(ids in en mentions)
    he_ids = set(ids in he mentions)

"""

