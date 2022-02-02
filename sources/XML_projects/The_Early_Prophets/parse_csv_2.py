from sources.functions import *
from data_utilities.dibur_hamatchil_matcher import match_text
import time
def dher(x):
    result = re.sub("<b>(.*?)</b>.*", "\g<1>", x).replace(":", "").replace("[", "").replace("]", "").replace(",", "").replace(".", "").replace(";", "")
    return bleach.clean(result, tags=[], strip=True)

def dher2(s):
    s = s.replace("… :", "").strip()
    poss = dher(s).split("…")[-1].strip()
    if poss == "":
        return dher(s).split("…")[0].strip()
    return poss


def dher3(s):
    return dher(s).split("…")[-1].strip()



books = ["Joshua", "Judges", "I Samuel", "Ii Samuel", "I Kings", "Ii Kings"]
with open("The Early Prophets Just Translation.csv", 'r') as f:

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
    prev_ftnote_verse = 0
    prev_verse = 0
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
        if re.search("^\d+-\d+", comm) is not None:
            print(comm)
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
            if ftnotes_bool:
                ftnote_ch = int(m.group(1))
            else:
                ch = int(m.group(1))

            which_ch = ftnote_ch if ftnotes_bool else ch


            if not ftnotes_bool:
                if ch not in text[books[book]]:
                    text[books[book]][which_ch] = []
                assert len(text[books[book]][which_ch]) == int(verse)-1
                verse -= len(text[books[book]][which_ch])
                while verse > 1:
                    text[books[book]][which_ch].append("")
                    verse -= 1
                text[books[book]][which_ch].append(comm)
            else:
                if ch not in ftnotes[books[book]]:
                    ftnotes[books[book]][which_ch] = {}
                comms = ["<b>"+c for c in comm.split("<b>")[1:]]
                ftnotes[books[book]][which_ch][int(verse)] = comms
                prev_ftnote_verse = int(verse)
        elif re.search("^\d+ ", comm) and ch >= 1:
            parsing = True
            verse = re.search("^(\d+) ", comm).group(1)
            if prev_ftnote_verse > int(verse) and ftnotes_bool:
                raise Exception
            comm = comm.replace(verse, "").strip()
            if not ftnotes_bool:
                text[books[book]][ch].append(comm)
                assert len(text[books[book]][ch]) == int(verse)
            else:
                comms = ["<b>" + c for c in comm.split("<b>")[1:]] if ftnotes_bool else [comm]
                ftnotes[books[book]][ftnote_ch][int(verse)] = comms
                prev_ftnote_verse = int(verse)
        elif ch >= 1 and parsing:
            if prev_ftnotes_bool:
                comms = ["<b>" + c for c in comm.split("<b>")[1:]] if ftnotes_bool else [comm]
                for comm in comms:
                    # ftnotes[books[book]][ftnote_ch][prev_ftnote_verse][-1] += "\n" + comm
                    ftnotes[books[book]][ftnote_ch][prev_ftnote_verse].append(comm)
            else:
                text[books[book]][ch][-1] += "\n" + comm


