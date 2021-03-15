from sources.functions import *
from bs4 import BeautifulSoup
import os
for f in os.listdir("./up to date txt files/"):
    if f.endswith("ftnotes_embedded.txt") and "Yoma" in f:
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
                i_tags = re.findall("<sup>(\d+)</sup><i class.*?>(.*?)</i>", comment)
                ftnotes[daf][i+1] = i_tags
                # soup = BeautifulSoup("<body>{}</body>".format(comment), parser='lxml')
                # i_tags = [x for x in soup.find_all("i") if "class" in x.attrs]
                # sup_tags = [x for x in soup.find_all("sup") if x.text.isdigit()]
                # assert len(i_tags) == len(sup_tags)
                # #for i, sup in zip(i_tags, sup_tags):

        title = f.replace("_ftnotes_embedded.txt", "")
        print(title)
        with open("just ftnotes/{} just ftnotes.txt".format(title), 'w') as new_f:
            writer = csv.writer(new_f)
            for daf in ftnotes:
                for segment in ftnotes[daf]:
                    i_tags = ftnotes[daf][segment]
                    for i in i_tags:
                        writer.writerow(["{} {}:{}".format(title, daf, segment), i[0], i[1]])