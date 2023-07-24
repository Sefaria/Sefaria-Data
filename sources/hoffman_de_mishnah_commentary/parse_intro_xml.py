import html
import bleach
import re

from utilities import map_to_sefaria_masechet

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


def grab_footnote_text(text):
    # Grabs footnote symbol/number and text from the introductions
    return re.findall(r"<ftnote id.*?>(.*?)[);]{1,2}(.*?)</ftnote>", text, re.DOTALL)


def grab_footnote_symbol(text):
    return re.findall(r"<xref rid=\"fn.*?>(.*?)</xref>", text, re.DOTALL)


def grab_footnote_substring(text):
    footnote_substring = re.findall(r"<xref rid=\"fn.*?>.*?</xref>", text, re.DOTALL)
    return footnote_substring[0]


def create_footnote(marker, comment_body):
    return f"<sup class=\"footnote-marker\">{marker}</sup><i class=\"footnote\">{comment_body}</i>"


def convert_to_sefaria_footnote(intro):
    footnote_data = grab_footnote_text(intro)[0]
    ftn_text = footnote_data[1]
    symbol_in_text = grab_footnote_symbol(intro)[0]
    substring = grab_footnote_substring(intro)
    sefaria_footnote_html = create_footnote(symbol_in_text, ftn_text)
    intro = intro.replace(substring, sefaria_footnote_html)
    return intro
    # TODO - clean out nested <sup>s if there. (2 cases)


def process_text(intro):
    if "<ftnote" in intro:
        intro = convert_to_sefaria_footnote(intro)
    clean_text = bleach.clean(intro,
                              tags=ALLOWED_TAGS,
                              attributes=ALLOWED_ATTRS,
                              strip=True)
    text = convert_hebrew_xml_values_to_he(clean_text)
    text = remove_hanging_text(text)
    return text


def process_xml(is_nezikin=False):
    intro_dict = {}
    files = ["zeraim.xml", "moed.xml", "naschim.xml", "kodaschim.xml", "toharot.xml"]

    if is_nezikin:
        # TODO Handle nezikin here
        # return something
        pass

    for file_name in files:
        with open(f'xml/{file_name}', 'r') as f:
            data = f.read()

        intros = re.findall(
            r"<(h1|title)>[TracktRACK]{7} (.*?)<\/\1>(.*?)ABSC[H]{0,1}NITT",  # Between Tractate and first chapter
            data,
            flags=re.DOTALL)

        for tag_name, masechet, intro in intros:
            text = process_text(intro)
            sefaria_masechet = map_to_sefaria_masechet(masechet)
            intro_dict[sefaria_masechet] = text

    return intro_dict


if __name__ == '__main__':
    d = process_xml(is_nezikin=False)
    print(list(d.keys()))
