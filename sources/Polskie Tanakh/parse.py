import requests
import django
django.setup()
import csv
from sefaria.model import *
from bs4 import BeautifulSoup, Tag, NavigableString
import re
from sources.functions import *

def create_url(book, chapter):
    assert book > 0
    assert chapter > 0
    url = "http://bibliepolskie.pl/zzteksty_ch.php?wid=18&book={}&chapter={}&e=".format(book, chapter)
    return url

books = library.get_indexes_in_category("Tanakh")
polish_order = """Genesis
Exodus
Leviticus
Numbers
Deuteronomy
Joshua
Judges
Ruth
I Samuel
II Samuel
I Kings
II Kings




Esther
Job
Psalms
Proverbs
Ecclesiastes
Song of Songs
Isaiah
Jeremiah
Lamentations
Ezekiel

Hosea
Joel
Amos
Obadiah
Jonah
Micah
Nahum
Habakkuk
Zephaniah
Haggai
Zechariah
Malachi""".splitlines()
text_info = {}
def get_tanakh():
    for book_n, book in enumerate(polish_order):
        if not book:
            continue
        print(book)
        found_something = False
        chapters = library.get_index(book).all_section_refs()
        opening = """Index Title,{}
        Version Title,Bible in Polish, trans. Izaak Cylkow, 1841-1908 [pl]
        Language,en
        Version Source,http://bibliepolskie.pl/
        Version Notes,""".format(book).splitlines()
        with open("{}.csv".format(book), 'w') as csv_f:
            writer = csv.writer(csv_f)
            for line in opening:
                writer.writerow(line.split(",", 1))
            for ch_n, chapter in enumerate(chapters):
                url = create_url(book_n+1, ch_n+1)
                content = requests.get(url).content
                soup = BeautifulSoup(content)
                strings = [str(element) for element in soup.find("div", {"class": re.compile(r'tekst-tlum')}).contents if
                           isinstance(element, NavigableString)]
                for line_n, line in enumerate(strings):
                    found_something = True
                    ref = "{} {}:{}".format(book, ch_n+1, line_n+1)
                    writer.writerow([ref, line])
            if not found_something:
                print()


def get_text(book):
    text = {}
    with open("{}.csv".format(book), 'r') as f:
        for row in csv.reader(f):
            ref, comment = row
            if ref.startswith(book):
                ch, verse = ref.split(book)[-1].split(":")
                if int(ch) not in text:
                    text[int(ch)] = []
                text[int(ch)].append(comment)
    return text


def move_extra(book, corrected_text=None):
    skip_next = False
    def print_func(book, chapter, diff):
        more_or_less = "more" if diff > 0 else "less"
        message = "{} Chapter {}: Sefaria text has {} {} verses than Polish".format(book, chapter, abs(diff), more_or_less)
        print(message)
    if not corrected_text:
        corrected_text = get_text(book)
    ch_diff = len(corrected_text.keys()) - len(library.get_index(book).all_section_refs())
    if abs(ch_diff) > 0:
        print(book)
        print(ch_diff)
    for chapter, polish_verses in corrected_text.items():
        polish_num_verses = len(polish_verses)
        actual_num_verses = len(Ref("{} {}".format(book, chapter)).all_segment_refs())
        diff = actual_num_verses - polish_num_verses
        if abs(diff) > 0:
            if skip_next:
                skip_next = False
                continue
            if chapter+1 not in corrected_text.keys():
                print_func(book, chapter, diff)
            else:
                actual_next_ch_num_verses = len(Ref("{} {}".format(book, chapter + 1)).all_segment_refs())
                polish_next_ch_verses = len(corrected_text[chapter + 1])
                next_ch_diff = actual_next_ch_num_verses - polish_next_ch_verses
                if diff + next_ch_diff == 0:
                    corrected_text[chapter], corrected_text[chapter+1] = move_text(corrected_text, chapter, diff)
                    skip_next = True
                else:
                    print_func(book, chapter, diff)
    if not corrected_text:
        return move_extra(book, corrected_text)
    else:
        return convertDictToArray(corrected_text)


def move_text(text, chapter, amount):
    if amount < 0:
        relevant_chapter = chapter
        verses = text[chapter]
        extra = verses[amount:]
        text[chapter+1] = extra + text[chapter+1]
        text[chapter] = verses[:amount]
    else:
        relevant_chapter = chapter+1
        verses = text[chapter+1]
        extra = text[chapter+1][:amount]
        text[chapter] += extra
        text[chapter+1] = text[chapter+1][amount:]
    return text[chapter], text[chapter+1]



if __name__ == "__main__":
    start = "Song of Songs"
    for book_n, book in enumerate(polish_order):
        if not book:
            continue
        # if book == start and start:
        #     start = ""
        # if start:
        #     continue
        text = move_extra(book)
        send_text = {
            "versionTitle": "Bible in Polish, trans. Izaak Cylkow, 1841 - 1908 [pl]",
            "language": "en",
            "versionSource": "http://bibliepolskie.pl/",
            "text": text
        }
        post_text(book, send_text)