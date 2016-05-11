# # -*- coding: utf-8 -*-

from sefaria.model import *
from sources import functions

months = [u'Nisan', u'Iyar', u'Sivan', u'Tammuz', u'Av', u'Elul', u'Tishrei',
          u'Cheshvan', u'Kislev', u'Tevet', u'Shevat', u'Adar']

he_months = [u'ניסן', u'אייר', u'סיוון', u'תמוז', u'אב', u'אלול', u'תשרי', u'חשון', u'כסלו', u'טבת', u'שבט', u'אדר' ]

# create index record
record = SchemaNode()
record.add_title('Megillat Taanit', 'en', primary=True,)
record.add_title(u'מגילת תענית', 'he', primary=True)
record.key = 'Megillat Taanit'

for index, month in enumerate(months):
    node = JaggedArrayNode()
    node.add_title(month, 'en', primary=True)
    node.add_title(he_months[index], 'he', primary=True)
    node.key = month
    node.depth = 1
    node.addressTypes = ['Integer']
    node.sectionNames = ['Verse']
    record.append(node)
record.validate()

index = {
        "title": "Megillat Taanit",
        "categories": ["Apocrypha", "Megillat Taanit"],
        "schema": record.serialize()
}
functions.post_index(index)

for month in months:
    book = {
        "versionTitle": "Fix me!",
        "versionSource": "Fix me!",
        "language": "he",
        "text": ['']
    }
    print month
    functions.post_text('Megillat Taanit, {}'.format(month), book)
