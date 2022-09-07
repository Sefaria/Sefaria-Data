import django

django.setup()

import csv
import re
import bleach
from sefaria.helper.normalization import RegexNormalizer

from sefaria.model import *
from utilities import sefaria_book_names, chabad_book_names, create_book_name_map, export_data_to_csv, ALLOWED_ATTRS, ALLOWED_TAGS

map = create_book_name_map(chabad_book_names, sefaria_book_names)


def create_chabad_ref(sefaria_ref):
    book_name_capture = re.findall(r"(.*) \d+.", sefaria_ref)
    sef_book_name = book_name_capture[0]
    chabad_book_name = ""

    for chabad_key in map:
        if map[chabad_key] == sef_book_name:
            chabad_book_name = chabad_key

    num_ref = re.findall(r"(\d+)\.", sefaria_ref)
    chapter_num = num_ref[0]
    return f"{chabad_book_name} - Chapter {chapter_num}"


def clean_dibbur_hamatchil(text):
    clean_dhm = re.findall(r"(.*?)[ -.]*?-$", text, re.DOTALL)
    if not clean_dhm:
        return text
    return clean_dhm[0]


def remove_all_html_punct(text):
    cleaned = re.sub(r"[^A-Za-z <>'\[\]\?\.,]|<i>|</i>|<br>", "", text)
    return cleaned


def clean_html(text):

    # Convert links
    links = re.findall(r"<a href=.*?>(.*?)<\/a>", text)
    for link in links:

        # Add escape characters to links data for matching
        if ")" in link or "(" in link:
            re_link = re.sub(r"\)", "\\)", link)
            re_link = re.sub(r"\(", "\\(", re_link)
        else:
            re_link = link
        clean_link = re.sub(r"[^A-Za-z :0-9]", " ", link)
        patt = f"<a href=.*?>{re_link}<\/a>"
        text = re.sub(patt, clean_link, text)

    text = bleach.clean(text,
                     tags=ALLOWED_TAGS,
                     attributes=ALLOWED_ATTRS,
                     strip=True)

    return text


def insert_footnote(insertion_index, halakha_text, commentary_text):
    footnote = f"<sup class=\"footnote-marker\">1</sup><i class=\"footnote\">{commentary_text}</i>"
    added_footnote = halakha_text[:insertion_index]+footnote+halakha_text[insertion_index:]
    return added_footnote


# Ingest cleaned MT as a dict
mt_dict = {}
with open('mishneh_torah_data_cleaned.csv', newline='') as csvfile:
    r = csv.reader(csvfile, delimiter=',')
    for row in r:
        ref = row[0]
        mt_dict[ref] = row[1]

count = 0
manual_comms = []
inserted_comms = []
with open('commentary.csv', newline='') as csvfile:
    r = csv.reader(csvfile, delimiter=',')
    for row in r:

        former_ref = ref
        ref = row[0]

        # skip first row
        if ref == "Blessings 4.6":
            inserted_text = ""

        if former_ref != ref:
            # text complete, append and reset
            inserted_comms.append({
                'ref': former_ref,
                'text': inserted_text
            })

            # reset the text
            inserted_text = ""


        chabad_ref = create_chabad_ref(ref)
        dhm = clean_dibbur_hamatchil(row[1])
        dhm = clean_html(dhm)
        com_txt = clean_html(row[2])
        body_text = mt_dict[ref] if inserted_text == "" else inserted_text

        if dhm in body_text:
            insert_footnote_index = body_text.index(dhm) + len(dhm)

        if dhm not in body_text:
            non_alphabetic_normalizer = RegexNormalizer("[,\.?'\":;!@#$%^&*\[\]{}()\s-]|<.*?>", '')
            normalized_dhm = non_alphabetic_normalizer.normalize(dhm)
            normalized_body_text = non_alphabetic_normalizer.normalize(body_text)

            norm_dhm_idx_start = normalized_body_text.find(normalized_dhm)
            if norm_dhm_idx_start == -1:
                manual_comms.append({
                    'sefaria_ref': ref,
                    'chabad_ref': chabad_ref,
                    'halakha_text': body_text,
                    'dibbur_hamatchil': dhm,
                    'commentary': com_txt
                })
                count += 1
            else:
                norm_dhm_range = (norm_dhm_idx_start, norm_dhm_idx_start + len(normalized_dhm))

                mapping = non_alphabetic_normalizer.get_mapping_after_normalization(body_text)
                orig_range = \
                non_alphabetic_normalizer.convert_normalized_indices_to_unnormalized_indices([norm_dhm_range], mapping)[
                    0]
                insert_footnote_index = orig_range[-1] + 1

        # Insert the footnote at the right index.
        inserted_text = insert_footnote(insert_footnote_index, body_text, com_txt)

    export_data_to_csv(manual_comms, "manual_commentaries",
                       headers_list=['sefaria_ref', 'chabad_ref', 'halakha_text', 'dibbur_hamatchil', 'commentary'])
    export_data_to_csv(inserted_comms, "inserted_commentaries", headers_list=['ref', 'text'])


# TODO in PP and here
# Bleach text for tags we don't want
# Report for </p><p> preceded by either a comma, or an alphabetic char
