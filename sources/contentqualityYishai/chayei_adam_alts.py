import django
django.setup()
from sefaria.model import *
from sources.functions import get_index_api, post_index
import copy

SERVER = 'https://www.sefaria.org'
#SERVER = 'https://yishai-bugs-week.cauldron.sefaria.org'

index = get_index_api('Chayei Adam', server=SERVER)
'''new = ArrayMapNode()
new.depth = 0
new.wholeRef = 'Chayei Adam, Shabbat and Festivals.138-142'
new.add_primary_titles('Laws of Rosh HaShanah', 'הלכות ראש השנה')
'''
alts = index['alt_structs']['Topic']['nodes']
alts[9]['wholeRef'] = 'Chayei Adam, Shabbat and Festivals.133-137'
new = copy.deepcopy(alts[9])
new['wholeRef'] = 'Chayei Adam, Shabbat and Festivals.138-142'
new['titles'][0]['text'] = 'Laws of Rosh HaShanah'
new['titles'][1]['text'] = 'הלכות ראש השנה'
alts.insert(10, new)
post_index(index, server=SERVER)
