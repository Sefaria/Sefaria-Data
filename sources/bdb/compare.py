import csv
import json
from bs4 import BeautifulSoup
from hub_al3rdphase import get_hub_text, get_al_text
import re
import django
django.setup()
from sefaria.model.lexicon import LexiconEntrySet, BDBEntry
from kevin_al import get_kev_text, get_bdbentry

def is_hebrew(word):
    return all(1424 < ord(l) < 1525 or l == ' ' for l in word)

def find_hebrew(string):
    hstrings = []
    heb = False
    for char in string:
        if 1424 < ord(char) < 1525:
            if heb == False:
                hstrings.append('')
            heb = True
        elif char not in ' –—-$[](),:׳':
            heb = False
        if heb:
            hstrings[-1] += char
    hstrings = [h.strip() for h in hstrings]
    return hstrings

X=1
def hebrew(texts):
    if 'al' in texts:
        t = re.sub('Kt \([^\)a-zA-Z]* Qr\)', '', texts['al'])
        if t != texts['al']:
            print(11111111, 'qri', texts['al'])
            texts['al'] = t
    h_words = {f'{k} words': find_hebrew(v) for k, v in texts.items()}
    h_words['hub words'] = [word for word in h_words['hub words'] if '֟'not in word]
    lens = [len(h_words[x]) for x in h_words]
    if lens[1:] != lens[:-1]:
        return h_words
        global X
        X+=1

def remove_garbage(string):
    return re.sub('\x98', '', string)

if __name__ == '__main__':
    with open('hub_dict_new.json') as fp:
        hub_dict = json.load(fp)

    manu = []
    for hub in hub_dict:
        print(hub)
        if 'add' in hub_dict[hub] or hub_dict[hub]['type'] == 'new from add':
            continue
        hub_text = get_hub_text(hub)
        if hub_dict[hub]['kevin']:
           kev_text = get_kev_text(hub_dict[hub]['kevin'])
        else:
            print(hub)
            continue
        texts = {'hub': hub_text, 'kev': kev_text}
        if hub_dict[hub]['al']:
            al_text = get_al_text(hub_dict[hub]['al'])
            texts['al'] = al_text
        texts = {k: remove_garbage(v) for k, v in texts.items()}
        hwords = hebrew(texts)
        if hwords:
            kev_num = hub_dict[hub]['kevin']
            kev_entry = get_bdbentry(kev_num)
            row = {'hw': kev_entry.headword, 'content': kev_entry.content['senses'][0]['definition'],
                   'hub num': hub, 'kev num': kev_num, 'al num': hub_dict[hub]['al']}
            row.update(texts)
            row.update(hwords)
            manu.append(row)
    print(X)
    with open('manu.csv', 'w', newline='') as fp:
        w = csv.DictWriter(fp, fieldnames=['hw', 'content', 'kev', 'hub', 'al', 'kev words', 'hub words', 'al words', 'kev num', 'hub num', 'al num'])
        w.writeheader()
        for row in manu:
            if 'al' not in row:
                row['al'] = row['al words'] = row ['al num'] = ''
            w.writerow(row)
