import django
django.setup()
from sefaria.model import *
from scripts.move_draft_text import ServerTextCopier

server = 'https://www.sefaria.org'
remain = ['Gilyon HaShas on Bava Batra',
 'Gilyon HaShas on Beitzah',
 'Gilyon HaShas on Chagigah',
 'Gilyon HaShas on Menachot',
 'Gilyon HaShas on Sukkah',
 'Gilyon HaShas on Pesachim',
 'Gilyon HaShas on Shevuot',
 'Gilyon HaShas on Temurah',
 'Gilyon HaShas on Taanit']
for title in remain: #library.get_indexes_in_category('Gilyon HaShas', include_dependant=True):
    print(title)
    copier = ServerTextCopier(server, apikey, title, True, None, False)
    copier.do_copy()
    print(title, 'text')
    copier = ServerTextCopier(server, apikey, title, False, 'all', False)
    copier.do_copy()
    print(title, 'links')
    copier = ServerTextCopier(server, apikey, title, False, None, 2)
    copier.do_copy()
