import django
django.setup()
from sefaria.model import *
import csv
import re
from linking_utilities.dibur_hamatchil_matcher import *
with open("Romemot El on Psalms - he - Romemot El, Warsaw 1875.csv") as f:
    reader = csv.reader(f)
    for row in reader:
        ref, comment = row
        psalms_ref = ref.split()[-1].rsplit(".", 1)[0]
        psalms_ref = "Psalms {}".format(psalms_ref)
        link = {"refs": [ref, psalms_ref], "auto": True, "type": "Commentary", "generated_by"}