# -*- coding: utf-8 -*-
import django

django.setup()

from sefaria.model import *
from sefaria.helper import category
from sources import functions


def create_term_and_category():
    # Create Term, if it doesn't yet exist
    ts = TermSet({'name': '/German Commentary/'})
    if ts.count() == 0:
        # Term for the Collective Title and the Category
        t = Term()
        t.name = "German Commentary"
        t.add_primary_titles("German Commentary", "פירוש גרמני")
        t.save()

    # Create a Category, if it doesn't yet exist
    cs = CategorySet({'sharedTitle': 'German Commentary'})
    if cs.count() == 0:
        category.create_category(["Mishnah", "Modern Commentary on Mishnah", "German Commentary"])
        sedarim = ["Seder Zeraim", "Seder Moed", "Seder Nashim", "Seder Nezikin", "Seder Kodashim", "Seder Tahorot"]
        for seder in sedarim:
            category.create_category(["Mishnah", "Modern Commentary on Mishnah", "German Commentary", seder])


def create_index_record(en_title, he_title):
    record = SchemaNode()
    record.add_title(en_title, 'en', primary=True, )
    record.add_title(he_title, "he", primary=True, )
    record.key = f"Commentary on {en_title}"
    return record


# Text node:
def add_text_node(record):
    text_node = JaggedArrayNode()
    text_node.key = record.primary_title()
    text_node.depth = 3
    text_node.addressTypes = ['Integer', 'Integer', 'Integer']
    text_node.sectionNames = ['Chapter', 'Mishnah', 'Paragraph']
    record.append(text_node)


def create_index_main():
    en_title = "My Book"
    he_title = "הספר שלי"

    record = create_index_record(en_title, he_title)
    add_text_node(record)
    record.validate()

    index = {
        "title": record.primary_title(),
        "categories": ["Mishnah", "Modern Commentary on Mishnah", "German Commentary"],
        "schema": record.serialize(),
        "base_text_titles": [en_title],
        "base_text_mapping": "many_to_one",
        "is_dependant": True,
        "dependence": "Commentary",
        "collective_title": "German Commentary"
    }

    functions.post_index(index)
    print(index)


if __name__ == '__main__':
    # create_term_and_category()
    create_index_main()
