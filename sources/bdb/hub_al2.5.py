##dal al doubles

import json
from hub_al3rdphase import get_al_text

x=0
with open('al_dict.json') as fp:
    al_dict = json.load(fp)
al_mis = [x for x in al_dict if not al_dict[x]['hub']]
al_have = {x:len(get_al_text(x)) for x in al_dict if al_dict[x]['hub']}
for mis in al_mis:
    print(1, len(al_mis))
    mis_text = get_al_text(mis)
    mis_len = len(mis_text)
    options = [x for x in al_have if al_have[x] == mis_len]
    for have in options:
        if mis_text == get_al_text(have):
            al_dict.pop(mis)
            x+=1
            print(x)
            with open('al_dict.json', 'w') as fp:
                json.dump(al_dict, fp)
            break
