import os
from tqdm import tqdm
import time
import django
django.setup()
from sefaria.model import *
import json
from sefaria import tracker
from sefaria.system.exceptions import DuplicateRecordError
from sefaria.local_settings import USE_VARNISH
from sefaria.system.varnish.wrapper import invalidate_ref
from multiprocessing import Pool

USER_ID = int(os.environ['USER_ID'])

with open('rif_links.json') as fp:
    links = json.load(fp)

def revarnish_link(link_obj):
    if USE_VARNISH:
        for ref in link_obj.refs:
            invalidate_ref(Ref(ref), purge=True)


def save_link(link_dict):
    try:
        link_obj = tracker.add(USER_ID, Link, link_dict)
        success = True
    except DuplicateRecordError as e:
        success = False
        print(e)
    if USE_VARNISH and success:
        try:
            revarnish_link(link_obj)
        except Exception as e:
            print(e)


for i, l in enumerate(links, 1):
    print(f'{i}/{len(links)}')
    start = time.time()
    save_link(l)
    end = time.time()
    print(end-start, 'elapsed')