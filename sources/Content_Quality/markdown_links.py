import django
django.setup()
from sefaria.model import *
from bs4 import BeautifulSoup
from collections import *
import re
#{'i', 'p', 'a', 'body', 'html', 'br'}

ts = TopicSet({'description': {'$exists': True}, "properties.source": "ashlag-glossary"})
for t in ts:
    orig_desc_dict = getattr(t, 'description', {})
    new_desc = {}
    change = False
    for lang in ['en', 'he']:
        orig_desc = orig_desc_dict.get(lang, '')
        if orig_desc:
            soup = BeautifulSoup(orig_desc)
            found = soup.find_all('i')+soup.find_all('b')+soup.find_all('br')+soup.find_all('a')
            if len(found) > 0:
                for i in soup.find_all('i'):
                    i.replace_with(f"*{i.string}*")
                for i in soup.find_all('b'):
                    i.replace_with(f"**{i.string}**")
                for i in soup.find_all('br'):
                    i.replace_with(f"  ")
                for i in soup.find_all('a'): #  class=\"namedEntityLink\" href=\"/topics/sefira1\">sefirot
                    href = i.attrs['href']
                    txt = i.string
                    i.replace_with(f"[{txt}]({href})")
                new_desc[lang] = soup.text
                change = True
    if change:
        print(t)
        t.change_description(new_desc)
        #t.save()



