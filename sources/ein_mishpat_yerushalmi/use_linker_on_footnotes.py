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


def insert_token_before_repeated_word(text, word, token):
    # Find all occurrences of the word and skip the first one
    matches = [m.start() for m in re.finditer(word, text)]

    # Only insert if there are two or more occurrences
    if len(matches) > 1:
        # We start from the second occurrence
        for i in range(1, len(matches)):
            text = text[:matches[i] + i - 1] + token + text[matches[i] + i - 1:]

    return text

if __name__ == '__main__':
    footnotes_list = csv_to_list("Ein Mishpat Yerusalmi Wikitext Footnotes Refs.csv")
    linker = library.get_linker("he")
    footnote = """
     1 ד_א מיי' פ ו' מהל' נדרים הלכה ג', |טור ושו"ע יו"ד סי' רכ"א סעיף א', סמ"ג לאוין רמב:
    """
    clean_footnote = "מיי'" + footnote.split("מיי'", 1)[1] if "מיי'" in footnote else footnote
    clean_footnote = insert_token_before_repeated_word(clean_footnote, "מיי'", ")  ")
    clean_footnote = clean_footnote.replace('סמ"ג', ' )סמ"ג')
    clean_footnote = clean_footnote.replace('|', ' ')
    doc = linker.link(clean_footnote, type_filter="citation", with_failures=True)



    footnote_and_refs = []
    for footnote in tqdm(footnotes_list):
        new_inference = []
        new_inference.append(footnote)
        clean_footnote = "מיי'" + footnote.split("מיי'", 1)[1] if "מיי'" in footnote else footnote
        clean_footnote = insert_token_before_repeated_word(clean_footnote, "מיי'", ")  ")
        clean_footnote = clean_footnote.replace('סמ"ג', ' )סמ"ג')
        clean_footnote = clean_footnote.replace('|', ' ')
        doc = linker.link(clean_footnote, type_filter="citation", with_failures=True)
        for citation in doc.resolved_refs:
            if citation and hasattr(citation, 'ref') and hasattr(citation.ref, 'tref') and 'Mishneh Torah' in citation.ref.tref:
                new_inference.append(citation.ref.tref)
        footnote_and_refs.append(new_inference)
    with open('footnote_and_MT_refs.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(footnote_and_refs)
