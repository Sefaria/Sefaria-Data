from sources.functions import *
import os
before_content = """Index Title,{}
Version Title,"{}"
Language,he
Version Source,{}
Version Notes,"""
for f in os.listdir("./mishnah"):
    text = {}
    perakim = []
    if f.endswith("csv") and "structured" not in f:
        title = f.replace(".csv", "")
        with open("./mishnah/"+f, 'r') as open_f:
            for row in csv.reader(open_f):
                ref, comment = row
                perek = ref.split(".")[0].replace(title+", ", "")
                if perek not in perakim:
                    perakim.append(perek)
                perek = len(perakim)
                if perek not in text:
                    text[perek] = []
                text[perek].append(comment)
        vtitle = "Talmud Bavli. German. Lazarus Goldschmidt. 1929"
        vsource = "https://www.nli.org.il/he/books/NNL_ALEPH001042448/NLI"
        with open("./mishnah/{}_structured.csv".format(title), 'w') as open_f:
            writer = csv.writer(open_f)
            for c in before_content.format(title.title(), vtitle, vsource).splitlines():
                writer.writerow(c.split(","))
            for perek in text:
                for i, line in enumerate(text[perek]):
                   writer.writerow(["{} {}:{}".format(title.title(), perek, i+1), line])
