import django

django.setup()

import csv
import re
from sefaria.model import *
from sefaria.model.schema import AddressTalmud


# This function generates a CSV given a list of dicts
def generate_csv(dict_list, headers, file_name):
    with open(f'{file_name}.csv', 'w+') as file:
        c = csv.DictWriter(file, fieldnames=headers)
        c.writeheader()
        c.writerows(dict_list)
    print(f"File writing of {file_name} complete")


def clean_text(raw_text):
    raw_text = str(raw_text)
    text_array = re.sub(r"\[|\]|\{|\}", "", raw_text)
    return text_array


def create_list_yerushalmi_masechtot():
    yerushalmi_masechtot = []
    talmud_indices = library.get_indexes_in_category("Yerushalmi")
    for index in talmud_indices:
        masechet = re.findall(r"Jerusalem Talmud (.*?)$", index)
        yerushalmi_masechtot.append(masechet[0])
    return yerushalmi_masechtot


# This function creates a list of mishnah trefs, and extracts any masechtot
# that are not also found in the Yerushalmi
def create_list_of_yerushalmi_mishnah_trefs():
    full_tref_list = []

    # Clean out non-Yerushalmi references
    talmud_indices = library.get_indexes_in_category("Yerushalmi", full_records=True)
    for index in talmud_indices:
        mishnah_refs = index.all_segment_refs()
        for mishnah in mishnah_refs:
            mishnah_tref = mishnah.normal()
            first_segment = re.match(r".*:1$", mishnah_tref)

            # First segment is usually the Mishnah text
            if first_segment:
                full_tref_list.append(mishnah_tref)
    return full_tref_list


# This function creates a list of mishnah trefs, and extracts any masechtot
# that are not Yerushalmi
def create_list_of_mishnah_mishnah_trefs():
    mishnah_indices = library.get_indexes_in_category("Mishnah", full_records=True)
    full_tref_list = []
    yerushalmi_mishnah_mishnah_refs = []
    for index in mishnah_indices:
        mishnah_refs = index.all_segment_refs()
        for mishnah in mishnah_refs:
            full_tref_list.append(mishnah.normal())
    yerushalmi_masechtot = create_list_yerushalmi_masechtot()

    for mishnah in full_tref_list:
        mishnah_masechet = Ref(mishnah).index.title
        if mishnah_masechet in yerushalmi_masechtot:
            yerushalmi_mishnah_mishnah_refs.append(mishnah)
    return yerushalmi_mishnah_mishnah_refs


def get_french_text(talmud_ref):
    french_text = talmud_ref.text('en', vtitle='Le Talmud de Jérusalem, traduit par Moise Schwab, 1878-1890 [fr]')
    french_text = french_text.text
    french_text = clean_text(french_text)
    return french_text


def get_hebrew_text(ref, type='yerushalmi-mishnah'):
    if type == 'yerushalmi-mishnah':
        heb_text = ref.text('he', vtitle='Mechon-Mamre')
        heb_text = heb_text.text
    elif type == 'mishnah-mishnah':
        heb_text = ref.text('he', vtitle='Torat Emet 357')
        heb_text = heb_text.text
        heb_text = heb_text[:-1]

    return heb_text


def parse_french_mishnah():
    mishnah_list = []

    ls = LinkSet({"generated_by": "yerushalmi-mishnah linker"})

    for link in ls:
        refs = link.refs
        mishnah_ref, talmud_ref = refs if "Mishnah" in refs[0] else reversed(refs)
        french_text = get_french_text(Ref(talmud_ref))
        mm_text = get_hebrew_text(Ref(mishnah_ref), type="mishnah-mishnah")
        ym_text = get_hebrew_text(Ref(talmud_ref), type="yerushalmi-mishnah")

        mishnah_list.append({
            'mishnah_tref': mishnah_ref,
            'talmud_tref': talmud_ref,
            'mishnah_mishnah_text': mm_text,
            'yerushalmi_mishnah_text': ym_text
        })
    return mishnah_list


# Given a tref, where the prev tref is the same
# Concatenate this yerushalmi mishnah text to the prev
# Delete this row
def post_processing_data(mishnah_list):
    cleaned_mishnah_list = [mishnah_list[0]]

    for i in range(1, len(mishnah_list)-1):
        prev = mishnah_list[i - 1]
        cur = mishnah_list[i]
        next = mishnah_list[i+1]

        # If there's a case of a repeated tref, concatenate the text
        # and eliminate the redundancy.
        if cur['mishnah_tref'] == prev['mishnah_tref']:
            prev['yerushalmi_mishnah_text'] += f" {cur['yerushalmi_mishnah_text']}"
            cleaned_mishnah_list.append(prev)
        elif cur['mishnah_tref'] != next['mishnah_tref']: # avoid double counting bug
            cleaned_mishnah_list.append(cur)

    return cleaned_mishnah_list


def generate_linkset_validation_csv():
    mishnah_list = parse_french_mishnah()
    mishnah_list.sort(key=lambda x: Ref(x["mishnah_tref"]).order_id())
    mishnah_list = post_processing_data(mishnah_list)
    generate_csv(mishnah_list, ['mishnah_tref',
                                'talmud_tref',
                                'mishnah_mishnah_text',
                                'yerushalmi_mishnah_text'], 'french_mishnah_list')


## Todo - note, we moved away from this approach since the linkset looks good
def pure_validation_csv():
    mm_csv_list = []
    ym_csv_list = []

    # For each Mishnah in Yerushalmi
    mishnah_mishnah_trefs = create_list_of_mishnah_mishnah_trefs()
    yerushalmi_mishnah_trefs = create_list_of_yerushalmi_mishnah_trefs()

    print(f"mm trefs: {len(mishnah_mishnah_trefs)}, ym_trefs: {len(yerushalmi_mishnah_trefs)}")
    # Retrieve Ref and Text
    for mm_tref in mishnah_mishnah_trefs:
        tref = mm_tref
        text = get_hebrew_text(Ref(tref), type="mishnah-mishnah")
        mm_csv_list.append({'mishnah_mishnah_tref': tref, 'mishnah_mishnah_text': text})
        # Append to list, and order

    mm_csv_list.sort(key=lambda x: Ref(x["mishnah_mishnah_tref"]).order_id())
    generate_csv(mm_csv_list,
                 headers=['mishnah_mishnah_tref',
                          'mishnah_mishnah_text'],
                 file_name='fr_mm_pure_validation')

    # Retrieve Ref and Text in Talmud
    for ym_tref in yerushalmi_mishnah_trefs:
        tref = ym_tref
        text = get_hebrew_text(Ref(tref), type="yerushalmi-mishnah")
        ym_csv_list.append({'yerushalmi_mishnah_tref': tref, 'yerushalmi_mishnah_text': text})

    ym_csv_list.sort(key=lambda x: Ref(x["yerushalmi_mishnah_tref"]).order_id())
    generate_csv(ym_csv_list,
                 headers=['yerushalmi_mishnah_tref',
                          'yerushalmi_mishnah_text'],
                 file_name='fr_ym_pure_validation')


if __name__ == "__main__":
    generate_linkset_validation_csv()
    # pure_validation_csv()
