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
valid_refs = []
for ref in new_text:
    for book in ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]:
        if ref.endswith(book):
            # parse mini essays and footnotes
            for line in new_text[ref]:
                m = re.search("<i>(.*?)</i>\s?(\(.*?\))", line)
                if m:
                    title, ref = m.group(1), m.group(2)
                    ref = ref.replace("(", "("+book+" ")
                    try:
                        Ref(ref[1:-1])
                        print(f"{title} -> {ref}")
                        valid_refs.append((title, ref))
                    except:
                        invalid_refs.append((title, ref))
        else:
            # parse major essays
            pass

vtitle = "https://www.penguinrandomhouse.com/books/55160/the-five-books-of-moses-by-everett-fox/"
print("\nINVALID REFS:")
for invalid_ref in invalid_refs:
    title, ref = invalid_ref
    print(f"*** {title} -> {ref}")