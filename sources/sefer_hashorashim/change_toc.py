import django
django.setup()
from sefaria.model import *
from sefaria.helper.category import move_index_into, move_category_into, create_category

enc = ['Reference', 'Encyclopedic Works']
create_category(enc, 'Encyclopedic Works', 'אנציקלופדיות')
move_category_into(['Reference', 'Shem HaGedolim'], enc)
move_index_into('Imrei Binah', ['Jewish Thought', 'Acharonim'])
for ind in [ 'Ayin Zokher', 'Devash Lefi', 'Midbar Kedemot', 'The Jewish Spiritual Heroes']:
    move_index_into(ind, enc)
dicts = ['Jastrow',
         'Klein Dictionary',
         'Sefer HaShorashim',
         'Sefer HeArukh',
         'Otzar Laazei Rashi',
         'Animadversions by Elias Levita on Sefer HaShorashim',
         "Hafla'ah ShebaArakhin on Sefer HeArukh"]
for i, dictionary in enumerate(dicts, 1):
    ind = library.get_index(dictionary)
    ind.order = [i]
    ind.save()
