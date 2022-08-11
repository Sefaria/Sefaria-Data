import django

django.setup()

import csv
import re

from sefaria.model import *


def setup_data():
    """
    This function reads the CSV from the scraping, and sets up a list of Chabad specific Rambam names,
    as well as a list of dictionaries of the scraping data for easy manipulation later
    """
    chabad_book_names = []
    mishneh_torah_list = []
    with open('mishneh_torah_data_scraped.csv', newline='') as csvfile:
        r = csv.reader(csvfile, delimiter=',')
        next(r, None)
        for row in r:
            book_ref = row[0]
            txt = row[1]
            mishneh_torah_list.append({'ref': book_ref, 'text': txt})
            book = re.findall(r"(.*) \d*.\d*", book_ref)[0]
            if book not in chabad_book_names:
                chabad_book_names.append(book)
    return chabad_book_names, mishneh_torah_list

def create_book_name_map(chabad_book_names):
    """
    This function creates a map between the Chabad Rambam names to the Sefaria Rambam names
    """
    sefaria_book_names = [
        'Foundations of the Torah',
        'Human Dispositions',
        'Torah Study',
        'Foreign Worship and Customs of the Nations',
        'Repentance',
        'Reading the Shema',
        'Prayer and the Priestly Blessing',
        'Tefillin, Mezuzah and the Torah Scroll',
        'Fringes',
        'Blessings',
        'Circumcision',
        'The Order of Prayer',
        'Sabbath',
        'Eruvin',
        'Rest on the Tenth of Tishrei',
        'Rest on a Holiday',
        'Leavened and Unleaved Bread',
        'Shofar, Sukkah and Lulav',
        'Sheqel Dues',
        'Sanctification of the New Month',
        'Fasts',
        'Scroll of Esther and Hanukkah',
        'Marriage',
        'Divorce',
        'Levirate Marriage and Release',
        'Virgin Maiden',
        'Woman Suspected of Infidelity',
        'Forbidden Intercourse',
        'Forbidden Foods',
        'Ritual Slaughter',
        'Oaths',
        'Vows',
        'Nazariteship',
        'Appraisals and Devoted Property',
        'Diverse Species',
        'Gifts to the Poor',
        'Heave Offerings',
        'Tithes',
        'Second Tithes and Fouth Year\'s Fruit',
        'First Fruits and other Gifts to Priests Outside the Sanctuary',
        'Sabbatical Year and the Jubilee',
        'The Chosen Temple',
        'Vessels of the Sanctuary and Those who Serve Therein',
        'Admission into the Sanctuary',
        'Things Forbidden on the Altar',
        'Sacrificial Procedure',
        'Daily Offerings and Additional Offerings',
        'Sacrifices Rendered Unfit',
        'Service on the Day of Atonement',
        'Trespass',
        'Paschal Offering',
        'Festival Offering',
        'Firstlings',
        'Offerings for Unintentional Transgressions',
        'Offerings for Those with Incomplete Atonement',
        'Substitution',
        'Defilement by a Corpse',
        'Red Heifer',
        'Defilement by Leprosy',
        'Those Who Defile Bed or Seat',
        'Other Sources of Defilement',
        'Defilement of Foods',
        'Vessels',
        'Immersion Pools',
        'Damages to Property',
        'Theft',
        'Robbery and Lost Property',
        'One Who Injures a Person or Property',
        'Murderer and the Preservation of Life',
        'Sales',
        'Ownerless Property and Gifts',
        'Neighbors',
        'Agents and Partners',
        'Slaves',
        'Hiring',
        'Borrowing and Deposit',
        'Creditor and Debtor',
        'Plaintiff and Defendant',
        'Inheritances',
        'The Sanhedrin and the Penalties within their Jursidiction',
        'Testimony',
        'Rebels',
        'Mourning',
        'Kings and Wars'
    ]

    # Confirmed that book names aligned, creating map
    name_map = {}
    for i in range(len(chabad_book_names)):
        name_map[chabad_book_names[i]] = sefaria_book_names[i]
    return name_map

def rename_refs_to_sefaria(mishneh_torah_list, name_map):
    """
    This function massages the Chabad Refs into Sefaria refs for the data list/dictionary
    """
    new_mt_list = []
    for halakha in mishneh_torah_list:
        ref = halakha['ref']
        book = re.findall(r"(.*) \d*.\d*", ref)[0]
        sef_book = name_map[book]
        sefaria_ref = re.sub(r"[^0-9.]+", f"{sef_book} ", ref)
        new_mt_list.append({'ref': sefaria_ref, 'text': halakha['text']})

    return new_mt_list

def export_cleaned_data_to_csv(mt_list):
    """
    This function writes the cleaned data to a new CSV
    """
    with open('mishneh_torah_data_cleaned.csv', 'w+') as csvfile:
        headers = ['ref', 'text']
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writerows(mt_list)


if __name__ == '__main__':
    chabad_book_names, mishneh_torah_list = setup_data()
    name_map = create_book_name_map(chabad_book_names)
    mishneh_torah_list = rename_refs_to_sefaria(mishneh_torah_list, name_map)
    export_cleaned_data_to_csv(mishneh_torah_list)