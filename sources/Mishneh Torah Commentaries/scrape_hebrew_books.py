from sources.functions import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
from bs4 import BeautifulSoup, Tag
import os
import time


def rambam_pages(driver):
    start = False
    start_url = "https://www.hebrewbooks.org/rambam.aspx?sefer=14&hilchos=79&perek=1&halocha=1"
    with open('results.txt', 'a') as f:
        cats = ["Sefer Madda", "Sefer Ahavah", "Sefer Zemanim", "Sefer Nashim", "Sefer Kedushah", "Sefer Haflaah",
                "Sefer Zeraim", "Sefer Avodah", "Sefer Korbanot", "Sefer Taharah", "Sefer Nezikim", "Sefer Kinyan",
                "Sefer Mishpatim", "Sefer Shoftim"]
        start_cat = 0
        total_books = 0
        for c, cat in enumerate(cats):
            if c == 2:
                total_books -= 1
            f.write(cat + "\n")
            curr_books = sorted([library.get_index(i) for i in library.get_indexes_in_category(cat)],
                                key=lambda x: int(x.order[0]))
            for b, book in enumerate(curr_books):
                f.write(book.title + "\n")
                book = book.title
                print(book)
                perek_pasuk = []
                for seg in library.get_index(book).all_segment_refs():
                    perek_pasuk.append(seg.sections)
                for perek, pasuk in perek_pasuk:
                    url = "https://www.hebrewbooks.org/rambam.aspx?sefer={}&hilchos={}&perek={}&halocha={}".format(
                        c + 1, b + 1 + total_books, perek, pasuk)
                    if start_url == url:
                        start = True
                    if start:
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
                                fileToWrite = open("hebrew books/{}/{} {},{}.html".format(c, book, perek, pasuk), "w")
                                fileToWrite.write(pageSource)
                                fileToWrite.close()
                            else:
                                f.write("\nCan't find {}".format(url))
            if c >= start_cat:
                total_books += len(curr_books)
        driver.quit()


def lechem_pages(driver, can_delete=False, raavad=False):
    deleted = 0
    lechem_pages_dict = defaultdict(dict)

    for dir in os.listdir("hebrew books/"):
        if not dir.isdigit():
            continue
        for f in os.listdir("hebrew books/" + dir + "/"):
            if f.endswith("html"):
                book = " ".join(f.split()[:-1])
                perek_pasuk = f.split()[-1].replace(".html", "")
                perek_pasuk = perek_pasuk.replace(',', ":")
                perek, pasuk = perek_pasuk.split(":")
                perek = int(perek)
                pasuk = int(pasuk)
                if f.endswith("html"):
                    delete = True
                    soup = BeautifulSoup(open("hebrew books/" + dir + "/" + f, 'r'))
                    if raavad and soup.find("div", {"class": "raavad"}):
                        if [l for l in soup.find("div", {"class": "raavad"}).contents if isinstance(l, Tag) and l.attrs.get("class", "") == ["five"]]:
                            raavads = [l for l in soup.find("div", {"class": "raavad"}).contents if isinstance(l, Tag) and l.attrs.get("class", "") == ["five"]]
                            delete = False
                            if perek not in lechem_pages_dict[book]:
                                lechem_pages_dict[book][perek] = defaultdict(dict)
                            lechem_pages_dict[book][perek][pasuk] = [r.text.strip() for r in raavads]
                    else:
                        a_tags = soup.find_all("a")
                        for a_tag in a_tags:
                            if a_tag.text == """השגות הראבד""":
                                delete = False
                                if perek not in lechem_pages_dict[book]:
                                    lechem_pages_dict[book][perek] = defaultdict(dict)
                                lechem_pages_dict[book][perek][pasuk] = "http://hebrewbooks.org/" + a_tag["href"]
                    if can_delete and delete:
                        os.remove("hebrew books/" + f)
                        deleted += 1
    print(deleted)
    return lechem_pages_dict


books = [Index().load({'title': 'Mishneh Torah, Sacrificial Procedure'}),
         Index().load({'title': 'Mishneh Torah, Sacrifices Rendered Unfit'}),
         Index().load({'title': 'Mishneh Torah, Paschal Offering'}),
         Index().load({'title': 'Mishneh Torah, Festival Offering'}),
         Index().load({'title': 'Mishneh Torah, Offerings for Unintentional Transgressions'}),
         Index().load({'title': 'Mishneh Torah, Offerings for Those with Incomplete Atonement'}),
         Index().load({'title': 'Mishneh Torah, Substitution'}),
         Index().load({'title': 'Mishneh Torah, Damages to Property'}),
         Index().load({'title': 'Mishneh Torah, Theft'}),
         Index().load({'title': 'Mishneh Torah, One Who Injures a Person or Property'}),
         Index().load({'title': 'Mishneh Torah, Sales'}),
         Index().load({'title': 'Mishneh Torah, Neighbors'}),
         Index().load({'title': 'Mishneh Torah, Agents and Partners'}),
         Index().load({'title': 'Mishneh Torah, Slaves'}),
         Index().load({'title': 'Mishneh Torah, Hiring'}),
         Index().load({'title': 'Mishneh Torah, Plaintiff and Defendant'}),
         Index().load({'title': 'Mishneh Torah, Inheritances'}),
         Index().load({'title': 'Mishneh Torah, The Sanhedrin and the Penalties within their Jurisdiction'}),
         Index().load({'title': 'Mishneh Torah, Testimony'}),
         Index().load({'title': 'Mishneh Torah, Rebels'}),
         Index().load({'title': 'Mishneh Torah, Mourning'}),
         Index().load({'title': 'Mishneh Torah, Kings and Wars'})]

