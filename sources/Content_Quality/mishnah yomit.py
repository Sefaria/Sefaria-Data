from sources.functions import *
from time import sleep
vtitle = "Mishnah Yomit by Dr. Joshua Kulp"
start = "Bava Metzia"
starting = False
for i in library.get_indexes_in_category("Mishnah"):
    if start in i:
        starting = True
    if not starting:
        continue
    tc = TextChunk(Ref(i), lang='en', vtitle=vtitle)
    if tc.text:
        for a, sec in enumerate(tc.text):
            for b, seg in enumerate(sec):
                #tc[a][b][c]
                find = re.search("([:?.]{1})([a-zA-Z]{2,})", seg)
                if find:
                    tc.text[a][b] = seg.replace(find.group(0), find.group(1)+" "+find.group(2))
        send_text = {
            "text": tc.text,
            "versionTitle": "Mishnah Yomit by Dr. Joshua Kulp",
            "versionSource": "http://learn.conservativeyeshiva.org/mishnah/",
            "language": "en"
        }
        post_text(i, send_text)
        sleep(60)

