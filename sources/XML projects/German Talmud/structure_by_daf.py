from sources.functions import *
from bs4 import BeautifulSoup
import os

def run_checks(folios, title):
    # check sequence and check total number is same
    daf = 3
    our_text_dappim = library.get_index(title).all_section_refs()
    for folio in folios:
        if folio.endswith("b") or folio == "Colb." or folio == "Co":
            daf += 1
        else:
            new_daf = (2*int(re.search("\d+", folio).group(0))) - 1
            if new_daf - daf != 1:
                print("{} but expected {} in {}".format(AddressTalmud.toStr("en", new_daf), AddressTalmud.toStr("en", daf+1), title))
                daf += 1
            else:
                daf = new_daf
    if daf != len(our_text_dappim)+2:
        print("{} but expected {} dappim in {}".format(daf, len(our_text_dappim)+2, title))

vsource = "https://www.nli.org.il/he/books/NNL_ALEPH001042448/NLI"
for file in os.listdir("."):
    if file.endswith(".csv") and not "ftnote" in file:
        title = file.replace(".csv", "")
        if not file[0].isupper():
            continue
        if "Chullin" not in file:
            continue
        print(file)
        text = ""
        with open("{}.csv".format(title), 'r') as f:
            for row in csv.reader(f):
                text += row[1]

        folios_text = re.findall("<folio>(.*?)</folio>", text)
        # for i, folio in enumerate(re.findall("<folio>(.*?)</folio>", text)):
        #     if i % 2 == 0 and not folio.endswith("b"):
        #         print(title)

        run_checks(folios_text, title)


        sec_refs = library.get_index(title).all_section_refs()
        #assert len(folios_text) + 1 == len(sec_refs) # add 1 because 2a is missing


        text = {3: []}
        curr = 3

        with open("{}.csv".format(title), 'r') as f:
            for row in csv.reader(f):
                divided_text = [x.strip() for x in re.split("<folio>.*?</folio>", row[1])]
                text[curr].append(divided_text[0])
                if len(divided_text) > 1:
                    divided_text = divided_text[1:]
                    for amud, text_portion in zip(re.findall("<folio>(.*?)</folio>", row[1]), divided_text):
                        if (("col" in amud or "Col" in amud) and "b" in amud) or "Co" == amud:
                            curr += 1
                            text[curr] = [text_portion]
                        else:
                            dig = re.search(".*?(\d+)", amud)
                            if not dig:
                                print("Uh oh... {}".format(amud))
                            else:
                                daf = dig.group(1)
                                curr = AddressTalmud(0).toNumber("en", "{}a".format(daf))
                                text[curr] = [text_portion]


        before_content = """Index Title,{}
Version Title,"{}"
Language,he
Version Source,{}
Version Notes,"""
        with open("CSVs/{}_ftnotes_embedded.csv".format(title), 'w') as f:
            vtitle = "Talmud Bavli. German. Lazarus Goldschmidt. 1929 -- footnotes"
            before_content = before_content.format(title, vtitle, vsource)
            writer = csv.writer(f)
            for c in before_content.splitlines():
                writer.writerow(c.split(","))
            for i, folio in text.items():
                if len(folio) > 0:
                    for j, line in enumerate(folio):
                        daf = AddressTalmud(0).toStr("en", i)
                        writer.writerow(["{} {}:{}".format(title, daf, j+1), line])

        with open("CSVs/{}_ftnote_markers_only.csv".format(title), 'w') as f:
            vtitle = "Talmud Bavli. German. Lazarus Goldschmidt. 1929 -- no footnotes"
            before_content = before_content.format(title, vtitle, vsource)
            writer = csv.writer(f)
            for c in before_content.splitlines():
                writer.writerow(c.split(","))
            for i, folio in text.items():
                if len(folio) > 0:
                    for j, line in enumerate(folio):
                        soup = BeautifulSoup("<body>{}</body>".format(line))
                        for i_tag in soup.find_all("i"):
                            if i_tag.attrs == {}:
                                i_tag.name = 'u'
                        line = str(soup).replace("<html><body>", "").replace("</body></html>", "")
                        line = re.sub("<sup>(\d+)</sup><i.*?</i>", "$fn\g<1>", line)
                        line = re.sub("<sup>(\d+)</sup><i.*?</i>\s", "$fn\g<1> ", line)
                        soup = BeautifulSoup("<body>{}</body>".format(line))
                        for u_tag in soup.find_all("u"):
                            if u_tag.attrs == {}:
                                u_tag.name = "i"
                        line = str(soup).replace("<html><body>", "").replace("</body></html>", "")
                        daf = AddressTalmud(0).toStr("en", i)
                        writer.writerow(["{} {}:{}".format(title, daf, j+1), line])
