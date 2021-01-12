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
                            "pretaggedFile": <FILEPATH> (OPTIONAL),
                            "pretaggedMentionsInDB": <BOOL> (OPTIONAL)
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
from sefaria.utils.hebrew import strip_cantillation
django.setup()
import re2 as re
import regex
from tqdm import tqdm
from sefaria.model import *
from collections import defaultdict

class TextNormalizer:
    b_replacements = [' ben ', ' bar ', ', son of ', ', the son of ', ' son of ', ' the son of ']
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
    normalizing_reg_en = r"\s*<[^>]+>\s*"
    normalizing_reg_he = "[\u0591-\u05bd\u05bf-\u05c5\u05c7]+"
    normalizing_rep_en = " "
    normalizing_rep_he = ""

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
        if rabbi.startswith('Rabbi '):
            expansions += [rabbi.replace('Rabbi ', 'R. ')]
        for expansion in expansions:
            if cls.b_token in expansion:
                for b_replacement in cls.b_replacements:
                    expansions += [expansion.replace(cls.b_token, b_replacement)]
        expansions = [strip_cantillation(expansion, True) for expansion in expansions]
        return expansions

    @classmethod
    def myunidecode(cls, text):
        for k, v in cls.unidecode_table.items():
            text = text.replace(k, v)
        return text

    @classmethod
    def normalize_text(cls, lang, s):
        s = cls.myunidecode(s)
        if lang == 'en':
            s = re.sub(cls.normalizing_reg_en, cls.normalizing_rep_en, s)
        else:
            s = re.sub(cls.normalizing_reg_he, cls.normalizing_rep_he, s)
            s = s.replace('־', ' ')
        return s

    @classmethod
    def get_find_text_to_remove(cls, lang):
        normalizing_reg = cls.normalizing_reg_en if lang == 'en' else cls.normalizing_reg_he
        normalizing_rep = cls.normalizing_rep_en if lang == 'en' else cls.normalizing_rep_he
        return lambda s: [(m, normalizing_rep) for m in re.finditer(normalizing_reg, s)]

