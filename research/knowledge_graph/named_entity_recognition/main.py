import django, csv
from tqdm import tqdm
django.setup()
from sefaria.model import *

mike_id = ' Rabbi ID after Link'
gen = ' Rabbi Generation after Link'
typ = ' Rabbi Type after Link'
nam = ' Rabbi Name after Link'
josh_id = 'bonayich'

DATA_LOC = "/home/nss/sefaria/datasets/ner/michael-sperling"

with open(f'{DATA_LOC}/AllNameReferences.csv', 'r') as fin:
    mike = list(csv.DictReader(fin))

with open('/home/nss/sefaria/data/research/knowledge_graph/named_entity_recognition/sefaria_bonayich_reconciliation - Sheet1.csv', 'r') as fin:
    josh = list(csv.DictReader(fin))
    josh_id_set = {j[josh_id] for j in josh}

missin_mike = {}
for m in mike:
    if m[mike_id] not in josh_id_set:
        missin_mike[m[mike_id]] = {
            'gen': m[gen],
            'typ': m[typ],
            'nam': m[nam]
        }

prev_rabbi_set = {}
ton_o_rabanan = []
for j in tqdm(josh):
    ts = TopicSet({'titles.text': j['sefaria_key']})
    if ts.count() == 1:
        j['Slug'] =  list(ts)[0].slug
with open('sefaria_bonayich_reconciliation - Sheet2.csv', 'w') as fout:
    c = csv.DictWriter(fout, josh[0].keys())
    c.writeheader()
    c.writerows(josh)
itls = IntraTopicLinkSet({'linkType': 'is-a', 'toTopic': 'talmudic-people'})
for l in tqdm(itls, total=itls.count()):
    if l.fromTopic in prev_rabbi_set:
        continue
    t = Topic.init(l.fromTopic)
    if len(t.titles) <= 2 and not getattr(t, 'properties', False):
        ton_o_rabanan += [t]
itls = IntraTopicLinkSet({'linkType': 'is-a', 'toTopic': 'mishnaic-people'})
for l in tqdm(itls, total=itls.count()):
    if l.fromTopic in prev_rabbi_set:
        continue
    t = Topic.init(l.fromTopic)
    if len(t.titles) <= 2 and not getattr(t, 'properties', False):
        ton_o_rabanan += [t]

with open('new rabbis.csv', 'w') as fout:
    c = csv.DictWriter(fout, ['Slug', 'En', 'He'])
    c.writeheader()
    for t in ton_o_rabanan:
        c.writerow({
            'Slug': t.slug,
            'En': t.get_primary_title('en'),
            'He': t.get_primary_title('he')
        })

with open('missing rabbis.csv', 'w') as fout:
    c = csv.DictWriter(fout, ['ID', 'Gen', 'Type', 'He'])
    c.writeheader()
    for i, m in missin_mike.items():
        c.writerow({
            'ID': i,
            'Gen': m['gen'],
            'Type': m['typ'],
            'He': m['nam']
        })