books = [b.title for b in library.get_indexes_in_category("Mishneh Torah")]
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome("/Users/stevenkaplan/Downloads/chromedriver", chrome_options=chrome_options)
perakim_that_matter = ["Hasagot HaRaavad on Mishneh Torah, Marriage"]
perakim_that_matter = [p.replace("Hasagot HaRaavad on ", "") for p in perakim_that_matter]
# rambam_pages(driver)
#
text_dict = lechem_pages(driver, raavad=True)
# before_sanhedrin = lechem_pages(driver)
#
# #
# # # before_sanhedrin.update(after_sanhedrin)
# start_book = "Mishneh Torah, Sacrifices Rendered Unfit"
# start_ch = 3
# start = True
# for book in before_sanhedrin:
#     if book != start_book and not start:
#         continue
#     for perek in sorted(before_sanhedrin[book].keys()):
#         if perek == start_ch:
#             start = True
#         if start and book in perakim_that_matter:
#             print(book)
#             for pasuk in before_sanhedrin[book][perek]:
#                 url = before_sanhedrin[book][perek][pasuk]
#                 source = selenium_get_url("/Users/stevenkaplan/Downloads/chromedriver94", url)
#                 with open("Hasagot HaRaavad html/{} {} {}.html".format(book, perek, pasuk), 'w') as f:
#                     f.write(source)
# text_dict = {}
# for f in os.listdir("Hasagot HaRaavad html"):
#     if not f.endswith("html"):
#         continue
#     perek = int(f.split()[-2])
#     pasuk = int(f.split()[-1].replace('.html', ''))
#     book = " ".join(f.split()[:-2])
#     if book not in perakim_that_matter:
#         continue
#     if book not in text_dict:
#         text_dict[book] = {}
#     if perek not in text_dict[book]:
#         text_dict[book][perek] = {}
#     text_dict[book][perek][pasuk] = []
#     orig = f
#     with open("Hasagot HaRaavad html/" + f, 'r') as f:
#         print(f)
#         soup = BeautifulSoup(f)
#         el = soup.find(class_="peirush")
#         for i, line in enumerate(el.contents):
#             line_text = line.text if isinstance(line, Tag) else str(line)
#             if isinstance(line, Tag) and line.get('class', None) in [["five"], ["four"]]:
#                 text_dict[book][perek][pasuk].append("<b>{}</b>".format(line_text))
#                 continue
#             elif isinstance(line, Tag) and line.get('class', False) != False:
#                 text_dict[book][perek][pasuk].append(line_text)
#             elif line_text.strip() != "":
#                 if len(text_dict[book][perek][pasuk]) == 0:
#                     print(orig)
#                     text_dict[book][perek][pasuk].append(line_text)
#                 else:
#                     text_dict[book][perek][pasuk][-1] += line_text
curr_hasagot = [x for x in library.get_indexes_in_category("Mishneh Torah", include_dependant=True) if x.startswith("Hasagot HaRaav")]
new_ones = [x for x in text_dict if "Hasagot HaRaavad on " + x not in curr_hasagot]
for book in text_dict:
    if book not in new_ones:
        continue
    root = JaggedArrayNode()
    index = library.get_index(book)
    subcat = index.categories[-1]
    book_he = index.get_title('he')
    root.add_primary_titles("Hasagot HaRaavad on {}".format(book),  """השגות הראב"ד על {}""".format(book_he))
    root.key = "Hasagot HaRaavad on {}".format(book)
    root.add_structure(["Chapter", "Halakhah", "Paragraph"])
    root.validate()
    indx = {
        "schema": root.serialize(),
        "dependence": "Commentary",
        "base_text_titles": [book],
        "base_text_mapping": "many_to_one",
        "title": "Hasagot HaRaavad on {}".format(book),
        "categories": ["Halakhah", "Mishneh Torah", "Commentary", "Hasagot HaRaavad", subcat],
        "collective_title": "Hasagot HaRaavad"
    }
    add_category(subcat, indx["categories"], server="https://www.sefaria.org")
    post_index(indx, server="https://www.sefaria.org")
    for perek in text_dict[book]:
        text_dict[book][perek] = convertDictToArray(text_dict[book][perek])
    text_dict[book] = convertDictToArray(text_dict[book])
    send_text = {
        "text": text_dict[book],
        "language": "he",
        "versionTitle": "Friedberg Edition",
        "versionSource": "https://fjms.genizah.org/"
    }
    post_text("Hasagot HaRaavad on {}".format(book), send_text, server="https://www.sefaria.org")
