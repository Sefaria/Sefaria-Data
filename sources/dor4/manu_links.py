import django
django.setup()
from sefaria.model import *
import csv

with open('/Users/yishaiglasner/Downloads/dor4manualLinks.csv') as fp:
    for row in csv.DictReader(fp):
        refs = []
        for i in (1, 2):
            ref = row[f'{i}']
            ref = ref.replace('_', ' ').replace('%2C', ',').replace('%3B', ';').replace('?', '').replace('%27', "'")
            ref = ref.split('/')[-1]
            oref = Ref(ref)
            if i == 1 and not oref.is_segment_level():
                oref = oref.as_ranged_segment_ref()
            refs.append(oref.normal())
        Link({
            'type': 'commentary',
            'refs': refs,
            'auto': True,
            'generated_by': 'dor revii manual links'
        }).save()

