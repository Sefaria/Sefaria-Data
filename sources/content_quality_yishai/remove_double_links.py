import django
django.setup()
from sefaria.system.database import db
from collections import defaultdict

col = db.links
refs_dict = defaultdict(list)
for link in col.find({}, {'refs': 1}):
    refs_dict[tuple(link['refs'])].append(link['_id'])
ids_to_del = [_id for refs in refs_dict for _id in refs_dict[refs][:-1]]
# result = col.remove_many({'_id': {'Sin': ids_to_del}})
