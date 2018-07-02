# encoding=utf-8

import unicodecsv
from sources.functions import get_index, post_index, numToHeb
from sefaria.model.schema import ArrayMapNode, TitledTreeNode

day_root, book_root = TitledTreeNode(), TitledTreeNode()
with open('psalms_30_day_cycle.csv') as infile:
    reader = unicodecsv.DictReader(infile)
    for item in reader:
        map_node = ArrayMapNode()
        map_node.add_title('Day {}'.format(item['Day']), 'en', primary=True)
        map_node.add_title(u'יום {}'.format(numToHeb(item['Day'])), 'he', primary=True)
        map_node.depth = 0
        map_node.includeSections = True
        map_node.wholeRef = item['Ref']
        day_root.append(map_node)

with open('psalms_books.csv') as infile:
    reader = unicodecsv.DictReader(infile)
    for item in reader:
        map_node = ArrayMapNode()
        map_node.add_title('Book {}'.format(item['Book en']), 'en', primary=True)
        map_node.add_title(u'ספר {}'.format(item['Book he']), 'he', primary=True)
        map_node.depth = 0
        map_node.includeSections = True
        map_node.wholeRef = item['Ref']
        book_root.append(map_node)
p_index = get_index('Psalms')
p_index['alt_structs'] = {
    'Books': book_root.serialize(),
    '30 Day Cycle': day_root.serialize()
}
post_index(p_index)
