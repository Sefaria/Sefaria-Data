import django
django.setup()
from sefaria.model import *

for index in library.get_indexes_in_category('Rif', include_dependant=True, full_records=True):
    index.delete()