import django
django.setup()
from sefaria.model import *
for l in derush:
    if hasattr(l, 'inline_reference'):
        data = l.inline_reference.pop('data-order')
        l.inline_reference['data_label'] = str(data)
        print(l.inline_reference)
