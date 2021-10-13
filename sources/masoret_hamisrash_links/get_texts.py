import django
django.setup()
from sefaria.model import *
import requests
from sources.functions import post_index, post_text, add_category, add_term

server = 'http://localhost:9000'
mv = 'Midrash_Rabbah,_Vilna,_1878'
mm = 'Masoret HaMidrash'
add_term(mm, 'מסורת המדרש', server=server)
add_category(mm, ['Midrash', 'Aggadic Midrash', 'Midrash Rabbah', 'Commentary', mm], server=server)

def post(index):
    text = requests.request('get', f'https://ezradev.cauldron.sefaria.org/api/texts/{index}?vhe={mv}&lang=he&pad=0')
    text = text.json()['he']
    text_dict = {'text': text, 'language': 'he', 'versionTitle': mv.replace('_', ' '), 'versionSource': ''}
    post_text(index, text_dict, server=server, index_count='on')
    index = index.replace('Bereishit', 'Bereshit')
    ind = requests.request('get', f'https://ezradev.cauldron.sefaria.org/api/v2/raw/index/{mm.replace(" ", "_")} on {index}').json()
    post_index(ind, server=server)
    text = requests.request('get', f'https://ezradev.cauldron.sefaria.org/api/texts/{mm.replace(" ", "_")} on {index}?vhe={mv}&lang=he&pad=0').json()['he']
    text_dict = {'text': text, 'language': 'he', 'versionTitle': mv.replace('_', ' '), 'versionSource': 'boo'}
    post_text(f'{mm.replace(" ", "_")} on {index}', text_dict, server=server, index_count='on')

for index in library.get_indexes_in_category('Midrash Rabbah'):
    node = library.get_index(index).nodes
    if isinstance(node, JaggedArrayNode):
        post(index)
    else:
        for child in node.children:
            post(f'{child}')
