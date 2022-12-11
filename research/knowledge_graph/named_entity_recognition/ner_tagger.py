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
            "pretagOverrideNamedEntities": <Same format as namedEntities. these namedEntities will only be used on pretagged segments>
            "normalizers": {
                "en": [<STRING>], (list of normalizers to use. will be applied in this same order. normalizer keys can be found in data_utilities/normalizations.py in NormalizerComposer)
                "he": [<STRING>]
            },
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
from typing import Union, List
from sefaria.utils.hebrew import strip_cantillation
django.setup()
try:
    import re2 as re
    re.set_fallback_notification(re.FALLBACK_WARNING)
except ImportError:
    import re
import regex
from pathlib import Path
import argparse
from typing import Dict
from tqdm import tqdm
from functools import partial, reduce
from sefaria.model import *
from collections import defaultdict
from sefaria.helper.normalization import AbstractNormalizer, NormalizerComposer, NormalizerByLang

GERSHAYIM = '\u05F4'
REGEX_TITLE_CHUNK = 100

class NormalizerTools:
    b_replacements = [' ben ', ' bar ', ', son of ', ', the son of ', ' son of ', ' the son of ', ' Bar ', ' Ben ']
    b_token = ' b. '
    starting_replacements = ['Ben ', 'Bar ', 'The ']

    @classmethod
    def get_rabbi_regex(cls, rabbi):
        reg = rabbi.replace(cls.b_token, f"(?:{u'|'.join(re.escape(b) for b in cls.b_replacements)})")
        for starter in cls.starting_replacements:
            starter = re.escape(starter)
            reg = re.sub(f'^{starter}', f"(?:{starter.lower()}|{starter})", reg)
        return reg

    @classmethod
    def get_rabbi_expansions(cls, rabbi):
        from itertools import product
        expansions = [rabbi]
        for starter in cls.starting_replacements:
            if rabbi.startswith(starter):
                expansions += [rabbi[0].lower() + rabbi[1:]]
        if rabbi.startswith('Rabbi '):
            expansions += [rabbi.replace('Rabbi ', 'R. ')]
        for expansion in expansions:
            if cls.b_token not in expansion: continue
            # need to replace b_token with every combo of b_replacements
            # first element of cartesian_input is b_replacements
            cartesian_input = reduce(lambda a, b: a + [cls.b_replacements] + [[b]], expansion.split(cls.b_token), [])[1:]
            temp_expansions = [''.join(title) for title in product(*cartesian_input)]
            expansions += temp_expansions
        expansions = [strip_cantillation(expansion, True) for expansion in expansions]
        return expansions

    @staticmethod
    def include_trailing_nikkud(span, text):
        start, end = span
        nikkud_match = re.match("[\u0591-\u05bd\u05bf-\u05c5\u05c7]+", text[end:])
        return start, end if nikkud_match is None else (end + nikkud_match.end())

