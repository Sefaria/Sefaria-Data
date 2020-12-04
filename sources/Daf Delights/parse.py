from sources.functions import *
from bs4 import BeautifulSoup, Tag
def get_daf(result):
    if result.count(" ") > 5:
        return ""
    else:
        result = bleach.clean(result, tags="", strip=True).strip()
        masechet, daf = " ".join(result.split()[:-1]), result.split()[-1]
        try:
            library.get_index(masechet)
        except Exception as e:
            return ""
        return "{} {}".format(masechet, (int(daf)*2)-1)#AddressTalmud.toStr("en", (int(daf)*2)-1))


def text_and_daf(contents, found_daf):
    def process(c):
        c = c if c.endswith(" ") else c + " "
        if c in ["(", ")", ",", ".", ":"]:
            c = c.strip()
        elif c.isupper() and len(c) == 1:
            c = c.strip()
        return c
    new_contents = ""
    for i, c in enumerate(contents):
        if not isinstance(c, Tag) and len(c.strip()) > 0:
            c = process(c)
            new_contents += c
        elif isinstance(c, Tag) and len(c.text.strip()) > 0:
            text = c.text.strip()
            if c.name in ["b", "i"]:
                text = "<{}>{}</{}>".format(c.name, text, c.name)
            text = process(text)
            new_contents += text
    c = new_contents.strip()
    c = c.replace(" . ", ". ").replace("( ", "(").replace(" )", ")")
    daf = get_daf(c)
    return c, daf

files = [f for f in os.listdir(".") if f.endswith("html")]
for f in files:
    if "Sanhedrin" not in f:
        continue
    if "errors" in f:
        continue
    text = {}
    next_broken_segment = False
    found_daf = False
    curr_daf = ""
    masechet = ""
    with open(f, 'r') as open_f:
        soup = BeautifulSoup(open_f)
        contents = soup.find('body').contents
        for i, el in enumerate(contents):
            if isinstance(el, Tag):
                if len(el.text.strip()) > 0:
                    result, poss_daf = text_and_daf(el.contents, found_daf)
                    if len(poss_daf) > 0:
                        next_broken_segment = False
                        assert poss_daf not in text
                        masechet = " ".join(poss_daf.split()[:-1])
                        poss_daf = poss_daf.split()[-1]
                        curr_daf = int(poss_daf)
                        text[curr_daf] = ""
                        found_daf = True
                    elif found_daf and result.isupper() and result.count(" ") < 4:
                        next_broken_segment = True
                    elif found_daf:
                        if next_broken_segment:
                            text[curr_daf] = text[curr_daf].strip()
                            text[curr_daf] += " "+result.strip()
                        else:
                            if "(" in text[curr_daf] and ")" not in text[curr_daf].split("(")[-1]:
                                text[curr_daf] += result
                            else:
                                text[curr_daf] += "\n"+result
                        next_broken_segment = False



    root = JaggedArrayNode()
    masechet = library.get_index(masechet)
    root.add_primary_titles("Daf Delights on "+masechet.get_title('en'), "שעשועי הדף "+masechet.get_title('he'))
    root.add_structure(["Daf", "Paragraph"], address_types=["Talmud", "Integer"])
    root.key = "Daf Delights on "+masechet.get_title('en')
    indx = {
        "schema": root.serialize(),
        "title": root.key,
        "categories": ["Modern Works", "Commentary"],
        "dependence": "Commentary",
        "base_text_titles": [masechet.get_title('en')]
    }
    post_index(indx)
    text = convertDictToArray(text, empty="")
    text = [daf.splitlines() for daf in text]
    send_text = {
        "language": "en",
        "versionTitle": "Daf Delights, Rabbi Zev Reichman, 2017-2019",
        "versionSource": "https://www.nli.org.il/he/books/NNL_ALEPH004779793",
        "text": text
    }
    post_text(root.key, send_text)