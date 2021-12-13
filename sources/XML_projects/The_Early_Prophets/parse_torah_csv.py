from sources.functions import *
refs = ["Torah, Exodus, Ii: in the Wilderness", "Torah, Exodus, Iii: the Meeting and Covenant At Sinai", "Torah, Exodus, Iv: the Instructions For the Dwelling and the Cult",]
new_rows = []
with open("Torah.csv", 'r') as f:
    curr_ref = ""
    for row in csv.reader(f):
        if re.search("^\d+ ", row[1]) and row[0].rsplit(".")[0] in refs:
            curr_ref = row[0].rsplit(".")[0]
        elif row[0].rsplit(".")[0] != curr_ref and len(curr_ref) > 0:
            #print(curr_ref)
            curr_ref = ""
        if len(curr_ref) == 0:
            new_rows.append(row)


new_text = defaultdict(list)
for row in new_rows:
    ref = row[0].rsplit(".")[0]
    new_text[ref].append(row[1])

invalid_refs = []
short_refs = {}
essay_refs = {}
for k in new_text:
    for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
        if book in k and not k.endswith(book):
            poss_ref = new_text[k][0]
            m = re.search("\((.*?)\)", poss_ref)
            if m and len(poss_ref) < 50:
                poss_ref = f"{book} {m.group(1)}".replace('–', "-").replace("1-4:43", "1:1-4:43")
                try:
                    essay_refs[(Ref(poss_ref), k)] = []
                except Exception as e:
                    print(e)

for k in new_text:
    for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
        if k.endswith(book):
            # parse mini essays and footnotes
            for line in new_text[k]:
                m = re.search("^<i>(.*?)</i>\s?(\(.*?\))", line)
                if m:
                    title, ref = m.group(1), m.group(2)
                    ref = ref.replace("(", "("+book+" ")
                    ref = ref.replace("2:4a", "2:4").replace("2:4b", "2:4").replace('–', "-")
                    ref = ref.replace("Exodus 28:6-12, 13-14", "Exodus 28:6-14").replace("Deuteronomy 2, 3:1-22", "Deuteronomy 2:1-3:22")
                    try:
                        for essay in essay_refs.keys():
                            essay_ref, essay_title = essay
                            if essay_ref.contains(Ref(ref[1:-1])):
                                essay_refs[(essay_ref, essay_title)].append((title, ref))
                    except Exception as e:
                        invalid_refs.append((title, ref))
vtitle = "https://www.penguinrandomhouse.com/books/55160/the-five-books-of-moses-by-everett-fox/"
for invalid_ref in invalid_refs:
    title, ref = invalid_ref
    print(f"!!! {title} -> {ref}")

