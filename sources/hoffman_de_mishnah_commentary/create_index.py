# -*- coding: utf-8 -*-
import django

django.setup()

from sefaria.model import *
from sources import functions


def create_term_and_category():
    # Create Term, if it doesn't yet exist
    ts = TermSet({'name': 'German Commentary'})
    if ts.count() == 0:
        t = Term()
        t.name = "German Commentary"
        t.add_primary_titles("German Commentary", "פירוש גרמני")
        t.save()

    # Create a Category, if it doesn't yet exist
    cs = CategorySet({'sharedTitle': 'German Commentary'})
    if cs.count() == 0:
        c = Category()
        c.path = ["Mishnah", "Modern Commentary on Mishnah", "German Commentary"]
        c.add_shared_term("German Commentary")
        c.save()


def create_index_record(masechet, he_masechet):
    record = SchemaNode()
    if masechet == "Pirkei Avot":
        he_title = "פירוש גרמני ל" + he_masechet  # f-String was not working well with RTL text
        en_title = f"German Commentary on {masechet}"
    else:
        he_title = "פירוש גרמני למסכת " + he_masechet  # f-String was not working well with RTL text
        en_title = f"German Commentary on Mishnah {masechet}"
    record.add_title(en_title, 'en', primary=True, )
    record.add_title(he_title, "he", primary=True, )
    record.key = f"German Commentary on {masechet}" if masechet == "Pirkei Avot" else f"German Commentary on Mishnah {masechet}"
    record.collective_title = "German Commentary"  # Must be a term
    return record


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
def add_text_node(record):
    text_node = JaggedArrayNode()
    text_node.key = "default"
    text_node.default = True
    text_node.depth = 3
    text_node.addressTypes = ['Integer', 'Integer', 'Integer']
    text_node.sectionNames = ['Chapter', 'Mishnah', 'Paragraph']
    record.append(text_node)


def create_index_main():
    mishnayot = library.get_indexes_in_category("Mishnah", full_records=True)

    for mishnah_index in mishnayot:
        en_title = mishnah_index.get_title("en").replace("Mishnah ", "")
        he_title = mishnah_index.get_title("he").replace("משנה ", "")

        record = create_index_record(en_title, he_title)
        add_intro_node(record)
        add_text_node(record)
        record.validate()
        index = {
            "title": record.primary_title(),
            "categories": ["Mishnah", "Modern Commentary on Mishnah"],
            "schema": record.serialize(),
            "base_text_titles": [f"{en_title}"] if en_title == 'Pirkei Avot' else [f"Mishnah {en_title}"],
            "base_text_mapping": "many_to_one",
            "is_dependant": True,
            "dependence": "Commentary"
        }

        functions.post_index(index)
        print(index)


if __name__ == '__main__':
    create_index_main()

# TODO - fix Ta'anit