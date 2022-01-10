import django
django.setup()
from sources.functions import post_index

dicts = ['Jastrow',
  'Klein Dictionary',
  'Sefer HaShorashim',
  'Sefer HeArukh',
  'Otzar Laazei Rashi',
  'Animadversions by Elias Levita on Sefer HaShorashim',
  "Hafla'ah ShebaArakhin on Sefer HeArukh"]

server = 'http://localhost:9000'
for i, dictionary in enumerate(dicts, 1):
  dictionary = post_index({'title': dictionary}, 'https://sefaria.org', 'GET')
  dictionary['order'] = [i]
  post_index(dictionary, server)