class Mention:

    def __init__(self, start=None, end=None, mention=None, id_matches=None, ref=None, versionTitle=None, language=None, prefix_span=None):
        self.start = start
        self.end = end
        self.mention = mention
        self.id_matches = id_matches
        self.ref = ref
        self.versionTitle = versionTitle
        self.language = language
        self.prefix_span = prefix_span
        self.is_nonliteral = False  # used for texts that include both literal and non-literal translations


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

    def get_mention_wo_prefix(self):
        if self.prefix_span is None: return self.mention
        p_start, p_end = self.prefix_span
        return self.mention[p_end-p_start:]

    @classmethod
    def load_ambiguous_map(cls):
        ambiguous_links = IntraTopicLinkSet({"linkType": "possibility-for"})
        cls.possibility_map = defaultdict(set)
        for l in ambiguous_links:
            cls.possibility_map[l.toTopic].add(l.fromTopic)
        
    @staticmethod
    def sort(m):
        return Ref(m.ref).order_id(), m.versionTitle, m.language, m.start, m.end

    def serialize(self, delete_keys=None):
        d = {
            "start": self.start,
            "end": self.end,
            "mention": self.mention,
            "id_matches": self.id_matches,
            "ref": self.ref,
            "versionTitle": self.versionTitle,
            "language": self.language,
            "prefix_span": self.prefix_span and list(self.prefix_span),
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
    def __init__(self, named_entities, normalizer: AbstractNormalizer, **kwargs):
        self.named_entities = named_entities
        self.normalizer = normalizer

    def fit(self):
        pass

    def predict(self, text):
        """
        Tags `text` with named entities
        Returns list of `Mentions`
        """
        pass

class NaiveNamedEntityRecognizer(AbstractNamedEntityRecognizer):
    word_breakers = r"|".join(re.escape(breaker) for breaker in ['.', ',', "'", '?', '!', '(', ')', '[', ']', '{', '}', ':', ';', '§', '<', '>', "'s", "׃", "׀", "־", "…"])

    def __init__(self, named_entities, normalizer: AbstractNormalizer, **kwargs):
        super().__init__(named_entities, normalizer)
        self.named_entity_regex_by_lang = {}
        self.lang_specific_params = kwargs.get('langSpecificParams', {})
        self.slugs_to_delete = set(kwargs.get('slugsToDelete', []))

    def fit(self):
        for lang in ("en", "he"):
            lang_params = self.lang_specific_params.get(lang, {})
            title_regs = []
            for ne in tqdm(self.named_entities, desc="fit ner"):
                if ne.slug in self.slugs_to_delete: continue
                for title in ne.get_titles(lang=lang, with_disambiguation=False):
                    title_regs += [re.escape(expansion) for expansion in NormalizerTools.get_rabbi_expansions(title)]
            title_regs.sort(key=lambda x: len(x), reverse=True)
            print(f"COMPILING {lang} REGEX using {len(title_regs)} titles. {len('|'.join(title_regs).encode('utf-8'))/1024} KBs")
            prefix_reg = lang_params.get('prefixRegex', None)
            self.named_entity_regex_by_lang[lang] = []
            for i in range(0, len(title_regs), REGEX_TITLE_CHUNK):
                title_regs_chunk = title_regs[i:i+REGEX_TITLE_CHUNK]
                regex_chunk = re.compile(fr"(?:(?:^|\s|{self.word_breakers})[\"{GERSHAYIM}]?(?P<prefix>{prefix_reg or ''}))(?P<ne>{'|'.join(title_regs_chunk)})(?=[\"{GERSHAYIM}]?(\s|{self.word_breakers}|$))")
                self.named_entity_regex_by_lang[lang] += [regex_chunk]
            # self.named_entity_regex_by_lang[lang] = re.compile(fr"(?:(?:^|\b){lang_params.get('prefixRegex', None) or ''})({'|'.join(title_regs)})(?:\b|$)")
    
    @staticmethod
    def filter_already_found_mentions(mentions, text, lang, pretagged_mentions=None):
        # can be generalized more. meant to avoid double linking things that are already linked
        # currnetly runs linker and skips named entities that overlap with linker results or pretagged mentions
        # however, retains mentions if they exactly overlap a pretagged mention because this is truly amibuous
        # TODO filters out 'citations' that are not in parentheses in Hebrew. This leads to us missing mentions like איוב כו'
        text = text.replace('\xa0', ' ')  # strange character
        unique_titles = set(library.get_titles_in_string(text, lang, True))
        all_reg = library.get_multi_title_regex_string(unique_titles, lang)
        reg = regex.compile(all_reg, regex.VERBOSE)

        already_found_indexes = set()
        already_found_mention_spans = set()
        for match in reg.finditer(text):
            if not Ref.is_ref(match.group(0)): continue
            already_found_indexes |= {i for i in range(match.start(), match.end())}
        if pretagged_mentions is not None:
            for mention in pretagged_mentions:
                already_found_mention_spans.add((mention.start, mention.end))
                already_found_indexes |= {i for i in range(mention.start, mention.end)}
        
        return list(filter(lambda m: len(already_found_indexes & set(range(m.start, m.end))) == 0 or (m.start, m.end) in already_found_mention_spans, mentions))

    def predict_segment(self, corpus_segment, pretagged_mentions=None):
        norm_text = self.normalizer.normalize(corpus_segment.text, lang=corpus_segment.language)
        mentions = []
        matched_indexes = set()
        for regex_chunk in self.named_entity_regex_by_lang[corpus_segment.language]:
            for match in regex_chunk.finditer(norm_text):
                # end = match.end(1)
                # if not (end == len(norm_text) or re.match(fr"(?:\s|{self.word_breakers}|$)", norm_text[end:end+2])):
                #     continue
                temp_matched_indexes = set(range(match.start('prefix'), match.end('ne')))
                if len(temp_matched_indexes & matched_indexes) != 0: continue
                matched_indexes |= temp_matched_indexes
                mentions += [Mention(match.start('prefix'), match.end('ne'), match.group('prefix') + match.group('ne'), prefix_span=match.span('prefix'), ref=corpus_segment.ref, versionTitle=corpus_segment.versionTitle, language=corpus_segment.language)]
        mention_indices = [(mention.start, mention.end) for mention in mentions]
        norm_map = self.normalizer.get_mapping_after_normalization(corpus_segment.text, lang=corpus_segment.language)
        mention_indices = self.normalizer.convert_normalized_indices_to_unnormalized_indices(mention_indices, norm_map)
        for mention, unnorm_span in zip(mentions, mention_indices):
            unnorm_start, unnorm_end = NormalizerTools.include_trailing_nikkud(unnorm_span, corpus_segment.text)
            unnorm_prefix_span = NormalizerTools.include_trailing_nikkud(self.normalizer.convert_normalized_indices_to_unnormalized_indices([mention.prefix_span], norm_map)[0], corpus_segment.text)
            mention.add_metadata(start=unnorm_start, end=unnorm_end, mention=corpus_segment.text[unnorm_start:unnorm_end], prefix_span=unnorm_prefix_span)
        mentions = self.filter_already_found_mentions(mentions, corpus_segment.text, corpus_segment.language, pretagged_mentions)
        return mentions

    def predict(self, corpus_segments, pretagged_mentions=None):
        mentions = []
        pretagged_mentions_by_segment = defaultdict(list)
        if pretagged_mentions is not None:
            for mention in pretagged_mentions:
                pretagged_mentions_by_segment[(mention.ref, mention.versionTitle, mention.language)] += [mention]
        if len(self.named_entities) == 0: return mentions  # most likely 0 in the case of pretagOverride
        for corpus_segment in tqdm(corpus_segments, desc="ner predict"):
            segment_pretagged_mentions = pretagged_mentions_by_segment[(corpus_segment.ref, corpus_segment.versionTitle, corpus_segment.language)]
            mentions += self.predict_segment(corpus_segment, segment_pretagged_mentions)
        return mentions

class AbstractEntityLinker:
    """
    Generic Entity Linker
    Subclasses implement specific el strategies
    """
    def __init__(self, named_entities, normalizer, **kwargs):
        self.named_entities = named_entities
        self.normalizer = normalizer

    def fit(self):
        pass

    def predict(self, text, mentions):
        """
        Links mentions in `text` to named entities
        Returns list of `Mentions` with id_matches
        """
        pass

class NaiveEntityLinker(AbstractEntityLinker):

    def __init__(self, named_entities, rules, normalizer, **kwargs):
        super().__init__(named_entities, normalizer)
        self.named_entity_table = defaultdict(dict)  # (lang, title) -> list of topics (dict now, but will be changed to list)
        self.rules = rules
        self.lang_specific_params = kwargs.get('langSpecificParams', {})
        self.titles_to_delete = kwargs.get('titlesToDelete', {})
    
        self.literal_text_map, self.has_nonliteral_version_set = get_literal_text_map(kwargs.get('nonLiteralCorpus', []))
        self.ambig_map = defaultdict(set)
        for link in IntraTopicLinkSet({"linkType": "possibility-for"}):
            self.ambig_map[link.toTopic].add(link.fromTopic)

    def should_skip_title(self, slug, title):
        return title in self.titles_to_delete.get(slug, [])

    def fit(self):
        for lang in ("en", "he"):
            for ne in tqdm(self.named_entities, desc="fit el"):
                for title in ne.get_titles(lang=lang, with_disambiguation=False):
                    if self.should_skip_title(ne.slug, title): continue
                    title_expansions = NormalizerTools.get_rabbi_expansions(title)
                    for expansion in title_expansions:
                        expansion = strip_cantillation(expansion, strip_vowels=True)
                        self.named_entity_table[(lang, expansion)][ne.slug] = ne
        for key, ne_dict in self.named_entity_table.items():
            self.named_entity_table[key] = sorted(ne_dict.values(), key=lambda x: getattr(x, 'numSources', 0), reverse=True)

    def expand_ambiguous_named_entities(self, ne_slug_list:list) -> list:
        ne_slug_set = set()
        for slug in ne_slug_list:
            ne_slug_set |= self.ambig_map.get(slug, {slug})
        return list(ne_slug_set)

    def combine_mentions(self, mentions: List[Mention]) -> List[Mention]:
        """
        We allow pretagged mentions and algo tagged mentions to exist if they exactly overlap
        We need to combine these into one ambiguous mention
        """
        mention_map = defaultdict(list)
        for m in mentions:
            mention_map[(m.ref, m.versionTitle, m.language, m.start, m.end)] += [m]
        out_mentions = []
        for m_list in mention_map.values():
            if len(m_list) == 0: continue  # unlikely to happen but technically possible
            combined_id_matches = list(reduce(lambda a, b: a | set(b.id_matches), m_list, set()))
            m_list[0].add_metadata(id_matches=combined_id_matches)
            out_mentions += [m_list[0]]
        return out_mentions

    def get_named_entity_ids_for_mention(self, mention: Mention) -> Union[list, None]:
        norm_mention = self.normalizer.normalize(mention.get_mention_wo_prefix(), lang=mention.language)
        ne_list = self.named_entity_table.get((mention.language, norm_mention), None)
        if ne_list is None: return
        return self.expand_ambiguous_named_entities([ne.slug for ne in ne_list])

    def predict(self, corpus_segments, mentions):
        grouped_by_ref = defaultdict(list)
        for mention in tqdm(mentions, desc="el predict"):
            grouped_by_ref[mention.ref] += [mention]

            # check if mention is in literal text
            has_nonliteral = (Ref(mention.ref).index.title, mention.versionTitle, mention.language) in self.has_nonliteral_version_set
            if has_nonliteral:
                # index is included in indexes that have nonliteral text
                temp_literal_indexes = self.literal_text_map.get((mention.versionTitle, mention.language, mention.ref), None)
                mention_indices = {i for i in range(mention.start, mention.end)}
                mention.is_nonliteral = temp_literal_indexes is None or len(temp_literal_indexes & mention_indices) == 0

            pretagged_id_matches = getattr(mention, 'id_matches', None)
            if pretagged_id_matches is None:
                ne_list = self.get_named_entity_ids_for_mention(mention)
                if ne_list is None:
                    print(f"No named entity matches '{self.normalizer.normalize(mention.get_mention_wo_prefix(), lang=mention.language)}'. Unnorm mention: '{mention.mention}', Ref: {mention.ref}")
                    mention.add_metadata(id_matches=[])
                    continue
                
                mention.add_metadata(id_matches=ne_list)
            else:
                mention.add_metadata(id_matches=self.expand_ambiguous_named_entities(mention.id_matches))
        out_mentions = []
        for tref, ref_mentions in grouped_by_ref.items():
            for rule in self.rules:
                rule.apply(ref_mentions)
            temp_mentions = list(filter(lambda mention: len(mention.id_matches) > 0, ref_mentions))  # remove any mentions that no longer have id_matches due to rules applied
            out_mentions += self.combine_mentions(temp_mentions)
        return out_mentions

class AbstractRule:

    def __init__(self, rule_dict):
        self.rule = rule_dict['rule']
        raw_named_entities = rule_dict.get('namedEntities', [])
        self.named_entities = None if raw_named_entities is None else set(raw_named_entities)
        self.mentions = rule_dict.get('mentions', None)
        if self.mentions is not None:
            self.mentions = set(self.mentions)

    def is_applicable(self, mention, mentions):
        return self.named_entities is None or len(set(mention.id_matches) & self.named_entities) > 0

    def apply(self, mentions):
        pass

    def on_applied_all(self, corpus_segments):
        """
        callback called after rule has been applied to all segments
        """
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

class NamedEntityNotInVersionDeleteRule(AbstractRule):
    """
    deletes mention if equivalent mention doesn't appear in specified version
    """
    def __init__(self, rule_dict):
        super(NamedEntityNotInVersionDeleteRule, self).__init__(rule_dict)
        self.applies_to_vtitle_set = {x['versionTitle'] for x in self.rule['appliesToVersions']}
        self.applies_to_lang_set = {x['language'] for x in self.rule['appliesToVersions']}
    
    def slug_applies(self, slug):
        return self.named_entities is None or slug in self.named_entities

    def apply(self, mentions):
        applicable_mentions = [mention for mention in mentions if self.is_applicable(mention, mentions)]
        compare_named_entities = set()
        for mention in mentions:
            if mention.versionTitle != self.rule['versionToCompare']['versionTitle'] or mention.language != self.rule['versionToCompare']['language'] or mention.is_nonliteral:
                continue
            compare_named_entities |= set(mention.id_matches)

        for mention in applicable_mentions:
            if mention.versionTitle not in self.applies_to_vtitle_set or mention.language not in self.applies_to_lang_set:
                continue
            mention.id_matches = [slug for slug in mention.id_matches if not self.slug_applies(slug) or slug in compare_named_entities]


class ManualCorrectionsRule(AbstractRule):

    def __init__(self, rule_dict):
        super().__init__(rule_dict)
        self.manual_corrections = srsly.read_json(self.rule['correctionsFile'])
        self.applies_to_dict = {}
        for correction in self.manual_corrections:
            self.applies_to_dict[self.get_applies_to_key(correction)] = correction

    @staticmethod
    def get_applies_to_key(mention):
        return (mention['ref'], mention['versionTitle'], mention['language'], mention['start'], mention['end'], mention['mention'])
    
    def is_applicable(self, mention, mentions):
        return self.get_applies_to_key(mention) in self.applies_to_dict

    def apply(self, mentions):
        mentions = filter(lambda m: self.is_applicable(m, mentions), mentions)
        for mention in mentions:
            correction = self.applies_to_dict[self.get_applies_to_key(mention)]
            if correction['correctionType'] == 'mistake':
                mention.id_matches = []
                correction['used'] = True
            elif correction['correctionType'] == 'manualIds':
                mention.id_matches = correction['id_matches']
                correction['used'] = True

    def on_applied_all(self, corpus_segments):
        if not self.rule.get("alertWhenMissing", False): return
        ref_version_set = {(s.ref, s.versionTitle, s.language) for s in corpus_segments}
        for correction in self.applies_to_dict.values():
            if (correction['ref'], correction['versionTitle'], correction['language']) not in ref_version_set: continue
            if not correction.get('used', False):
                print("UNUSED CORRECTION. Start and end chars may have shifted in text.")
                print(correction)

class RequiredOtherNamedEntitiesRule(AbstractRule):
    """
    deletes mention if all of "otherNamedEntities" dont appear in segment or any of "notOtherNamedEntities" appear
    """
    def __init__(self, rule_dict):
        super(RequiredOtherNamedEntitiesRule, self).__init__(rule_dict)
        self.other_named_entities = set(self.rule.get('otherNamedEntities', []))
        self.not_other_named_entities = set(self.rule.get('notOtherNamedEntities', []))

    def apply(self, mentions):
        applicable_mentions = [mention for mention in mentions if self.is_applicable(mention, mentions)]
        other_id_matches = reduce(lambda a, b: a | set(b.id_matches), mentions, set())
        if (len(other_id_matches & self.other_named_entities) == len(self.other_named_entities)) and \
            (len(other_id_matches & self.not_other_named_entities) == 0):
            # all other named entities appear in segment and none of "not other named entities" appear.
            # mentions can go unchanged
            return
        for mention in applicable_mentions:
            mention.id_matches = [slug for slug in mention.id_matches if slug not in self.named_entities]

class RuleFactory:

    key_rule_map = {
        "minRef": MinMaxRefRule,
        "maxRef": MinMaxRefRule,
        "exactRefs": ExactRefRule,
        "namedEntityNotInVersionDelete": NamedEntityNotInVersionDeleteRule,
        "manualCorrections": ManualCorrectionsRule,
        "requiredOtherNamedEntities": RequiredOtherNamedEntitiesRule,
    }

    @classmethod
    def create(cls, rule_dict):
        return cls.key_rule_map[rule_dict['rule']['id']](rule_dict)



class CorpusSegment:

    def __init__(self, is_pretagged, text, language, versionTitle, ref):
        self.is_pretagged = is_pretagged
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
        self.rules = []
        self.mentions = []
        self.corpus_version_queries = []
        self.corpus_segments = []
        self.read_tagging_params_file(tagging_params_file)

    def read_tagging_params_file(self, tagging_params_file):
        with open(tagging_params_file, "r") as fin:
            tagging_params = json.load(fin)
        self.normalizer = self.create_normalizer(tagging_params.get("normalizers", {}))
        self.named_entities                 = self.create_named_entities(tagging_params["namedEntities"])
        self.pretag_override_named_entities = self.create_named_entities(tagging_params.get("pretagOverrideNamedEntities", []))
        self.rules = self.create_rules(tagging_params.get("rules", []))
        self.ner                    = NaiveNamedEntityRecognizer(self.named_entities, self.normalizer, **tagging_params.get('namedEntityRecognizerParams', {}))
        self.pretag_override_ner = NaiveNamedEntityRecognizer(self.pretag_override_named_entities, self.normalizer, **tagging_params.get('namedEntityRecognizerParams', {}))
        self.el = NaiveEntityLinker(self.named_entities + self.pretag_override_named_entities, self.rules, self.normalizer, **tagging_params.get('namedEntityLinkerParams', {}))
        self.ner.fit()
        self.pretag_override_ner.fit()
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
                        for key in ('versionTitle', 'language'):
                            mention[key] = version_query.get(key) or mention[key]
                        pretagged_mentions += [Mention().add_metadata(**mention)]
            if pretagged_in_db:
                mention_links = RefTopicLinkSet({"linkType": "mention", "charLevelData.versionTitle": version_query['versionTitle'], "charLevelData.language": version_query['language']})
                for link in mention_links:
                    pretagged_mentions += [Mention().add_metadata_from_link(link)]
            query = {"title": version_query['title'], "language": version_query['language']}
            if version_query.get('versionTitle'):
                query['versionTitle'] = version_query['versionTitle']
            version_set = VersionSet(query).array()
            if len(version_set) == 0: continue
            version = version_set[0]
            is_pretagged = pretagged_file is not None or pretagged_in_db
            version.walk_thru_contents(partial(self.create_corpus_segment, is_pretagged, version_query['refFilter']))
        
        pretagged_corpus_segments, untagged_corpus_segments = self.partition_corpus_segments()
        ner_mentions = self.ner.predict(untagged_corpus_segments)
        pretag_override_ner_mentions = self.pretag_override_ner.predict(pretagged_corpus_segments, pretagged_mentions)
        ner_mentions += pretagged_mentions + pretag_override_ner_mentions
        el_mentions = self.el.predict(self.corpus_segments, ner_mentions)
        self.mentions = el_mentions
        self.deduplicate_mentions()
        self.validate_mention_matches_text()
        self.on_applied_all_rules()

    def on_applied_all_rules(self):
        for rule in self.rules:
            rule.on_applied_all(self.corpus_segments)

    def partition_corpus_segments(self):
        pretagged_corpus_segments, untagged_corpus_segments = [], []
        for x in self.corpus_segments:
            pretagged_corpus_segments.append(x) if x.is_pretagged else untagged_corpus_segments.append(x)
        return pretagged_corpus_segments, untagged_corpus_segments

    def deduplicate_mentions(self):
        self.mentions = list(set(self.mentions))

    def validate_mention_matches_text(self):
        """
        Sometimes mentions are created where the "mention" does not match text[start:end]
        This mostly happens in pretagged mentions, but running on entire mention
        """
        seg_map = {
            (seg.ref, seg.versionTitle, seg.language): seg for seg in self.corpus_segments
        }
        mismatched_matches = []
        def matches_text(m):
            nonlocal mismatched_matches
            key = (m.ref, m.versionTitle, m.language)
            if key not in seg_map: return False
            matches_text = m.mention == seg_map[key].text[m.start:m.end]
            if not matches_text:
                mismatched_matches += [m]
            return matches_text

        self.mentions = list(filter(matches_text, self.mentions))
        print("MISMATCHED", len(mismatched_matches))
        fixed_matches = []
        still_mismached_matches = []
        for m in mismatched_matches:
            max_abs_dist = 3
            key = (m.ref, m.versionTitle, m.language)
            if key not in seg_map: continue
            found_match = False
            num_punct = len(list(re.finditer(r'[\.,;—:?!״]', seg_map[key].text)))  # common cause of rabbis being offset is added punctuation
            for abs_offset in list(range(1, max(max_abs_dist, num_punct+3))) + [len('<big><strong></strong></big>')]:  # big strong was added into william davidson since last links were created
                if found_match: break
                for side in (1,-1):
                    offset = side*abs_offset
                    if m.start+offset < 0: continue
                    if m.mention == seg_map[key].text[m.start+offset:m.end+offset]:
                        m.start += offset
                        m.end += offset
                        fixed_matches += [m]
                        found_match = True
                        break
            if not found_match:
                still_mismached_matches += [m]

        print("FIXED", len(fixed_matches))
        for m in still_mismached_matches:
            print(m)
        self.mentions += fixed_matches

    def save_mentions(self):
        out = [mention.serialize() for mention in tqdm(self.mentions, desc="save mentions")]
        with open(self.mentions_output_file, "w") as fout:
            json.dump(out, fout, ensure_ascii=False, indent=2)

    def create_corpus_segment(self, is_pretagged, ref_filter, segment_text, en_tref, he_tref, version):
        if ref_filter is not None and en_tref not in ref_filter:
            return
        self.corpus_segments += [CorpusSegment(is_pretagged, segment_text, version.language, version.versionTitle, en_tref)]

    @staticmethod
    def create_rules(raw_rules):
        return [RuleFactory.create(raw_rule) for raw_rule in raw_rules]

    @staticmethod
    def create_normalizer(raw_normalizers):
        normalizers = {}
        for lang, step_keys in raw_normalizers.items():
            normalizers[lang] = NormalizerComposer(step_keys=step_keys)
        return NormalizerByLang(normalizers)

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
                    version_query_copy = temp_version_query.copy()
                    version_query_copy["title"] = title
                    version_query_copy["refFilter"] = item.get("refFilter", None)
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
            slug = slugs[0] if len(slugs) > 0 else ''
            other_slugs = slugs[1:]
            link = f"""<a href="https://www.sefaria.org/topics/{slug}" class="{"no-ids" if len(slug) == 0 else "missing" if ':' in slug else "found"}">{mention}</a>"""
            if len(other_slugs) > 0:
                link += f'''<sup>{", ".join([f"""<a href="https://www.sefaria.org/topics/{temp_slug}" class="{"missing" if ':' in temp_slug else "found"}">[{i+1}]</a>""" for i, temp_slug in enumerate(other_slugs)])}</sup>'''
            return link
        linked_text = re.sub(r"\$+", repl, dummy_text)
        return linked_text

    def generate_html_files_for_mentions(self, special_slug_set=None):
        mentions_by_ref = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        special_mentions_by_ref = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        text_by_version = defaultdict(dict)
        def collect_text(s, en_tref, he_tref, v: Version):
            nonlocal text_by_version
            text_by_version[v.title][(en_tref, v.versionTitle, v.language)] = s
        unique_versions = set()
        for mention in tqdm(self.mentions, desc="html group by ref"):
            title = Ref(mention.ref).index.title
            unique_versions.add((title, mention.versionTitle, mention.language))
            mentions_by_ref[title][mention.ref][f"{mention.versionTitle}|||{mention.language}"] += [mention]
            if special_slug_set is not None and len(special_slug_set & set(mention.id_matches)) > 0:
                temp_special_slugs = special_slug_set & set(mention.id_matches)
                for temp_slug in temp_special_slugs:
                    special_mentions_by_ref[temp_slug][mention.ref][f"{mention.versionTitle}|||{mention.language}"] += [mention]
        for title, vtitle, lang in unique_versions:
            version = Version().load({"title": title, "versionTitle": vtitle, "language": lang})
            version.walk_thru_contents(collect_text)
        for book, ref_dict in tqdm(mentions_by_ref.items(), desc="make html"):
            self.generate_html_file(book, ref_dict, text_by_version[book])
        for slug, ref_dict in tqdm(special_mentions_by_ref.items(), desc="make special html"):
            self.generate_html_file(slug, ref_dict)

    def generate_html_file(self, filename, ref_dict, text_by_version=None, annotations_by_ref=None):
        annotations_by_ref = annotations_by_ref or {}
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
                    .errors {
                        background-color: #ccc;
                        display: flex;
                        justify-content: space-between;
                    }
                    .error-span {
                        margin-right: 7px;
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
            if ref in annotations_by_ref:
                html += f"""
                <p class="errors">
                    {"".join([f"<span class='error-span'>{k}: {v}</span>" for k, v in annotations_by_ref[ref].items()])}
                </p>
                """
            sorted_versions = sorted(versions.items(), key=lambda x: x[0])
            for version_lang, temp_mentions in sorted_versions:
                vtitle, lang = version_lang.split('|||')
                if text_by_version is not None:
                    segment_text = text_by_version[(ref, vtitle, lang)]
                else:
                    segment_text = oref.text(lang, vtitle=vtitle).text
                linked_text = self.add_html_links(temp_mentions, segment_text)
                linked_text = TextChunk.strip_itags(linked_text)
                html += f"""
                    <p class="{lang}">{linked_text}</p>
                """
        html += """
            </body>
        </html>
        """
        with open(self.mentions_html_folder + f'/{filename}.html', "w") as fout:
            fout.write(html)

    def generate_html_file_for_refs(self, filename, limit_to_refs, annotations_by_ref=None):
        if len(self.mentions) == 0: self.load_mentions()
        mentions_by_ref = defaultdict(lambda: defaultdict(list))
        for mention in tqdm(self.mentions, desc="html group by ref"):
            if mention.ref not in limit_to_refs: continue
            mentions_by_ref[mention.ref][f"{mention.versionTitle}|||{mention.language}"] += [mention]
        self.generate_html_file(filename, mentions_by_ref, annotations_by_ref=annotations_by_ref)

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
                "Text 1": Ref(v[0]).text('he', "Guggenheimer (structured)").text
            }]
            for i in range(1, min(len(v), 6)):
                common_rows[-1][f'Ref {i}'] = v[i]
        with open(common_mistakes_output_file, 'w') as fout:
            c = csv.DictWriter(fout, ['Action', 'Rabbi', 'With Rabbi', 'Num', 'Text 1'] + [f'Ref {i}' for i in range(1, 6)])
            c.writeheader()
            c.writerows(common_rows)
        
        # output HTML file of segments with errors
        refs_with_diff = {row['Ref'] for row in out_rows}
        annotations_by_ref = {
            row["Ref"]: {"Type": row["Type"], "Name": row["Rabbi"], "With Name": row.get("With Rabbi", "")}
            for row in out_rows
        }
        self.generate_html_file_for_refs("Errors", refs_with_diff)

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

    def filter_cross_validation_by_topics(self, in_file, out_file, raw_named_entities):
        named_entity_slugs = {ne.slug for ne in CorpusManager.create_named_entities(raw_named_entities)}
        def filter_rows(row):
            if len(set(row['Rabbi'].split(', ')) & named_entity_slugs) > 0:
                return True
            if len(set(row['With Rabbi'].split(', ')) & named_entity_slugs) > 0:
                return True
            return False

        with open(in_file, 'r') as fin:
            cin = csv.DictReader(fin)
            rows = list(filter(filter_rows, cin))
            rows.sort(key=lambda x: Ref(x['Ref']).order_id())
        with open(out_file, 'w') as fout:
            cout = csv.DictWriter(fout, cin.fieldnames)
            cout.writeheader()
            cout.writerows(rows)

        # output HTML file of segments with errors
        refs_with_diff = {row['Ref'] for row in rows}
        annotations_by_ref = {
            row["Ref"]: {"Type": row["Type"], "Name": row["Rabbi"], "With Name": row.get("With Rabbi", "")}
            for row in rows
        }
        self.generate_html_file_for_refs("Filtered Errors", refs_with_diff, annotations_by_ref)
    
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
    has_nonliteral_version_set = set()
    for vquery in tqdm(version_queries, desc="get literal ranges"):
        query = {"title": vquery['title'], "language": vquery['language']}
        if vquery.get('versionTitle') is not None:
            query['versionTitle'] = vquery['versionTitle']
        version_set = VersionSet(query).array()  # load versionset in case versionTitle is None and you want top priority version
        if len(version_set) == 0:
            print("Version is None for", vquery['title'], vquery['language'], vquery['versionTitle'])
            continue
        version = version_set[0]
        version.walk_thru_contents(partial(literal_walker.walk, vquery['literalRegex']))
        has_nonliteral_version_set.add((vquery['title'], vquery['versionTitle'], vquery['language']))
    
    literal_index_set_map = {}
    for key, temp_ranges in literal_walker.range_map.items():
        literal_indexes = set()
        for s, e in temp_ranges:
            literal_indexes |= {i for i in range(s, e)}
        literal_index_set_map[key] = literal_indexes
    return literal_index_set_map, has_nonliteral_version_set

