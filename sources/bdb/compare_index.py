import pymongo
import django
django.setup()
from sefaria.model import *
from sources.functions import post_index, post_text
from sefaria.model.lexicon import BDBEntry

server = 'http://localhost:9000'
# server = 'https://bdb.cauldron.sefaria.org'

record = JaggedArrayNode()
record.add_primary_titles('Comp', 'השוואה')
record.addressTypes = ['Integer']
record.sectionNames = ['Paragraph']
record.depth = 1
record.validate()
index_dict = {
              "title": 'Comp',
              "categories": ['Reference', 'Dictionary'],
              "schema": record.serialize()}
post_index(index_dict, server=server)

new = []
les = LexiconEntrySet({'rid': {'$regex': 'H00[01]\d\d'}, 'parent_lexicon': 'BDB Dictionary'})
for le in les:
    new.append(' '.join(le.as_strings()))
text_version = {
        'versionTitle': 'new',
        'versionSource': '',
        'language': 'en',
        'text': new}
post_text('Comp', text_version, server=server, index_count='on')

old = []
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
db = myclient['sefaria']
col = db['bdbtemp']
les = col.find({'rid': {'$regex': 'A00[01]\d\d'}})
for le in les:
    old.append(' '.join(BDBEntry(le).as_strings()))
text_version = {
        'versionTitle': 'old',
        'versionSource': '',
        'language': 'en',
        'text': old}
post_text('Comp', text_version, server=server, index_count='on')

