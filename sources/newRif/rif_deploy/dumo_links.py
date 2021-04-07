import django
django.setup()
from sefaria.model import *
from scripts.move_draft_text import ServerTextCopier
import json

DEST = 'https://catstos.cauldron.sefaria.org'
APIKEY = os.environ['APIKEY']
indexes = set(library.get_indexes_in_category('Rif', include_dependant=True))
links = []
for index in indexes:
    copier = ServerTextCopier(DEST, APIKEY, index, post_index=False, post_links=2)
    copier.load_objects()
    links += [l.contents() for l in copier._linkset if not getattr(l, 'source_text_oid', None)]
links = list({tuple(l['refs']): l for l in links}.values())
with open('rif_links.json', 'w') as fp:
    json.dump(links, fp)