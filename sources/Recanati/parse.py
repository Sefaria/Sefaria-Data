#encoding=utf-8
import django
django.setup()
from sefaria.model import *
import requests
from bs4 import BeautifulSoup, Tag
from data_utilities.dibur_hamatchil_matcher import *
from sources.functions import *

def dh_extracter(str):
    dh = str.split(".", 1)[0]
    if len(dh.split()) < 8:
        return dh
    else:
        return u" ".join(str.split()[0:8])


def remove_apostrophe(str):
    arr = re.findall(u"\(.*\s.*\s.*?\)", str)
    if arr:
        for el in arr:
            if len(el.split()) == 3 and el.split(u"'") > 2:
                new_el = el.replace(u"'", u"", 1)
                str = str.replace(el, new_el)
    return str


def parsha_name(current_parsha, current_sefer):
    return library.get_index(current_sefer).alt_structs["Parasha"]["nodes"][current_parsha]["sharedTitle"]

if __name__ == "__main__":

    # site = requests.get("http://www.hebrew.grimoar.cz/rekanati_al_ha-torah.html",
    #                     headers={'User-Agent': 'Mozilla/4.0 (Macintosh; Intel Mac OS X 11_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'})
    # f = open("recanati.txt", 'w')
    # f.write(site.content)
    text = {}
    current_parsha = current_sefer = 0
    parshiot = []
    with open("recanati.html") as f:
        soup = BeautifulSoup(f)
        contents = soup.contents[1].contents[2].contents[2:]
        contents = [el for el in contents if isinstance(el, Tag)]
        for n, el in enumerate(contents):
            if el.name == "h2" and el.text.strip().startswith(u"ספר"):
                current_sefer = library.get_index(el.text.split()[1]).title
                text[current_sefer] = {}
                current_parsha = -1
            elif el.contents and el.contents[0].name == "b" \
                    and el.text.strip().startswith(u"פרשת"):
                current_parsha += 1
                text[current_sefer][parsha_name(current_parsha, current_sefer)] = []
                parshiot.append(parsha_name(current_parsha, current_sefer))
            else:
                text[current_sefer][parsha_name(current_parsha, current_sefer)].append(remove_apostrophe(el.text))

    root = SchemaNode()
    root.add_primary_titles("Recanati on the Torah", u"רקנאטי על התורה")
    root.key = "recanati"
    for parsha in parshiot:
        parsha_node = JaggedArrayNode()
        parsha_node.add_primary_titles(parsha, Term().load({"name": parsha}).get_primary_title("he"))
        parsha_node.add_structure(["Paragraph"])
        root.append(parsha_node)

    root.validate()

    index = {
        "schema": root.serialize(),
        "title": "Recanati on the Torah",
        "categories": ["Kabbalah"],
        "dependence": "Commentary",
    }
    post_index(index, server=SEFARIA_SERVER)

    links = []
    for sefer, parshiot in text.items():
        for parsha, comments in parshiot.items():
            print parsha
            send_text = {
                "text": comments,
                "versionTitle": "Recanati on the Torah",
                "versionSource": "http://www.hebrew.grimoar.cz/rekanati_al_ha-torah.html",
                "language": "he"
            }
            post_text("Recanati on the Torah, {}".format(parsha), send_text, server=SEFARIA_SERVER, index_count="on")
            new_links = match_ref_interface("Parashat " + parsha, "Recanati on the Torah, {}".format(parsha), comments, lambda x: x.split(), dh_extracter)

            links.extend(new_links)
    #post_link(links, server=SEFARIA_SERVER)

