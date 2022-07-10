#del unmatchin

import json
from bs4 import BeautifulSoup

def find_symmetric_distance(s1, s2, substitution=2):
    array = [[n] for n in range(len(s2)+1)]
    array[0] = [n for n in range(len(s1)+1)]
    for n in range(len(s2)):
        for m in range(len(s1)):
            subs = array[n][m] if s1[m] == s2[n] else array[n][m] + substitution
            array[n+1].append(min(subs, array[n][m+1]+1, array[n+1][m]+1))
    return array[-1][-1]

with open('hub_dict.json') as fp:
    hub_dict = json.load(fp)
with open('al_dict.json') as fp:
    al_dict = json.load(fp)

def similar(al, hub):
    al_num, al_key = al.split('_', 1)
    with open(f'alhatorah/{al_num}.json') as fp:
        al_soup = BeautifulSoup(json.load(fp)['BDB'][al_key], 'html.parser')
    al_text = al_soup.text
    with open(f'bh_divided/{hub}.html') as fp:
        hub_soup = BeautifulSoup(fp.read(), 'html.parser')
    hub_text = hub_soup.text
    al_text, hub_text = ' '.join(al_text.split()), ' '.join(hub_text.split())
    if len(hub_text) > 1000 and len(al_text) > 1000:
        ratio = len(al_text) / len(hub_text)
        len_al = int(500 * ratio)
        return (find_symmetric_distance(hub_text[:500], al_text[:len_al]) < 500) and (find_symmetric_distance(hub_text[-500:], al_text[-len_al:]) < 500)
    else:
        return find_symmetric_distance(hub_text, al_text) < min(len(hub_text), len(al_text))

if __name__ == '__main__':
    x,y=0,0
    for entry in al_dict:
        hub_key = al_dict[entry]['hub']
        if not hub_key:
            continue
        if not similar(entry, hub_key):
            hub_dict[hub_key] = {'type': 'unknown'}
            al_dict[entry]['hub'] = None
            x+=1
    print(x,y)
    with open('hub_dict.json', 'w') as fp:
        json.dump(hub_dict, fp)
    with open('al_dict.json', 'w') as fp:
        json.dump(al_dict, fp)
