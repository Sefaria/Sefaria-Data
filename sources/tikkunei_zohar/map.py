import django
django.setup()
from sefaria.model import *
from sefaria.utils.talmud import daf_to_section, section_to_daf
import re
from parsing_utilities.text_align import CompareBreaks
import json

def strip_text(string):
    string = re.sub('\([^\)]*\)', '', string)
    string = re.sub('\[[^\]]*\]', '', string)
    string = re.sub('^<big>.*</big>$', '', string)
    return re.sub('[^ א-ת"\']', '', string)

start = '17a'
end = '62b'
old_version = 'Tikkunei Zohar'
new_version = 'Constantinople, 1740'
mappings = {}
for i in range(daf_to_section(start), daf_to_section(end)+1):
    daf = section_to_daf(i)
    tref = f'Tikkunei Zohar {daf}'
    ref = Ref(tref)
    old_text = [strip_text(x) for x in ref.text('he', old_version).text]
    new_text = [strip_text(x) for x in ref.text('he', new_version).text]
    comparer = CompareBreaks(old_text, new_text)
    compare_dict = comparer.create_mapping()
    for section in compare_dict:
        first = min(compare_dict[section])
        last = max(compare_dict[section])
        new_section = first if first == last else f'{first}-{last}'
        mappings[f'{tref}:{section}'] = f'{tref}:{new_section}'

with open('mappings.json', 'w') as fp:
    json.dump(mappings, fp)
