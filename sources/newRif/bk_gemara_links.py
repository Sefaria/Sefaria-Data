import django
django.setup()
from sources import functions
from rif_utils import path, remove_metadata

def base_tokenizer(string):
    return remove_metadata(string, 'Bava Kamma').split()

match_ref(Ref('Bava Kamma').text('he'), Ref('Rif Bava Kamma').text('he'), base_tokenizer=base_tokenizer, dh_extract_method=lambda x: ' '.join(x).split()[:8]):
    links.append({
    "refs": [item.a.ref.tref, item.b.ref.tref],
    "type": "Commentary",
    "auto": True,
    "generated_by": 'rif gemara matcher'
    })

print(len(links))
server = 'http://localhost:8000'
#server = 'https://glazner.cauldron.sefaria.org'
functions.post_link(links, server = server)
