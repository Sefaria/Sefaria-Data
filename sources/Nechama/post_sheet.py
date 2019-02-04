# -*- coding: utf-8 -*-
"""
Post a sheet form the local enviornment to a remote enviornment, using an API Key.
"""
import django
django.setup()

import sys
import json
import urllib
import urllib2

from sefaria.system.database import db
from sefaria.sheets import get_sheet
from sources.functions import post_sheet
from sources.local_settings import *


def change_sheet(id, del_tags=[], add_tags=[]):
    this_sheet = get_sheet(id)
    # deal with tags
    for tag in this_sheet[u'tags']:
        if tag.isdigit():
            # todo: deal with the pdf link
            this_sheet['summary'] = this_sheet['summary'] + u" http://www.nechama.org.il/pdf/{}.pdf".format(tag)
            this_sheet[u'tags'].remove(tag)
        if (tag in del_tags):
            this_sheet[u'tags'].remove(tag)
    this_sheet[u'tags'].extend(add_tags)
    # deal with owner todo: make this work also throw the api post
    this_sheet["owner"] = 51461
    return this_sheet


sheets = db.sheets.find({"tags": "Bilingual"})
for sheet in sheets:
    got = change_sheet(sheet[u'id'], add_tags=['test'])
    del got['_id']
    del got['id']
    post_sheet(got, server=SEFARIA_SERVER)
pass