import django
django.setup()
from sefaria.model import *
from sources.functions import get_index_api, post_index, post_category

if __name__ == "__main__":
    SERVER = "http://proto.sefaria.org"
    c = Category()
    c.path = ["Tanakh", "Commentary", "Joseph ibn Yahya"]
    c.add_shared_term("Joseph ibn Yahya")
    c.save()
    post_category(c.contents(), server=SERVER)

    c = Category()
    c.path = ["Tanakh", "Commentary", "Joseph ibn Yahya", "Writings"]
    c.add_shared_term("Writings")
    c.save()
    post_category(c.contents(), server=SERVER)

    index = get_index_api("Joseph ibn Yahya on Esther", server=SERVER)
    index["categories"] = ["Tanakh", "Commentary", "Joseph ibn Yahya", "Writings"]
    post_index(index, server=SERVER)