#encoding=utf-8
import django
django.setup()
from sefaria.model import *
import requests
from data_utilities.util import numToHeb
from bs4 import BeautifulSoup, NavigableString, Tag
from sources.functions import *

def generate_URLs(books):
    urls = []
    opening = u"""https://he.wikisource.org/wiki/מלבי"ם_על_"""
    for book_title in books:
        book = library.get_index(book_title)
        heTitle = book.get_title('he')
        for perek_n, perek in enumerate(book.all_section_refs()):
            url = u"{}{}_{}".format(opening, heTitle, numToHeb(perek_n+1))
            urls.append((url, book_title, perek_n+1))
    return urls



def download_html(url):
    headers = {
        'User-Agent': 'Mozilla/4.0 (Macintosh; Intel Mac OS X 11_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    return requests.get(url, headers=headers).content



def structure(text):
    text_depth_2 = {}
    curr_pasuk = 1
    text_depth_2[1] = []
    for line_n, line in enumerate(text):
        psukim = re.findall(u"^\(.*?\)", line.strip())
        set_psukim = set(psukim)
        assert len(set_psukim) in [0, 1]
        if len(set_psukim) is 0:
            text_depth_2[curr_pasuk].append(line.strip())
        elif len(set_psukim) is 1:
            curr_pasuk = getGematria(psukim[0].split("-")[0])
            if curr_pasuk not in text_depth_2:
                text_depth_2[curr_pasuk] = [line.strip()]

    check_errors(text_depth_2)
    return convertDictToArray(text_depth_2)

def get_contents(el, found_comment):
    text = u""
    if not found_comment:
        return el.text
    for sub_el in el.contents:
        if isinstance(sub_el, NavigableString):
            text += sub_el.replace(u"\n", u" ") + u" "
        elif sub_el.name == "b" or (sub_el.name == "span" and "class" in sub_el.attrs and sub_el.attrs["class"] == ["psuq"]):
            text += "<b>" + sub_el.text.replace(u"\n", u" ") + "</b>"
        else:
            text += sub_el.text.replace(u"\n", u" ")
    text = u" ".join(text.split())
    text = re.sub(u"\" (<b>.*?</b>)\"", r"\1", text)
    text = text.replace(chr(1), u"").replace("( ", "(").replace(" .", ".").replace(" ,", ",")
    return text.strip()

def parse_linked_list(root):
    contents = [el for el in root.contents if (isinstance(el, NavigableString) and len(el) >= 3)
                or not isinstance(el, NavigableString)]
    if len(contents) is 1:
        return {}
    else:
        contents, next = contents[0:-1], contents[-1]
        found_comment = False
        comments = {}
        curr_pasuk = 0
        for el in contents:
            relevant_text = el if isinstance(el, NavigableString) else get_contents(el, found_comment)
            relevant_text = relevant_text.strip()
            if isinstance(el, Tag) and el.name == "h2":
                curr_pasuk = getGematria(u" ".join(relevant_text.split()[1]))
                assert curr_pasuk not in comments
                comments[curr_pasuk] = []
            if u"עריכה" in relevant_text:
                found_comment = True
                continue
            if isinstance(el, Tag) and "style" in el.attrs and "display:none" in el.attrs["style"]:
                continue
            if found_comment:
                #relevant_text = re.sub(u"^\(.*?\)", u"", relevant_text)
                while u"  " in relevant_text:
                    relevant_text = relevant_text.replace(u"  ", u" ")
                comments[curr_pasuk].append(relevant_text.strip())
        comments.update(parse_linked_list(next))
        return comments

def parse_judges(root):
    found_start = False
    text = {}
    for el in root.contents:
        if not found_start and el.name == "h2":
            found_start = True
        if found_start:
            if el.name == "h2":
                el_text = el.text.split()
                assert len(el_text) == 2
                curr_pasuk = getGematria(el_text[-1])
                if curr_pasuk not in text:
                    text[curr_pasuk] = []
            elif el.name == "p":
                text[curr_pasuk].append(get_contents(el, True))
    check_errors(text)
    return convertDictToArray(text)

def check_errors(text):
    chs = text.keys()
    num_chs = len(chs)
    max_ch = max(chs)
    chs.remove(max_ch)
    second_max_ch = max(chs)
    if max_ch > 5 + second_max_ch:
        print url

if __name__ == "__main__":
    URLs = generate_URLs(["Ezra", "Judges", "Joshua"])
    books = {}
    for n, url_tuple in enumerate(URLs):
        text = []
        url, book, perek = url_tuple
        html = BeautifulSoup(download_html(url))
        root = html.find("div", {"class": "mw-parser-output"})
        p_tags = [el for el in root.contents if isinstance(el, Tag) and el.name == "p" and el.text != "\n"]
        if root.find("div", {"class": "flatToc"}) and root.find("h2"):
            text = parse_judges(root)
        elif len(p_tags) >= 2:
            text = structure([get_contents(p, True) for p in p_tags])
        elif len(p_tags) <= 2:
            arr = [el for el in root.contents if isinstance(el, Tag)][-1]
            text = convertDictToArray(parse_linked_list(arr))
        if book not in books.keys():
            books[book] = {}
        books[book][perek] = text

    for book, text_dict in books.items():
        text_arr = convertDictToArray(text_dict)
        send_text = {
            "text": text_arr,
            "language": "he",
            "versionSource": "https://he.wikisource.org/",
            "versionTitle": "Wikisource"
        }
        post_text("Malbim on {}".format(book), send_text, server=SEFARIA_SERVER, index_count="on")

