import django
django.setup()
from sefaria.model import *
from sources.functions import post_link
import re

links = []
for book in ['Genesis', 'Jeremiah', 'Daniel', 'Ezra']:
    for ref in Ref(f'Sefer HaShorashim, Biblical Aramaic Lexicon, {book}').all_segment_refs():
        sref = ref.normal()
        base = sref.split(',')[-1]
        base = re.sub(':[^:]*$', '', base)
        links.append({'type': 'commentary',
                      'refs': [sref, Ref(base).normal()],
                      'auto': True,
                      'generated_by': 'aramic shorashim linker'})
post_link(links, server='http://localhost:9000', skip_lang_check=False, VERBOSE=False)