def compare_two_versions_ner_tagger_output(filea, fileb, ner_file_prefix, vtitle=None, lang=None):
    """
    Given 2 filenames, save 2 files; a_not_b.json and b_not_a.json
    """
    def get_set(filename):
        temp_set = {Mention().add_metadata(**m) for m in srsly.read_json(f'{ner_file_prefix}/{filename}')}
        if vtitle is None: return temp_set
        return set(filter(lambda m: m.versionTitle == vtitle and m.language == lang, temp_set))

    def save_set(temp_set, filename):
        j = [m.serialize() for m in sorted(temp_set, key=Mention.sort)]
        with open(filename, 'w') as fout:
            json.dump(j, fout, ensure_ascii=False, indent=2)

    a = get_set(filea)
    b = get_set(fileb)
    a_not_b = a.difference(b)
    b_not_a = b.difference(a)
    print("A not B", len(a_not_b))
    print("B not A", len(b_not_a))
    save_set(a_not_b, f'{ner_file_prefix}/a_not_b.json')
    save_set(b_not_a, f'{ner_file_prefix}/b_not_a.json')


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", dest="config_filename", help="Config filename. Existing configs exist in `ner_input` directory")
    parser.add_argument("-o", "--output", dest="output_directory", help="Output directory where various output files will be saved.")
    parser.add_argument("-t", "--tag-entities", dest="tag_entities", help="Tag entities?", default=False, action='store_true')
    parser.add_argument("--primary-evaluation-language", dest="evaluation_language", help="For evaluation, the primary language you want to evaluate results against. Should be language with the best and most complete results.")
    parser.add_argument("--primary-evaluation-version-title", dest="evaluation_version_title", help="For evaluation, the primary version title you want to evaluate results against. Should be the version title with the best and most complete results.")
    """
    Example commands for running
    - Mishnah
        python ner_tagger.py -c ner_input/ner_tagger_input_mishnah.json -o output/mishnah -t --primary-evaluation-language en --primary-evaluation-version-title "Mishnah Yomit by Dr. Joshua Kulp"
    - Bavli
        python ner_tagger.py -c ner_input/ner_tagger_input_bavli.json -o output/bavli -t --primary-evaluation-language he --primary-evaluation-version-title "William Davidson Edition - Aramaic"
    - Jerusalem Talmud
        python ner_tagger.py -c ner_input/ner_tagger_input_yerushalmi.json -o output/yerushalmi -t --primary-evaluation-language en --primary-evaluation-version-title "The Jerusalem Talmud, translation and commentary by Heinrich W. Guggenheimer. Berlin, De Gruyter, 1999-2015"
    """
    return parser


