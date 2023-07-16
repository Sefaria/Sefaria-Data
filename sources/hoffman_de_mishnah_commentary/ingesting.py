import django

django.setup()

from sefaria.model import *
from collections import defaultdict
from sefaria.model import *
from sefaria.tracker import modify_bulk_text
from sources.functions import post_text, post_link
from sources.hoffman_de_mishnah_commentary.extract_commentary import create_text_data_dict
from sources.hoffman_de_mishnah_commentary.parse_intro_xml import process_xml
from sources.hoffman_de_mishnah_commentary.create_index import create_index_main

# Todo - links going both ways
# Then cauldron


def create_mappings():
    mappings = defaultdict(dict)
    data_dict, links = create_text_data_dict()

    for tref in data_dict:
        if "Berakhot" in tref:  # Todo, temp filter, eventually remove
            mappings[Ref(tref).index.title][tref] = data_dict[tref]
    return mappings, links


def generate_text_post_format(text, is_intro=False):
    if is_intro:
        text = [text]
    return {
        "text": text,
        "versionTitle": "Mischnajot mit deutscher Übersetzung und Erklärung. Berlin 1887-1933 [de]",
        "versionSource": "talmud.de",
        "language": "en"
    }


def upload_text(mappings):
    for book, book_map in mappings.items():
        print(f"Uploading text for {book}")

        intro_dict = process_xml()
        tref = "German Commentary on Mishnah Berakhot, Introduction"
        text = generate_text_post_format(intro_dict["Traktat Berachot"], is_intro=True)
        post_text(ref=tref, text=text, server="http://localhost:8000")

        version = Version().load({'title': 'German Commentary on Mishnah Berakhot'})
        modify_bulk_text(user=142625,
                         version=version,
                         text_map=book_map,
                         skip_links=True,
                         count_after=False)
        print(f"Text for {version.title} uploaded")


def pre_local_clean_up(links):
    cur_version = VersionSet({'title': f'German Commentary on Mishnah Berakhot',
                              'versionTitle': "Mischnajot mit deutscher Übersetzung und Erklärung. Berlin 1887-1933 [de]"})
    if cur_version.count() > 0:
        cur_version.delete()

    for link in links:
        if 'Berakhot' in link['refs'][0]: # Todo, temp filter, eventually remove
            l = Link().load({'refs': link['refs']})
            if l:
                l.delete()


if __name__ == '__main__':

    create_index_main()

    map, links = create_mappings()
    pre_local_clean_up(links)

    upload_text(map)
    for link in links:
        if 'Berakhot' in link['refs'][0]:
            post_link(link)
