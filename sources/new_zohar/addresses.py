import re
import django
django.setup()
from sefaria.model import *
from sefaria.utils.talmud import section_to_daf, daf_to_section

def iterate_nodes(nodes):
    for node in nodes:
        if 'nodes' in node:
            yield from iterate_nodes(node['nodes'])
        else:
            yield node

def find_page(ref, startingAddress):
    while True:
        text = ref.text('he', vtitle='Sulam').text
        text = re.sub(' *\([^\)]*\) *', '', text)
        pages = re.findall(f'<i data-overlay="Vilna Pages" data-value="([^"]*)">', text)
        if pages:
            return pages[-1]
        if ref.normal().endswith(' 1:1'):
            return startingAddress
        ref = ref.prev_segment_ref()

def change_node(node):
    addresses = []
    for ref in node['refs']:
        ref = Ref(ref).all_segment_refs()[0]
        addresses.append(find_page(ref, node['startingAddress']))
    if addresses[0] != node['startingAddress']:
        print(f"first ref is {node['startingAddress']}, but {addresses[0]} was found")
        print(node)
        addresses[0] = node['startingAddress']
    all_dafs = [section_to_daf(sec) for sec in range(daf_to_section(addresses[0]), daf_to_section(addresses[-1])+1)]
    diff = 2 * len(addresses) - len(all_dafs)
    if diff < 0:
        node['addresses'] = [daf_to_section(a) for a in addresses]
    elif diff > 0:
        skipped_addresses = [ad for ad in all_dafs if ad not in addresses]
        if skipped_addresses:
            node['skipped_addresses'] = [daf_to_section(a) for a in skipped_addresses]

if __name__ == '__main__':
    index = library.get_index('Zohar TNNNG')
    nodes = index.alt_structs['Pages']['nodes']
    for node in iterate_nodes(nodes):
        change_node(node)
    index.alt_structs['Pages']['nodes'] = nodes
    print(nodes)
