import json
from hub_al3rdphase import get_hub_text
import re
import django
django.setup()
from kevin_al import similar, get_kev_text, get_bdbentry

if __name__ == '__main__':
    with open('hub_dict_new.json') as fp:
        hub_dict = json.load(fp)
    with open('kev_dict.json') as fp:
        kev_dict = json.load(fp)
    hub_mis = {x: len(get_hub_text(x)) for x in hub_dict if not hub_dict[x]['kevin']}
    kev_mis = {x: len(get_kev_text(x)) for x in kev_dict if not kev_dict[x]['hub']}

    c,y=0,0
    while kev_mis:
        kev_max = max(list(kev_mis), key=lambda x: kev_mis[x])
        hw = re.sub('[^א-ת ]', '', get_bdbentry(kev_max).headword)
        hub_options = [x for x in hub_mis if kev_mis[kev_max]*1.1 < hub_mis[x] < kev_mis[kev_max]*1.5]
        for option in hub_options:
            # first = get_hub_text(option).split()[0]
            # first = re.sub('[^א-ת ]', '', first).replace('צ', 'ח')
            # if first != hw:
            #     continue
            if similar(kev_max, option):
                kev_dict[kev_max]['hub'] = option
                hub_dict[option]['kevin'] = kev_max
                hub_mis.pop(option)
                c+=1
                break
        kev_mis.pop(kev_max)

    with open('hub_dict_try.json', 'w') as fp:
        json.dump(hub_dict, fp)
    with open('kev_dict_try.json', 'w') as fp:
        json.dump(kev_dict, fp)
    print(c,y)
