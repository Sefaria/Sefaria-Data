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

folder = u'./Maaseh Rokeah'

### Parse the individual files
chapter_regex = ur"@55\u05e4(?P<gim>.*)@66"
halacha_regex = ur"@77(?P<gim>.*)@88"


def clean_segments(segments):
    def clean_segment(seg):
        seg = re.sub(ur"(.*)@03\s*", ur"\1", seg)
        seg = seg.replace(u"@05", u"<b>")\
            .replace(u"@06", u"</b>")\
            .replace(u"@01", u"<b>")\
            .replace(u"@02", u"</b>")\
            .replace(u"@03", u"<br/>")\
            .replace(u"@79", u"<b>") \
            .replace(u"@89", u"</b>")\
            .strip()
        return seg

    return [clean_segment(s) for s in segments if clean_segment(s)]

processed = {}
sefarim = set()
regexes = [chapter_regex, halacha_regex]
for the_file in [x for x in os.listdir(folder) if "xml" not in x]:
    name = the_file.replace(".txt", "").split("-")[2]
    sefer = the_file.split("-")[1]

    if sefer == u"ספר קרבנות":
        sefer = u"ספר קורבנות"
    if sefer == u"ספר קנין":
        sefer = u"ספר קניין"

    sefarim.add(sefer)
    if name in processed:
        # Skip second version of Nashim
        continue
    file_path = os.path.join(folder, the_file)
    with codecs.open(file_path, "r", "utf-8") as infile:
        j = file_to_ja_g(3, infile, regexes, clean_segments, gimatria=True)
        processed[name] = {"cat": sefer, "text": j.array()}


        ja_to_xml(j.array(), ["Chapter","Halacha","Comment"], file_path.replace("txt","xml"))


processed[u"הלכות תפילה וברכת כהנים"] = {
    "cat": processed[u"הלכות תפלה"]["cat"],
    "text": processed[u"הלכות תפלה"]["text"][:13] + processed[u"הלכות נשיאת כפים"]["text"][13:]
}
del processed[u"הלכות תפלה"]
del processed[u"הלכות נשיאת כפים"]


processed[u"הלכות תפילין ומזוזה וספר תורה"] = {
    "cat": processed[u"הלכות תפילין"]["cat"],
    "text": processed[u"הלכות תפילין"]["text"][:4] + processed[u"הלכות מזוזה"]["text"][4:6] + processed[u"הלכות ספר תורה"]["text"][6:]
}
del processed[u"הלכות תפילין"]
del processed[u"הלכות מזוזה"]
del processed[u"הלכות ספר תורה"]


hebrew_titles = [u'\u05d4\u05dc\u05db\u05d5\u05ea \u05e2\u05e8\u05db\u05d9\u05df \u05d5\u05d7\u05e8\u05de\u05d9\u05df',
 u'\u05d4\u05dc\u05db\u05d5\u05ea \u05de\u05e2\u05e9\u05e8',
 u'\u05d4\u05dc\u05db\u05d5\u05ea \u05d1\u05db\u05d5\u05e8\u05d9\u05dd',
 u'\u05d4\u05dc\u05db\u05d5\u05ea \u05e2\u05d1\u05d5\u05d3\u05ea \u05db\u05d5\u05db\u05d1\u05d9\u05dd',
 u'\u05d4\u05dc\u05db\u05d5\u05ea \u05db\u05dc\u05d9 \u05d4\u05de\u05e7\u05d3\u05e9',
 u'\u05d4\u05dc\u05db\u05d5\u05ea \u05d0\u05d9\u05e1\u05d5\u05e8\u05d9 \u05de\u05d6\u05d1\u05d7',
 u'\u05d4\u05dc\u05db\u05d5\u05ea \u05ea\u05de\u05d9\u05d3\u05d9\u05df \u05d5\u05de\u05d5\u05e1\u05e4\u05d9\u05df',
 u'\u05d4\u05dc\u05db\u05d5\u05ea \u05d8\u05d5\u05de\u05d0\u05ea \u05d0\u05d5\u05db\u05dc\u05d9\u05df',
 u'\u05d4\u05dc\u05db\u05d5\u05ea \u05e8\u05d5\u05e6\u05d7 \u05d5\u05e9\u05de\u05d9\u05e8\u05ea \u05d4\u05e0\u05e4\u05e9',
 u'\u05d4\u05dc\u05db\u05d5\u05ea \u05d6\u05db\u05d9\u05d4 \u05d5\u05de\u05ea\u05e0\u05d4']

english_titles = ['Mishneh_Torah,_Appraisals_and_Devoted_Property',
 'Mishneh_Torah,_Tithes',
 'Mishneh_Torah,_First_Fruits_and_other_Gifts_to_Priests_Outside_the_Sanctuary',
 'Mishneh_Torah,_Foreign_Worship_and_Customs_of_the_Nations',
 'Mishneh_Torah,_Vessels_of_the_Sanctuary_and_Those_who_Serve_Therein',
 'Mishneh_Torah,_Things_Forbidden_on_the_Altar',
 'Mishneh_Torah,_Daily_Offerings_and_Additional_Offerings',
 'Mishneh_Torah,_Defilement_of_Foods',
 'Mishneh_Torah,_Murderer_and_the_Preservation_of_Life',
 'Mishneh_Torah,_Ownerless_Property_and_Gifts']

mapping = dict(zip(hebrew_titles, english_titles))

# Make a term
# Maaseh Rokeah
# מעשה רוקח
add_term("Maaseh Rokeach", u"מעשה רקח", "commentary_works")

# Make categories
http_request(SEFARIA_SERVER + "/api/category", body={'apikey': API_KEY}, json_payload={"path":["Halakhah","Mishneh Torah","Commentary","Maaseh Rokeach"], "sharedTitle": "Maaseh Rokeach"}, method="POST")
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
