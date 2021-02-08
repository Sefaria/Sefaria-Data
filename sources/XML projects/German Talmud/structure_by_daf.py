from sources.functions import *
title = "Pesachim"
text = ""
with open("{}.csv".format(title), 'r') as f:
    for row in csv.reader(f):
        text += row[1]

folios_text = re.findall("<folio>(.*?)</folio>", text)
for i, folio in enumerate(re.findall("<folio>(.*?)</folio>", text)):
    if i % 2 == 0 and not folio.endswith("b"):
        print()


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
                if "Col" in amud and "b" in amud:
                    curr += 1
                    text[curr] = [text_portion]
                else:
                    daf = re.search(".*?(\d+)", amud).group(1)
                    curr = AddressTalmud(0).toNumber("en", "{}a".format(daf))
                    text[curr] = [text_portion]

with open("pesachim_ftnotes_embedded.csv", 'w') as f:
    writer = csv.writer(f)
    for i, folio in text.items():
        if len(folio) > 0:
            for j, line in enumerate(folio):
                daf = AddressTalmud(0).toStr("en", i)
                writer.writerow(["Pesachim {}:{}".format(daf, j+1), line])

with open("pesachim_ftnote_markers_only.csv", 'w') as f:
    writer = csv.writer(f)
    for i, folio in text.items():
        if len(folio) > 0:
            for j, line in enumerate(folio):
                line = re.sub("<sup>(\d+)</sup>.*?</i>\s", "$fn\g<1> ", line)
                line = re.sub("<sup>(\d+)</sup>.*?</i>", "$fn\g<1>", line)
                daf = AddressTalmud(0).toStr("en", i)
                writer.writerow(["Pesachim {}:{}".format(daf, j+1), line])
