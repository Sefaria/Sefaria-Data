import django
django.setup()
import json
import re
from linking_utilities.dibur_hamatchil_matcher import match_ref
from rif_utils import tags_map, path, remove_metadata
from sefaria.model import *
from mefaresh_parse import split_dh, find_dh
from functools import partial

def base_tokenizer(string, masechet):
    string = remove_metadata(string, masechet)
    string = re.sub(r'<sup>.*?<\/i>', '', string)
    string = re.sub('<[^>]*>|\([^)]*\)', '', string)
    return string.split()

def add_gemara_links(links):
    new = []
    for item in links:
        for link in Ref(item['refs'][1]).linkset():
            if link.generated_by == 'rif gemara matcher':
                g_text = Ref(link.refs[0]).text('he')
                m_text = Ref(item['refs'][0]).text('he')
                g_matches = match_ref(g_text, m_text, partial(base_tokenizer, masechet=masechet), dh_extract_method=find_dh, char_threshold=0.24, dh_split=split_dh)["matches"]
                for g_match in g_matches:
                    if g_match != None:
                        new.append({
                        "refs": [item['refs'][0], g_match.tref],
                        "type": "Commentary",
                        "auto": True,
                        "generated_by": 'rif mefaresh matcher'
                        })
    return links + new

for masechet in tags_map:
    print(masechet)
    with open(path+'/Mefaresh/json/{}_links.json'.format(masechet)) as fp:
        data = json.load(fp)
    links = add_gemara_links(data)
    with open(path+'/Mefaresh/json/{}_links.json'.format(masechet), 'w') as fp:
        json.dump(links, fp)
