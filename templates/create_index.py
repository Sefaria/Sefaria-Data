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

        # Term for the Collective Title
        t = Term()
        t.name = "New Index"
        t.add_primary_titles("New Index", "אינ")
        t.save()

    # Create a Category, if it doesn't yet exist
    cs = CategorySet({'sharedTitle': 'German Commentary'})
    if cs.count() == 0:
        category.create_category(["Mishnah", "Modern Commentary on Mishnah", "German Commentary"])
        sedarim = ["Seder Zeraim", "Seder Moed", "Seder Nashim", "Seder Nezikin", "Seder Kodashim", "Seder Tahorot"]
        for seder in sedarim:
            category.create_category(["Mishnah", "Modern Commentary on Mishnah", "German Commentary", seder])


def create_index_record(masechet, he_masechet):
    record = SchemaNode()
    he_title = "פירוש גרמני על " + he_masechet  # f-String was not working well with RTL text
    en_title = f"German Commentary on {masechet}"
    record.add_title(en_title, 'en', primary=True, )
    record.add_title(he_title, "he", primary=True, )
    record.key = f"German Commentary on {masechet}" if masechet == "Pirkei Avot" else f"German Commentary on {masechet}"
    record.collective_title = "German Commentary"  # Must be a term
    return record


# Text node:
def add_text_node(record, is_nezikin=False):
    text_node = JaggedArrayNode()
    text_node.key = "default"
    text_node.default = True if not is_nezikin else record.primary_title()
    text_node.depth = 3
    text_node.addressTypes = ['Integer', 'Integer', 'Integer']
    text_node.sectionNames = ['Chapter', 'Mishnah', 'Paragraph']
    record.append(text_node)


def create_index_main():
    mishnayot = library.get_indexes_in_category("Mishnah", full_records=True)

    for mishnah_index in mishnayot:
        en_title = mishnah_index.get_title("en")
        he_title = mishnah_index.get_title("he")

        record = create_index_record(en_title, he_title)

        record.validate()
        index = {
            "title": record.primary_title(),
            "categories": ["Mishnah", "Modern Commentary on Mishnah", "German Commentary", seder],
            "schema": record.serialize(),
            "base_text_titles": [en_title],
            "base_text_mapping": "many_to_one",
            "is_dependant": True,
            "dependence": "Commentary"
        }

        functions.post_index(index)
        print(index)


if __name__ == '__main__':
    # create_term_and_category()
    create_index_main()