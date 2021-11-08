from sources.functions import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import re
from bs4 import BeautifulSoup
curr_books = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua",
               "Judges", "Ruth", "I Samuel", "II Samuel", "I Kings", "II Kings", "I Chronicles",
                  "II Chronicles", "Ezra", "Nehemiah", "Esther", "Job", "Psalms",
                  "Proverbs", "Ecclesiastes", "Song of Songs", "Isaiah", "Jeremiah", "Lamentations",
                  "Ezekiel", "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah",
                  "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi"]
def scrape():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome("/Users/stevenkaplan/Downloads/chromedriver94", chrome_options=chrome_options)

    total = 0

    for b, book in enumerate(curr_books):
        for p, perek in enumerate(library.get_index(book).all_section_refs()):
            url = f"https://www.levangile.com/Bible-CAH-{b+1+total}-{p+1}-1-complet-Contexte-oui.htm"
            print(url)
            driver.get(url)
            retrieved = True
            try:
                driver.get(url)
            except Exception as e:
                print(e)
                try:
                    driver.get(url)
                except Exception as e:
                    print("Double fault!")
                    retrieved = False
            if retrieved:
                pageSource = driver.page_source
                print("retrieved")
                if len(pageSource) > 16000:
                    print(url)
                    fileToWrite = open(f"{book}_{p+1}.html", "w")
                    fileToWrite.write(pageSource)
                    fileToWrite.close()
                else:
                    print("Can't find {} {}".format(book, perek))


def parse():
    books = {}
    for f in sorted(os.listdir(".")):
        if f.endswith("html") and not f.startswith("errors"):
            ref = f.replace('.html', '').replace("_", " ")
            book, ch = f.replace('.html', '').split("_")
            if book not in books:
                books[book] = {}
            soup = BeautifulSoup(open(f, 'r'))
            num_verses = len(soup.find_all('span', {"class": "verset 1902"}))
            diff = num_verses - len(Ref(ref).all_segment_refs())
            if diff > 0:
                print(f"{ref} in French has {diff} more verses")
            elif diff < 0:
                print(f"{ref} in French has {-1*diff} less verses")
            spans = soup.find_all('span', {"class": "verset 1902"})

            # make sure we have verses in order
            verse_nums = [int(s.text.strip()) for s in spans]
            assert len(verse_nums) == verse_nums[-1]
            assert sorted(verse_nums) == verse_nums

            # now get the text
            text = [re.sub("[;?@:!]", "", str(s.nextSibling).strip().replace("\xa0", "")) if isinstance(s.nextSibling, NavigableString) else None for s in spans]
            assert None not in text
            books[book][int(ch)] = text

    for book in books:
        if len(library.get_index(book).all_section_refs()) != len(books[book].keys()):
            print(book)
        books[book] = convertDictToArray(books[book])
        send_text = {"language": "en", "versionTitle": "La Bible, Traduction Nouvelle, Samuel Cahen, 1831 [fr]",
                     "versionSource": "https://www.levangile.com/Bible-CAH-1-1-1-complet-Contexte-oui.htm", "text": books[book]}
        post_text(book, send_text, server="http://localhost:8000")


if __name__ == "__main__":
    parse()