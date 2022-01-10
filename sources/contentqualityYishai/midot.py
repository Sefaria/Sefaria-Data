import django
django.setup()
from sefaria.model import *
from sefaria.helper.schema import change_node_title, reorder_children
import csv
import json
import requests
import codecs
from sefaria.settings import USE_VARNISH, MULTISERVER_ENABLED
from sefaria.system.multiserver.coordinator import server_coordinator
import time
if USE_VARNISH:
    from sefaria.system.varnish.wrapper import invalidate_title

API_KEY = ""
server = ''

def http_request(url, params=None, body=None, json_payload=None, method="GET"):
    if params is None:
        params = {}
    if body is None:
        body = {}
    if json_payload:
        body['json'] = json.dumps(json_payload)  # Adds the json as a url parameter - otherwise json gets lost

    if method == "GET":
        response = requests.get(url)
    elif method == "POST":
        response = requests.post(url, params=params, data=body)
    elif method == "DELETE":
        response = requests.delete(url, params=params, data=body)
    else:
        raise ValueError("Cannot handle HTTP request method {}".format(method))

    success = True
    try:
        json_response = response.json()
        if isinstance(json_response, dict) and json_response.get("error"):
            success = False
            print("Error: {}".format(json_response["error"]))
    except ValueError:
        success = False
        json_response = ''
        with codecs.open('errors.html', 'w', 'utf-8') as outfile:
            outfile.write(response.text)

    if success:
        print("\033[92m{} request to {} successful\033[0m".format(method, url))
        return json_response
    else:
        print("\033[91m{} request to {} failed\033[0m".format(method, url))
        return response.text

def post_index(index, server, method="POST"):
    url = server+'/api/v2/raw/index/' + index["title"].replace(" ", "_")
    return http_request(url, body={'apikey': API_KEY}, json_payload=index, method=method)

ind = 'Sefer HaMiddot'
i = post_index({'title': ind}, 'https://sefaria.org', 'GET')
i['schema']['nodes'][75]['titles'] = [{'lang': 'en', 'text': 'Book', 'primary': True},
  {'lang': 'he', 'text': 'ספר', 'primary': True}]
i['schema']['nodes'][75].pop('sharedTitle')
post_index(i, server)

oref = Ref(ind)
library.refresh_index_record_in_cache(oref.index)
library.reset_text_titles_cache()
vs = VersionState(index=oref.index)
vs.refresh()
library.update_index_in_toc(oref.index)

if MULTISERVER_ENABLED:
    server_coordinator.publish_event("library", "refresh_index_record_in_cache", [oref.index.title])
    server_coordinator.publish_event("library", "update_index_in_toc", [oref.index.title])
elif USE_VARNISH:
    invalidate_title(oref.index.title)

change_node_title(Ref(f'{ind}, Book ').index_node, 'Book', 'en', 'A Holy Book')
p_node = library.get_index(ind).nodes
data = list(csv.DictReader(open('Sefer_HaMiddot_Alignment__-_New.csv', encoding='utf-8', newline='')))
new_order = ['Introduction', 'Second Introduction'] + [row['English Old'] for row in data]
reorder_children(p_node, new_order)
data.pop(71)
for row in data:
    old = row['English Old']
    node = Ref(f'{ind}, {old}').index_node
    new = row['English New']
    if old == 'Book':
        delattr(node, 'sharedTitle')
    if old != new:
        print(f'changing {old} to {new}')
        change_node_title(node, old, 'en', new)
    if row['Hebrew'] == 'פדיון':
        print('changing פדיון to פדיון שבויים')
        change_node_title(node, 'פדיון', 'he', 'פדיון שבויים')
    time.sleep(10)
