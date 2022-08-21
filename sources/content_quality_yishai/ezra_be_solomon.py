import django
django.setup()
from sefaria.model import *
import urllib
import json
import requests
import codecs

API_KEY = ""

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

def post_term(term_dict, server, update=False):
    name = term_dict['name']
    # term_JSON = json.dumps(term_dict)
    url = '{}/api/terms/{}'.format(server, urllib.parse.quote(name))
    if update:
        url += "?update=1"
    return http_request(url, body={'apikey': API_KEY}, json_payload=term_dict, method="POST")

def add_term(en_title, he_title, server, scheme='toc_categories'):
    term_dict = {
    'name': en_title,
    'scheme': scheme,
    'titles': [{'lang': 'en', 'text': en_title, 'primary': True}, {'lang': 'he', 'text': he_title, 'primary': True}]
    }
    res = post_term(term_dict, server)

add_term('Ezra ben Solomon', 'עזרא בן שלמה', 'https://pele.cauldron.sefaria.org')
ind = library.get_index('Ezra ben Solomon on Song of Songs')
ind.dependence = 'Commentary'
ind.collective_title = 'Ezra ben Solomon'
ind.save()
for ref in Ref('Ezra ben Solomon on Song of Songs').all_segment_refs():
    ref = ref.normal()
    link = Link({'refs': [ref, ':'.join(ref.replace('Ezra ben Solomon on ', '').split(':')[:-1])],
            'type': 'commentary',
            'auto': True,
            'generated_by': 'ezra ben solomon linker'})
    link._set_expanded_refs()
    link._set_available_langs()
    link.save()