if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()
    Path(args.output_directory + "/html").mkdir(parents=True, exist_ok=True)
    corpus_manager = CorpusManager(
        args.config_filename,
        f"{args.output_directory}/mentions.json",
        f"{args.output_directory}/html"
    )
    if args.tag_entities:
        corpus_manager.tag_corpus()
        corpus_manager.save_mentions()
    else:
        corpus_manager.load_mentions()
    corpus_manager.generate_html_files_for_mentions(special_slug_set={'rabi', 'rav'})
    corpus_manager.cross_validate_mentions_by_lang_literal(f"{args.output_directory}/cross_validated_by_language.csv", f"{args.output_directory}/cross_validated_by_language_common_mistakes.csv", f"{args.output_directory}/cross_validated_by_language_ambiguities.csv", (args.evaluation_version_title, args.evaluation_language), with_replace=True)
    corpus_manager.filter_cross_validation_by_topics(f"{args.output_directory}/cross_validated_by_language.csv", f"{args.output_directory}/cross_validated_by_language_filtered.csv", [{
            "id": "biblical-figures",
            "idIsSlug": True,
            "getLeaves": True
        }
    ])
    #     compare_two_versions_ner_tagger_output('ner_output_talmud.json', 'ner_output_talmud_word_breakers.json', ner_file_prefix)
    #     compare_two_versions_ner_tagger_output('ner_output_mishnah.json', 'sperling_mentions_mishnah.json', ner_file_prefix, 'Torat Emet 357', 'he')

"""
This file depends on first running
- find_missing_rabbis.convert_final_en_names_to_ner_tagger_input() which creates sperling_named_entities
- convert_sperling_data.convert_to_mentions_file() which converts 

Current results: both talmud and mishnah are 97.4% accurate

TODO add NamedEntityInVersionAddRule which checks if named entity is in reference version.
If so, search for named entity in target versions regardless of if corpus segment is pretagged. 
This rule should ideally only run at named entity recognizer stage
"""
