from sources.functions import *
with open("The Early Prophets.csv", 'r') as f:
    reader = csv.reader(f)
    text = defaultdict(dict)
    books = ["Joshua", "Judges", "I Samuel", "Ii Samuel", "I Kings", "Ii Kings"]
    book = 0
    ch = 0
    ftnotes = defaultdict(dict)
    start_ftnotes = False
    lines = list(reader)
    for r, row in enumerate(lines):
        ref, comm = row
        while book < len(books) and books[book] not in ref:
            book += 1
            ch = 0
        if comm.replace("_", "").strip() == "":
            start_ftnotes = True
            continue
        if re.search("^\d+:1 ", comm):
            ch += 1
            text[books[book]][ch] = []
            ftnotes[books[book]][ch] = []
            comm = comm.replace(re.search("^\d+:1 ", comm).group(0), "", 1)
            start_ftnotes = False
            text[books[book]][ch].append(comm)
        elif start_ftnotes:
            assert comm[0].isdigit()
            comm = " ".join(comm.split()[1:])
            ftnotes[books[book]][ch].append(comm)
        else:
            if re.search("^\d+ ", comm) and ch >= 1:
                pasuk = re.search("^(\d+) ", comm).group(1)
                comm = comm.replace(pasuk, "").strip()
                text[books[book]][ch].append(comm)
            elif ch >= 1:
                text[books[book]][ch][-1] += "\n" + comm


print(text)
for text_type in [("Book",text), ("Footnotes", ftnotes)]:
    for type, book in text_type:
        with open(f"{type} {book}.csv", 'w') as f:
            writer = csv.writer(f)
            for ch in text_type[book]:
                pasukim = text_type[book][ch]
                for p, pasuk in enumerate(pasukim):
                    writer.writerow([f"{book} {ch}:{p+1}", pasuk])
