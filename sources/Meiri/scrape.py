from sources.functions import *
import requests
from bs4 import BeautifulSoup, Tag
import bleach

def extract_comments(comment):
    comments = []
    comment = comment.replace("<p>", "").replace("</p>", "")
    comment = re.sub("<a.*?>", "", comment).replace("</a>", "")
    comment = bleach.clean(comment, tags=["b"], strip=True)  # re.sub("<span.*?>", "", comment)
    x = len(comment.split(":\n<b>"))
    v = len(comment.split(":"))

    for subcomment in comment.split(":\n<b>"):
        subcomment = subcomment.strip()
        if subcomment:
            if not subcomment.startswith("<b>") and "</b>" in subcomment:
                subcomment = "<b>" + subcomment
            if not subcomment.endswith(":"):
                subcomment += ":"
            comments.append(subcomment)
    return comments

def dher(str):
    dh = " ".join(bleach.clean(str, tags=[], strip=True).split()[:8])
    return dh

content = requests.get("https://he.wikisource.org/wiki/%D7%9E%D7%90%D7%99%D7%A8%D7%99_%D7%A2%D7%9C_%D7%94%D7%A9%22%D7%A1/%D7%91%D7%A8%D7%9B%D7%95%D7%AA", headers=headers)
soup = BeautifulSoup(content.content)
a_tags = ["https://he.wikisource.org"+a["href"] for a in soup.find("div", {"class": "mw-parser-output"}).contents[0].find_all("a")[1:]]
for a_tag in a_tags:
    print(a_tag)
perakim_url = """https://he.wikisource.org/wiki/%D7%9E%D7%90%D7%99%D7%A8%D7%99_%D7%A2%D7%9C_%D7%94%D7%A9%22%D7%A1/%D7%91%D7%A8%D7%9B%D7%95%D7%AA/%D7%94%D7%A7%D7%93%D7%9E%D7%94
https://he.wikisource.org/wiki/%D7%9E%D7%90%D7%99%D7%A8%D7%99_%D7%A2%D7%9C_%D7%94%D7%A9%22%D7%A1/%D7%91%D7%A8%D7%9B%D7%95%D7%AA/%D7%A4%D7%A8%D7%A7_%D7%90
https://he.wikisource.org/wiki/%D7%9E%D7%90%D7%99%D7%A8%D7%99_%D7%A2%D7%9C_%D7%94%D7%A9%22%D7%A1/%D7%91%D7%A8%D7%9B%D7%95%D7%AA/%D7%A4%D7%A8%D7%A7_%D7%91
https://he.wikisource.org/wiki/%D7%9E%D7%90%D7%99%D7%A8%D7%99_%D7%A2%D7%9C_%D7%94%D7%A9%22%D7%A1/%D7%91%D7%A8%D7%9B%D7%95%D7%AA/%D7%A4%D7%A8%D7%A7_%D7%92
https://he.wikisource.org/wiki/%D7%9E%D7%90%D7%99%D7%A8%D7%99_%D7%A2%D7%9C_%D7%94%D7%A9%22%D7%A1/%D7%91%D7%A8%D7%9B%D7%95%D7%AA/%D7%A4%D7%A8%D7%A7_%D7%93
https://he.wikisource.org/wiki/%D7%9E%D7%90%D7%99%D7%A8%D7%99_%D7%A2%D7%9C_%D7%94%D7%A9%22%D7%A1/%D7%91%D7%A8%D7%9B%D7%95%D7%AA/%D7%A4%D7%A8%D7%A7_%D7%94
https://he.wikisource.org/wiki/%D7%9E%D7%90%D7%99%D7%A8%D7%99_%D7%A2%D7%9C_%D7%94%D7%A9%22%D7%A1/%D7%91%D7%A8%D7%9B%D7%95%D7%AA/%D7%A4%D7%A8%D7%A7_%D7%95
https://he.wikisource.org/wiki/%D7%9E%D7%90%D7%99%D7%A8%D7%99_%D7%A2%D7%9C_%D7%94%D7%A9%22%D7%A1/%D7%91%D7%A8%D7%9B%D7%95%D7%AA/%D7%A4%D7%A8%D7%A7_%D7%96
https://he.wikisource.org/wiki/%D7%9E%D7%90%D7%99%D7%A8%D7%99_%D7%A2%D7%9C_%D7%94%D7%A9%22%D7%A1/%D7%91%D7%A8%D7%9B%D7%95%D7%AA/%D7%A4%D7%A8%D7%A7_%D7%97
https://he.wikisource.org/wiki/%D7%9E%D7%90%D7%99%D7%A8%D7%99_%D7%A2%D7%9C_%D7%94%D7%A9%22%D7%A1/%D7%91%D7%A8%D7%9B%D7%95%D7%AA/%D7%A4%D7%A8%D7%A7_%D7%98""".splitlines()
text = {}
intro = perakim_url[0]
intro = requests.get(intro, headers=headers)
intro = BeautifulSoup(intro.content)
intro = [extract_comments(str(el))[0] for el in intro.find("div", {"class": "mw-parser-output"}).contents if isinstance(el, Tag)]


