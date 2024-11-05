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
    if marker[-1] == ")":
        marker = marker[0:-1]
    return f"<sup class=\"footnote-marker\">{marker}</sup><i class=\"footnote\">{comment_body}</i>"


def convert_to_sefaria_footnote(intro):
    footnote_data = grab_footnote_text(intro)[0]
    ftn_text = footnote_data[1]
    symbol_in_text = grab_footnote_symbol(intro)[0]
    substring = grab_footnote_substring(intro)
    sefaria_footnote_html = create_footnote(symbol_in_text, ftn_text)

    ftn_substring_in_sup = f"<sup>{substring}</sup>"
    if ftn_substring_in_sup in intro:
        intro = intro.replace(ftn_substring_in_sup, sefaria_footnote_html)
    else:
        intro = intro.replace(substring, sefaria_footnote_html)
    return intro


def handle_nezikin_footnotes(intro):
    matches = re.findall(r"<ftnote id=(.*?)><sup>(.*?)</sup>[);]{1,2}(.*?)</ftnote>", intro, re.DOTALL)
    for m in matches:
        xml_id = m[0]
        symbol = m[1]
        ftn_text = m[2]
        substring = f"<sup><xref rid={xml_id}>{symbol}</xref></sup>"
        remove_substring = f"<ftnote id={xml_id}><sup>{symbol}</sup>){ftn_text}</ftnote>"
        sefaria_footnote_html = create_footnote(symbol, ftn_text)
        if substring in intro:
            intro = intro.replace(substring, sefaria_footnote_html)
            intro = intro.replace(remove_substring, "")
    return intro


def process_text(intro, is_nezikin=False):
    if is_nezikin:
        intro = handle_nezikin_footnotes(intro)
    elif "<ftnote" in intro:
        intro = convert_to_sefaria_footnote(intro)
    clean_text = bleach.clean(intro,
                              tags=ALLOWED_TAGS,
                              attributes=ALLOWED_ATTRS,
                              strip=True)
    text = convert_hebrew_xml_values_to_he(clean_text)
    text = remove_hanging_text(text)
    return text


def process_xml():
    intro_dict = {}
    files = ["zeraim.xml", "moed.xml", "naschim.xml", "kodaschim.xml", "toharot.xml", "nezikin.xml"]

    for file_name in files:
        with open(f'xml/{file_name}', 'r') as f:
            data = f.read()

        if file_name == "nezikin.xml":
            intro = re.findall(r"<title>Einleitung\.</title>(.*?)<title>Tractat Baba kama\.</title>", data,
                               flags=re.DOTALL)[0]
            text = process_text(intro, is_nezikin=True)
            text = text.split("\n")
            text = [segment for segment in text if segment]  # filter out empty strings

            intro_dict["German Commentary, Introduction to Seder Nezikin"] = text

        else:
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
    d = process_xml()
    # print(list(d.keys()))
