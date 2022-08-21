import json
from hub_al3rdphase import get_hub_text
import re
import django
django.setup()
from kevin_al import similar, get_kev_text, get_bdbentry
from kevin_al3 import first_hebrew_word

if __name__ == '__main__':
    with open('hub_dict_new.json') as fp:
        hub_dict = json.load(fp)
    with open('kev_dict.json') as fp:
        kev_dict = json.load(fp)
    hub_mis = {x: re.sub('[^א-ת ]', '', first_hebrew_word(get_hub_text(x))).replace('צ', 'ח').replace('פ', 'מ') for x in hub_dict if not hub_dict[x]['kevin']}
    kev_mis = {x: re.sub('[^א-ת ]', '', get_bdbentry(x).headword).split()[0].replace('פ', 'מ').replace('צ', 'ח') for x in kev_dict if not kev_dict[x]['hub']}

    x=0

    for k in kev_dict:
        hw = get_bdbentry(k).headword
        kb = re.sub('[^א-ת ]', '', hw).split()[0].replace('פ', 'מ').replace('צ', 'ח')
        hub = kev_dict[k]['hub']
        if hub:
            hubhw = first_hebrew_word(get_hub_text(hub))
            if hubhw:
                hubb = re.sub('[^א-ת ]', '', hubhw).replace('צ', 'ח').replace('פ', 'מ')
            else:
                print('no first word', hub)
                hubb = ''
            if kb != hubb:
                print(hw, hubhw)
                print(kb, hubb)
                x+=1

    # for k in kev_mis:
    #     hw = kev_mis[k]
    #     options = [x for x in hub_mis if hub_mis[x] == hw]
    #     if len(options) == 1:
    #         ratio = len(get_hub_text(options[0])) / len(get_kev_text(k))
    #         if ratio < 0.11 or ratio > 4.9:
    #             continue
    #         kev_dict[k]['hub'] = options[0]
    #         hub_dict[options[0]]['kevin'] = k
    #         if ratio > 1.83:
    #             hub_dict[options[0]]['add'] = True
    #         x+=1

    # for h in hub_mis:
    #     hw = hub_mis[h]
    #     options = [x for x in kev_mis if kev_mis[x] == hw]
    #     if len(options) == 0:
    #         print(first_hebrew_word(get_hub_text(h)))
    #         x+=1

    # for h in hub_mis:
    #     hw = hub_mis[h]
    #     if not hw.strip():
    #         print(get_hub_text(h), '\n')

    with open('hub_dict_new.json', 'w') as fp:
        json.dump(hub_dict, fp)
    with open('kev_dict.json', 'w') as fp:
        json.dump(kev_dict, fp)

    print(x)
