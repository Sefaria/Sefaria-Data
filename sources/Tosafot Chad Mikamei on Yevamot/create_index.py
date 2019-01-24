#encoding=utf-8
import django
django.setup()
from sefaria.model import *
from sources.functions import *
#1. get daf
#2. if we already have daf, increment count of segment, otherwise segment is 1;
text = {}
chad_ref = ""
links = []
add_term("Tosafot Chad Mikamei", u"תוספות חד מקמאי", server=SEFARIA_SERVER)
with open("final input.csv") as f:
    for line in f:
        ref, line_text = line.split(",", 1)
        line_text = line_text.decode('utf-8')
        line_text = line_text.replace(u'""', u'"')
        if line_text[0] == u'"':
            line_text = line_text[1:]
        if line_text[-3] == u'"':
            line_text = line_text[:-3]
        sefaria_ref = Ref(ref)
        if sefaria_ref.sections[0] not in text.keys():
            text[sefaria_ref.sections[0]] = []
        text[sefaria_ref.sections[0]].append(line_text)
        segment = len(text[sefaria_ref.sections[0]])
        chad_ref = u"Tosafot Chad Mikamei on Yevamot {}:{}".format(AddressTalmud.toStr("en", sefaria_ref.sections[0]), segment)
        link = {
            "refs": [chad_ref, ref],
            "auto": True,
            "type": "Commentary",
            "generated_by": "tos_chad_mikamei"
        }
        links.append(link)

root = JaggedArrayNode()
root.add_primary_titles("Tosafot Chad Mikamei on Yevamot", u"תוספות חד מקמאי על יבמות")
root.add_structure(["Daf", "Paragraph"], address_types=["Talmud", "Integer"])
root.validate()
index = {
    "title": "Tosafot Chad Mikamei on Yevamot",
    "schema": root.serialize(),
    "categories": ["Talmud", "Bavli", "Commentary"],
    "base_text_titles": ["Yevamot"],
    "dependence": "Commentary",
    "collective_title": "Tosafot Chad Mikamei"
}
post_index(index, server=SEFARIA_SERVER)
send_text = {
    "text": convertDictToArray(text),
    "versionTitle": "Tosafot Chad Mikamei Vilna Edition",
    "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
    "language": "he"
}
post_text("Tosafot Chad Mikamei on Yevamot", send_text, server=SEFARIA_SERVER)
post_link(links, server=SEFARIA_SERVER)