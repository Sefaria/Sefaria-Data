import django
django.setup()
from sefaria.model import *

for t in library.get_indexes_in_category('Kessef Mishneh', include_dependant=True):
    i = library.get_index(t)
    i.base_text_mapping = "many_to_one"
    i.save()
    Ref(t).autolinker().refresh_links()
