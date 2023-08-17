import re

import django

django.setup()

import csv
from sefaria.model import *
from parsing_utilities.text_align import CompareBreaks


# Todo
# Debug why breaking
# Add comments

def convert_csv():
    tref_to_index_map = {}
    text_str_by_masechet = {}

    with open('beeri_version.csv', newline='') as csvfile:
        beeri_csv = csv.reader(csvfile)
        for row in beeri_csv:
            tref = row[0]
            text_segment = row[1]
            masechet = re.findall(r"Mekhilta DeRabbi Yishmael Beeri, (.*) [^A-Za-z]*$", tref)[0]
            if masechet in text_str_by_masechet:
                text_str_by_masechet[masechet].append(text_segment)
                tref_to_index_map[masechet].append(tref)
            else:
                text_str_by_masechet[masechet] = [text_segment]
                tref_to_index_map[masechet] = [tref]

    return text_str_by_masechet, tref_to_index_map


def get_prod_list_of_strs():
    all_text_by_masechet = {}
    tref_index_map = {}

    category_masechet_map = {
        'Tractate Pischa': Ref('Mekhilta d\'Rabbi Yishmael 12:1-13:16'),
        'Tractate Vayehi Beshalach': Ref('Mekhilta d\'Rabbi Yishmael 13:17-14:31'),
        "Tractate Shirah": Ref('Mekhilta d\'Rabbi Yishmael 15:1-21'),
        "Tractate Vayassa": Ref('Mekhilta d\'Rabbi Yishmael 15:22-17:7'),
        "Tractate Amalek": Ref('Mekhilta d\'Rabbi Yishmael 17:8-18:27'),
        "Tractate Bachodesh": Ref('Mekhilta d\'Rabbi Yishmael 19:1-20:26'),
        "Tractate Nezikin": Ref('Mekhilta d\'Rabbi Yishmael 21:1-22:23'),
        "Tractate Kaspa": Ref('Mekhilta d\'Rabbi Yishmael 22:24-23:19'),
        "Tractate Shabbata": Ref('Mekhilta d\'Rabbi Yishmael 31:12-35:3')
    }

    def action(segment_str, tref, he_tref, version):
        nonlocal all_text_by_masechet
        nonlocal tref_index_map

        for masechet in category_masechet_map:
            if Ref(tref) in category_masechet_map[masechet].all_segment_refs():
                if masechet in all_text_by_masechet:
                    all_text_by_masechet[masechet].append(segment_str)
                    tref_index_map[masechet].append(tref)
                else:
                    all_text_by_masechet[masechet] = [segment_str]
                    tref_index_map[masechet] = [tref]

    mekhilta_version = Version().load({'versionTitle': "Mechilta, translated by Rabbi Shraga Silverstein"})
    mekhilta_version.walk_thru_contents(action)
    return all_text_by_masechet, tref_index_map


def write_to_csv(masechet, map):
    # Get the header row
    header = map[0].keys()

    # Create a CSV writer object
    with open(f"{masechet}_mapping.csv", "w") as f:
        writer = csv.writer(f)
        # Write the header row
        writer.writerow(header)
        # Write the data rows
        for row in map:
            writer.writerow(row.values())
    print(map)


if __name__ == "__main__":
    csv_file = "beeri_version.csv"
    beeri_text_strs, beeri_tref_to_index_map = convert_csv()
    prod_text_strs, prod_tref_to_index_map = get_prod_list_of_strs()

    print(len(prod_text_strs))
    print(len(beeri_text_strs))

    for masechet in beeri_text_strs:
        cb = CompareBreaks(beeri_text_strs[masechet], prod_text_strs[masechet])
        map = cb.create_mapping()

        # print(f"Masechet: {masechet}")
        # print(map)
        # print("\n\n\n")

        # trial for Shabbata
        expanded_mapping = []
        if masechet not in ["Tractate Nezikin", "Tractate Shirah", "Tractate Vayehi Beshalach"]:
            for beeri_idx in map:
                prod_idx = list(map[beeri_idx])  # TODO - iterate through if ever spanning more
                if prod_idx:
                    prod_idx = prod_idx[0]-1
                    print(f"len:{len(prod_tref_to_index_map[masechet])}, idx: {prod_idx}")
                    expanded_mapping.append({"Beeri Ref": beeri_tref_to_index_map[masechet][beeri_idx-1],
                                             "Wiki Ref": prod_tref_to_index_map[masechet][prod_idx]})
            print(f"Writing {masechet} to CSV")
            write_to_csv(masechet, expanded_mapping)
