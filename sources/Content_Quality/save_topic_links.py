import django
django.setup()
from sefaria.model import *
import json
#nes = json.load(open("../../../tetra/temp/ner_output_tetragramatton.json", 'r'))
nes = json.load(open("ner.json", 'r'))
for ne in nes:
    mention_link = {
        "toTopic": "the-tetragrammaton",
        "linkType": "mention",
        "dataSource": "sefaria",
        "class": "refTopic",
        "is_sheet": False,
        "ref": ne["ref"],
        "expandedRefs": [ne["ref"]],
        "charLevelData": {
            "startChar": ne["start"],
            "endChar": ne["end"],
            "versionTitle": ne["versionTitle"],
            "language": ne["language"],
            "text": ne["mention"]
        }
    }
    RefTopicLink(mention_link).save()



    required_attrs = [
        "language",
        "title",    # FK to Index.title
        "versionSource",
        "versionTitle",
        "chapter"  # required.  change to "content"?
    ]

    """
    Regarding the strange naming of the parameters versionTitleInHebrew and versionNotesInHebrew: These names were
    chosen to avoid naming conflicts and ambiguity on the TextAPI. See TextFamily for more details.
    """
    optional_attrs = [
        "status",
        "priority",
        "license",
        "versionNotes",
        "digitizedBySefaria",
        "method",
        "heversionSource",  # bad data?
        "versionUrl",  # bad data?
        "versionTitleInHebrew",  # stores the Hebrew translation of the versionTitle
        "versionNotesInHebrew",  # stores VersionNotes in Hebrew
        "shortVersionTitle",
        "shortVersionTitleInHebrew",
        "extendedNotes",
        "extendedNotesHebrew",
        "purchaseInformationImage",
        "purchaseInformationURL",
        "hasManuallyWrappedRefs",  # true for texts where refs were manually wrapped in a-tags. no need to run linker at run-time.
    ]

vs = VersionSet({"versionTitle": "The Five Books of Moses, by Everett Fox"})
for v in vs:
    print(v)
    v.versionTitle = "The Five Books of Moses, by Everett Fox. New York, Schocken Books, 1995"
    v.shortVersionTitle = "The Five Books of Moses, by Everett Fox"
    v.purchaseInformationImage = "https://images-na.ssl-images-amazon.com/images/I/41mR7aOmNyL._SX350_BO1,204,203,200_.jpg"
    v.purchaseInformationURL = "https://www.amazon.com/Five-Books-Moses-Leviticus-Deuteronomy/dp/0805211195"
    v.versionSource = "https://www.nli.org.il/he/books/NNL_ALEPH001730367/NLI"