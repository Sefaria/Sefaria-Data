import csv
import json
from hub_al3rdphase import get_hub_text
import re
import csv
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

    kev = list(kev_mis) + ['' for _ in range(13)]
    kev_hw = list(kev_mis.values()) + ['' for _ in range(13)]
    hub = list(hub_mis)
    hub_hw = list(hub_mis.values())

    t = []
    for i in range(80):
        t.append({'kevin': kev[i],
                  'kevin hw': kev_hw[i],
                  'kevin text': get_kev_text(kev[i]) if kev[i] else '',
                  'hub': hub[i],
                  'hub hw': hub_hw[i],
                  'hub text': get_hub_text(hub[i] )})
    with open('bla.csv', 'w', newline='') as fp:
        w = csv.DictWriter(fp, fieldnames=['kevin', 'kevin hw', 'kevin text', 'hub', 'hub hw', 'hub text'])
        w.writeheader()
        for r in t:
            w.writerow(r)
