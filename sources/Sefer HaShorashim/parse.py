from sources.functions import *
from bs4 import BeautifulSoup
with open("words.xml") as f:
    soup = BeautifulSoup(f)
    for c in soup.descendants:
        print(c)

parsing = False
text = {}
curr_letter = ""
lines = [x.strip() for x in list(f) if x.strip()]
for i, line in enumerate(lines):
    if line.count(" ") == 1 and line.startswith("אות "):
        parsing = True
        curr_letter = line.split()[-1]
        curr_letter = curr_letter[1] if len(curr_letter) > 2 else curr_letter[0]
        if curr_letter not in text:
            text[curr_letter] = []
        curr_word = ""
    # elif line.startswith("נשלמה") and line.count(" ") == 2 and "אות" in line:
    #     parsing = False
    elif parsing and line.count(" ") == 0:
        curr_word = line
        text[curr_letter].append("<b>"+curr_word+"</b>")
    elif parsing and curr_word:
        text[curr_letter][-1] += "<br>"+line
#
# root = SchemaNode()
# root.add_primary_titles("Sefer HaShorashim", "ספר השרשים")
en_letters = """Alef
Bet
Gimel
Dalet
Hey
Vav
Zayin
Chet
Tet
Yod
Kaf
Lamed
Mem
Nun
Samech
Ayin
Pay
Tsade
Qof
Resh
Shin
Tav""".splitlines()
en_letters = [node.get_titles('en')[0] for node in library.get_index("Mahberet Menachem").nodes.children[1:-1]]
# for h, e in zip(text.keys(), en_letters):
#     letter_node = JaggedArrayNode()
#     letter_node.add_primary_titles(e, h)
#     letter_node.add_structure(["Paragraph"])
#     letter_node.key = e
#     root.append(letter_node)
# root.validate()
# post_index({"title": "Sefer HaShorashim", "categories": ["Reference"], "schema": root.serialize()})
for h, e in zip(text.keys(), en_letters):

    send_text = {
        "text": text[h],
        "language": "he",
        "versionTitle": "Sefer HaShorashim",
        "versionSource": "http://www.sefaria.org"
    }
    post_text("Sefer HaShorashim, {}".format(e), send_text)