class Mention:

    def __init__(self, start=None, end=None, mention=None, id_matches=None, ref=None, versionTitle=None, language=None):
        self.start = start
        self.end = end
        self.mention = mention
        self.id_matches = id_matches
        self.ref = ref
        self.versionTitle = versionTitle
        self.language = language
        self.is_non_literal = False  # used for texts that include both literal and non-literal translations


    def add_metadata(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self

    def add_metadata_from_link(self, link:RefTopicLink):
        if getattr(self, 'possibility_map', None) is None:
            self.load_ambiguous_map()
        cld = link.charLevelData
        self.start = cld['startChar']
        self.end = cld['endChar']
        self.mention = cld['text']
        self.id_matches = list(self.possibility_map.get(link.toTopic, [link.toTopic]))
        self.ref = link.ref
        self.versionTitle = cld['versionTitle']
        self.language = cld['language']
        return self

    @classmethod
    def load_ambiguous_map(cls):
        ambiguous_links = IntraTopicLinkSet({"linkType": "possibility-for"})
        cls.possibility_map = defaultdict(set)
        for l in ambiguous_links:
            cls.possibility_map[l.toTopic].add(l.fromTopic)
        

    def serialize(self, delete_keys=None):
        d = {
            "start": self.start,
            "end": self.end,
            "mention": self.mention,
            "id_matches": self.id_matches,
            "ref": self.ref,
            "versionTitle": self.versionTitle,
            "language": self.language
        }
        if delete_keys is not None:
            for key in delete_keys:
                del d[key]
        return d

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        id_hash = "|".join(sorted(self.id_matches))
        return hash(f"{self.start}|{self.end}|{self.mention}|{self.ref}|{self.versionTitle}|{self.language}|{id_hash}")

    def __str__(self):
        return f'{self.mention} ({self.ref})[{self.start}:{self.end}]'

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.start}, {self.end}, {self.mention}, {self.id_matches}, {self.ref}, {self.versionTitle}, {self.language})'

    def __getitem__(self, key):
        return getattr(self, key)

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
        self.named_entity_regex_by_lang = {}
        self.lang_specific_params = kwargs.get('langSpecificParams', {})
    def fit(self):
        for lang in ("en", "he"):
            lang_params = self.lang_specific_params.get(lang, {})
            title_regs = []
            for ne in tqdm(self.named_entities, desc="fit ner"):
                for title in ne.get_titles(lang=lang, with_disambiguation=False):
                    title_regs += [re.escape(expansion) for expansion in TextNormalizer.get_rabbi_expansions(title)]
            title_regs.sort(key=lambda x: len(x), reverse=True)
            word_breakers = r"|".join(re.escape(breaker) for breaker in ['.', ',', '"', '?', '!', '(', ')', '[', ']', '{', '}', ':', ';', '§', '<', '>', "'s", "׃", "׀", "־"])
            self.named_entity_regex_by_lang[lang] = re.compile(fr"(?:(?:^|\s|{word_breakers}){lang_params.get('prefixRegex', None) or ''})({'|'.join(title_regs)})(?=\s|{word_breakers}|$)")
    
    @staticmethod
    def filter_already_found_mentions(mentions, text, lang):
        # can be generalized more. meant to avoid double linking things that are already linked
        # currnetly runs linker and skips named entities that overlap with linker results
        text = text.replace('\xa0', ' ')  # strange character
        unique_titles = set(library.get_titles_in_string(text, lang, True))
        all_reg = library.get_multi_title_regex_string(unique_titles, lang)
        reg = regex.compile(all_reg, regex.VERBOSE)

        already_found_indexes = set()
        for match in reg.finditer(text):
            already_found_indexes |= {i for i in range(match.start(), match.end())}
        return list(filter(lambda m: len(already_found_indexes & set(range(m.start, m.end))) == 0, mentions))

    def predict_segment(self, corpus_segment):
        from data_utilities.util import get_mapping_after_normalization, convert_normalized_indices_to_unnormalized_indices

        norm_text = TextNormalizer.normalize_text(corpus_segment.language, corpus_segment.text)
        mentions = []
        for match in re.finditer(self.named_entity_regex_by_lang[corpus_segment.language], norm_text):
            mentions += [Mention(match.start(1), match.end(1), match.group(1), ref=corpus_segment.ref, versionTitle=corpus_segment.versionTitle, language=corpus_segment.language)]
        mention_indices = [(mention.start, mention.end) for mention in mentions]
        norm_map = get_mapping_after_normalization(corpus_segment.text, TextNormalizer.get_find_text_to_remove(corpus_segment.language))
        mention_indices = convert_normalized_indices_to_unnormalized_indices(mention_indices, norm_map)
        for mention, (unnorm_start, unnorm_end) in zip(mentions, mention_indices):
            mention.add_metadata(start=unnorm_start, end=unnorm_end, mention=corpus_segment.text[unnorm_start:unnorm_end])
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

    def __init__(self, named_entities, rules, **kwargs):
        self.named_entities = named_entities
        self.named_entity_table = defaultdict(dict)  # (lang, title) -> list of topics (dict now, but will be changed to list)
        self.rules = rules
        self.lang_specific_params = kwargs.get('langSpecificParams', {})
        self.literal_text_map = get_literal_text_map(kwargs.get('nonLiteralCorpus', []))


    def fit(self):
        for lang in ("en", "he"):
            for ne in tqdm(self.named_entities, desc="fit el"):
                for title in ne.get_titles(lang=lang, with_disambiguation=False):
                    title_expansions = TextNormalizer.get_rabbi_expansions(title)
                    for expansion in title_expansions:
                        expansion = strip_cantillation(expansion, strip_vowels=True)
                        self.named_entity_table[(lang, expansion)][ne.slug] = ne
        for key, ne_dict in self.named_entity_table.items():
            self.named_entity_table[key] = sorted(ne_dict.values(), key=lambda x: getattr(x, 'numSources', 0), reverse=True)

    def predict(self, corpus_segments, mentions):
        grouped_by_ref = defaultdict(list)
        for mention in tqdm(mentions, desc="el predict"):
            grouped_by_ref[mention.ref] += [mention]

            # check if mention is in literal text
            temp_literal_indexes = self.literal_text_map.get((mention.versionTitle, mention.language, mention.ref), None)
            mention_indices = {i for i in range(mention.start, mention.end)}
            mention.is_non_literal = temp_literal_indexes is not None and len(temp_literal_indexes & mention_indices) == 0

            pretagged_id_matches = getattr(mention, 'id_matches', None)
            if pretagged_id_matches is None:
                norm_mention = TextNormalizer.normalize_text(mention.language, mention.mention)
                ne_list = self.named_entity_table.get((mention.language, norm_mention), None)
                if ne_list is None:
                    print(f"No named entity matches '{norm_mention}'. Unnorm mention: '{mention.mention}', Ref: {mention.ref}")
                    mention.add_metadata(id_matches=[])
                    continue
                mention.add_metadata(id_matches=[ne.slug for ne in ne_list])
        out_mentions = []
        for _, ref_mentions in grouped_by_ref.items():
            for rule in self.rules:
                rule.apply(ref_mentions)
            out_mentions += list(filter(lambda mention: len(mention.id_matches) > 0, ref_mentions))  # remove any mentions that no longer have id_matches due to rules applied           
        return out_mentions

