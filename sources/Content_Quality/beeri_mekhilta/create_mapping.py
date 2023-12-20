import django

django.setup()

import csv
import re
from sefaria.model import *
from parsing_utilities.text_align import CompareBreaks


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
    print(f"Wrote {masechet} to CSV")


def normalize_string(text_segment):
    return ''.join(letter for letter in text_segment if letter.isalnum())


def compare_text_approach(beeri_text_strs, beeri_tref_to_index_map, prod_text_strs, prod_tref_to_index_map):
    """Note: This only worked for 6/9 of the Masechtot, which is why we filter the "breaking" masechtot on top."""
    for masechet in beeri_text_strs:

        if masechet not in ["Tractate Nezikin", "Tractate Shirah", "Tractate Vayehi Beshalach"]:
            cb = CompareBreaks(beeri_text_strs[masechet], prod_text_strs[masechet])
            map = cb.create_mapping()

            expanded_mapping = []

            for beeri_idx in map:
                prod_idx = list(map[beeri_idx])
                if prod_idx:
                    prod_idx = prod_idx[0]
                    expanded_mapping.append({"Beeri Ref": beeri_tref_to_index_map[masechet][beeri_idx - 1],
                                             "Wiki Ref": prod_tref_to_index_map[masechet][prod_idx - 1]})
            write_to_csv(masechet, expanded_mapping)


def normalize_text(beeri_text_strs, prod_text_strs):
    normalized_prod_text_strs = {}
    normalized_beeri_text_strs = {}

    for masechet in beeri_text_strs:
        for seg in prod_text_strs[masechet]:
            if masechet in normalized_prod_text_strs:
                normalized_prod_text_strs[masechet].append(normalize_string(seg))
            else:
                normalized_prod_text_strs[masechet] = [normalize_string(seg)]
        for seg in beeri_text_strs[masechet]:
            if masechet in normalized_beeri_text_strs:
                normalized_beeri_text_strs[masechet].append(normalize_string(seg))
            else:
                normalized_beeri_text_strs[masechet] = [normalize_string(seg)]
    return normalized_beeri_text_strs, normalized_prod_text_strs


def brute_force_mapping(normalized_beeri, normalized_prod, beeri_tref_to_index_map, prod_tref_to_index_map):
    """Brute force approach to get a quasi-map for the failing masechtot (Nezikin, Vayehi Beshalach, and Shirah) -
    which failed the compare breaks approach. The generated CSV will need some manual work. """
    for masechet in ["Tractate Nezikin", "Tractate Shirah", "Tractate Vayehi Beshalach"]:
        expanded_mapping = []
        prod_list = normalized_prod[masechet]
        for i in range(len(normalized_beeri[masechet])):
            beeri_segment = normalized_beeri[masechet][i]
            if not beeri_segment:
                continue
            for j, prod_seg in enumerate(prod_list):
                prod_segment = normalized_prod[masechet][j]

                if beeri_segment[:100] in prod_segment:
                    beeri_ref = beeri_tref_to_index_map[masechet][i]
                    prod_ref = prod_tref_to_index_map[masechet][j]
                    expanded_mapping.append({"Beeri Ref": beeri_ref, "Prod Ref": prod_ref})
                    prod_list[j:]

        write_to_csv(f"manual_report_{masechet}", expanded_mapping)


def generate_report_beeri():
    # Set up "all" list
    beeri_refs_all = []
    with open('beeri_version.csv', newline='') as csvfile:
        beeri_csv = csv.reader(csvfile)
        for row in beeri_csv:
            tref = row[0]
            masechet = re.findall(r"Mekhilta DeRabbi Yishmael Beeri, (.*) [^A-Za-z]*$", tref)[0]
            if masechet in ["Tractate Nezikin", "Tractate Shirah", "Tractate Vayehi Beshalach"]:
                beeri_refs_all.append(tref)

    # Set up "processed" list
    beeri_refs_processed = []
    with open('manual_report_Tractate Vayehi Beshalach_mapping.csv', newline='') as csvfile:
        beeri_csv = csv.reader(csvfile)
        for row in beeri_csv:
            tref = row[0]
            beeri_refs_processed.append(tref)

    with open('manual_report_Tractate Shirah_mapping.csv', newline='') as csvfile:
        beeri_csv = csv.reader(csvfile)
        for row in beeri_csv:
            tref = row[0]
            beeri_refs_processed.append(tref)

    with open('manual_report_Tractate Nezikin_mapping.csv', newline='') as csvfile:
        beeri_csv = csv.reader(csvfile)
        for row in beeri_csv:
            tref = row[0]
            beeri_refs_processed.append(tref)

    unreported_refs = set(beeri_refs_all) - set(beeri_refs_processed)
    for ref in unreported_refs:
        print(ref)


if __name__ == "__main__":
    csv_file = "beeri_version.csv"
    beeri_text_strs, beeri_tref_to_index_map = convert_csv()
    prod_text_strs, prod_tref_to_index_map = get_prod_list_of_strs()

    # Compare Text Approach to map Masechtot Pischa, Vayassa, Amalek, Bachodesh, Kaspa and Shabbata
    compare_text_approach(beeri_text_strs, beeri_tref_to_index_map, prod_text_strs, prod_tref_to_index_map)

    # Approach for "breaking" masechtot: Vayehi Beshalach, Shirah and Nezikin

    # Step One: Normalize English text
    normalized_beeri, normalized_prod = normalize_text(beeri_text_strs, prod_text_strs)

    # Step Two: Apply a Brute Force mapping algorithm
    brute_force_mapping(normalized_beeri, normalized_prod, beeri_tref_to_index_map, prod_tref_to_index_map)

    # Step Three: Generate a report of missing segments to aid manual work
    generate_report_beeri()
