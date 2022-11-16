import django

django.setup()

from sefaria.model import *
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

        # Create a new primary title
        if new_en_title:
            node.add_title(new_en_title, "en", primary=True, replace_primary=True)
        if new_he_title:
            node.add_title(new_he_title, "he", primary=True, replace_primary=True)

        # Make the current one an alt title
        if retire_en_title:
            node.add_title(retire_en_title, "en")
        if retire_he_title:
            node.add_title(retire_he_title, "he")

    tanya_index.save()


if __name__ == '__main__':
    tanya_title_replace_run()
