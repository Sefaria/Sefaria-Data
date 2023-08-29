from sefaria.system.database import db
import json
from bson.objectid import ObjectId

with open('found.json') as fp:
    records = json.load(fp)

for rec in records:
    col = getattr(db, rec['col'])
    query = rec['query']
    query['_id'] = ObjectId(rec['_id'])
    docs = col.find(query)
    n = col.count_documents(query)
    if n != 1:
        pass
        # print(n, col, query)
    else:
        col.update_one(query, rec['update'])
        print('update', query['_id'])
        print(rec['update'])
