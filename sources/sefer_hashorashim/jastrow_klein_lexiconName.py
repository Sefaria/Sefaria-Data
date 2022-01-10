import django
django.setup()
from sources.functions import post_index

server = 'https://shorashim.cauldron.sefaria.org'
for ind in ['Jastrow', 'Klein Dictionary']:
    i = post_index({'title': ind}, 'https://sefaria.org', 'GET')
    i['schema']['nodes'][0]['lexiconName'] = i['lexiconName']
    post_index(i, server)
