# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
from bs4 import BeautifulSoup
from bs4 import NavigableString
from sefaria.model import *
from sefaria.helper.schema import migrate_to_complex_structure, cascade, change_node_structure
import sys

def fix(title):
    things_to_replace = {
            u'\xa0': u'',
            u'\u015b': u's',
            u'\u2018': u"'",
            u'\u2019': u"'"
        }
    for x in things_to_replace:
        title = title.replace(x, things_to_replace[x])
    return title

def create_schema_and_map(title, he_tile, filename, new_structure):
    soup = BeautifulSoup(open(filename), "xml")
    contents = soup.contents[0].contents[3].contents
    root = SchemaNode()
    root.add_primary_titles(title, he_title)
    main_count = 0
    mapping = {}
    for main_tag in contents:
        if type(main_tag) is not NavigableString:
            main_count += 1
            if len(main_tag.contents) > 0:
                new_node = SchemaNode()
                node_he, node_en = main_tag['text'].split(" / ")
                node_en = fix(node_en)
                new_node.add_primary_titles(node_en, node_he)
                child_count = 0
                for child in main_tag:
                    if type(child) is not NavigableString:
                        assert len(child.contents) == 0
                        child_count += 1
                        child_node = JaggedArrayNode()
                        child_he, child_en = child['text'].split(" / ")
                        child_en = fix(child_en)
                        orig_ref = "{} {}:{}".format(title, main_count, child_count)
                        mapping[orig_ref] = "{}, {}, {}".format(title, node_en, child_en)
                        child_node.add_primary_titles(child_en, child_he)
                        child_node.add_structure(new_structure[2:])
                        new_node.append(child_node)
            else:
                new_node = JaggedArrayNode()
                node_he, node_en = main_tag['text'].split(" / ")
                node_en = fix(node_en)
                orig_ref = "{} {}:1".format(title, main_count)
                mapping[orig_ref] = "{}, {}".format(title, node_en)
                new_node.add_primary_titles(node_en, node_he)
                new_node.add_structure(new_structure[2:])
            root.append(new_node)
    root.validate()
    return root.serialize(), mapping


if __name__ == "__main__":
    title = "Siddur, Edot HaMizrach"
    i = library.get_index(title)
    i.set_title("Siddur Edot HaMizrach")
    i.save()
    title = title.replace(",", "")
    he_title = i.get_title('he')
    filename = "siddur.xml"
    new_structure = i.schema['sectionNames']
    schema, mapping = create_schema_and_map(title, he_title, filename, new_structure)
    migrate_to_complex_structure(title, schema, mapping)