import django

django.setup()

from sefaria.model import *
from sefaria.tracker import modify_text
import csv


def unlock_all():
    rambam_vs = VersionSet(
        {'versionTitle': 'Mishneh Torah, trans. by Eliyahu Touger. Jerusalem, Moznaim Pub. c1986-c2007'})
    for version in rambam_vs:
        version.status = ''
        version.save()


def lock_all():
    rambam_vs = VersionSet(
        {'versionTitle': 'Mishneh Torah, trans. by Eliyahu Touger. Jerusalem, Moznaim Pub. c1986-c2007'})
    for version in rambam_vs:
        version.status = 'locked'
        version.save()


def ingest_fixed_text(ref, new_text):
    oref = Ref(f"Mishneh Torah, {ref}")
    modify_text(user=142625,
                oref=oref,
                vtitle="Mishneh Torah, trans. by Eliyahu Touger. Jerusalem, Moznaim Pub. c1986-c2007",
                lang="en",
                text=new_text)
    print(f"Saved new text for {ref}")


if __name__ == '__main__':
    unlock_all()
    with open('mishneh_torah_data_non_manual_cleaned.csv', newline='') as f:
        reader = csv.reader(f)
        for line in reader:
            ref = line[0]
            text = line[1]
            ingest_fixed_text(ref, text)
    lock_all()
