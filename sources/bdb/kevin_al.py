import json
from bs4 import BeautifulSoup
from hub_al3rdphase import get_hub_text
from hub_al2ndphase import find_symmetric_distance
import re
import django
django.setup()
from sefaria.model.lexicon import LexiconEntrySet, BDBEntry

def get_bdbentry(key):
    par, rid = key.split('_')
    return BDBEntry().load({'parent_lexicon': par, 'rid': rid})

def get_kev_text(key):
    text = ' '.join(get_bdbentry(key).as_strings())
    return BeautifulSoup(text, 'html.parser').text

def similar(kev, hub):
    kev_text, hub_text = get_kev_text(kev), get_hub_text(hub)
    kev_text, hub_text = ' '.join(kev_text.split()), ' '.join(hub_text.split())
    if len(hub_text) > 1000 and len(kev_text) > 1000:
        ratio = len(kev_text) / len(hub_text)
        len_al = int(500 * ratio)
        return (find_symmetric_distance(hub_text[:500], kev_text[:len_al]) < 500) and (find_symmetric_distance(hub_text[-500:], kev_text[-len_al:]) < 500)
    else:
        return find_symmetric_distance(hub_text, kev_text) < min(len(hub_text), len(kev_text))

if __name__ == '__main__':
    with open('hub_dict_new.json') as fp:
        hub_dict = json.load(fp)
    with open('kev_dict.json') as fp:
        kev_dict = json.load(fp)
    with open('al_dict_new.json') as fp:
        al_dict = json.load(fp)
    kevin = LexiconEntrySet({'parent_lexicon': {'$regex': '^BDB.*?Dictionary$'}})

    c=0
    for le in kevin:
        if hasattr(le, 'strong_numbers'):
            s_nums = []
            print(le.rid)
            for num in le.strong_numbers:
                if '–' not in num:
                    s_nums.append(num)
                else:
                    first, last = num.split('–')
                    last = first[:len(first)-len(last)] + last
                    s_nums += [str(x) for x in range(int(first), int(last)+1)]
            kev = f'{le.parent_lexicon}_{le.rid}'
            if kev_dict[kev]['hub']:
                continue

            options = [x for x in hub_dict if any(re.search(f'^{n}_', x) for n in s_nums) and not hub_dict[x]['kevin']]
            al = [x for x in al_dict if any(re.search(f'^{n}_', x) for n in s_nums)]
            more = []
            for x in al:
                if al_dict[x]['hub'] not in options and al_dict[x]['hub'] != 'ind':
                    more.append(al_dict[x]['hub'])
            options += more

            for opt in options:
                if similar(kev, opt):
                    kev_dict[kev]['hub'] = opt
                    hub_dict[opt]['kevin'] = kev
                    c+=1
                    with open('hub_dict_new.json', 'w') as fp:
                        json.dump(hub_dict, fp)
                    with open('kev_dict.json', 'w') as fp:
                        json.dump(kev_dict, fp)
                    break
    print(c)