send_text = {
    "text": intro,
    "language": "he",
    "versionTitle": "Wikisource",
    "versionSource": "https://he.wikisource.org/wiki/%D7%9E%D7%90%D7%99%D7%A8%D7%99_%D7%A2%D7%9C_%D7%94%D7%A9%22%D7%A1/%D7%91%D7%A8%D7%9B%D7%95%D7%AA"
}
post_text("Meiri on Berakhot, Introduction", send_text)

perakim_url = perakim_url[1:]
for i, perek_url in enumerate(perakim_url):
    # with open("perek {}.html".format(i+1), 'r') as f:
        content = requests.get(perek_url, headers=headers).content
        soup = BeautifulSoup(content)
        daf_headers = [daf for daf in soup.find_all("h2") if 2 <= daf.text.count(" ") < 4 and daf.text.startswith("דף")]
        curr = daf_headers[0]
        while "NewPP" not in curr:
            if isinstance(curr, Tag) and curr.name == "h2" and curr not in daf_headers:
                break
            if curr.name == "h2":
                daf = curr.contents[1].text
                daf = daf.split()[1]
                amud = curr.contents[1].text.split()[2]
                daf = getGematria(daf) * 2
                daf = daf-1 if """ע"א""" in curr.text or "עמוד א" in curr.text else daf
                if daf not in text:
                    text[daf] = []
            elif curr.name == "p":
                text[daf] += extract_comments(str(curr))

            curr = curr.next_sibling
links = []
for daf in text:
    comments = text[daf]
    he_daf = AddressTalmud.toStr("en", daf)
    links += match_ref_interface("Berakhot "+he_daf, "Meiri on Berakhot "+he_daf, comments, lambda x: x.split(), dh_extract_method=dher)

root = SchemaNode()
root.add_primary_titles("Meiri on Berakhot", "מאירי על ברכות")
root.key = "Meiri on Berakhot"
intro = JaggedArrayNode()
intro.key = "Introduction"
intro.add_shared_term("Introduction")
intro.add_structure(["Paragraph"])
intro.validate()
default = JaggedArrayNode()
default.default = True
default.key = "default"
default.add_structure(["Talmud", "Integer"])
default.validate()
root.append(intro)
root.append(default)
root.validate()

post_index(
    {"title": "Meiri on Berakhot", "schema": root.serialize(),
     "dependence": "Commentary", "base_text_titles": ["Berakhot"],
     "categories": ["Talmud", "Bavli", "Commentary", "Chidushei HaMeiri"]})

text = convertDictToArray(text)
send_text = {
    "text": text,
    "language": "he",
    "versionTitle": "Wikisource",
    "versionSource": "https://he.wikisource.org/wiki/%D7%9E%D7%90%D7%99%D7%A8%D7%99_%D7%A2%D7%9C_%D7%94%D7%A9%22%D7%A1/%D7%91%D7%A8%D7%9B%D7%95%D7%AA"
}
post_text("Meiri on Berakhot", send_text)



post_link(links)
print(links)
