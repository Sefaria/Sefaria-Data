import django
django.setup()
from sefaria.model import *
from scripts.move_draft_text import ServerTextCopier
import requests
import json

#DEST = 'https://www.sefaria.org'
DEST = 'https://rif-deploy.cauldron.sefaria.org'
APIKEY = 'tqtFa8WngaNO1Gx8MVOU1YRQm03oEPoLvzS0IxX4IGo'

def deploy_index(index):
    copier = ServerTextCopier(DEST, APIKEY, index, post_index=True)
    copier.do_copy()

def deploy_text(index):
    copier = ServerTextCopier(DEST, APIKEY, index, post_index=False, versions='all')
    copier.do_copy()

if __name__ == '__main__':
    '''indexes = set(library.get_indexes_in_category('Rif', include_dependant=True))
    done = set(library.get_indexes_in_category('Bavli'))
    while indexes - done:
        for index in indexes - done:
            bases = getattr(library.get_index(index), 'base_text_titles', False)
            if not bases or all(i in done for i in bases):
                print(index)
                deploy_index(index)
                done.add(index)'''

    for index in library.get_indexes_in_category('Rif', include_dependant=True)[195:]:
        deploy_text(index)