class AbstractRule:

    def __init__(self, rule_dict):
        self.rule = rule_dict['rule']
        self.named_entities = set(rule_dict.get('namedEntities', []))
        self.mentions = rule_dict.get('mentions', None)
        if self.mentions is not None:
            self.mentions = set(self.mentions)

    def is_applicable(self, mention, mentions):
        return len(set(mention.id_matches) & self.named_entities) > 0

    def apply(self, mentions):
        pass

class MinMaxRefRule(AbstractRule):

    def __init__(self, rule_dict):
        super(MinMaxRefRule, self).__init__(rule_dict)
        self.rule['maxRef'] = Ref(self.rule['maxRef']) if 'maxRef' in self.rule else None
        self.rule['minRef'] = Ref(self.rule['minRef']) if 'minRef' in self.rule else None


    def apply(self, mentions):
        mentions = [mention for mention in mentions if self.is_applicable(mention, mentions)]
        for mention in mentions:
            rule_satisfied = True
            if self.mentions is None or strip_cantillation(mention.mention, strip_vowels=True) in self.mentions:
                if self.rule['minRef'] is not None and Ref(mention.ref).order_id() < self.rule['minRef'].order_id():
                    rule_satisfied = False
                if self.rule['maxRef'] is not None and Ref(mention.ref).order_id() > self.rule['maxRef'].order_id():
                    rule_satisfied = False
            if not rule_satisfied:
                mention.id_matches = list(set(mention.id_matches).difference(self.named_entities))

class ExactRefRule(AbstractRule):

    def __init__(self, rule_dict):
        super(ExactRefRule, self).__init__(rule_dict)
        self.rule['exactRefs'] = set(self.rule['exactRefs'])

    def apply(self, mentions):
        mentions = [mention for mention in mentions if self.is_applicable(mention, mentions)]
        for mention in mentions:
            rule_satisfied = mention.ref in self.rule['exactRefs']
            if not rule_satisfied:
                mention.id_matches = list(set(mention.id_matches).difference(self.named_entities))

