from sources.functions import *
books = ["Joshua", "Judges", "I Samuel", "Ii Samuel", "I Kings", "Ii Kings"]
with open("The Early Prophets.csv", 'r') as f:

    # if new chapter, dont add anything until we get to "\d .*?".  then we check to see if it has <bold> tags to decide if it's a footnote
    # all the while, we
    reader = csv.reader(f)
    text = defaultdict(dict)

    book = 0
    ch = 0
    ftnote_ch = 0
    ftnotes = defaultdict(dict)
    ftnotes_bool = False
    lines = list(reader)
    for r, row in enumerate(lines):
        ref, comm = row
        while book < len(books) and books[book] not in ref:
            book += 1
            ch = 0
            parsing = False
            ftnote_ch = 0
        if comm.replace("_", "").strip() == "":
            continue

        prev_ftnotes_bool = ftnotes_bool
        ftnotes_bool = bool(re.search("^\d+:\S+ .*?<b>", comm)) or bool(re.search("^\d+ .*?<b>", comm))

        if ref.split()[-1].split(".")[-1] == '1':
            parsing = False

        if re.search("^\d+:\S+ ", comm):
            parsing = True
            m = re.search("^(\d+):(\S+) ", comm)
            verse = m.group(2)
            while not verse.isdigit():
                verse = verse[:-1]
            verse = int(verse)
            comm = comm.replace(m.group(0), "", 1).strip()
            which_dict = ftnotes if ftnotes_bool else text

            if ftnotes_bool:
                ftnote_ch = int(m.group(1))
            else:
                ch = int(m.group(1))

            which_ch = ftnote_ch if ftnotes_bool else ch
            if ch not in which_dict[books[book]]:
                which_dict[books[book]][which_ch] = []
            verse -= len(which_dict[books[book]][which_ch])
            while verse > 1:
                which_dict[books[book]][which_ch].append("")
                verse -= 1
            which_dict[books[book]][which_ch].append(comm)

        elif re.search("^\d+ ", comm) and ch >= 1:
            parsing = True
            pasuk = re.search("^(\d+) ", comm).group(1)
            comm = comm.replace(pasuk, "").strip()
            text[books[book]][ch].append(comm) if not ftnotes_bool else ftnotes[books[book]][ftnote_ch].append(comm)
        elif ch >= 1 and parsing:
            if prev_ftnotes_bool:
                ftnotes[books[book]][ftnote_ch][-1] += "\n" + comm
            else:
                text[books[book]][ch][-1] += "\n" + comm
        else:
            print(row)


for book in books:
    our_book = book.replace("Ii", "II")
    diff = len(library.get_index(our_book).all_section_refs()) - len(text[book].keys())
    if diff != 0:
        print(book)
        print(f"{diff} chapters differ")
    with open(f"{book}.csv", 'w') as f:
        writer = csv.writer(f)
        for ch in text[book]:
            diff = len(Ref(f"{our_book} {ch}").all_segment_refs()) - len(text[book][ch])
            if diff != 0:
                print(f"{diff} verses differ in {our_book} {ch}")
            pasukim = text[book][ch]
            for p, pasuk in enumerate(pasukim):
                writer.writerow([f"{book} {ch}:{p+1}", pasuk])
    with open(f"ftnotes_{book}.csv", 'w') as f:
        writer = csv.writer(f)
        for ch in ftnotes[book]:
            pasukim = ftnotes[book][ch]
            for p, pasuk in enumerate(pasukim):
                writer.writerow([f"{book} {ch}:{p+1}", pasuk])