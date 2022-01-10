import django
django.setup()
from sefaria.model import *
import csv


with open('yalkut.csv') as fp:
    data = list(csv.DictReader(fp))
    for row in data:
        if not Ref(row['Index Title']).text('he').text:
            print(row['Index Title'])
