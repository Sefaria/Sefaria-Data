import django
django.setup()
import csv
from sources.functions import *
import os
from sefaria.system.exceptions import InputError
#
# with open("Shulchan_Arukh,_Yoreh_De_ah_-_he_-_183-195.csv", 'r') as f:
#     rows = list(csv.reader(f))
#     title = rows[0][1]
#     vtitle = rows[1][1]
#     lang = rows[2][1]
#     vsource = rows[3][1]
#     text = {}
#     for row in rows[5:]:
#         ref, para = row
#         siman, seg = ref.split()[-1].split(":")
#         siman = int(siman)
#         seg = int(seg)
#         if siman not in text:
#             text[siman] = {}
#         text[siman][seg] = para
#     for siman in text:
#         text[siman] = convertDictToArray(text[siman])
#     text = convertDictToArray(text)
#     send_text = {
#         "language": lang,
#         "versionTitle": vtitle,
#         "versionSource": vsource,
#         "text": text
#     }
#     post_text(title, send_text)
def create_node(ref):
    alt_node = ArrayMapNode()
    alt_node.add_primary_titles("Seder {}".format(seder), "סדר {}".format(numToHeb(seder)))
    alt_node.depth = 0
    alt_node.wholeRef = ref.normal()
    alt_node.refs = []
    alt_node.validate()
    return alt_node

nodes = {}
for f in os.listdir("./Tanakh Sedarim alt toc "):
    if not f.endswith(".csv"):
        continue
    try:
        titles = [library.get_index(f[:-4]).title]
    except Exception as e:
        continue
        # if f == 'תרי עשר.csv':
        #     titles = "Hoshea, Yoel, Amos, Ovadiah, Yonah, Micha, Nahum, Habakuk, Zephaniah, Haggai, Zechariah, Malachi".split(", ")
        # else:
        #     continue
    title_counter = -1

    with open("Tanakh Sedarim alt toc /"+f) as open_csv:
        rows = list(csv.reader(open_csv))
        for row in rows[1:]:
            seder, start, end = row
            if start == "1:1":
                title_counter += 1
                nodes[titles[title_counter]] = []
            try:
                wholeRef = Ref("{} {}".format(titles[title_counter], start)).to(Ref("{} {}".format(titles[title_counter], end)))
                alt_node = create_node(wholeRef)
                nodes[titles[title_counter]].append(alt_node.serialize())
            except InputError as e:
                try:
                    endingRef = Ref("{} {}".format(titles[title_counter], start)).to(Ref(titles[title_counter]).last_segment_ref())
                    alt_node = create_node(endingRef)
                    nodes[titles[title_counter]].append(alt_node.serialize())
                    title_counter += 1
                    startingRef = Ref(titles[title_counter]).first_available_section_ref().to(Ref("{} {}".format(titles[title_counter], end)))
                    alt_node = create_node(startingRef)
                    nodes[titles[title_counter]] = []
                    nodes[titles[title_counter]].append(alt_node.serialize())
                except IndexError as e:
                    print(e)



for title, node in nodes.items():
    if library.get_index(title).categories[-1] == "Writings":
        index = get_index_api(title, server="https://www.sefaria.org")
        curr_alt_struct = index["alt_structs"] if "alt_structs" in index else {}
        curr_alt_struct["Seder"] = {"nodes": node}
        index['alt_structs'] = curr_alt_struct
        post_index(index)

