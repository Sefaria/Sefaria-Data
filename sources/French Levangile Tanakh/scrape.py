from sources.functions import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome("/Users/stevenkaplan/Downloads/chromedriver94", chrome_options=chrome_options)

for cat in ["Tanakh", "Prophets", "Writings"]:
    for b, book in enumerate(sorted([library.get_index(i) for i in library.get_indexes_in_category(cat)], key=lambda x: int(x.order[0]))):
        for p, perek in enumerate(book.all_section_refs()):
            url = f"https://www.levangile.com/Bible-CAH-{b+1}-{p+1}-1-complet-Contexte-oui.htm"
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
                    fileToWrite = open(f"{book.title}_{p+1}.html", "w")
                    fileToWrite.write(pageSource)
                    fileToWrite.close()
                else:
                    print("Can't find {} {}".format(book, perek))