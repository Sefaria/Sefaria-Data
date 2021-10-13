import json
import django
django.setup()
from sources.functions import post_link
with open('masoret_links.json') as fp:
    links = json.load(fp)
post_link(links, server = 'http://localhost:9000')
