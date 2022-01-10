import django
django.setup()
from sefaria.model import *
from move_draft_text import ServerTextCopier

server = 'https://www.sefaria.org'
apikey = 'F3XF80E9J46VMrT95bwASLRPYkhmLT1GYrr34fGC2kw'
for ind in library.get_indexes_in_category('Shem HaGedolim', include_dependant=True)[::-1]:
    print(ind)
    stc = ServerTextCopier(server, apikey, ind, versions='all', post_links=2, step = 400)
    stc.do_copy()
    print('index posted')
