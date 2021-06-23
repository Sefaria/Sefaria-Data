import django
django.setup()
from sefaria.model import *
from scripts.move_draft_text import ServerTextCopier

dest = 'https://www.sefaria.org'
#dest = 'https://yishai-bugs-week.cauldron.sefaria.org'
apikey = "F3XF80E9J46VMrT95bwASLRPYkhmLT1GYrr34fGC2kw"

for index in library.get_indexes_in_category('Piskei Tosafot', include_dependant=True):
    if all(x not in index for x in ['Ketubot', 'Megillah', 'Nedarim', 'Nidah', 'Sotah', 'Taanit']):
        continue
    print(index)
    s = ServerTextCopier(dest, apikey, index)
    s.do_copy()
    print('text')
    s = ServerTextCopier(dest, apikey, index, False, 'all')
    s.do_copy()
    print('links')
    s = ServerTextCopier(dest, apikey, index, False, None, 2)
    s.do_copy()
