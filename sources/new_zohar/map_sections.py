import django
django.setup()
from sefaria.model import *
from sefaria.utils.talmud import section_to_daf, daf_to_section
import json

def get_node_titles(node):
    if node.children:
        return [title for child in node.children for title in get_node_titles(child)]
    else:
        return [node]

OPTIONS = {}
def get_nodes(volume):
    global OPTIONS
    volume = int(volume)-1
    try:
        return OPTIONS[volume]
    except KeyError:
        alt_node = library.get_index('Zohar').get_alt_structure('Daf').children[volume]
        OPTIONS[volume] = get_node_titles(alt_node)
        return OPTIONS[volume]

def get_page(node, page):
    if daf_to_section(node.startingAddress) <= daf_to_section(page) < daf_to_section(node.startingAddress) + len(node.refs):
        return node.refs[daf_to_section(page)-daf_to_section(node.startingAddress)]
    else:
        pass

def get_first_segment_in_page(volume, page):
    nodes =  get_nodes(volume)
    for node in nodes:
        ref = get_page(node, page)
        if ref:
            return Ref(ref).all_segment_refs()[0].normal()


if __name__ == '__main__':
    d = {}
    for vol, num in zip(range(1, 4), [534, 556, 618]):
        for n in range(num):
            new = get_first_segment_in_page(vol, section_to_daf(n+1))
            old = f'Zohar {vol}:{section_to_daf(n+1)}'
            d[old] = new

    with open('section_mapping.json', 'w') as fp:
        json.dump(d, fp)
