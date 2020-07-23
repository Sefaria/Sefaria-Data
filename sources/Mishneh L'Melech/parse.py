# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from sources.functions import *
from sefaria.model import *
from sefaria.helper.schema import *
import bleach
import os
import re
curr_perek = 0
curr_halacha = 0
curr_hilchot = ""
text = {}
for f in os.listdir("."):
    if f.endswith(".txt"):
        major_division = f.split()[0].replace('קרבנות', 'קורבנות').replace('קנין', 'קניין')
        text[major_division] = {}
        print(f)
        lines = list(open(f))
        for line_n, line in enumerate(lines):
            if len(line.strip()) < 2:
                continue
            orig = line
            line = line.replace("\n", " ")
            hilchot = re.search("\$(.*?)\$", line)
            halacha = re.search("@EE(.*?)@FF", line)
            perek = re.search("\#(.*?)\#", line)
            if hilchot:
                curr_hilchot = hilchot.group(1).replace('הלכות בכורים', 'הלכות ביכורים ושאר מתנות כהונה שבגבולין').replace('הלכות מעשר', 'הלכות מעשרות')
                curr_hilchot = curr_hilchot.replace('הלכות ערכין וחרמין', 'הלכות ערכים וחרמין').replace('הלכות מלכים', 'הלכות מלכים ומלחמות')
                curr_hilchot = curr_hilchot.replace('הלכות עבודת כוכבים', 'הלכות עבודה זרה וחוקות הגויים').replace('הלכות ביאת המקדש', 'הלכות ביאת מקדש')
                curr_hilchot = curr_hilchot.replace('הלכות איסורי מזבח', 'הלכות איסורי המזבח').replace('הלכות תמידין ומוספין', 'הלכות תמידים ומוספין')
                curr_hilchot = curr_hilchot.replace('הלכות זכיה ומתנה', 'הלכות זכייה ומתנה').replace('הלכות שאלה ופקדון', 'הלכות שאלה ופיקדון')
                curr_hilchot = curr_hilchot.replace('הלכות כלי המקדש והעובדים בו', 'הלכות כלי המקדש והעובדין בו')
                curr_hilchot = curr_hilchot.replace('הלכות מלוה ולוה', 'הלכות מלווה ולווה')
                curr_hilchot = curr_hilchot.replace('הלכות טומאת אוכלין', 'הלכות טומאת אוכלים')
                curr_hilchot = curr_hilchot.replace('הלכות מעשרות שני ונטע רבעי', 'הלכות מעשר שני ונטע רבעי')
                curr_hilchot = curr_hilchot.replace('הלכות נשיאת כפים', 'הלכות תפילה וברכת כהנים')
                #curr_hilchot = curr_hilchot.replace('הלכות נשיאת כפים', '')
                curr_halacha = 0
                curr_perek = 0
                relevant = "הלכות תשובה"
                text[major_division][curr_hilchot] = {}
            elif halacha:
                halacha = halacha.group(1)
                if halacha != 'שם':
                    curr_halacha = getGematria(halacha.split()[-1])
                    assert curr_perek > 0
                    assert curr_halacha > 0
                    text[major_division][curr_hilchot][curr_perek][curr_halacha] = ""
            elif perek:
                perek = perek.group(1)
                curr_perek = getGematria(perek.split()[-1])
                text[major_division][curr_hilchot][curr_perek] = {}
                curr_halacha = 0
            else:
                text[major_division][curr_hilchot][curr_perek][curr_halacha] += line

