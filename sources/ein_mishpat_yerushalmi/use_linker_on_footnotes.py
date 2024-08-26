import django

django.setup()
from tqdm import tqdm
import os
superuser_id = 171118
import csv
import re
from sefaria.model import *
from tqdm import tqdm


def csv_to_list(file_path):
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        data = [row[0] for row in reader]  # Convert each row into a list
    return data


if __name__ == '__main__':
    footnotes_list = csv_to_list("Ein Mishpat Yerusalmi Wikitext Footnotes Refs.csv")
    linker = library.get_linker("he")
    text = """
    מיי' פ"א מהל' יום טוב הלכה י"ט
    """
    doc = linker.link(text, type_filter="citation", with_failures=True)


    footnote_and_refs = []
    for footnote in tqdm(footnotes_list):
        new_inference = []
        new_inference.append(footnote)
        clean_footnote = footnote.split("מיי'", 1)[1] if "מיי'" in footnote else footnote
        doc = linker.link(clean_footnote, type_filter="citation", with_failures=True)
        for citation in doc.resolved_refs:
            if citation and hasattr(citation, 'ref') and hasattr(citation.ref, 'tref') and 'Mishneh Torah' in citation.ref.tref:
                new_inference.append(citation.ref.tref)
        footnote_and_refs.append(new_inference)
    with open('footnote_and_MT_refs.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(footnote_and_refs)
