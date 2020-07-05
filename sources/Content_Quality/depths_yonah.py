#encoding=utf-8
import django
django.setup()
from sefaria.model import *
import csv
from data_utilities.XML_to_JaggedArray import roman_to_int, int_to_roman
from sources.functions import *
file = open("depths of yonah - depths of yonah.csv")
section = 0
nodes = []
schema_node = None
chapter = 0
acknowledgements = ArrayMapNode()
acknowledgements.depth = 0
acknowledgements.refs = []
acknowledgements.add_primary_titles("Acknowledgements", u"תודות")
acknowledgements.wholeRef = "Depths of Yonah, Acknowledgements"
acknowledgements.validate()
nodes.append(acknowledgements.serialize())
for row in csv.reader(file):
    what_is_it, en, he = row
    if what_is_it.startswith("Section"):
        if schema_node:
            schema_node.validate()
            nodes.append(schema_node.serialize())
        section = roman_to_int(what_is_it.split()[-1])
        schema_node = SchemaNode()
        schema_node.add_primary_titles(what_is_it+": "+en, he)
        chapter = 0
    else:
        sub_section = int(what_is_it[:-1])
        child_node = ArrayMapNode()
        chapter += 1
        child_node.add_primary_titles("Chapter {}: {}".format(int_to_roman(chapter), en), he)
        child_node.depth = 0
        child_node.refs = []
        child_node.wholeRef = "Depths of Yonah {}:{}".format(section, sub_section)
        child_node.validate()
        schema_node.append(child_node)


nodes.append(schema_node.serialize())

index = get_index_api("Depths of Yonah", server="http://rosh.sandbox.sefaria.org")
index['alt_structs'] = {"Chapter": {"nodes": nodes}}
index["default_struct"] = "Chapter"
post_index(index, server="http://rosh.sandbox.sefaria.org")
