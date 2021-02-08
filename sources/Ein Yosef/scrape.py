from sources.functions import *
from bs4 import BeautifulSoup, Tag
import requests
import bleach
root = JaggedArrayNode()
root.add_primary_titles("Ein Yosef on Sefer HaMitzvot", "עין יוסף על ספר המצוות")
root.key = "Ein Yosef on Sefer HaMitzvot"
root.add_structure(["Mitzvah", "Paragraph"])
root.validate()
indx = {
    "title": root.key,
    "categories": ["Halakhah", "Commentary"],
    "schema": root.serialize(),
    "dependence": "Commentary",
    "base_text_titles": ["Sefer HaMitzvot"],
}
#post_index(indx)

r = requests.get("https://he.wikisource.org/wiki/%D7%A2%D7%99%D7%9F_%D7%99%D7%95%D7%A1%D7%A3", headers=headers)
soup = BeautifulSoup(r.content)
elements = [x for x in soup.find_all("div")[11].contents[11].contents[2].contents[0].contents[0].contents[2:] if isinstance(x, Tag)]
text = {}
for el in elements:
    href = "https://he.wikisource.org" + el["href"]
    print(href)
    siman = el.text.split("-")[0]
    r = requests.get(href, headers=headers)
    soup = BeautifulSoup(r.content)
    arr = [x for x in soup.find("div", {"class": "mw-parser-output"}).contents if isinstance(x, Tag) and x.name == "p"]
    text[getGematria(siman)] = [bleach.clean(str(x).replace("<p>", "").replace("</p>", ""), tags=["i", "b"],  strip=True) for x in arr]
    text[getGematria(siman)][0] = text[getGematria(siman)][0].replace("<i>", "<b>").replace("</i>", "</b>")
send_text = {
    "versionTitle": "Ein Yosef, Jerusalem, 1974",
    "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH002043124/NLI",
    "language": "he",
    "text": convertDictToArray(text)
}
post_text(root.key, send_text)