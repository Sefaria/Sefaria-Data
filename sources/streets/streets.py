# encoding=utf-8

import csv
from sefaria.model import *

if __name__ == "__main__":
    f = open("streets.csv")
    streets = []
    reader = csv.reader(f)
    for i, row in enumerate(reader):
        if i == 0:
            continue
        city = row[2]
        street = row[4]
        try:
            assert Ref(street)
            print street
        except AssertionError:
            person = Person().load({"names.text": street})
            if person:
                print street
            continue
        if "ירושלים" == city.replace(" ", ""):
            streets.append(street)
