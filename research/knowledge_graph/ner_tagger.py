"""
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
import django, re, json, srsly, csv
django.setup()
from sefaria.model import *
from collections import defaultdict

class Mention:

    def __init__(self, start, end, mention, id_matches, ref, vtitle, lang):
        self.start = start
        self.end = end
        self.mention = mention
        self.id_matches = id_matches
        self.ref = ref
        self.vtitle = vtitle
        self.lang = lang

    def serialize(self):
        return {
            "start": self.start,
            "end": self.end,
            "mention": self.mention,
            "id_matches": self.id_matches,
            "ref": self.ref,
            "vtitle": self.vtitle,
            "lang": self.lang
        }

class AbstractNamedEntityRecognizer:
    """
    Generic NER classifier
    Subclasses implement specific ner strategies
    """
    def __init__(self, named_entities):
        raise Exception("AbstractNamedEntityRecognizer should not be instantiated. Instantiate a subclass.")

    def fit(self):
        pass

    def predict(self, text):
        """
        Tags `text` with named entities
        Returns list of `Mentions`
        """
        pass

class NaiveNamedEntityRecognizer(NERClassifier):

    def __init__(self, named_entities):
        pass

class EntityLinker:
    pass


class CorpusManager:

    def __init__(self, tagging_params_file, output_file):
        self.output_file = output_file
        self.named_entities = []
        self.mentions = []
        self.corpus_version_queries = []
        self.read_tagging_params_file(tagging_params_file)

    def read_tagging_params_file(self, tagging_params_file):
        with open(tagging_params_file, "r") as fin:
            tagging_params = json.load(tagging_params_file)
        self.named_entities = self.create_named_entities(tagging_params["namedEntities"])
        self.corpus_version_queries = self.create_corpus_version_queries(tagging_params["corpus"])

    def tag_corpus(self):
        for version_query in self.corpus_version_queries:
            pretaggedFile = version_query.get("pretaggedFile", None)
            if pretaggedFile is not None:
                pass  # TODO read Mentions from pretaggedFile
            else:
                version = Version(version_query)
                version.walk_thru_contents(self.recognize_named_entities_in_segment)

    def recognize_named_entities_in_segment(self, segment_text, en_tref, he_tref, version):
        pass

    @staticmethod
    def create_named_entities(raw_named_entities):
        named_entities = []
        for ne in raw_named_entities:
            if ne["idIsSlug"]:
                topic = Topic.init(ne["id"])
                if ne.get("getLeaves", False):
                    named_entities += topic.topics_by_link_type_recursively(only_leaves=True)
                else:
                    named_entities += [topic]
            else:
                topic = Topic({
                    "slug": ne["id"],
                    "titles": ne["manualTitles"]
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
                    temp_version_query["title"] = title
                    version_queries += [temp_version_query]
        return version_queries
