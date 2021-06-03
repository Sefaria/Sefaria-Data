from sources.functions import *
from bs4 import BeautifulSoup
import os
for f in os.listdir("./up to date txt files/"):
    if f.endswith("ftnotes_embedded.txt"):
        text = {}
        ftnotes = {}
        print(f)
        starting = False
        for line in open("./up to date txt files/"+f):
            if line.startswith("Daf"):
                daf = line.split()[-1]
                text[daf] = []
                starting = True
            elif starting and len(line) > 1:
                text[daf].append(line)
        for daf in text:
            ftnotes[daf] = {}
            for i, comment in enumerate(text[daf]):
                ftnotes[daf][i + 1] = []
                soup = BeautifulSoup("<body>{}</body>".format(comment), parser='lxml')
                i_tags = [x for x in soup.find_all("i") if "class" in x.attrs]
                for i_tag in i_tags:
                    assert i_tag.previousSibling.name == "sup"
                    sup = i_tag.previousSibling
                    ftnotes[daf][i+1].append([str(sup), str(i_tag)])

        title = f.replace("_ftnotes_embedded.txt", "")
        print(title)
        with open("just ftnotes/{} just ftnotes.txt".format(title), 'w') as new_f:
            writer = csv.writer(new_f)
            for daf in ftnotes:
                for segment in ftnotes[daf]:
                    i_tags = ftnotes[daf][segment]
                    for i in i_tags:
                        writer.writerow(["{} {}:{}".format(title, daf, segment), i[0], i[1]])