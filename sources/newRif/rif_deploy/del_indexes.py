import django
django.setup()
from sefaria.model import *

items = library.get_indexes_in_category('Rif', include_dependant=True, full_records=True)
for i, index in enumerate(items, 1):
    print(i, 'out of', len(items))
    index.delete()