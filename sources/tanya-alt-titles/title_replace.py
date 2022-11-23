import django

django.setup()

from sefaria.model import *
from sefaria.helper.schema import change_node_title
import csv

def tanya_title_replace_run():
    title_dict = {}

    # Ingest CSV
    with open('title_refactor.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = f"{row['current eng']}"
            title_dict[key] = row

    tanya_index = library.get_index("Tanya")
    tanya_nodes = tanya_index.nodes.children
    for node in tanya_nodes:
        print(node.get_primary_title())
        info = title_dict[node.get_primary_title()]
        new_en_title = info['new eng']
        retire_en_title = info['current eng']
        new_he_title = info['new heb']
        retire_he_title = info['current heb']

        if len(node.children) > 0:
            children = node.children
            for child in children:
                child_title = child.get_primary_title()
                print(child_title)
                if child_title == "The Education of the Child":
                    change_node_title(child, old_title="The Education of the Child", lang="en", new_title="Chinukh Katan")
                    child.add_title("The Education of the Child", "en")
                print(child.get_primary_title())


        # Create a new primary title
        if new_en_title:
            change_node_title(node, old_title=retire_en_title, lang="en", new_title=new_en_title)
        if new_he_title:
            change_node_title(node, old_title=retire_he_title, lang="he", new_title=new_he_title)

        # Make the current one an alt title
        if retire_en_title:
            node.add_title(retire_en_title, "en")
        if retire_he_title:
            node.add_title(retire_he_title, "he")
        print()
    tanya_index.save()


if __name__ == '__main__':
    tanya_title_replace_run()
