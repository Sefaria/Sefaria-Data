import django

django.setup()

from sefaria.model import *
from sefaria.helper.schema import cascade
import csv


def ingest_map():
    with open("full_mapping.csv", "r") as f:
        reader = csv.DictReader(f)
        map = {}
        for row in reader:
            map[row["prod_ref"]] = row["beeri_ref"]
    return map


def rewriter_function(prod_ref):
    mapper = ingest_map()
    if prod_ref in mapper:
        return mapper[prod_ref]
    else:
        print(f"{prod_ref} not in map")  # TODO - add here check if ranged
        return "Dummy ref"


def action(segment_str, tref, he_tref, version):
    global prod_refs
    prod_refs.append(tref)


def retrieve_version_text():
    version_query = {"versionTitle": "Mekhilta -- Wikisource",
                     "title": "Mekhilta d'Rabbi Yishmael Old"}
    wiki_version = VersionSet(version_query)
    for v in wiki_version:
        v.walk_thru_contents(action)


if __name__ == '__main__':
    prod_refs = []
    retrieve_version_text()

    mapper = ingest_map()
    for prod_ref in prod_refs:
        cascade(prod_ref, rewriter=lambda beeri_ref: mapper[prod_ref], skip_history=False)
