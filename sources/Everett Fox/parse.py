from sources.functions import *
from collections import *
text = {}
with open("SB Bible.txt", 'r') as f:
    lines = list(f)
    for i, line in enumerate(lines):
        lines[i] = lines[i].replace("@", "")
        lines[i] = lines[i].replace("   ", "\t").replace("\t\t", "\t")
        if len(lines[i].strip().split()) == 1:
            book = lines[i].split()[0].strip().title()
            chapter = 1
            text[book] = defaultdict(dict)
            text[book][chapter] = defaultdict(dict)
        else:
            sc_texts = re.findall("<sc>(.*?)</sc>", lines[i])
            for sc_text in sc_texts:
                lines[i] = lines[i].replace(f"<sc>{sc_text}</sc>", f"<small>{sc_text.upper()}</small>")
            if lines[i].split()[0].isdigit():
                verse, comm = lines[i].split("\t", 1)
                if verse.strip() == "1":
                    chapter += 1
                    text[book][chapter] = defaultdict(dict)
            elif ":" in lines[i].split()[0]:
                verse = lines[i].split()[0]
                comm = lines[i].replace(verse, "").strip()
                poss_chapter, poss_verse = verse.split(":")
                verse = int(poss_verse)
                poss_chapter = int(poss_chapter)
                assert poss_chapter - chapter in [0, 1]
                chapter = poss_chapter
            else:
                comm = lines[i]
            comm = comm.replace("\t", " ").replace("<br>", "<br/>").replace("  ", " ").strip()


            text[book][chapter][verse] = comm


    with open("results.csv", 'w') as f:
        writer = csv.writer(f)
        for book in text:
            chapter_diff = len(text[book].values()) - len(library.get_index(book).all_section_refs())
            if chapter_diff != 0:
                print("{} has chapter diff of {}".format(book, chapter_diff))
            for ch in text[book]:
                pasuk_diff = len(text[book][ch].values()) - len(Ref("{} {}".format(book, ch)).all_segment_refs())
                if pasuk_diff != 0:
                    print("{} {} has pasuk diff of {}".format(book, ch, pasuk_diff))
                    for p, pasuk in text[book][ch].items():
                        writer.writerow(["{} {} {}".format(book, ch, p), pasuk])
