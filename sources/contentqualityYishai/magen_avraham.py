import django
django.setup()
from sefaria.model import *

def check(ind):
    for ref in Ref(ind).all_segment_refs():
        links = [l for l in ref.linkset() if l.generated_by in ['magen_avraham_shulchan_aruch_linker', 'Vilna Link Fixer', 'Shulchan Arukh Parser']]
        if len(links) != 1:
            print(f'{ref} has {len(links)} links to sa')
            continue
        link = links[0]
        try:
            if ref.normal().split(':')[-1] != str(link.inline_reference['data-order']):
                print(f'{ref} has data order {link.inline_reference["data-order"]}')
        except AttributeError:
            print(f'attribue error in {ref}')

ind = "Be'er HaGolah on Shulchan Arukh, Orach Chayim"
check(ind)

