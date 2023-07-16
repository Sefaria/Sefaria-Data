# -*- coding: utf-8 -*-
import django

django.setup()

from sefaria.model import *
from sources import functions


def create_index_record(masechet, he_masechet):
    record = SchemaNode()
    he_title = "פירוש גרמני למסכת " + he_masechet  # f-String was not working well with RTL text
    en_title = f"German Commentary on Mishnah {masechet}"
    record.add_title(en_title, 'en', primary=True, )
    record.add_title(he_title, "he", primary=True, )
    record.key = 'German Commentary on Mishnah Berakhot'
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
    # text_node.toc_zoom = 2
    text_node.addressTypes = ['Integer', 'Integer', 'Integer']
    text_node.sectionNames = ['Chapter', 'Mishnah', 'Paragraph']
    record.append(text_node)


def create_index_main():
    # In theory, eventually wrap in for loop for each Masechet.
    record = create_index_record("Berakhot", "ברכות")
    add_intro_node(record)
    add_text_node(record)
    record.validate()
    index = {
        "title": record.primary_title(),
        "categories": ["Mishnah"],  # Todo - add Seder?
        "schema": record.serialize()
    }
    print(index)
    functions.post_index(index)
