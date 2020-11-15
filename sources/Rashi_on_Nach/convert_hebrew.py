from sources.functions import *
versionTitles = """Isaiah
---
Isaiah, English translation by I.W. Slotki, Soncino Press, 1949
https://www.nli.org.il/en/books/NNL_ALEPH002642658/NLI

---

Jeremiah
---
Jeremiah, English translation by H. Freedman, Soncino Press, 1949
https://www.nli.org.il/en/books/NNL_ALEPH002579486/NLI

---

Ezekiel
---
Ezekiel, English translation by S. Fisch, Soncino Press, 1950
https://www.nli.org.il/en/books/NNL_ALEPH002642688/NLI

---

The Twelve Prophets
---
The Twelve Prophets, English translation by A. Cohen, Soncino Press, 1948
https://www.nli.org.il/en/books/NNL_ALEPH002644211/NLI

---

Psalms
---
The Psalms, English translation by A. Cohen, Soncino Press, 1945
https://www.nli.org.il/en/books/NNL_ALEPH002643011/NLI

---

Proverbs
---
Proverbs, English translation by A. Cohen, Soncino Press, 1945
https://www.nli.org.il/en/books/NNL_ALEPH002643042/NLI

---

Job
---
Job, English translation by Victor E. Reichert, Soncino Press, 1946
https://www.nli.org.il/en/books/NNL_ALEPH002643064/NLI

---

The Five Megilloth
---
The Five Megilloth, English translation by A. Cohen, Soncino Press, 1946
https://www.nli.org.il/en/books/NNL_ALEPH002644163/NLI

---

Daniel, Ezra and Nehemiah
---
Daniel, Ezra and Nehemiah, English translation by Judah J. Slotki, Soncino Press, 1951
https://www.nli.org.il/en/books/NNL_ALEPH002644183/NLI

---

Chronicles
---
Chronicles, English translation by I.W. Slotki, Soncino Press, 1952
https://www.nli.org.il/en/books/NNL_ALEPH002644317/NLI""".split("---")
def get_vtitle(desired_title):
    curr = ""
    if desired_title.startswith("Chronicles"):
        desired_title = "Chronicles"
    elif desired_title in ["Daniel", "Ezra", "Nehemiah"]:
        desired_title = "Daniel, Ezra and Nehemiah"
    elif desired_title in ["Song of Songs", "Ruth", "Esther", "Lamentations", "Ecclesiastes"]:
        desired_title = "The Five Megilloth"

    for i, title in enumerate(versionTitles):
        if i % 2 == 1:
            if curr == desired_title:
                return [t for t in title.splitlines() if t.strip()]
        else:
            curr = title.strip()
    else:
        return ["The Twelve Prophets, English translation by A. Cohen, Soncino Press, 1948", "https://www.nli.org.il/en/books/NNL_ALEPH002644211/NLI"]


text = {}
for f in os.listdir("."):
    if f.startswith("RASHI") and f.endswith(".txt"):
        with open(f, 'r') as open_f:
            rashi, title, chapter, verse = f.split(" - ")
            if title not in text:
                text[title] = {}
            chapter = chapter.split()[-1].replace("_", " ").strip().split()
            actual_chapter = 0
            for ch_num in chapter:
                actual_chapter += int(ch_num)
            if actual_chapter not in text[title]:
                text[title][actual_chapter] = {}
            verse = verse.replace("_", " ").replace(".txt", "").strip().split()
            actual_verse = 0
            for v_num in verse:
                actual_verse += int(v_num)
            if actual_verse not in text[title][actual_chapter]:
                text[title][actual_chapter][actual_verse] = []
            orig_lines = list(open_f)
            lines = [l for l in orig_lines if len(l.strip().replace("פרק", "").replace("דברי הימים", "").split()) > 2]
            first_line = lines[0]
            assert getGematria(first_line.split()[0]) == actual_verse
            lines[0] = " ".join(first_line.split()[1:])
            for line in lines:
                if "." in line:
                    dh, comment = line.split(".", 1)
                    text[title][actual_chapter][actual_verse].append("<b>{}</b> {}".format(dh, comment))
                else:
                    text[title][actual_chapter][actual_verse].append(line)

start = "Zephaniah"
starting = False
for title in text:
    if start in title:
        starting = True
    if not starting:
        continue
    for ch in text[title]:
        text[title][ch] = convertDictToArray(text[title][ch])
    text[title] = convertDictToArray(text[title])
    vtitle, vsource = get_vtitle(title.replace("2", "II").replace("1", "I"))
    send_text = {
        "language": "he",
        "versionTitle": "Soncino Hebrew",
        "versionSource": vsource,
        "text": text[title]
    }
    title = title.replace("_40__30__1__20__10_", "Malachi")
    post_text("Rashi on {}".format(title.replace("2", "II").replace("1", "I")), send_text)





    # cmd = """iconv -f ISO-8859-8 -t UTF-8 < "{}" > "./converted_{}" -c""".format(f, f)
    # print(cmd)
    # os.popen(cmd)
