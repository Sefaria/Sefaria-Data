import csv
import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db
from sefaria.helper.topic import recalculate_secondary_topic_data
from pymongo import UpdateOne

print('iterating links')

link_ids_to_del = []
link_ids_to_update = []
with open('topic links final.csv') as fp:
    good_ref_links = {(row['slug'], row['ref']) for row in csv.DictReader(fp)}
for link in db.topic_links.find({"generatedBy" : "sheet-topic-aggregator", 'class': 'refTopic'}):
    if (link['toTopic'], link['ref']) not in good_ref_links:
        link_ids_to_del.append(link['_id'])
    else:
        link_ids_to_update.append(link['_id'])
with open('topic intralinks final.csv') as fp:
    good_ref_links = {(row['toTopic'], row['fromTopic']) for row in csv.DictReader(fp)}
for link in db.topic_links.find({"generatedBy" : "sheet-topic-aggregator", 'class': 'intraTopic'}):
    if (link['toTopic'], link['fromTopic']) not in good_ref_links:
        link_ids_to_del.append(link['_id'])
    else:
        link_ids_to_update.append(link['_id'])

print('deleting links')
db.topic_links.delete_many({'_id': {'$in': link_ids_to_del}})

print('updating links')
db.topic_links.bulk_write([
    UpdateOne({"_id": l['_id']}, {"$set": {"generatedBy": 'from-sheets-by-GPT'}})
    for l in link_ids_to_update
])

print('updating topics')
for topic in TopicSet():  #TODO do it with pymongo directly?
    topic.update_after_link_change('sheets')
    topic.update_after_link_change('textual')
    if not topic.pools:
        print(f'topic without links to meither sources nor sheets, slug: {topic.slug}')
    if hasattr(topic, 'good_to_promote'):
        topic.pools.append('torahtab')
        delattr(topic, 'good_to_promote')
        topic.save()
