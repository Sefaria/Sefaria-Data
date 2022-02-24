import django
django.setup()
from sefaria.model import *
import json
nes = json.load(open("../../../tetra/temp/ner.json", 'r'))
#nes = json.load(open("ner.json", 'r'))
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
