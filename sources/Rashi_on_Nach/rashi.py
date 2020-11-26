from sources.functions import *
from sources.Rashi_on_Nach.parse_converted_files import get_vtitle
from time import sleep
verse = chapter = 0
text = {}
with open("all in one.txt", 'r') as f:
    lines = list(f)

    for line in lines:
        title = re.search("~(.*)", line)
        ch = re.search("#(\d+)", line)
        v = re.search("@(\d+)", line)
        if title:
            curr_title = title.group(1).strip()
            text[curr_title] = {}
            chapter = 0
        elif ch:
            poss_ch = int(ch.group(1))
            assert poss_ch > chapter
            chapter = poss_ch
            text[curr_title][chapter] = {}
            verse = 0
        elif v:
            poss_v = int(v.group(1))
            assert poss_v > verse
            verse = poss_v
            text[curr_title][chapter][verse] = []
        else:
            text[curr_title][chapter][verse].append(line)

start = "Chronicles 1"
starting = False
for title in text.keys():
    if title == start:
        starting = True
    if not starting:
        continue
    vtitle, vsource = get_vtitle(title)
    for ch in text[title]:
        text[title][ch] = convertDictToArray(text[title][ch])
    send_text = {
        "versionTitle": vtitle,
        "versionSource": vsource,
        "language": "en",
        "text": convertDictToArray(text[title])
    }
    title = title.replace("Chronicles 1", "I Chronicles").replace("Chronicles 2", "II Chronicles")
    post_text("Rashi on {}".format(title), send_text)
