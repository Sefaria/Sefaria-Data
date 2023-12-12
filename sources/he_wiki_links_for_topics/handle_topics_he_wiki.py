import django

django.setup()

superuser_id = 171118
# import statistics
import csv
from sefaria.model import *
# import re


# from sefaria.helper.schema import insert_last_child, reorder_children
# from sefaria.helper.schema import remove_branch
from sefaria.tracker import modify_bulk_text

# from sefaria.helper.category import create_category
# from sefaria.system.database import db

import wikipediaapi


def get_hebrew_entry_url(english_wiki_url):
    headers = {
        'User-Agent': 'YourAppName/1.0 (your@email.com)'
    }
    wiki_wiki = wikipediaapi.Wikipedia('en', headers=headers)

    # Extract the page title from the English Wikipedia URL
    page_title = english_wiki_url.split("/")[-1]

    # Get the English Wikipedia page
    page_en = wiki_wiki.page(page_title)

    # Check if the page exists
    if not page_en.exists():
        # print(f"Error: Page '{page_title}' does not exist on English Wikipedia.")
        return None

    # Get the interlanguage link to the Hebrew entry
    hebrew_entry_url = page_en.langlinks.get('he')

    if hebrew_entry_url:
        return hebrew_entry_url.fullurl
    else:
        # print(f"No Hebrew entry link found for '{page_title}'.")
        return None

if __name__ == '__main__':
    data_source = "wikidata"
    print("hello world")
    english_wiki_url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    hebrew_entry_url = get_hebrew_entry_url(english_wiki_url)
    topic_set = TopicSet({}).array()
    for t in topic_set:
        if hasattr(t, "properties"):
            if t.properties.get("enWikiLink") and not t.properties.get("heWikiLink"):
                # print(t)
                he_url = get_hebrew_entry_url(t.properties.get("enWikiLink").get("value"))
                if he_url:
                    he_wiki_link_dict = {"data_source": data_source, "value": he_url}
                    t.properties["heWikiLink"] = he_wiki_link_dict
                    t.save()
                    print(f"updated topic: {t}")
                    # print(t.properties["heWikiLink"]["value"])

    print("end")
