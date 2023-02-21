import django

django.setup()

django.setup()
superuser_id = 171118
# import statistics
import csv
from sefaria.model import *
from sefaria.system.database import db
from sefaria.model.schema import AddressTalmud
import time
from datetime import datetime, timezone
from sefaria.system.database import db



yerusalmi_masechtot =[
'Berakhot',
'Peah',
'Demai',
'Kilayim',
'Sheviit',
'Terumot',
'Maasrot',
'Maaser Sheni',
'Challah',
'Orlah',
'Bikkurim',
'Shabbat',
'Eruvin',
'Pesachim',
'Yoma',
'Shekalim',
'Sukkah',
'Rosh Hashanah',
'Beitzah',
'Taanit',
'Megillah',
'Chagigah',
'Moed Katan',
'Yevamot',
'Sotah',
'Ketubot',
'Nedarim',
'Nazir',
'Gittin',
'Kiddushin',
'Bava Kamma',
'Bava Metzia',
'Bava Batra',
'Sanhedrin',
'Shevuot',
'Avodah Zarah',
'Makkot',
'Horayot',
'Niddah'
]
vilna_to_ref_map = {}


def num_to_gematria(number):
    hebrew_letters = {
        1: 'א',
        2: 'ב',
        3: 'ג',
        4: 'ד',
        5: 'ה',
        6: 'ו',
        7: 'ז',
        8: 'ח',
        9: 'ט',
        10: 'י',
        20: 'כ',
        30: 'ל',
        40: 'מ',
        50: 'נ',
        60: 'ס',
        70: 'ע',
        80: 'פ',
        90: 'צ',
        100: 'ק',
        200: 'ר',
        300: 'ש',
        400: 'ת'
    }
    result = ''
    for value, letter in sorted(hebrew_letters.items(), reverse=True):
        while number >= value:
            result += letter
            number -= value
    result = result.replace('יה', 'טו')
    result = result.replace('יו', 'טז')
    return result


# def convert_date_format(date_string):
#     # date_string = '9/12/2035'
#
#     # Parse the date string into a datetime object
#     date = datetime.strptime(date_string, '%m/%d/%Y')
#
#     # Add timezone information
#     date_with_tz = date.replace(tzinfo=timezone.utc)
#
#     # Convert datetime object to ISO 8601 format with UTC offset
#     iso_date_string = date_with_tz.isoformat(timespec='milliseconds') + '+00:00'
#
#     return(iso_date_string)

def rectify_yersuhalmi_ref(ref_string):
    string = ref_string

    # Find the index of the last space in the string
    last_space_index = string.rfind(" ")
    last_part = string[last_space_index + 1:]
    # last_part = last_part+'a - '+last_part+'b'

    if last_space_index == -1:
        print("No space character found in string")
    else:
        # Replace the last part of the string with the new part
        if 'Peah 10a' in 'Jerusalem Talmud '+ string[:last_space_index + 1] + last_part + "a":
            real_ref =  Ref(vilna_to_ref_map['Jerusalem Talmud '+ string[:last_space_index + 1] + last_part + "b"])

        else:
            amud_a_ref = Ref(vilna_to_ref_map['Jerusalem Talmud '+ string[:last_space_index + 1] + last_part + "a"])
            if 'Jerusalem Talmud '+ string[:last_space_index + 1] + last_part + "b" in vilna_to_ref_map.keys():
                amud_b_ref = Ref(vilna_to_ref_map['Jerusalem Talmud '+ string[:last_space_index + 1] + last_part + "b"])
                real_ref = amud_a_ref.to(amud_b_ref)
            else:
                real_ref = amud_a_ref
        # new_string = 'Jerusalem Talmud '+ string[:last_space_index + 1] + last_part
        # real_ref = vilna_to_ref_map[new_string]
        return (real_ref)

def fill_vilna_to_ref_map():
    for masechet in yerusalmi_masechtot:
        talmud_addr = AddressTalmud(0)
        index = library.get_index("Jerusalem Talmud " + masechet)
        alt_struct = index.get_alt_structure("Vilna")
        amud_to_chapter_map = {}
        for chapter in alt_struct.children:
            starting_address = chapter.startingAddress
            starting_index = talmud_addr.toNumber('en', starting_address)
            for amud_offset, amud_ref in enumerate(chapter.refs):
                amud_str = talmud_addr.toStr('en', starting_index + amud_offset)
                if amud_str in amud_to_chapter_map:
                    # prev chapter and next chapter are on same amud
                    # combine refs
                    amud_ref = Ref(amud_to_chapter_map[amud_str]).to(Ref(amud_ref)).normal()
                amud_to_chapter_map[amud_str] = amud_ref
                vilna_to_ref_map["Jerusalem Talmud " + masechet + " " + amud_str] = amud_ref
                # print(masechet, amud_str, amud_ref)


if __name__ == '__main__':
    print("hello world")
    fill_vilna_to_ref_map()
    # a = Ref('Jerusalem Talmud Niddah 3:5:3-4')
    # a = a.he_book()

    collection = []
    with open('Yerushalmi_Yomi_Cal_-_Sheet1.csv', 'r') as file:
        reader = csv.reader(file, delimiter=',')
        for row in reader:
            # if row[3] != '' and row[3] != "Niddah 13":
            if row[3] != '':
                ref = rectify_yersuhalmi_ref(row[3]).normal('en')
                last_space_index = row[3].rfind(" ")
                last_part = row[3][last_space_index + 1:]
                he_display = Ref(ref).he_book() + " " + str(num_to_gematria(int(last_part)))
                # ref = Ref("Jerusalem Talmud Vilna, Berakhot  1a").normal('en')

                # date = convert_date_format(row[0])
                entry = {
                    "date": datetime.strptime(row[0], "%m/%d/%Y"),
                    "ref": ref,
                    "displayValue": "Jerusalem Talmud " + row[3],
                    "heDisplayValue": he_display
                }
                collection.append(entry)
    yy = db.yerushalmi_yomi
    db.drop_collection(yy)
    for entry in collection:
        yy.insert_one(entry)
    yy.create_index("date")

    # for e in db_entries:
    #     hy.replace_one({'date': e['date']}, e, upsert=True)
    # hy.create_index("date")
    # print(collection)










