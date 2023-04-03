import django

django.setup()

django.setup()
superuser_id = 171118
# import statistics
from sefaria.model import *
#


def ingest_term(en_title, he_title):
    new_term = Term()
    new_term.name = en_title
    new_term.scheme = 'commentary_works'
    new_term.set_titles([{'lang': 'en', 'text': en_title, 'primary': True}, {'lang': 'he', 'text': he_title, 'primary': True}])
    new_term.save()
    # post_index(index, server="https://guide-commentaries.cauldron.sefaria.org")

if __name__ == '__main__':
    print("hello world")


    ingest_term("Crescas", "קרשקש")
    ingest_term("Efodi", "אפודי")
    ingest_term("Narboni", "נרבוני")
    ingest_term("Shem Tov", "שם טוב")








