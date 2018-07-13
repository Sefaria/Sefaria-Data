# -*- coding: utf-8 -*-

import os
import codecs
import re

from sefaria.model import *
from sources.functions import http_request, add_term, post_index, post_text
from data_utilities.util import file_to_ja_g, ja_to_xml
from sources.local_settings import SEFARIA_SERVER, API_KEY

# @55 / @66 - chapter
# @77 / @88 - halacha
# @05 Starts dibur hamatchil - may be multiple before @06
# @06 Ends dibur hamatchil, begins comment body
# @03 End comment paragraph. (May be multiple in one comment)
# @01 begins bold
# @02 ends bold

#         clean_50s = re.compile(ur"@05([^6]*)@06")
#         split_pattern = re.compile(ur"(\s*@(?:55|77)" + u"(?:[^@]+)" + u"@(?:66|88)\s*)")

folder = u'./Zemanim Output'

### Parse the individual files
chapter_regex = ur"@55\u05e4(?P<gim>.*)@66"
halacha_regex = ur"@77(?P<gim>.*)@88"


def clean_segments(segments):
    def clean_segment(seg):
        seg = re.sub(ur"(.*)@03\s*", ur"\1", seg)
        seg = seg.replace(u"@05", u"<b>") \
            .replace(u"@04", u"<b>")\
            .replace(u"@06", u"</b>")\
            .replace(u"@01", u"<b>")\
            .replace(u"@02",u"</b>") \
            .replace(u"@79", u"<b>") \
            .replace(u"@89", u"</b>") \
            .replace(u"@03", u"<br/>")\
            .replace(u"@99", u" ")\
            .strip()
        return seg

    return [clean_segment(s) for s in segments if clean_segment(s)]

processed = {}
sefarim = set()
regexes = [chapter_regex, halacha_regex]
for the_file in [x for x in os.listdir(folder) if "xml" not in x]:
    name = the_file.replace(".txt", "").split("-")[2]
    sefer = the_file.split("-")[1]

    sefarim.add(sefer)
    if name in processed:
        # Skip second version of Nashim
        continue
    file_path = os.path.join(folder, the_file)
    with codecs.open(file_path, "r", "utf-8") as infile:
        j = file_to_ja_g(3, infile, regexes, clean_segments, gimatria=True)
        processed[name] = {"cat": sefer, "text": j.array()}


        ja_to_xml(j.array(), ["Chapter","Halacha","Comment"], file_path.replace("txt","xml"))

processed[u"הלכות שופר וסוכה ולולב"] = {
    "cat": processed[u"הלכות שופר"]["cat"],
    "text": processed[u"הלכות שופר"]["text"][:3] + processed[u"הלכות סוכה"]["text"][3:6] + processed[u"הלכות לולב"]["text"][6:]
}
del processed[u"הלכות שופר"]
del processed[u"הלכות סוכה"]
del processed[u"הלכות לולב"]

processed[u"הלכות מגילה וחנוכה"] = {
    "cat": processed[u"הלכות מגילה"]["cat"],
    "text": processed[u"הלכות מגילה"]["text"][:2] + processed[u"הלכות חנוכה"]["text"][2:]
}
del processed[u"הלכות מגילה"]
del processed[u"הלכות חנוכה"]

for name, data in processed.iteritems():
    full_name = u"משנה תורה, " + name
    if not Ref.is_ref(full_name):
        print full_name

del processed[u"[בנוסח ההגדה]"]

hebrew_titles = [u"הלכות יום טוב"]
english_titles = ["Mishneh_Torah,_Rest_on_a_Holiday"]
mapping = dict(zip(hebrew_titles, english_titles))

# Make a term
# Maaseh Rokeach
# מעשה רקח
# add_term("Maaseh Rokeach", u"מעשה רקח", "commentary_works")

# Make categories
for sefer in sefarim:
    t = Term().load({"titles.text": sefer})
    if not isinstance(t, Term):
        print u"ARGGG! {}".format(sefer)

    http_request(SEFARIA_SERVER + "/api/category", body={'apikey': API_KEY},
                 json_payload={"path": ["Halakhah", "Mishneh Torah", "Commentary", "Maaseh Rokeach", t.get_primary_title("en")],
                               "sharedTitle": t.get_primary_title("en")}, method="POST")


for name, data in processed.iteritems():
    full_name = u"משנה תורה, " + name
    if not Ref.is_ref(full_name):
        full_name = mapping[name]
    r = Ref(full_name)
    print r.normal()
    short_base_title = r.normal().replace("Mishneh Torah, ", "")

    en_title = "Maaseh Rokeach on " + short_base_title
    he_title = u"מעשה רקח על " + name

    j = JaggedArrayNode()
    j.add_primary_titles(en_title, he_title)
    j.add_structure(["Chapter", "Halacha", "Comment"])

    index_json = {
        "title": en_title,
        "categories": ["Halakhah", "Mishneh Torah", "Commentary", "Maaseh Rokeach"] + [Term().load({"titles.text": data["cat"]}).get_primary_title("en")],
        "schema": j.serialize(),
        "dependence": "Commentary",
        "base_text_titles": [r.normal()],
        "base_text_mapping": "many_to_one",
        "collective_title": "Maaseh Rokeach"
    }

    post_index(index_json)

    version_json = {
        "versionTitle": "Friedberg Edition",
        "versionSource": "https://fjms.genizah.org/",
        "language": "he",
        "text": data["text"]
    }

    post_text(en_title, version_json, index_count="on")
