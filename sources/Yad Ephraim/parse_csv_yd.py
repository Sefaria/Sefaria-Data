#encoding=utf-8
import django
django.setup()
from sources.functions import *
from sefaria.model import *
import csv
if __name__ == "__main__":
    root = JaggedArrayNode()
    root.add_primary_titles("Yad Ephraim on Shulchan Arukh, Yoreh De'ah", u"יד אפרים על שלחן ערוך יורה דעה")
    root.key = "Yad Ephraim on Shulchan Arukh, Yoreh De'ah"
    root.add_structure(["Siman", "Comment"])
    index = {
        "schema": root.serialize(),
        "title": root.key,
        "dependence": "Commentary",
        "categories": ["Halakhah", "Shulchan Arukh", "Commentary"],
        "collective_title": "Yad Ephraim",
        "base_text_titles": ["Shulchan Arukh, Yoreh De'ah"],
        "base_text_mapping": None
    }
    post_index(index)
    text = {}
    links = []
    curr_siman = curr_seif = -1
    with open("yad ephraim yd.csv") as f:
        reader = csv.reader(f)
        for row in reader:
            siman, seif, seif_orig, comment = row
            comment = comment.replace("@11", "<b>").replace("@33", "</b>")
            if siman:
                curr_siman = getGematria(siman)
                if curr_siman not in text.keys():
                    text[curr_siman] = []
            text[curr_siman].append(comment)
            if seif:
                curr_seif = getGematria(seif.split()[-1])
            sa_ref = "Shulchan Arukh, Yoreh De'ah {}:{}".format(curr_siman, curr_seif)
            yad_ref = "{} {}:{}".format(root.key, curr_siman, len(text[curr_siman]))
            links.append({"refs": [sa_ref, yad_ref], "generated_by": "yad_ephraim", "type": "Commentary", "auto": True})
    text = convertDictToArray(text)
    text = {
        "text": text,
        "language": "he",
        "versionTitle": "Ashlei Ravrevei: Shulchan Aruch Yoreh Deah, Lemberg, 1888",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002084080"
    }
    
    post_text(root.key, text)
    post_link(links, server=SEFARIA_SERVER)