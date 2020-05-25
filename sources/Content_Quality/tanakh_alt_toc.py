import django
django.setup()
import csv
from sources.functions import *
import os
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
for f in os.listdir("./Tanakh Sedarim alt toc "):
    try:
        title = library.get_index(f[:-4]).title
        index = get_index_api(title, server="https://www.sefaria.org")
        nodes = []
        with open("Tanakh Sedarim alt toc /"+f) as open_csv:
            rows = list(csv.reader(open_csv))
            for row in rows[1:]:
                seder, start, end = row
                alt_node = ArrayMapNode()
                alt_node.add_primary_titles("Seder {}".format(seder), "סדר {}".format(numToHeb(seder)))
                alt_node.depth = 0
                wholeRef = Ref("{} {}".format(title, start)).to(Ref("{} {}".format(title, end)))
                alt_node.wholeRef = wholeRef.normal()
                alt_node.refs = []
                alt_node.validate()
                nodes.append(alt_node.serialize())
        curr_alt_struct = index["alt_structs"] if "alt_structs" in index else {}
        curr_alt_struct["Seder"] = {"nodes": nodes}
        index['alt_structs'] = curr_alt_struct
        #post_index(index)
    except Exception as e:
        print(e)




