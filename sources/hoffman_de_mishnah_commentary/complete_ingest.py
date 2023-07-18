import django

django.setup()

import time
from collections import defaultdict
from sefaria.model import *
from sefaria.tracker import modify_bulk_text
from sources.functions import post_text, post_link
from sources.local_settings import SEFARIA_SERVER
from sources.hoffman_de_mishnah_commentary.extract_commentary import create_text_data_dict
from sources.hoffman_de_mishnah_commentary.parse_intro_xml import process_xml
from sources.hoffman_de_mishnah_commentary.create_index import create_index_main, create_term_and_category


# This is the complete flow for the index creation and text index
# when running on a cauldron, one has to use the cauldron-specific files
# in the following order: 1) create_index, 2) post_intro (LOCAL), 3) ingest_text, 4) post_links (LOCAL)


def create_mappings():
    mappings = defaultdict(dict)
    data_dict, hoffman_links = create_text_data_dict()

    for tref in data_dict:
        if "Berakhot" in tref:  # Todo, temp filter, eventually remove
            mappings[Ref(tref).index.title][tref] = data_dict[tref]
    return mappings, hoffman_links


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
        post_text(ref=tref, text=text, server=SEFARIA_SERVER)

        for tref in book_map:
            formatted_text = generate_text_post_format(book_map[tref])
            post_text(ref=tref, text=formatted_text, server=SEFARIA_SERVER)


def pre_local_clean_up(hoffman_links):
    cur_version = VersionSet({'title': f'German Commentary on Mishnah Berakhot',
                              'versionTitle': "Mischnajot mit deutscher Übersetzung und Erklärung. Berlin 1887-1933 [de]"})
    if cur_version.count() > 0:
        cur_version.delete()

    for link in hoffman_links:
        if 'Berakhot' in link['refs'][0]:  # Todo, temp filter, eventually remove
            l = Link().load({'refs': link['refs']})
            if l:
                l.delete()


if __name__ == '__main__':

    # mishnah = library.get_indexes_in_category("Mishnah", full_records=True)

    # create_term_and_category()  #TODO - fix to use POST functions?
    # print("UPDATE: Terms and categories added")
    #
    # create_index_main()
    # print("UPDATE: Index created")

    map, hoffman_links = create_mappings()
    # print("UPDATE: Map and links generated")
    #
    upload_text(map)
    # print("UPDATE: Text ingest complete")
