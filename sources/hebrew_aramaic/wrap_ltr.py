import django
django.setup()
from sefaria.model import *
import re

def wrap(string):
    return re.sub('([A-Za-z][^א-ת]*</i>)', r'<span class="englishWithinHebrew" dir="ltr">\1</span>', string)

def change_strings(content):
    if isinstance(content, str):
        content = wrap(content)
    elif 'binyans' in content:
        for b, binyan in enumerate(content['binyans']):
            for d in range(len(binyan)):
                content['binyans'][b][d] = change_strings(binyan[d])
    elif 'senses' in content:
        for s, sense in enumerate(content['senses']):
            content['senses'][s] = change_strings(sense)
    else:
        for key in content:
            if key in ['pos', 'binyan-form', 'binyan-name', 'number']:
                pass
            elif key in ['definition', 'notes']:
                content[key] = change_strings(content[key])
            else:
                print('unknown key:', key)
    return content


for le in LexiconEntrySet({'parent_lexicon': 'Krupnik Dictionary'}):
    le.content = change_strings(le.content)
    try:
        le.save()
    except Exception as e:
        print(777, e, le.headword, le.content)

