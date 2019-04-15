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

def parsha_name(current_parsha, current_sefer):
    return library.get_index(current_sefer).alt_structs["Parasha"]["nodes"][current_parsha]["sharedTitle"]

if __name__ == "__main__":
    # site = requests.get("http://www.hebrew.grimoar.cz/rekanati_al_ha-torah.html",
    #                     headers={'User-Agent': 'Mozilla/4.0 (Macintosh; Intel Mac OS X 11_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'})
    # f = open("recanati.txt", 'w')
    # f.write(site.content)
    text = {}
    current_parsha = current_sefer = 0
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
            else:
                text[current_sefer][parsha_name(current_parsha, current_sefer)].append(el.text)

    root = SchemaNode()
    root.add_primary_titles("Recanati on the Torah", u"רקנאטי על התורה")
    root.key = "recanati"
    for sefer, parshiot in text.items():
        sefer_node = SchemaNode()
        sefer_node.key = sefer
        sefer_node.add_primary_titles(sefer, library.get_index(sefer).get_title('he'))

        for parsha, comments in parshiot.items():
            parsha_node = JaggedArrayNode()
            parsha_node.add_primary_titles(parsha, Term().load({"name": parsha}).get_primary_title("he"))
            parsha_node.add_structure(["Paragraph"])
            sefer_node.append(parsha_node)

        sefer_node.validate()
        root.append(sefer_node)
    root.validate()

    index = {
        "schema": root.serialize(),
        "title": "Recanati on the Torah",
        "categories": ["Tanakh", "Commentary"]
    }
    #post_index(index, server=SEFARIA_SERVER)


    for sefer, parshiot in text.items():
        for parsha, comments in parshiot.items():
            send_text = {
                "text": comments,
                "versionTitle": "Recanati on the Torah",
                "versionSource": "http://www.hebrew.grimoar.cz/rekanati_al_ha-torah.html",
                "language": "he"
            }
            #post_text("Recanati on the Torah, {}, {}".format(sefer, parsha), send_text, server=SEFARIA_SERVER, index_count="on")
            new_links = match_ref_interface(Ref("Parashat " + parsha), comments, lambda x: x.split(), dh_extracter)

            pass

