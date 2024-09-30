import django

django.setup()
from sefaria.model import *
from sefaria.tracker import modify_bulk_text
import os
from bs4 import BeautifulSoup
import re
import csv
superuser_id = 171118


if __name__ == '__main__':
    books = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]
    for book in books:
        seg_refs = library.get_index(book).all_segment_refs()
        for ref in seg_refs:
            if ref.text(vtitle="The Torah; Chabad House Publications, Los Angeles, 2015-2023").text == "":
                print(ref)

