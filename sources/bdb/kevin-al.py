import json
import re
import django
django.setup()
from sefaria.model import *
from sefaria.utils.hebrew import strip_nikkud
import diff_match_patch as dmp_module

with open('bdb.json') as fp:
    al = json.load(fp)

# sa = LexiconEntrySet({'parent_lexicon': 'BDB Augmented Strong'})
# words = [x.headword for x in sa]
# striped_words = [strip_nikkud(x) for x in words]
words = [x['keyword'] for x in al if x['keyword']]
striped_words = [strip_nikkud(x) for x in words]

for le in LexiconEntrySet({'parent_lexicon': 'BDB Dictionary'}):
    if le.content['senses'][0].strip().startswith('v. '):
        continue
    hw = le.headword
    if len(hw) == 1:
        continue
    found = [x for x in words if x==hw]
    if len(found) == 0:
        shw = strip_nikkud(hw)
        if len(hw) == len(shw) == 3:
            continue
        found = [x for x in words if strip_nikkud(x) == shw]
    if len(found) != 1:
        continue
        print(hw, len(found))


    al_word = [x for x in al if x['keyword'] == found[0]]
    try:
        al_text = al_word[0]['BDB']
    except:
        continue
        # print(al_text)
    if len(al_text) != 1:
        continue
        # print(al_word[0]['keyword'], al_text)
    al_text = al_text[list(al_text.keys())[0]]
    al_text = re.sub('<[^>]*>', '', al_text)
    k_text = le.headword + ' '.join(le.content['senses'])
    k_text = re.sub('<[^>]*>', '', k_text)
    dmp = dmp_module.diff_match_patch()
    diff = dmp.diff_main(k_text, al_text)
    dmp.diff_cleanupSemantic(diff)
    print(diff)
    try:
        boo
        break
    except:
        boo = True