bad_results = []
not_found = []
bad = 0
ITAG_HOLDER = "$#%^!" # characters that dont occur in text hold place of itags during iteration
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
            diff = len(Ref(f"{our_book} {ch}").all_segment_refs()) - len(text[book][ch])
            if diff != 0:
                print(f"{diff} more verses: {our_book} {ch}")
            for p, pasuk in enumerate(text[book][ch]):
                if p+1 in ftnotes[book][ch]:
                    orig = text[book][ch][p]
                    base_words = bleach.clean(text[book][ch][p], tags=[], strip=True).replace("\n", "\n ").replace(":", "").replace("[", "").replace("]", "").replace(",", "").replace(".", "").replace(";", "")
                    base_words = base_words.split()
                    results = match_text(base_words, ftnotes[book][ch][p+1], dh_extract_method=dher2, lang='en')
                    # if (-1, -1) in results["matches"]:
                    #    results = match_text(base_words, ftnotes[book][ch][p+1], dh_extract_method=dher2, lang='en', prev_matched_results=results["matches"])
                    # if (-1, -1) in results["matches"]:
                    #     results = match_text(base_words, ftnotes[book][ch][p+1], dh_extract_method=dher3, lang='en', prev_matched_results=results["matches"])
                    curr = 0
                    total += len(results["matches"])
                    i_tags = []
                    text[book][ch][p] = text[book][ch][p].replace("\n", " <br/>")
                    words = text[book][ch][p]
                    text[book][ch][p] = text[book][ch][p].split()
                    curr = 0
                    for i, x in enumerate(results["matches"]):

                        ellipsis = [el.strip() for el in re.search("<b>(.*?)</b>", ftnotes[book][ch][p + 1][i]).group(1).split("…")]

                        ellipsis_or_not_found = False
                        if x == (-1, -1):
                            j = i
                            while j < len(results["matches"]) - 1 and results["matches"][j] == (-1, -1):
                                j += 1
                            end = results["matches"][j][1]
                            if end != -1:
                                end += 1
                            if curr >= 0 and end > curr:
                                phrase = " ".join(base_words[curr:end])
                            elif curr >= 0:
                                phrase = " ".join(base_words[curr:])
                            else:
                                phrase = " ".join(base_words)
                            if len(phrase) > 0 and phrase.find(results["match_text"][i][1]) >= 0:
                                ellipsis_or_not_found = True
                            else:
                                if f"{book} {ch}:{p+1} -- footnote {ftnotes[book][ch][p+1][i]} not found." not in not_found:
                                    not_found.append(f"{book} {ch}:{p+1} -- footnote {ftnotes[book][ch][p+1][i]} not found.")
                                bad_results.append(results["match_text"][i][1])

                        if ellipsis_or_not_found and len(results["match_text"][i][1]) > 0:
                            word_num = phrase.split(results["match_text"][i][1])[0].count(" ")+curr
                        else:
                            word_num = x[1]

                        if x != (-1, -1):
                            curr = x[1]
                        if word_num >= 0:
                            text[book][ch][p][word_num] = text[book][ch][p][word_num]+ITAG_HOLDER
                            i_tags.append("<sup>•</sup><i class='footnote'>" + ftnotes[book][ch][p + 1][i].strip() + "</i>")
                        else:
                            if f"{book} {ch}:{p + 1} -- footnote {ftnotes[book][ch][p + 1][i]} not found." not in not_found:
                                not_found.append(f"{book} {ch}:{p + 1} -- footnote {ftnotes[book][ch][p + 1][i]} not found.")
                    text[book][ch][p] = " ".join(text[book][ch][p]).replace("\n", "<br/>")
                    for i_tag in i_tags:
                        text[book][ch][p] = text[book][ch][p].replace(ITAG_HOLDER, i_tag, 1)
    with open(f"ftnotes_{book}.csv", 'w') as f:
        writer = csv.writer(f)
        for ch in ftnotes[book]:
            pasukim = ftnotes[book][ch]
            for p, pasuk in enumerate(pasukim):
                writer.writerow([f"{book} {ch}:{p+1}", pasuk])

for book in text:
    if book in ["Joshua", "Judges", "I Samuel", "II Samuel"]:
        continue
    text[book] = convertDictToArray(text[book])
    send_text = {
        "language": "en",
        "versionSource": "https://www.penguinrandomhouse.com/books/55159/the-early-prophets-joshua-judges-samuel-and-kings-by-everett-fox/",
        "versionTitle": "The Early Prophets, by Everett Fox",
        "text": text[book]
    }
    post_text(book.replace("Ii", "II"), send_text,server="https://ste.cauldron.sefaria.org")
    time.sleep(300)

for x in not_found:
    print(x)