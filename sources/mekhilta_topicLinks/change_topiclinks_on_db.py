import django
django.setup()
from sefaria.model import *
from sefaria.system.database import db
import csv

col = db.topic_linkks
with open('topic_links_changes.csv') as fp:
    links = list(csv.DictReader(fp))

for row in links:
    tl = RefTopicLink().load({'toTopic': row['topic slug'], 'dataSource': row['data source'],
                              'ref': row['ref'].replace('Yishmael', 'Yishmael Old')})
    if not tl:
        print('canoot find topic_link',{'fromTopic': row['topic slug'], 'dataSource': row['data source'],
                              'ref': row['ref'].replace('Yishmael', 'Yishmael Old')})
        continue
    if not row['refined']:
        tl.delete()
        pass
    else:
        new_ref = f"{row['new ref'].split('-')[0].split(':')[0]}:{row['refined']}".replace(' Beeri', '')
        try:
            new_ref = Ref(new_ref)
        except:
            print('new ref is not valid', new_ref)
        else:
            tl.ref = new_ref.normal()
            tl.save()

links = RefTopicLinkSet({'ref': {'$regex': '^Mekhilta DeRabbi Yishmael Old'}})
if links:
    for link in links:
        print(link._id)
