import django
django.setup()
from sefaria.model import *
from sefaria.helper.schema import cascade

def rewriter(tref):
    return tref.replace('Shivchei Haran 1', 'The Praises of Rabbi Nachman 1').replace('Shivchei Haran 2', 'The Praises of Rabbi Nachman, An Account of His Pilgrimage to the Holy Land')
cascade('Shivchei Haran', rewriter=rewriter)
