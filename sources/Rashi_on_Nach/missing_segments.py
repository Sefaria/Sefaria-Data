from sources.functions import *
from sources.Rashi_on_Nach.parse_converted_files import get_vtitle
empty_he = {}
empty_en = {}
titles = ["Psalms", "Proverbs", "Daniel", "Job", "Chronicles I", "Chronicles II"]
for f in os.listdir("."):
    if f.startswith("final_"):
        f = f.replace('final_converted_', '').replace('.txt', '')
        empty_en[f] = 0
        empty_he[f] = 0
        versionTitle, vsource = get_vtitle(f)
        print(f)
        print(versionTitle)
        for ref in library.get_index("Rashi on {}".format(f)).all_segment_refs():
            en_ = TextChunk(ref, lang='en', vtitle=versionTitle)
            he_ = TextChunk(ref, lang='he', vtitle=versionTitle)
            if (he_.text and not en_.text):
                empty_en[f] += 1
            elif (not he_.text and en_.text):
                empty_he[f] += 1
for f in empty_en:
    if empty_he[f] > 0 or empty_en[f] > 0:
        print("{} has {} missing English segments".format(f, empty_en[f]))
        print("{} has {} missing Hebrew segments\n".format(f, empty_he[f]))
