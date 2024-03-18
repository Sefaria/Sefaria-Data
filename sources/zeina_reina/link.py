import re
import django
django.setup()
from sefaria.model import *
from sources.functions import post_link

title = "Ze'enah uRe'enah"
index = library.get_index(title)
refs = []
starting_ref = None
for n, node in enumerate(index.nodes.children[:54] + index.nodes.children[54].children + index.nodes.children[55].children):
    parasha = node.get_primary_title()
    if n > 58:
        if parasha == 'Vayeilech':
            continue
        parasha = f'Haftarot, {parasha}'
        for segment in  Ref(f'{title}, {parasha}').all_segment_refs()[:2]:
            whole_ref = re.findall('^ *(?:<b>)? *\[(.*?)\] *(?:</b>)? *$', segment.text('en').text)
            if whole_ref:
                break
        book = Ref(whole_ref[0].split(',')[0]).index.title
    else:
        base = Ref(parasha.replace('Vayeitze', 'Vayetze').replace('Megillat ', ''))
        book = base.index.title
        if parasha == 'Lamentations':
            node = node.children[0]
        if n > 53:
            parasha = f'Megillot, {parasha}'
    for segment in Ref(f'{title}, {parasha}').all_segment_refs():
        s = segment.sections[-1] - 1
        text = segment.text('en').text
        perek_pasuk = re.findall(r'^ *“<i>.*?</i>” *\[(\d+:\d+)\]', text)
        if perek_pasuk or s == 0:
            if starting_ref:
                prev_ref = Ref(f'{starting_ref}-{potential_end}').normal()
                refs.append([base_ref, prev_ref])
            if s == 0 and not perek_pasuk:
                starting_ref = None
                continue
            base_ref = f'{book} {perek_pasuk[0]}'
            starting_ref = segment.normal()
        potential_end = segment.sections[-1]
prev_ref = Ref(f'{starting_ref}-{potential_end}').normal()
refs.append([base_ref, prev_ref])

links = [{
    'refs': r,
    'auto': True,
    'type': 'commentary',
    'generated_by': 'zeino_reino_linker'
} for r in refs]
post_link(links, server='http://localhost:8000', skip_lang_check=False)
