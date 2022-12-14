import django

django.setup()

from sefaria.model import *
import csv


def ingest_fixed_text(ref, new_text):
    oref = Ref(f"Mishneh Torah, {ref}")
    tc = TextChunk(oref, vtitle="Mishneh Torah, trans. by Eliyahu Touger. Jerusalem, Moznaim Pub. c1986-c2007", lang="en")
    tc.text = new_text
    tc.save()
    print(f"Saved new text for {ref}")


if __name__ == '__main__':
    with open('mishneh_torah_data_non_manual_cleaned.csv', newline='') as f:
        reader = csv.reader(f)
        for line in reader:
            ref = line[0]
            text = line[1]
            ingest_fixed_text(ref, text)