for major_division in text.keys():
    for curr_hilchot in text[major_division]:
        for curr_perek in text[major_division][curr_hilchot]:
            for curr_halacha in text[major_division][curr_hilchot][curr_perek]:
                line = text[major_division][curr_hilchot][curr_perek][curr_halacha]
                line = re.sub("[@J{]{3,4}(.*?)}@LL", "NEW<b>\g<1></b>", line)
                line = re.sub("@GG(.*?)@HH", "<br/><b>\g<1></b>", line)
                line = re.sub("[{\}\@\d|A-Z]{1,}", "", line)
                if line.startswith("NEW"):
                    line = line.replace("NEW", "", 1)
                line = line.replace("\n", " ").replace("  ", " ")
                text[major_division][curr_hilchot][curr_perek][curr_halacha] = line.split("NEW")

                # if curr_halacha > 0 and curr_perek > 0:
                #     if "@JJ" in line:
                #         line = re.sub("^[@J{]{3,4}(.*?)}@LL", "<b>\g<1></b>", line)
                #         line = re.sub("[{\}\@\d|A-Z]{1,}", "", line)
                #         if ("<b>" in line and "</b>" not in line) or ("<b>" not in line and "</b>" in line):
                #             line = line.replace("<b>", "").replace("</b>", "")
                #         text[major_division][curr_hilchot][curr_perek][curr_halacha].append(line)
                #     else:
                #         line = re.sub("@GG(.*?)@HH", "<br/><b>\g<1></b>", line)
                #         line = re.sub("[{\}\@\d|A-Z]{1,}", "", line)
                #         if text[major_division][curr_hilchot][curr_perek][curr_halacha] == []:
                #             text[major_division][curr_hilchot][curr_perek][curr_halacha].append("")
                #         text[major_division][curr_hilchot][curr_perek][curr_halacha][-1] += line
                # else:
                #     print("Perek {} Halacha {} found at line {}".format(curr_perek, curr_halacha, line))
t = Term()
t.name = "Mishneh LaMelech"
# t.add_primary_titles(t.name, u"משנה למלך")
# t.save()
# c = Category()
# c.add_shared_term(t.name)
# c.path = "Halakhah", "Mishneh Torah", "Commentary", "Mishneh LaMelech"
# c.save()
go = True
indices = """Mishneh LaMelech on Mishneh Torah, Divorce
Mishneh LaMelech on Mishneh Torah, Virgin Maiden
Mishneh LaMelech on Mishneh Torah, Forbidden Intercourse
Mishneh LaMelech on Mishneh Torah, Sacrificial Procedure
Mishneh LaMelech on Mishneh Torah, Creditor and Debtor
Mishneh LaMelech on Mishneh Torah, Marriage""".splitlines()
for major_division in text.keys():

    en_major_division = Term().load({"titles.text": u"ספר {}".format(major_division)}).get_titles('en')[0]
    print(en_major_division)
    for hilchot in text[major_division]:
        full_name = u"משנה תורה, {}".format(hilchot)
        try:
            en_full_name = library.get_index(full_name).title
        except:
            print(major_division)
            print(full_name)
            print()
            continue
        if not go:
            continue
        root = JaggedArrayNode()
        if "Mishneh LaMelech on {}".format(en_full_name) in indices:
            root.add_primary_titles("Mishneh LaMelech on {}".format(en_full_name), u"משנה למלך על {}".format(full_name))
            root.add_structure(["Chapter", "Halakhah", "Paragraph"])
            root.validate()
            index = {
                "title": "Mishneh LaMelech on {}".format(en_full_name),
                "schema": root.serialize(),
                "categories": ["Halakhah", "Mishneh Torah", "Commentary", "Mishneh LaMelech", en_major_division],
                "dependence": "Commentary",
                "base_text_titles": [en_full_name],
                "base_text_mapping": "many_to_one",
                "collective_title": "Mishneh LaMelech"
            }
            add_category(en_major_division, index["categories"], server="https://www.sefaria.org")
            post_index(index, server="https://www.sefaria.org")
            for perek in text[major_division][hilchot]:
                text[major_division][hilchot][perek] = convertDictToArray(text[major_division][hilchot][perek])
            text[major_division][hilchot] = convertDictToArray(text[major_division][hilchot])
            send_text = {
                "text": text[major_division][hilchot],
                "language": "he",
                "versionTitle": "Warsaw, 1881",
                "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH001763900/NLI"
            }
            post_text("Mishneh LaMelech on {}".format(en_full_name), send_text, index_count="on", server="https://www.sefaria.org")

#         arr = """Hiring
# Creditor and Debtor
# Slaves
# Other Sources of Defilement
# Offerings for Unintentional Transgressions
# The Chosen Temple
# Sacrificial Procedure
# Heave Offerings
# Second Tithes and Fourth Year's Fruits""".splitlines()
#         arr = ["Mishneh Torah, " + el for el in arr]
#         if en_full_name == "Mishneh Torah, Second Tithes and Fourth Year's Fruit":
#             print("""./run scripts/move_draft_text.py "{}" --noindex -d 'https://www.sefaria.org' -v "all" -l '2' -k 'kAEw7OKw5IjZIG4lFbrYxpSdu78Jsza67HgR0gRBOdg'""".format("Mishneh LaMelech on {}".format(en_full_name)))
