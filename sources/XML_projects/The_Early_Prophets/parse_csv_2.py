from sources.functions import *
from data_utilities.dibur_hamatchil_matcher import match_text

def dher(x):
    result = re.sub("<b>(.*?)</b>.*", "\g<1>", x).replace(":", "").replace("[", "").replace("]", "")
    return bleach.clean(result, tags=[], strip=True)

def dher2(s):
    strings = sorted(dher(s).split("…"), key=lambda x: -len(x))
    return strings[0].strip()

def dher3(s):
    strings = sorted(dher(s).split("…"), key=lambda x: -len(x))
    if len(strings) > 1:
        return strings[1].strip()
    else:
        return strings[0]


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
        ftnotes_bool = bool(re.search("^\d+[:.]{1}\S+ .*?<b>", comm)) or bool(re.search("^\d+ .*?<b>", comm))

        if ref.split()[-1].split(".")[-1] == '1':
            parsing = False

        if re.search("^\d+[:.]{1}\S+ ", comm):
            parsing = True
            m = re.search("^(\d+)[:.]{1}(\S+) ", comm)
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

            comms = ["<b>"+c for c in comm.split("<b>")[1:]] if ftnotes_bool else [comm]
            for comm in comms:
                which_dict[books[book]][which_ch].append(comm)

        elif re.search("^\d+ ", comm) and ch >= 1:
            parsing = True
            pasuk = re.search("^(\d+) ", comm).group(1)
            comm = comm.replace(pasuk, "").strip()
            if not ftnotes_bool:
                text[books[book]][ch].append(comm)
            else:
                comms = ["<b>" + c for c in comm.split("<b>")[1:]] if ftnotes_bool else [comm]
                for comm in comms:
                    ftnotes[books[book]][ftnote_ch].append(comm)
        elif ch >= 1 and parsing:
            if prev_ftnotes_bool:
                comms = ["<b>" + c for c in comm.split("<b>")[1:]] if ftnotes_bool else [comm]
                for comm in comms:
                    ftnotes[books[book]][ftnote_ch][-1] += "\n" + comm
            else:
                text[books[book]][ch][-1] += "\n" + comm
        else:
            print(row)

bad_results = []
bad = 0
total = 0
for book in books:
    our_book = book.replace("Ii", "II")
    diff = len(library.get_index(our_book).all_section_refs()) - len(text[book].keys())
    if diff != 0:
        print(book)
        print(f"{diff} chapters differ")
    with open(f"{book}.csv", 'w') as f:
        writer = csv.writer(f)
        for ch in text[book]:

            tc = TextChunk(Ref(f"{our_book} {ch}"), lang='en')
            base_words = bleach.clean(" \n\n ".join(text[book][ch]).replace("\n", " "), tags=[], strip=True).split()
            results = match_text(base_words, ftnotes[book][ch], dh_extract_method=dher, lang='en')
            if (-1, -1) in results["matches"]:
                results = match_text(base_words, ftnotes[book][ch], dh_extract_method=dher2, lang='en', prev_matched_results=results["matches"])
            if (-1, -1) in results["matches"]:
                results = match_text(base_words, ftnotes[book][ch], dh_extract_method=dher3, lang='en', prev_matched_results=results["matches"])
            diff = len(Ref(f"{our_book} {ch}").all_segment_refs()) - len(text[book][ch])
            curr = 0
            poss_match_positions = []
            for i, x in enumerate(results["matches"]):
                if x == (-1, -1) and i == len(results["matches"]) - 1:
                    poss_match_positions.append((poss_match_positions[i-1][1]+1, len(base_words)))
                elif x == (-1, -1) and results["matches"][i+1] == (-1, -1):
                    poss_match_positions.append((curr, curr))
                elif x == (-1, -1):
                    poss_match_positions.append((curr, results["matches"][i+1][0]-1))
                    assert results["matches"][i+1][0]-1 >= curr
                else:
                    poss_match_positions.append(x)
                    curr = x[1]+1
            found = True
            for i, x in enumerate(results["matches"]):
                if x == (-1, -1) and results["match_text"][i][1] != "":
                    bad_results.append(results["match_text"][i][1])
                # if x == (-1, -1) and results["match_text"][i][1] != "":
                #     pos = " ".join(base_words[poss_match_positions[i][0]:poss_match_positions[i][1]]).find(results["match_text"][i][1])
                #     if pos == -1:
                #         bad_results.append(results["match_text"][i][1])
                #         found = False
                #     else:
                #         actual_pos = " ".join(base_words[poss_match_positions[i][0]:poss_match_positions[i][1]]).split(results["match_text"][i][1]).count(" ")
                #         results["matches"][i] = (actual_pos, actual_pos)
                # if found:
                #     start = results["matches"][i][0]
                #     end = results["matches"][i][1]
                #     i_tag = f"<sup>^</sup><i class='footnote'>{ftnotes[book][ch][i]}</i>"
                #     base_words[start] = base_words[start]+i_tag
                #     if end > start:
                #         base_words[end] = base_words[end]+"<sup>^</sup>"
                #     words_in_text = 0
                #     for p, pasuk in enumerate(text[book][ch]):
                #         words_in_text += len(pasuk.split())

            total += len(results["matches"])
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
print("BAD")
print(len(bad_results))
print(total)

for x in bad_results:
    print(x)