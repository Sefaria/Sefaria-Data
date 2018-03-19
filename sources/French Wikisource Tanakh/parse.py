from bs4 import BeautifulSoup
import re
import os
from sources.functions import convertDictToArray

def parse_into_chapters(contents):
    # remove \n
    contents = [line for line in contents if line != "\n"]
    text = {}
    chapter = 0
    for line_n, line in enumerate(contents):
        assert hasattr(line, "text")
        if line.text.find("Chapitre ") == -1:
            if chapter == 0:
                continue
            text[chapter].append(line)
        else:
            if chapter >= 1: # there is already a chapter, so parse its verses
                text[chapter] = parse_verses(text, chapter)
            assert str(chapter+1) == line.text.replace("Chapitre ", "")
            chapter += 1
            text[chapter] = []
    #parse last chapter; first remove last line of last chapter which is not content
    text[chapter] = text[chapter][0:-1]
    text[chapter] = parse_verses(text, chapter) # parse last chapter
    return text


def parse_verses(text, ch_num):
    def flag():
        print u"Chapter {}: {}".format(ch_num, verse.text)
        print u"Previous line: {}\n".format(prev_verse_text)

    chapter = text[ch_num]
    prev_verse = 0
    lines = []
    for verse in chapter:
        if not verse.text:
            continue
        match = re.compile("^(\d+) (.*)").match(verse.text)
        if match:
            verse_num, verse_text = int(match.group(1)), match.group(2)
            if verse_num - 1 != prev_verse:
                flag()
                assert verse_num - 2 == prev_verse
                lines.append(u"")
            lines.append(verse_text)
            prev_verse = verse_num
            prev_verse_text = verse.text
        else:
            flag()
            verse_text = verse.text
            prev_verse += 1
            prev_verse_text = verse.text
            lines.append(verse_text)
    return lines


def check_chapters(chapters):
    for num, chapter in enumerate(chapters):
        if "<p>" in " ".join(chapter):
            print num

if __name__ == "__main__":
    book_files = os.listdir("HTML")
    for book in book_files:
        print book
        soup = BeautifulSoup(open("HTML/"+book))
        divs = soup.find_all("div", class_="mw-parser-output")
        div = [div for div in divs if div.contents != []][0]
        contents = div.contents[0].contents
        if book == "Obadiah":
            contents = contents[11:]
            contents[0].string = "Chapitre 1"
        chapters = parse_into_chapters(contents)
        chapters = convertDictToArray(chapters)
        check_chapters(chapters)
        versionTitle = "Bible du Rabbinat 1899 [fr]"
        versionSource = "https://fr.wikisource.org/wiki/Bible_du_Rabbinat_1899"
        text = {"text": chapters, "versionTitle": versionTitle, "versionSource": versionSource, "language": "en"}
        #post_text(book, text, server="http://draft.sefaria.org")