class NamedEntityInVersionRule(AbstractRule):
    """
    deletes mention if equivalent mention doesn't appear in specified version
    """
    def __init__(self, rule_dict):
        super(NamedEntityInVersionRule, self).__init__(rule_dict)
        self.applies_to_vtitle_set = {x['versionTitle'] for x in self.rule['appliesToVersions']}
        self.applies_to_lang_set = {x['language'] for x in self.rule['appliesToVersions']}
    
    def apply(self, mentions):
        applicable_mentions = [mention for mention in mentions if self.is_applicable(mention, mentions)]
        compare_named_entities = set()
        for mention in mentions:
            if mention.versionTitle != self.rule['versionToCompare']['versionTitle'] or mention.language != self.rule['versionToCompare']['language'] or mention.is_non_literal:
                continue
            compare_named_entities |= set(mention.id_matches)

        for mention in applicable_mentions:
            if mention.versionTitle not in self.applies_to_vtitle_set or mention.language not in self.applies_to_lang_set:
                continue
            if len(set(mention.id_matches) & compare_named_entities) == 0:
                # equivalent named entity doesn't appear in versionToCompare
                # delete id_matches
                mention.id_matches = []

class ManualCorrectionsRule(AbstractRule):

    def __init__(self, rule_dict):
        super().__init__(rule_dict)
        self.manual_corrections = srsly.read_json(self.rule['correctionsFile'])
        self.applies_to_dict = {}
        for correction in self.manual_corrections:
            self.applies_to_dict[self.get_applies_to_key(correction)] = correction['correctionType']

    @staticmethod
    def get_applies_to_key(mention):
        return (mention['ref'], mention['versionTitle'], mention['language'], mention['start'], mention['end'], mention['mention'])
    
    def is_applicable(self, mention, mentions):
        return self.get_applies_to_key(mention) in self.applies_to_dict

    def apply(self, mentions):
        mentions = filter(lambda m: self.is_applicable(m, mentions), mentions)
        for mention in mentions:
            correction_type = self.applies_to_dict[self.get_applies_to_key(mention)]
            if correction_type == 'mistake':
                print("NABBED!", mention)
                mention.id_matches = []
