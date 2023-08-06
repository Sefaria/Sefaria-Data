# -*- coding: utf-8 -*-
import django

django.setup()

from sefaria.model import *
from sefaria.helper import category
from sources import functions

nezikin_masechtot = ['Bava Kamma',
                     'Bava Metzia',
                     'Bava Batra',
                     'Sanhedrin',
                     'Makkot',
                     'Shevuot',
                     'Eduyot',
                     'Avodah Zarah',
                     'Pirkei Avot',
                     'Horayot']


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
        category.create_category(["Mishnah", "Modern Commentary on Mishnah", "German Commentary"])
        sedarim = ["Seder Zeraim", "Seder Moed", "Seder Nashim", "Seder Nezikin", "Seder Kodashim", "Seder Tahorot"]
        for seder in sedarim:
            category.create_category(["Mishnah", "Modern Commentary on Mishnah", "German Commentary", seder])



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


def get_seder(masechet):
    if masechet != "Pirkei Avot":
        return library.get_index(f'Mishnah {masechet}').categories[-1]
    return library.get_index(f'{masechet}').categories[-1]

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


def create_nezikin_intro():
    # Create record
    record = SchemaNode()

    he_title = "פירוש גרמני, הקדמה לסדר נזיקין"
    en_title = f"German Commentary, Introduction to Seder Nezikin"
    record.add_title(en_title, 'en', primary=True, )
    record.add_title(he_title, "he", primary=True, )
    record.key = f"German Commentary, Introduction to Seder Nezikin"
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
        "categories": ['Mishnah', 'Modern Commentary on Mishnah', 'German Commentary'],
        "schema": record.serialize(),
        "is_dependant": True,
        "dependence": "Commentary"
    }

    print(index)
    functions.post_index(index)


def create_index_main():
    mishnayot = library.get_indexes_in_category("Mishnah", full_records=True)

    for mishnah_index in mishnayot:
        en_title = mishnah_index.get_title("en").replace("Mishnah ", "")
        he_title = mishnah_index.get_title("he").replace("משנה ", "")

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
            "base_text_titles": [f"{en_title}"] if en_title == 'Pirkei Avot' else [f"Mishnah {en_title}"],
            "base_text_mapping": "many_to_one",
            "is_dependant": True,
            "dependence": "Commentary"
        }

        functions.post_index(index)
        print(index)


if __name__ == '__main__':
    create_term_and_category()
    create_index_main()
    create_nezikin_intro()