import os
from num2words import num2words

def sorter(x):
    rashi, title, chapter, verse = x.split(" - ")
    chapter = int(chapter.split()[-1])
    verse = int(verse.replace(".rtf", ""))
    return chapter + float(verse/100)

def sorter_he(x):
    rashi, title, chapter, verse = x.split(" - ")
    chapter = chapter.split()[-1].replace("_", " ").strip().split()
    actual_chapter = 0
    for ch_num in chapter:
        actual_chapter += int(ch_num)
    verse = verse.replace("_", " ").replace(".rtf", "").strip().split()
    actual_verse = 0
    for v_num in verse:
        actual_verse += int(v_num)
    return actual_chapter + float(actual_verse / 100)

files = sorted(os.listdir("rashi's on nakh v2"))
files_dict = {}
text = {}
for f in files:
    if f.endswith("rtf") and f.startswith("RASHI"):
        rashi, title, chapter, verse = f.split(" - ")
        if title not in files_dict:
            files_dict[title] = []
            text[title] = bytes()
        files_dict[title].append(f)



for title in files_dict:
    sorted_files = sorted(files_dict[title], key=sorter_he)
    for f in sorted_files:
        with open("rashi's on nakh v2/"+f, 'rb') as open_f:
            lines = open_f.read()
            text[title] += lines

        cmd = """iconv -f ISO-8859-8 -t UTF-8 < "./{}.rtf" > "./converted_{}.rtf" -c""".format(f, f)
        print(cmd)
        os.popen(cmd)
        os.popen("pwd")
    #
    with open(title+".rtf", 'wb') as title_f:

        title_f.write(text[title])
