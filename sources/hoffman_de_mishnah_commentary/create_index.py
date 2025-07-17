# -*- coding: utf-8 -*-
import django

django.setup()

from sefaria.model import *
from sefaria.helper import category
from sources import functions

nezikin_masechtot = ['Mishnah Bava Kamma',
                     'Mishnah Bava Metzia',
                     'Mishnah Bava Batra',
                     'Mishnah Sanhedrin',
                     'Mishnah Makkot',
                     'Mishnah Shevuot',
                     'Mishnah Eduyot',
                     'Mishnah Avodah Zarah',
                     'Pirkei Avot',
                     'Mishnah Horayot']


def create_term_and_category():
    # Create Term, if it doesn't yet exist
    ts = TermSet({'name': '/German Commentary/'})
    if ts.count() == 0:

        # Term for the Collective Title
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


def create_index_record(masechet, he_masechet):
    record = SchemaNode()
    he_title = "פירוש גרמני על " + he_masechet  # f-String was not working well with RTL text
    en_title = f"German Commentary on {masechet}"
    record.add_title(en_title, 'en', primary=True, )
    record.add_title(he_title, "he", primary=True, )
    record.key = f"German Commentary on {masechet}" if masechet == "Pirkei Avot" else f"German Commentary on {masechet}"
    record.collective_title = "German Commentary"  # Must be a term
    return record


def get_seder(masechet):
    return library.get_index(masechet).categories[-1]


# Introduction node:
def add_intro_node(record):
    intro_node = JaggedArrayNode()
    intro_node.add_title("Introduction", 'en', primary=True)
    intro_node.add_title("הקדמה", 'he', primary=True)
    intro_node.key = "Introduction"
    intro_node.depth = 1
    intro_node.addressTypes = ['Integer']
    intro_node.sectionNames = ['Paragraph']
    record.append(intro_node)


# Text node:
def add_text_node(record, is_nezikin=False):
    text_node = JaggedArrayNode()
    text_node.key = "default"
    text_node.default = True if not is_nezikin else record.primary_title()
    text_node.depth = 3
    text_node.addressTypes = ['Integer', 'Integer', 'Integer']
    text_node.sectionNames = ['Chapter', 'Mishnah', 'Paragraph']
    record.append(text_node)


def create_intros(type="nezikin"):
    # Create record
    record = SchemaNode()

    if type == "nezikin":
        he_title = "פירוש גרמני על המשנה, הקדמה לסדר נזיקין"
        en_title = f"German Commentary, Introduction to Seder Nezikin"
    elif type == "general":
        he_title = "פירוש גרמני, הקדמה"
        en_title = f"German Commentary, Introduction"
    record.add_title(en_title, 'en', primary=True, )
    record.add_title(he_title, "he", primary=True, )
    record.key = f"German Commentary, Introduction to Seder Nezikin" if type == "nezikin" else f"German Commentary, Introduction"
    record.collective_title = "German Commentary"  # Must be a term

    # Add text node
    text_node = JaggedArrayNode()
    text_node.key = "default"
    text_node.default = record.primary_title()
    text_node.depth = 1
    text_node.addressTypes = ['Integer']
    text_node.sectionNames = ['Paragraph']
    record.append(text_node)

    # Post the index
    record.validate()
    index = {
        "title": record.primary_title(),
        "schema": record.serialize(),
        "is_dependant": True,
        "dependence": "Commentary"
    }
    if type == "nezikin":
        index["categories"] = ['Mishnah', 'Modern Commentary on Mishnah', 'German Commentary',
                               'Seder Nezikin']
    elif type == "general":
        index["categories"] = ['Mishnah', 'Modern Commentary on Mishnah', 'German Commentary']

    print(index)
    functions.post_index(index)


def create_index_main():
    mishnayot = library.get_indexes_in_category("Mishnah", full_records=True)

    create_intros(type="nezikin")
    create_intros(type="general")

    for mishnah_index in mishnayot:
        en_title = mishnah_index.get_title("en")
        he_title = mishnah_index.get_title("he")

        record = create_index_record(en_title, he_title)

        seder = get_seder(en_title)

        # Nezikin masechtot don't have intros
        if en_title not in nezikin_masechtot:
            add_intro_node(record)
            add_text_node(record)
        else:
            add_text_node(record, is_nezikin=True)

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
