import os
import time
import django
django.setup()
from sefaria.model import *
from sefaria.profiling import prof
import json
from sefaria import tracker
from sefaria.system.exceptions import DuplicateRecordError
from sefaria.local_settings import USE_VARNISH
from sefaria.system.varnish.wrapper import invalidate_ref
from multiprocessing import Pool

USER_ID = int(os.environ['USER_ID'])
print(USE_VARNISH)

with open('rif_links.json') as fp:
    links = json.load(fp)

# todo: shuffle links and then run this script on two or three pods simultaneously

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
    # if USE_VARNISH and success:
    #     try:
    #         revarnish_link(link_obj)
    #     except Exception as e:
    #         print(e)
    return success

for i, l in enumerate(links, 1):
    print(f'{i}/{len(links)}')
    start = time.time()
    s = save_link(l)
    end = time.time()
    if i % 100 == True and s:
        print(end-start, 'elapsed')