from sources.functions import *
from time import sleep
vtitle = "Mishnah Yomit by Dr. Joshua Kulp"
start = "Bava Metzia"
starting = False
with open("report_of_corrected_phrases.csv", 'w') as f:
    writer = csv.writer(f)
    for i in library.get_indexes_in_category("Mishnah"):
        tc = TextChunk(Ref(i), lang='en', vtitle=vtitle)
        if tc.text:
            for a, sec in enumerate(tc.text):
                for b, seg in enumerate(sec):
                    #tc[a][b][c]
                    find = re.search("([:?.]{1})([a-zA-Z]{2,})", seg)
                    if find:
                        words = seg.split()
                        pos = -1
                        for j, w in enumerate(words):
                            if find.group(0) in w:
                                pos = j
                                break
                        assert pos != -1
                        words = " ".join(words[pos-2:pos+2]) if pos >= 2 else " ".join(words[0:pos+2])
                        assert len(words) > 0
                        writer.writerow([words, "{} {}:{}".format(i, a+1, b+1)])
                        tc.text[a][b] = seg.replace(find.group(0), find.group(1)+" "+find.group(2))
                        send_text = {
                            "text": tc.text[a][b],
                            "versionTitle": "Mishnah Yomit by Dr. Joshua Kulp",
                            "versionSource": "http://learn.conservativeyeshiva.org/mishnah/",
                            "language": "en"
                        }
                        #post_text("{} {}:{}".format(i, a+1, b+1), send_text)

#
# from sefaria.helper.schema import *
# indices = """Shevuot
# Sanhedrin
# Eduyot
# Makkot
# Sheviit
# Kilayim
# Makhshirin
# Avodah Zarah""".splitlines()
# for l in indices:
#     l = library.get_index("English Explanation of Mishnah {}".format(l))
#     print(l)
#     intro = JaggedArrayNode()
#     intro.add_structure(["Paragraph"])
#     intro.add_shared_term("Introduction")
#     intro.key = "Introduction"
#     insert_first_child(intro, l.nodes)
#     refresh_version_state(l.title)
# library.rebuild(include_toc=True)