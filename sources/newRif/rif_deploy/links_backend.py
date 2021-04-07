import django
django.setup()
from sefaria.model import *
import json
from sefaria import tracker
from sefaria.system.exceptions import DuplicateRecordError
from sefaria.local_settings import USE_VARNISH
from sefaria.system.varnish.wrapper import invalidate_ref

with open('rif_links.json') as fp:
    links = json.load(fp)

def revarnish_link(link_obj):
    if USE_VARNISH:
        for ref in link_obj.refs:
            invalidate_ref(Ref(ref), purge=True)

def create_link_saver(uid):
    def save_link(link_dict):
        try:
            link_obj = tracker.add(uid, Link, link_dict)
            success = True
        except DuplicateRecordError as e:
            success = False
            print(e)
        if USE_VARNISH and success:
            try:
                revarnish_link(link_obj)
            except Exception as e:
                print(e)
    return save_link

uid = 1000
link_saver = create_link_saver(uid)
for i, l in enumerate(links, 1):
    print(f'{i}/{len(links)}')
    link_saver(l)