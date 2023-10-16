import django

django.setup()

superuser_id = 171118
import csv
from sefaria.model import *
from sefaria.tracker import modify_bulk_text
from sefaria.helper.category import create_category
from sefaria.system.database import db
from datetime import datetime


def create_jsons_list(csv_path):
    limud_jsons = []
    with open(csv_path, 'r') as csv_file:
        # Create a CSV reader
        csv_reader = csv.reader(csv_file)

        for row in csv_reader:
            normalized_tref = Ref(row[1].replace('_', ' ').replace("%2C", '').replace(".", " ").replace("Arukh HaShulchan", "Arukh HaShulchan,")).normal()

            # Original date in the format MM/DD/YYYY
            original_date_str = row[0]

            # Convert the string to a datetime object
            original_date = datetime.strptime(original_date_str, "%m/%d/%Y")

            # Format the datetime object to the desired format
            formatted_date_str = original_date.strftime("%Y-%m-%dT00:00:00.000+0000")
            # print(formatted_date_str, normalized_tref)
            limud_jsons.append({"date": original_date, "refs": normalized_tref})
        return limud_jsons

if __name__ == '__main__':
    print("hello")
    jsons_list = create_jsons_list("AhS_Yomi_Calendar_-_Sefaria - AhS_Yomi_Calendar_-_Sefaria.csv")
    arukh_hashulchan_collection = db.arukh_hashulchan
    db.drop_collection(arukh_hashulchan_collection)
    for entry in jsons_list:
        arukh_hashulchan_collection.insert_one(entry)

    print("hi")
