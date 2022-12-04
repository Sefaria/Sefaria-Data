import django
django.setup()
from sefaria.model import *
from move_draft_text import ServerTextCopier

APIKEY = ''
for ind in IndexSet({'title': {'$regex': '^Ohr LaYesharim on'}}):
    title = ind.title
    if not any(w in title for w in ['Rosh Hashanah']):
        continue
    print(title)
    stc = ServerTextCopier('https://www.sefaria.org', APIKEY, title)
    stc.do_copy()
    stc = ServerTextCopier('https://www.sefaria.org', APIKEY, title, False, 'all')
    stc.do_copy()
    stc = ServerTextCopier('https://www.sefaria.org', APIKEY, title, False, post_links=2)
    stc.do_copy()

