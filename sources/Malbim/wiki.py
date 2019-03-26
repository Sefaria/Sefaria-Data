#encoding=utf-8
import django
django.setup()
from sefaria.model import *
import requests
from data_utilities.util import numToHeb
from bs4 import BeautifulSoup, NavigableString, Tag

def generate_URLs(books):
    urls = []
    opening = u"""https://he.wikisource.org/wiki/מלבי"ם_על_"""
    for book_title in books:
        book = library.get_index(book_title)
        heTitle = book.get_title('he')
        for perek_n, perek in enumerate(book.all_section_refs()):
            num_segments = len(perek.all_segment_refs())
            url = u"{}{}_{}".format(opening, heTitle, numToHeb(perek_n+1))
            urls.append((url, num_segments))
    return urls



def download_html(url):
    headers = {
        'User-Agent': 'Mozilla/4.0 (Macintosh; Intel Mac OS X 11_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    return requests.get(url, headers=headers).content


def parse_flat(root):
    pass

def parse_linked_list(root):
    pass

if __name__ == "__main__":
    URLs = generate_URLs(["Joshua", "Judges", "Ezra"])
    for n, url_and_segments in enumerate(URLs):
        url, num_segments = url_and_segments
        html = BeautifulSoup(download_html(url))
        root = html.find("div", {"class": "mw-parser-output"})
        p_tags = [el for el in root.contents if isinstance(el, Tag) and el.tag == "p"]
        if len(p_tags) >= 2:
            parse_flat(p_tags)
        else:
            parse_linked_list([el for el in root.contents if isinstance(el, Tag)])
