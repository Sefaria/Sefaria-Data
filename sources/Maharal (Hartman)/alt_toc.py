import csv
with open("Ner Mitzvah.csv") as f:
    for row in csv.reader(f):
        if row[0].startswith("Ner Mitzvah"):
            if row[2]:
                en, he = row[2], row[3]
                ref = row[0]