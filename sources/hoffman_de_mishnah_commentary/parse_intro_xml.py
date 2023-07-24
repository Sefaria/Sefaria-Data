import html
import bleach
from bs4 import BeautifulSoup
import re

ALLOWED_TAGS = ("i", "b", "br", "u", "strong", "em", "big", "small", "img", "sup", "sub", "span", "a")
ALLOWED_ATTRS = {
    'sup': ['class'],
    'span': ['class', 'dir'],
    'i': ['data-overlay', 'data-value', 'data-commentator', 'data-order', 'class', 'data-label', 'dir'],
    'img': lambda name, value: name == 'src' and value.startswith("data:image/"),
    'a': ['dir', 'class', 'href', 'data-ref', "data-ven", "data-vhe"],
}


def convert_hebrew_xml_values_to_he(text):
    return html.unescape(text)


def remove_hanging_text(text):
    # Removes instances of text ending with multiple new lines, and then extra text (i.e. "\n\n Berachot.")
    return re.sub(r"\n\n+.*$", "", text)


def process_xml(file_name, is_nezikin=False):
    # TODO add a nezikin flag
    with open(f'xml/{file_name}', 'r') as f:
        data = f.read()

    intro_dict = {}

    if is_nezikin:
        # Handle nezikin here
        pass

    else:
        intros = re.findall(
            r"<(h1|title)>[TracktRACKA]{7} (.*?)<\/\1>(.*?)ABSC[H]{0,1}NITT", # Between Tractate and first chapter
            data,
            flags=re.DOTALL)

    for tag_name, masechet, intro in intros:
        # TODO - insert footnotes before cleaning, handle nicely the punct (i.e. Moed Katan = MO&#x2018;ED &#x1E32;A&#x1E6C;AN.), images -- see intro to Erubin?
        if "<ftnote" in intro:
            num = intro.count("<ftnote")
            print(f"Masechet {masechet} has {num} footnotes in its intro")
            print(intro)
            print("-------------------------\n")
        clean_text = bleach.clean(intro,
                                  tags=ALLOWED_TAGS,
                                  attributes=ALLOWED_ATTRS,
                                  strip=True)
        text = convert_hebrew_xml_values_to_he(clean_text)
        text = remove_hanging_text(text)
        intro_dict[masechet] = text
    return intro_dict


if __name__ == '__main__':
    # Todo handle footnotes
    # WORKS for: Zeraim, Moed, Naschim, Kodaschim (Meila has a funny german unicode character in it),
    # ALERT: Nezikin must be handled differently!

    files = ["zeraim.xml", "moed.xml", "naschim.xml", "kodaschim.xml", "toharot.xml"]
    for f in files:
        d = process_xml(file_name=f, is_nezikin=False)
    # print(d.keys())
    # for k in d:
    #     print(k)
    #     print(d[k])
    #     print("-----------------------------------------------")
