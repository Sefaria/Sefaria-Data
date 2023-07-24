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


def process_xml():
    with open('xml/zeraim.xml', 'r') as f:
        data = f.read()

    intro_dict = {}

    intros = re.findall(r"<title>Traktat (.*?).<\/title>(.*?)ABSCHNITT", data, flags=re.DOTALL)

    for masechet, intro in intros:

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
    # Run code on all sedarim - figure out separateing combined intros, like a bunch in Nezikin
    d = process_xml()
    for k in d:
        print(k)
        print(d[k])
        print("-----------------------------------------------")

