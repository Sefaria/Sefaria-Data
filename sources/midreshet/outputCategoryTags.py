# encoding=utf-8

import json
import pymongo
from collections import defaultdict
from sources.midreshet.extract_midreshet_sheets import MidreshetCursor


def build_category_map() -> dict:
    def build_row_dict(row):
        return {
            'parent_id': row.parent_id,
            'name': row.name.rstrip().lstrip(),
        }
    cursor = MidreshetCursor()
    cursor.execute('SELECT * FROM Category')
    return {r.id: build_row_dict(r) for r in cursor}


def get_category(category_id, category_mapping, accumulator: list = None):
    if not accumulator:
        accumulator = []
    else:
        assert isinstance(accumulator, list)
    cat = category_mapping.get(category_id, None)
    if not cat:
        return accumulator
    accumulator.append(cat['name'])
    parent_id = cat['parent_id']
    if parent_id in category_mapping:
        get_category(parent_id, category_mapping, accumulator)

    return accumulator


result, missing = defaultdict(list), set()
mapping = build_category_map()
m_cursor = MidreshetCursor()
mongo_client = pymongo.MongoClient()
m_cursor.execute('SELECT * FROM PagesCategory')
for p in m_cursor:
    sefaria_page_map = mongo_client.yonis_data.server_map.find_one({
        'pageId': p.page_id, 'server': 'https://www.sefaria.org'
    })
    if sefaria_page_map:
        category_id = p.category_id
        result[sefaria_page_map['serverIndex']].extend(get_category(category_id, mapping))
    else:
        missing.add(p.page_id)

with open('addTags.json', 'w') as fp:
    json.dump(result, fp)

m_cursor.execute('SELECT id FROM Pages')
valid_ids = set([i.id for i in m_cursor])
true_missing = [i for i in missing if i in valid_ids]

with open('missingPages.json', 'w') as fp:
    json.dump(true_missing, fp)

print(f'Missing pages: {len(true_missing)}, resolved pages: {len(result)}')

