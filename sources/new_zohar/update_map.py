import json
import re
import django
django.setup()
from sefaria.model import *

with open('map_old_to_new-old.json') as fp:
    data = json.load(fp)
new = {}
for k, v in data.items():
    print(v)
    if v:
        ref = Ref(v)
        nref = Ref(re.sub('(?:Genesis|Exodus|Leviticus|Numbers|Deuteronomy), ', '', ref.section_ref().normal()).replace('TNNG', 'TNNNG'))
        obj = ref._core_dict()
        obj['sections'] = nref.sections
        obj['toSections'] = nref.toSections
        bref = Ref(_obj=obj)
        if nref.text('he').text != bref.text('he').text:
            print(111111, nref, bref)
        new[k] = nref.normal()
    else:
        new[k] = None
with open('map_old_to_new.json', 'w') as fp:
    data = json.dump(new, fp)