class RuleFactory:

    key_rule_map = {
        "minRef": MinMaxRefRule,
        "maxRef": MinMaxRefRule,
        "exactRefs": ExactRefRule,
        "namedEntityInVersion": NamedEntityInVersionRule,
        "manualCorrections": ManualCorrectionsRule,
    }

    @classmethod
    def create(cls, rule_dict):
        return cls.key_rule_map[rule_dict['rule']['id']](rule_dict)



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
        self.named_entities = []
        self.ner = None
        self.el = None
        self.mentions = []
        self.corpus_version_queries = []
        self.corpus_segments = []
        self.read_tagging_params_file(tagging_params_file)

    def read_tagging_params_file(self, tagging_params_file):
        with open(tagging_params_file, "r") as fin:
            tagging_params = json.load(fin)
        self.named_entities = self.create_named_entities(tagging_params["namedEntities"])
        rules = self.create_rules(tagging_params.get("rules", []))
        self.ner = NaiveNamedEntityRecognizer(self.named_entities, **tagging_params.get('namedEntityRecognizerParams', {}))
        self.el = NaiveEntityLinker(self.named_entities, rules, **tagging_params.get('namedEntityLinkerParams', {}))
        self.ner.fit()
        self.el.fit()
        self.corpus_version_queries = self.create_corpus_version_queries(tagging_params["corpus"])

    def tag_corpus(self):
        pretagged_mentions = []
        for version_query in tqdm(self.corpus_version_queries, desc="load corpus"):
            pretagged_file = version_query.get("pretaggedFile", None)
            pretagged_in_db = version_query.get("pretaggedMentionsInDB", False)
            if pretagged_file is not None:
                with open(pretagged_file, "r") as fin:
                    raw_pretagged_mentions = json.load(fin)
                    for mention in raw_pretagged_mentions:
                        pretagged_mentions += [Mention().add_metadata(versionTitle=version_query['versionTitle'], language=version_query['language'], **mention)]
            if pretagged_in_db:
                mention_links = RefTopicLinkSet({"linkType": "mention", "charLevelData.versionTitle": version_query['versionTitle'], "charLevelData.language": version_query['language']})
                for link in mention_links:
                    pretagged_mentions += [Mention().add_metadata_from_link(link)]
            if pretagged_file is None and not pretagged_in_db:
                # no pretagged mentions
                version = Version().load(version_query)
                if version is None: continue
                version.walk_thru_contents(self.recognize_named_entities_in_segment)
        ner_mentions = self.ner.predict(self.corpus_segments)
        ner_mentions += pretagged_mentions
        el_mentions = self.el.predict(self.corpus_segments, ner_mentions)
        self.mentions = el_mentions

    def save_mentions(self):
        out = [mention.serialize() for mention in tqdm(self.mentions, desc="save mentions")]
        with open(self.mentions_output_file, "w") as fout:
            json.dump(out, fout, ensure_ascii=False, indent=2)

    def recognize_named_entities_in_segment(self, segment_text, en_tref, he_tref, version):
        self.corpus_segments += [CorpusSegment(segment_text, version.language, version.versionTitle, en_tref)]

    @staticmethod
    def create_rules(raw_rules):
        return [RuleFactory.create(raw_rule) for raw_rule in raw_rules]

    @staticmethod
    def create_named_entities(raw_named_entities):
        named_entities = []
        for ne in raw_named_entities:
            if ne.get("idIsSlug", False):
                topic = Topic.init(ne["id"])
                if ne.get("getLeaves", False):
                    named_entities += topic.topics_by_link_type_recursively(only_leaves=True)
                else:
                    topic.titles += ne.get("manualTitles", [])
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
            if item.get('skip', None) is not None:
                skip_set = set(item['skip'])
                title_list = list(filter(lambda x: x not in skip_set, title_list))
            for title in title_list:
                for temp_version_query in item["versions"]:
                    if temp_version_query.get("pretaggedFile", False) or temp_version_query.get('pretaggedMentionsInDB', False):
                        # no need to include every index for a pretagged version
                        continue
                    version_query_copy = temp_version_query.copy()
                    version_query_copy["title"] = title
                    version_queries += [version_query_copy]
            for temp_version_query in item["versions"]:
                # pretagged files and pretaggedmentions in db here!
                if not (temp_version_query.get("pretaggedFile", False) or temp_version_query.get('pretaggedMentionsInDB', False)):
                    continue
                version_queries += [temp_version_query]
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
            slug = slugs[0] if len(slugs) > 0 else ''
            other_slugs = slugs[1:]
            link = f"""<a href="https://www.sefaria.org/topics/{slug}" class="{"no-ids" if len(slug) == 0 else "missing" if ':' in slug else "found"}">{mention}</a>"""
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
                        .no-ids {
                            color: purple;
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

    def cross_validate_mentions_by_lang(self, output_file, common_mistakes_output_file, ambiguities_output_file):
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
                        "example ref": example_ref,
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
        total_mistakes = 0
        for (versionTitle, language, id_key, _type, ambiguous), temp_dict in sorted(common_mistakes.items(), key=lambda x: x[1]['count'], reverse=True):
            if ambiguous:
                continue
            total_mistakes += temp_dict['count']
            common_rows += [{
                "versionTitle": versionTitle,
                "language": language,
                "id": id_key,
                "type": _type,
                "count": temp_dict['count'],
                "rowIds": ", ".join(str(rowId) for rowId in temp_dict['rowIds'])
            }]
        ambiguous_rows = []
        total_ambiguities = 0
        for (versionTitle, language, id_key, _type, ambiguous), temp_dict in sorted(common_mistakes.items(), key=lambda x: x[1]['count'], reverse=True):
            if not ambiguous:
                continue
            total_ambiguities += temp_dict['count']
            ambiguous_rows += [{
                "versionTitle": versionTitle,
                "language": language,
                "id": id_key,
                "type": _type,
                "count": temp_dict['count'],
                "rowIds": ", ".join(str(rowId) for rowId in temp_dict['rowIds'])
            }]
        with open(output_file, "w") as fout:
            c = csv.DictWriter(fout, ["rowId","versionTitle", "language", "id", "type", "ambiguous", "passage", "mentions", "example ref", "example snippet"])
            c.writeheader()
            c.writerows(rows)
        with open(common_mistakes_output_file, "w") as fout:
            c = csv.DictWriter(fout, ["versionTitle", "language", "id", "type", "count", "rowIds"])
            c.writeheader()
            c.writerows(common_rows)
        with open(ambiguities_output_file, "w") as fout:
            c = csv.DictWriter(fout, ["versionTitle", "language", "id", "type", "count", "rowIds"])
            c.writeheader()
            c.writerows(ambiguous_rows)
        print("TOTAL MENTIONS", len(self.mentions))
        print("TOTAL MISTAKES", total_mistakes)
        print("TOTAL AMBIGUITIES", total_ambiguities)

    def load_mentions(self):
        with open(self.mentions_output_file, "r") as fin:
            print("Loading mentions...")
            mentions = json.load(fin)
            print("Done")
            self.mentions = [Mention().add_metadata(**m) for m in tqdm(mentions, desc="load mentions")]

    def cross_validate_mentions_by_lang_literal(self, output_file, common_mistakes_output_file, ambiguities_output_file, primary_version_key=None, with_replace=True):
        from difflib import SequenceMatcher
        mentions_by_passage = defaultdict(lambda: defaultdict(list))
        primary_version, primary_lang = None, None
        if primary_version_key is not None:
            primary_version, primary_lang = primary_version_key
        for mention in tqdm(self.mentions, desc="group by passage"):
            literal_indexes = self.el.literal_text_map.get((mention.versionTitle, mention.language, mention.ref), None)
            if literal_indexes is not None:
                mention_indices = {i for i in range(mention.start, mention.end)}
                if len(mention_indices & literal_indexes) == 0:
                    continue
            version_key = (mention.versionTitle,mention.language)
            if primary_version_key is None:
                # arbitrarily pick first version you come across
                primary_version_key = version_key
                primary_version, primary_lang = version_key
            mentions_by_passage[mention.ref][version_key] += [mention]
        # sort by position
        for ref, version_dict in mentions_by_passage.items():
            for version_key, mention_list in version_dict.items():
                version_dict[version_key].sort(key=lambda x: x.start)
        """
        Choose 'primary' version. Diff other versions against this.

        """
        out_rows = []
        common_issues = defaultdict(list)
        def get_rows_from_opcode(tag, i1, i2, j1, j2, a, b, a_text, b_text):
            if tag == 'equal': return []
            temp_rows = []
            if tag == 'replace':
                if i2 - i1 == 1 and j2 - j1 == 1:
                    temp_a = set(a[i1].id_matches)
                    temp_b = set(b[j1].id_matches)
                    if len(temp_a & temp_b) > 0:
                        # ambiguity. currently won't count as a difference
                        return []
                if with_replace:
                    temp_rows += [{
                        "Type": "Replace",
                        "Rabbi": ", ".join([x.id_matches[0] for x in a[i1:i2]]),
                        "Rabbi Snippet": " | ".join([self.get_snippet(a_text, x) for x in a[i1:i2]]),
                        "With Rabbi": ", ".join([x.id_matches[0] for x in b[j1:j2]]),
                        "With Rabbi Snippet": " | ".join([self.get_snippet(b_text, x) for x in b[j1:j2]]),
                        "Start": ", ".join([str(x.start) for x in a[i1:i2]]),
                        "End": ", ".join([str(x.end) for x in a[i1:i2]]),
                        "With Start": ", ".join([str(x.start) for x in b[j1:j2]]),
                        "With End": ", ".join([str(x.end) for x in b[j1:j2]]),
                    }]
                else:
                    temp_rows += get_rows_from_opcode('delete', i1, i2, j1, j1, a, b, a_text, b_text)
                    temp_rows += get_rows_from_opcode('insert', i1, i1, j1, j2, a, b, a_text, b_text)
            elif tag == 'delete':
                for i in range(i1, i2):

                    temp_rows += [{
                        "Type": "Extra",
                        "Rabbi": a[i].id_matches[0],
                        "Rabbi Snippet": self.get_snippet(a_text, a[i]),
                        "Start": a[i].start,
                        "End": a[i].end,
                    }]
            elif tag == 'insert':
                for i in range(j1, j2):
                    temp_rows += [{
                        "Type": "Missing",
                        "Rabbi": b[i].id_matches[0],
                        "Rabbi Snippet": self.get_snippet(b_text, b[i]),
                        "Start": b[i].start,
                        "End": b[i].end,
                    }]
            return temp_rows
   
        for ref, version_dict in tqdm(mentions_by_passage.items(), total=len(mentions_by_passage), desc='calc diff'):
            a_mentions = version_dict[primary_version_key]
            a_text = Ref(ref).text(primary_lang, vtitle=primary_version).text
            for version_key, b_mentions in version_dict.items():
                version, lang = version_key
                if version == "William Davidson Edition - Vocalized Aramaic":
                    continue
                if version_key == primary_version_key:
                    continue
                # do diff
                a_mention_ids = [tuple(x.id_matches) for x in a_mentions]
                b_mention_ids = [tuple(x.id_matches) for x in b_mentions]
                b_text = Ref(ref).text(lang, vtitle=version).text
                s = SequenceMatcher(None, a_mention_ids, b_mention_ids, False)
                codes = s.get_opcodes()
                for tag, i1, i2, j1, j2 in codes:
                    temp_rows = get_rows_from_opcode(tag, i1, i2, j1, j2, a_mentions, b_mentions, a_text, b_text)
                    for r in temp_rows:
                        r['Ref'] = ref
                        r['Version'] = primary_version if r['Type'] == 'Extra' else version
                        r['Language'] = primary_lang if r['Type'] == 'Extra' else lang
                        r['Rabbi Missing in Text'] = a_text if r['Type'] == 'Missing' else ''
                        r['URL'] = f"https://www.sefaria.org/{Ref(ref).url()}?v{r['Language']}={r['Version'].replace(' ', '_')}"
                        common_issues[(r['Type'], r['Rabbi'], r.get('With Rabbi', None))] += [r['Ref']]
                    out_rows += temp_rows
        with open(output_file, "w") as fout:
            c = csv.DictWriter(fout, ['Ref', 'Version', 'Language', 'Type', 'Rabbi', 'With Rabbi', 'Rabbi Snippet', 'Rabbi Missing in Text','With Rabbi Snippet', 'URL', 'Start', 'End', 'With Start', 'With End'])
            c.writeheader()
            c.writerows(out_rows)
        print("TOTAL MENTIONS", len(self.mentions))
        print("TOTAL MISTAKES", len(out_rows))
        print("PERC CORRECT", (len(self.mentions)-len(out_rows))/len(self.mentions))
        print("UNIQUE MISTAKES", len(common_issues))

        common_rows = []
        for i, ((t, r, w), v) in enumerate(sorted(common_issues.items(), key=lambda x: len(x[1]), reverse=True)):
            common_rows += [{
                "Action": t,
                "Rabbi": r,
                "Num": len(v),
                "With Rabbi": w or '',
                "Refs": ", ".join(v)
            }]
        with open(common_mistakes_output_file, 'w') as fout:
            c = csv.DictWriter(fout, ['Action', 'Rabbi', 'With Rabbi', 'Num', 'Refs'])
            c.writeheader()
            c.writerows(common_rows)

    def merge_rabbis_in_mentions(self, swap_file):
        """
        Just merge rabbis as they appear in mentions. Actual topics will be merged at a later step
        Swap file is an object where each key is a slug that should be changed to the value slug
        """
        with open(swap_file, 'r') as fin:
            swaps = json.load(fin)
        for mention in self.mentions:
            mention.id_matches = list({swaps.get(slug, slug) for slug in mention.id_matches})

    def export_named_entities(self, output_file):
        rows = []
        max_alt_title = 0
        for ne in self.named_entities:
            row = {
                "Slug": ne.slug,
                "Description": getattr(ne, "description", {}).get("en", "")
            }
            titles = ne.get_titles()
            if len(titles) > max_alt_title:
                max_alt_title = len(titles)
            for ititle, title in enumerate(titles):
                row[f"Title {ititle + 1}"] = title
            rows += [row]
        with open(output_file, "w") as fout:
            c = csv.DictWriter(fout, ['Slug', 'Description'] + [f'Title {i}' for i in range(1, max_alt_title+1)])
            c.writeheader()
            c.writerows(rows)
        

class LiteralTextWalker:

    def __init__(self):
        self.range_map = {}  # (versionTitle, language, tref) -> list of 2-tuples
    
    def walk(self, literal_regex, segment_text, en_tref, he_tref, version):
        self.range_map[(version.versionTitle, version.language, en_tref)] = self.get_literal_ranges(segment_text, literal_regex)

    @staticmethod
    def get_literal_ranges(text, literal_regex):
        return [m.span() for m in re.finditer(literal_regex, text)]

def get_literal_text_map(raw_literal_corpus):
    from functools import partial
    literal_walker = LiteralTextWalker()
    version_queries = CorpusManager.create_corpus_version_queries(raw_literal_corpus)
    for vquery in tqdm(version_queries, desc="get literal ranges"):
        version = Version().load({"title": vquery['title'], "language": vquery['language'], "versionTitle": vquery['versionTitle']})
        if version is None:
            # print("Version is None for", vquery['title'], vquery['language'], vquery['versionTitle'])
            continue
        version.walk_thru_contents(partial(literal_walker.walk, vquery['literalRegex']))
    
    literal_index_set_map = {}
    for key, temp_ranges in literal_walker.range_map.items():
        literal_indexes = set()
        for s, e in temp_ranges:
            literal_indexes |= {i for i in range(s, e)}
        literal_index_set_map[key] = literal_indexes
    return literal_index_set_map

if __name__ == "__main__":
    ner_file_prefix = "/home/nss/sefaria/datasets/ner/sefaria"
    corpus_manager = CorpusManager(
        "research/knowledge_graph/named_entity_recognition/ner_tagger_input_mishnah.json",
        f"{ner_file_prefix}/ner_output_mishnah.json",
        f"{ner_file_prefix}/html"
    )
    # corpus_manager.export_named_entities(f"{ner_file_prefix}/named_entities_export.csv")
    corpus_manager.tag_corpus()
    # corpus_manager.merge_rabbis_in_mentions(f"{ner_file_prefix}/swap_rabbis.json")
    corpus_manager.save_mentions()

    # corpus_manager.load_mentions()
    corpus_manager.generate_html_file()
    # corpus_manager.cross_validate_mentions_by_lang(f"{ner_file_prefix}/cross_validated_by_language.csv", f"{ner_file_prefix}/cross_validated_by_language_common_mistakes.csv", f"{ner_file_prefix}/cross_validated_by_language_ambiguities.csv")
    corpus_manager.cross_validate_mentions_by_lang_literal(f"{ner_file_prefix}/cross_validated_by_language.csv", f"{ner_file_prefix}/cross_validated_by_language_common_mistakes.csv", f"{ner_file_prefix}/cross_validated_by_language_ambiguities.csv", ("Mishnah Yomit by Dr. Joshua Kulp", "en"), with_replace=True)
"""
This file depends on first running
- find_missing_rabbis.convert_final_en_names_to_ner_tagger_input() which creates sperling_named_entities
- convert_sperling_data.convert_to_mentions_file() which converts 

"""
