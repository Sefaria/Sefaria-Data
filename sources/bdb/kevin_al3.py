import json
from hub_al3rdphase import get_hub_text
from hub_al import is_hebrew
from hub_al2ndphase import find_symmetric_distance
import re
import django
django.setup()
from kevin_al import similar, get_kev_text, get_bdbentry

def first_hebrew_word(text):
    for word in text.split():
        word = re.sub('[\[\],\.]', '', word)
        if not word:
            continue
        if is_hebrew(word) or (re.search('^\[.*\]$', word) and is_hebrew(word[1:-1])):
            return word

def sim_start(kev, hub):
    kev_text, hub_text = get_kev_text(kev), get_hub_text(hub)
    kev_text, hub_text = ' '.join(kev_text.split()[:7]), ' '.join(hub_text.split()[:7])
    return find_symmetric_distance(hub_text, kev_text) < min(len(hub_text), len(kev_text)) *0.8

def sim_wo_add(kev, hub):
    kev_text, hub_text = get_kev_text(kev), get_hub_text(hub)
    hub_text = hub_text.split('**')[0]
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
    hub_mis = [x for x in hub_dict if not hub_dict[x]['kevin']]
    kev_mis = {x: re.sub('[^א-ת ]', '', get_bdbentry(x).headword).split()[0].replace('פ', 'מ').replace('צ', 'ח') for x in kev_dict if not kev_dict[x]['hub']}

    c=0
    addenda = []
    for hub in hub_mis:
        hw = first_hebrew_word(get_hub_text(hub))
        hw = re.sub('[^א-ת ]', '', hw).replace('צ', 'ח').replace('פ', 'מ')
        options = [x for x in kev_mis if kev_mis[x] == hw]
        for option in options:
            # if sim_start(option, hub):
            #     addenda.append({'hub': hub, 'kev': option, 'hw': [get_bdbentry(option).headword, hw]})
            #     print(hw)
            #     print(get_hub_text(hub))
            #     print(get_kev_text(option))
            #     print('\n')
            #     break

            if sim_wo_add(option, hub):
                kev_dict[option]['hub'] = hub
                hub_dict[hub]['kevin'] = option
                kev_mis.pop(option)
                c += 1
                break

    with open('hub_dict_new.json', 'w') as fp:
        json.dump(hub_dict, fp)
    with open('kev_dict.json', 'w') as fp:
        json.dump(kev_dict, fp)
    print(c)

    # with open('addenda.json', 'w') as fp:
    #     json.dump(addenda, fp)

