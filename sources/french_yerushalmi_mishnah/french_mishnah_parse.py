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


def get_numbers_from_yerushalmi_tref(y_tref):
    result = re.findall(r".* (\d*:\d*:\d*)$", y_tref)
    if result:
        return result[0]
    else:
        return y_tref


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


def get_yerushalmi_linkset_mishnahs():
    ym_list = []
    ls = LinkSet({"generated_by": "yerushalmi-mishnah linker"})
    for link in ls:
        refs = link.refs
        mishnah_ref, talmud_ref = refs if "Mishnah" in refs[0] else reversed(refs)
        ym_list.append(mishnah_ref)
    return ym_list


# Given a tref, where the prev tref is the same
# Concatenate this yerushalmi mishnah text to the prev
# Delete this row
def handle_duplicated_single_ref(mishnah_list):
    cleaned_mishnah_list = [mishnah_list[0]]

    for i in range(1, len(mishnah_list) - 1):
        prev = mishnah_list[i - 1]
        cur = mishnah_list[i]
        next = mishnah_list[i + 1]

        # If there's a case of a repeated tref, concatenate the text
        # and eliminate the redundancy.
        if cur['mishnah_tref'] == prev['mishnah_tref']:
            prev['yerushalmi_mishnah_text'] += f" {cur['yerushalmi_mishnah_text']}"
            cleaned_mishnah_list.append(prev)
        elif cur['mishnah_tref'] != next['mishnah_tref']:  # avoid double counting bug
            cleaned_mishnah_list.append(cur)

    return cleaned_mishnah_list


def process_ranged_ref(mishnah_list):
    cleaned_mishnah_list = []
    ym_list = get_yerushalmi_linkset_mishnahs()
    i = 0
    while i < len(mishnah_list):  # changes dynamically with remove()
        mishnah = mishnah_list[i]
        is_overlapping = False
        if Ref(mishnah['mishnah_tref']).is_range():
            refs = Ref(mishnah['mishnah_tref']).range_list()
            refs_normal = []
            for ref in refs:
                refs_normal.append(ref.normal())
            for each_ref in refs_normal:
                if each_ref in ym_list:
                    is_overlapping = True

            # In the case of a ranged ref without overlap (i.e.
            # Mishnah Berakhot 1:1, Mishnah Berakhot 1:2-3, Mishnah Berakhot 1:4...
            # as opposed to Mishnah Berakhot 1:2, Mishnah Berakhot 1:2-3 where 1:2 is repeated.
            if not is_overlapping:
                cleaned_mishnah_list.append({
                    'mishnah_tref': refs_normal[0],
                    'talmud_tref': mishnah['talmud_tref'],
                    'mishnah_mishnah_text': mishnah['mishnah_mishnah_text'],
                    'yerushalmi_mishnah_text': mishnah['yerushalmi_mishnah_text']
                })
                for j in range(1, len(refs_normal)):
                    cleaned_mishnah_list.append({
                        'mishnah_tref': refs_normal[j],
                        'talmud_tref': '',
                        'mishnah_mishnah_text': '',
                        'yerushalmi_mishnah_text': ''
                    })
            elif is_overlapping:  # if it is an overlapping ranged ref
                # Determine, is the overlap with the prev or the next
                prev = mishnah_list[i - 1] if i != 0 else None
                next = mishnah_list[i + 1] if i != len(mishnah_list) - 1 else None
                # if prev, pre-concat to the ranged ref
                if prev['mishnah_tref'] in refs_normal:
                    print(mishnah)
                    mishnah[
                        'yerushalmi_mishnah_text'] = f"{prev['yerushalmi_mishnah_text']} {mishnah['yerushalmi_mishnah_text']}"
                    mishnah['talmud_tref'] = f"{prev['talmud_tref']}, {get_numbers_from_yerushalmi_tref(mishnah['talmud_tref'])}"
                    print(mishnah)
                    cleaned_mishnah_list.remove(prev)  # already was appended

                # if next, concat to the ranged ref
                elif next['mishnah_tref'] in refs_normal:
                    mishnah['yerushalmi_mishnah_text'] += f" {next['yerushalmi_mishnah_text']}"
                    mishnah['talmud_tref'] += f", {get_numbers_from_yerushalmi_tref(next['talmud_tref'])}"
                    mishnah_list.remove(next)

                # only append the ranged ref
                cleaned_mishnah_list.append(mishnah)

        else:
            cleaned_mishnah_list.append(mishnah)
        i +=1

    return cleaned_mishnah_list


def post_processing_data(mishnah_list):
    mishnah_list = handle_duplicated_single_ref(mishnah_list)
    mishnah_list = process_ranged_ref(mishnah_list)
    return mishnah_list


def generate_linkset_validation_csv():
    mishnah_list = parse_french_mishnah()
    mishnah_list.sort(key=lambda x: Ref(x["mishnah_tref"]).order_id())
    mishnah_list = post_processing_data(mishnah_list)
    generate_csv(mishnah_list, ['mishnah_tref',
                                'talmud_tref',
                                'mishnah_mishnah_text',
                                'yerushalmi_mishnah_text'], 'french_mishnah_list')


if __name__ == "__main__":
    generate_linkset_validation_csv()
