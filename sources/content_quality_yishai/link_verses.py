import django
django.setup()
from sefaria.model import *
import csv

def link_verses(index_name, save=False):
    index = library.get_index(index_name)
    links = []
    for ref in index.all_segment_refs():
        ref = ref.normal()
        b_ref = ':'.join(ref.split(' on ')[-1].split(':')[:-1])
        links.append({'refs': [ref, b_ref],
                     'type': 'commentary',
                     'auto': True,
                     'generated_by': f'{index_name} linker'})
    if save:
        for link in links:
            link = Link(link)
            link.save()
    return links

if __name__ == '__main__':
    index = 'Siftei Chakhamim on Song of Songs'
    links = link_verses(index, True)
    with open('map.csv', encoding='utf-8', newline='') as fp:
        for row in csv.DictReader(fp):
            link = Link({'refs': [f'{index} {row["Siftei "]}', f'Rashi on Song of Songs {row["Rashi"]}'],
                     'type': 'commentary',
                     'auto': True,
                     'generated_by': f'{index} linker'})
            link.save()
