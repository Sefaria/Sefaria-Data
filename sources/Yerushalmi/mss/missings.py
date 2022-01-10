import django
django.setup()
from sefaria.model import *

for ind in library.get_indexes_in_category('Yerushalmi'):
    for ref in Ref(ind).all_segment_refs():
        mss = ['leiden-manuscript', 'jerusalem-talmud-bomberg-(venice)-pressing-(1523-ce)']
        if 'Shekalim' in ind:
            mss.append('munich-manuscript-95-(1342-ce)')
        for ms in mss:
            if not ManuscriptPageSet({'$and': [{'expanded_refs': ref.normal()}, {'manuscript_slug': ms}]}):
                print(f'no {ms} page for {ref.normal()}')
