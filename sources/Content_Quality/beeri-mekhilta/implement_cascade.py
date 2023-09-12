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
    else:  # Handle ranged refs
        for ref_key in mapper:
            if Ref(ref_key).contains(Ref(prod_ref)):
                return mapper[ref_key]


def action(segment_str, tref, he_tref, version):
    global prod_refs
    prod_refs.append(tref)


def retrieve_version_text():
    version_query = {"versionTitle": "Mekhilta -- Wikisource",
                     "title": "Mekhilta d'Rabbi Yishmael Old"}
    wiki_version = VersionSet(version_query)
    for v in wiki_version:
        v.walk_thru_contents(action)


def rename_books():
    index_query = {"title": "Mekhilta d'Rabbi Yishmael"}
    index = Index().load(index_query)
    print(f"Retrieved {index.title}")
    index.set_title("Mekhilta d'Rabbi Yishmael Old")
    index.save()
    print(f"Saved and renamed {index.title}")

    index_query = {"title": "Mekhilta DeRabbi Yishmael Beeri"}
    index = Index().load(index_query)
    print(f"Retrieved {index.title}")
    index.set_title("Mekhilta d'Rabbi Yishmael")
    index.save()
    print(f"Saved and renamed {index.title}")


if __name__ == '__main__':

    # TODO - Run this first
    # rename_books()

    prod_refs = []
    retrieve_version_text()

    mapper = ingest_map()
    for prod_ref in prod_refs:
        print(f"Working on {prod_ref}")
        cascade(prod_ref, rewriter=lambda beeri_ref: rewriter_function(prod_ref), skip_history=False)
