import pymongo
import django
django.setup()
from sefaria.model import *

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = myclient['prodigy']
col = db['input']
for le in LexiconEntrySet({'parent_lexicon': {'$regex': 'BDB.*?Dictionary'}}):
    meta = {'lexicon': le.parent_lexicon, 'rid': str(int(le.rid.replace('A', ''))), 'headword': le.headword}
    if not col.find_one({'meta': meta}):
        col.insert_one({'meta': meta, 'spans': [], 'text': le.content['senses'][0]['definition']})

