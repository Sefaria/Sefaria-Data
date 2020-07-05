# encoding=utf-8

import csv
import json
import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db
from sefaria.sheets import Sheet


def get_unique_topics(sheet_map: dict) -> set:
    unique_topics = set()
    for topic_list in sheet_map.values():
        for t in topic_list:
            unique_topics.add(t)

    return unique_topics


def topics_to_add(topic_set: set) -> list:
    def topic_exists(t):
        topic_obj = Topic().load({'titles.text': t})
        return bool(topic_obj)
    return [to for to in topic_set if not topic_exists(to)]


with open('addTags.json') as fp:
    tag_dict = json.load(fp)

unique_tops = get_unique_topics(tag_dict)
print(len(unique_tops), *unique_tops, sep='\n')
to_add = topics_to_add(unique_tops)
print('\n\n\ntopics to add:\n', *sorted(to_add), len(to_add), sep='\n')
# with open('TopicVariations.csv', 'w') as fp:
#     writer = csv.DictWriter(fp, fieldnames=['original', 'normalized'])
#     writer.writeheader()
#     writer.writerows([{'original': original_topic, 'normalized': ''} for original_topic in to_add])
for top in to_add:
    top_obj = Topic({'slug': top, 'titles': [{'text': top, 'lang': 'he', 'primary': True}]})
    top_obj.save()

topic_collection = db.topics

missing_topics = set()

for sheet_id, topic_list in tag_dict.items():
    sheet_id = int(sheet_id)
    sheet_obj = Sheet().load({'id': sheet_id})
    if not sheet_obj:
        continue
    if not getattr(sheet_obj, 'topics'):
        sheet_obj.topics = []
    sheet_topics = set(st['slug'] for st in sheet_obj.topics)
    for topic_string in topic_list:
        topic_dict = topic_collection.find_one({'titles.text': topic_string}, sort=[('numSources', -1)])
        if not topic_dict:
            missing_topics.add(topic_string)
            continue

        topic_obj = Topic().load_from_dict(topic_dict, True)
        if topic_obj.slug in sheet_topics:
            continue
        sheet_obj.topics.append({'asTyped': topic_string, 'slug': topic_obj.slug})
    print(f'updating sheet {sheet_id}')
    sheet_obj.save()

print('missing topics:', *sorted(missing_topics), sep='\n')
