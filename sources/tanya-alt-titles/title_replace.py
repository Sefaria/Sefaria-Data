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
            key = f"Tanya, {row['current eng']}"
            title_dict[key] = row

    tanya_index = library.get_index("Tanya")
    tanya_nodes = tanya_index.nodes.children
    for node in tanya_nodes:
        info = title_dict[str(node)]
        new_en_title = info['new eng'] if not "" else None
        retire_en_title = info['current eng'] if not "" else None
        new_he_title = info['new heb'] if not "" else None
        retire_he_title = info['current heb'] if not "" else None

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
