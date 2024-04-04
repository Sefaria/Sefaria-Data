import django

django.setup()
from tqdm import tqdm
superuser_id = 171118
from sefaria.model import *
# import csv
# import re

# from sefaria.utils.talmud import daf_to_section, section_to_daf
# from typing import List
# from pprint import pprint
# import copy

if __name__ == "__main__":
    print("hi")
    for author in AuthorTopicSet():
        # print(author)
        if author.aggregate_authors_indexes_by_category() == "critical":
            print(author.slug)


    print("bye")
