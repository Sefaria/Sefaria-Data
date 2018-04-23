from bs4 import BeautifulSoup
import re
import os
from sources.functions import *
from sefaria.model import *

def parse_into_chapters(book, contents):
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
                text[chapter] = parse_verses(book, text, chapter)
            assert str(chapter+1) == line.text.replace("Chapitre ", "")
            chapter += 1
            text[chapter] = []
    #parse last chapter; first remove last line of last chapter which is not content
    text[chapter] = text[chapter][0:-1]
    text[chapter] = parse_verses(book, text, chapter) # parse last chapter
    return text


def parse_verses(book, text, ch_num):
    def flag():
        print
        # print book
        # print u"Chapter {}: {}".format(ch_num, verse.text)
        # print u"Previous line: {}\n".format(prev_verse_text)

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


def check_chapters(book, chapters):
    # print out possible mistakes
    for num, chapter in enumerate(chapters):
        if "<p>" in " ".join(chapter):
            print num

    # now check that the chapters all have the right lengths compared to JPS version
    messages = []
    JPS_chapters = TextChunk(Ref(book), lang="en").text
    for i, JPS_ch in enumerate(JPS_chapters):
        diff = len(JPS_ch) - len(chapters[i])
        if diff < 0:
            messages.append("JPS chapter {} is {} segments less than French Wikisource".format(i+1, abs(diff)))
        elif diff > 0:
            messages.append("French Wikisource chapter {} is {} segments less than JPS".format(i+1, abs(diff)))
    if messages:
        print "Issues with {}".format(book)
        for msg in messages:
            print msg



if __name__ == "__main__":
    #parse HTML French Wikisource -- finished
    #remaining problem is \xa0 and space before punctuation marks, need to remove them below
    from sefaria.system.exceptions import InputError
    versionTitle = "Bible du Rabbinat 1899 [fr]"
    ch = 0
    chars = ["?", ".", ",", "!", ":", ";"]
    for book in library.get_indexes_in_category("Tanakh"):
        print book
        index = library.get_index(book)
        version = Version().load({"title": book, "versionTitle": versionTitle})
        version.status = "locked"
        version.license = "Public Domain"
        version.save()
        print """./run scripts/move_draft_text.py "{}" -v "en:{}" --noindex -d "https://www.sefaria.org" -k 'kAEw7OKw5IjZIG4lFbrYxpSdu78Jsza67HgR0gRBOdg'""".format(book, versionTitle)
        while True:
            ch += 1
            try:
                tc = TextChunk(Ref("{} {}".format(book, ch)), lang="en", vtitle=versionTitle)
                verses = tc.text
                for v_num, verse in enumerate(verses):
                    matches = re.findall(u"[\s\xa0][?.,!:;]", verse)
                    for match in matches:
                        print "FOUND {} {}:{}".format(book, ch, v_num+1)
                        desired_char = match[-1]
                        verse = verse.replace(match, desired_char)
                    verses[v_num] = verse
                tc.text = verses
                tc.save(force_save=True)
            except InputError as e:
                ch = 0
                break

    #code below does actual parsing which is finished
        #
        # for ch_num, chapter in enumerate(tc.text):
        #     for v_num, verse in enumerate(chapter):

    #     soup = BeautifulSoup(open("HTML/"+book))
    #     divs = soup.find_all("div", class_="mw-parser-output")
    #     div = [div for div in divs if div.contents != []][0]
    #     contents = div.contents[0].contents
    #     if book == "Obadiah":
    #         contents = contents[11:]
    #         contents[0].string = "Chapitre 1"
    #     chapters = parse_into_chapters(book, contents)
    #     chapters = convertDictToArray(chapters)
    #     check_chapters(book, chapters)
    #     versionSource = "https://fr.wikisource.org/wiki/Bible_du_Rabbinat_1899"
    #     text = {"text": chapters, "versionTitle": versionTitle, "versionSource": versionSource, "language": "en"}
        #post_text(book, text, server="http://draft.sefaria.org")