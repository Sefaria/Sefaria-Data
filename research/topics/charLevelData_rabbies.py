import django, re, requests, json
django.setup()
from research.quotation_finder.dicta_api import *
import pymongo
from sefaria.settings import *
import cProfile
from functools import reduce
from sefaria.tracker import modify_bulk_text
from sefaria.system.database import *


def get_rabbis(tref, vtitle):
    cursor = db.topic_links.find({"charLevelData": {"$exists": True}, "ref": tref,  "charLevelData.versionTitle": vtitle})
    chld = [l["charLevelData"]['startChar'] for l in cursor]
    return chld


if __name__ == '__main__':
    print(get_rabbis('Shabbat 8b:9'))
