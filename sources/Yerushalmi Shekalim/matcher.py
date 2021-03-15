from sources.functions import *
from data_utilities.dibur_hamatchil_matcher import *
def dher(str):
    if not "<b>" in str or not "</b>" in str:
        return ""
    else:
        return re.search("<b>(.*?)</b>", str).group(1)

files = [("Pnei Moshe", open("Pnei Moshe.csv", 'r')), ("Korban HaEidah", open("Korban HaEidah.csv", 'r'))]
for title, file in files:
    new_data = []
    text = {}
    perek = 1
    halakhah = 1
    reader = csv.reader(file)
    for row in reader:
        poss_perek, poss_halakhah, segment = row[0], row[1], row[2]
        poss_halakhah = poss_halakhah.replace("הלכה ", "")
        perek = getGematria(poss_perek) if len(poss_perek) > 0 else perek
        halakhah = getGematria(poss_halakhah) if len(poss_halakhah) > 0 else halakhah
        if perek not in text:
            text[perek] = {}
        if halakhah not in text[perek]:
            text[perek][halakhah] = []
        text[perek][halakhah].append(segment)
    links = []
    for perek in text:
        print(perek)
        for halakhah in text[perek]:
            comments = text[perek][halakhah]
            curr_links = match_ref_interface("Jerusalem Talmud Shekalim", title+" {}".format(perek), comments, lambda x: x.split(), dher, vtitle="William Davidson Edition - Hebrew", padding=True)
            assert len(curr_links) == len(comments)
            for link, comment in zip(curr_links, comments):
                link_ref = link["refs"][1] if "refs" in link else ""
                new_data.append([numToHeb(perek), numToHeb(halakhah), comment, link_ref])

    print(len(links))
    with open("{}_with_links.csv".format(title), 'w') as f:
        writer = csv.writer(f)
        for row in new_data:
            writer.writerow(row)
