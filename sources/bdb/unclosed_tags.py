import re
import django
django.setup()
from sefaria.model import *
from finishings import iterate_sense

def unbalanced(le):
   text = le.as_strings().replace('<br>', '')
   return len(re.findall('<[^/][^<>]*>', text)) != len(re.findall('</[^<>]*>', text))

with open('balance.txt') as fp:
   balance = fp.read()
balance = [x.strip() for x in balance.split('\n') if x.strip()]

for le in LexiconEntrySet({'parent_lexicon': {'$regex': 'BDB.*?Dict'}}):
   if unbalanced(le):
      for sense, _ in iterate_sense(le.content):
         if re.search('<strong>[^<]*$', sense['definition']):
            sense['definition'] += '</strong>'
      if unbalanced(le):
         for sense, _ in iterate_sense(le.content):
            text = sense['definition']
            if len(re.findall('<[^/][^<>]*>', text)) != len(re.findall('</[^<>]*>', text)):
               text = balance.pop(0)
               if len(re.findall('<[^/][^<>]*>', text)) != len(re.findall('</[^<>]*>', text)):
                  print(le.headword)
                  print(text)
               sense['definition'] = text
      le.save()

if balance:
   print(1111,balance)
