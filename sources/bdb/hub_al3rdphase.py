import json
from bs4 import BeautifulSoup
from hub_al2ndphase import similar
from hub_al2ndphase import find_symmetric_distance

def get_al_text(key):
    al_num, al_key = key.split('_', 1)
    with open(f'alhatorah/{al_num}.json') as fp:
        al_soup = BeautifulSoup(json.load(fp)['BDB'][al_key], 'html.parser')
    al_text = al_soup.text
    return ' '.join(al_text.split())

def get_hub_text(key):
    with open(f'bh_divided/{key}.html') as fp:
        hub_soup = BeautifulSoup(fp.read(), 'html.parser')
    hub_text = hub_soup.text
    return ' '.join(hub_text.split())

def sim2(al, hub):
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
        return (find_symmetric_distance(hub_text[:500], al_text[:len_al]) < 600) and (find_symmetric_distance(hub_text[-500:], al_text[-len_al:]) < 600)
    else:
        return find_symmetric_distance(hub_text, al_text) < min(len(hub_text), len(al_text)) * 1.2


x=0
if __name__ == '__main__':
    with open('hub_dict_new.json') as fp:
        hub_dict = json.load(fp)
    with open('al_dict_new.json') as fp:
        al_dict = json.load(fp)

    al_mis = {x: len(get_al_text(x)) for x in al_dict if not al_dict[x]['hub']}
    print(len(al_mis))
    hub_mis = {x: len(get_hub_text(x)) for x in hub_dict if 'al' not in hub_dict[x]}
    while al_mis:
        al_max = max(list(al_mis), key=lambda x: al_mis[x])
        hub_options = [x for x in hub_mis if al_mis[al_max]*0.5 < hub_mis[x] < al_mis[al_max]*2]
        # if len(hub_options) > 70:
        #     al_mis.pop(al_max)
        #     continue
        for option in hub_options:
            if similar(al_max, option):
                al_dict[al_max] = {'hub': option}
                hub_dict[option] = {'al': al_max, 'type': 'regular'}
                hub_mis.pop(option)
                x+=1
                break
            # if '8674' in option or len(get_al_text(al_max))>2000:
            #     continue
            # if sim2(al_max, option):
            #     # al_dict[al_max] = {'hub': option}
            #     # hub_dict[option] = {'al': al_max, 'type': 'regular'}
            #     print(al_max, option)
            #     print(1, get_hub_text(option))
            #     print('\n')
            #     print(2, get_al_text(al_max))
            #     print('\n\n')
            #     break
        al_mis.pop(al_max)

    with open('hub_dict_new.json', 'w') as fp:
        json.dump(hub_dict, fp)
    with open('al_dict_new.json', 'w') as fp:
        json.dump(al_dict, fp)
    print(x)
