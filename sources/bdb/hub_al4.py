import json
from bs4 import BeautifulSoup
from hub_al3rdphase import get_al_text, get_hub_text
from hub_al3rdphase import sim2 as similar

with open('hub_dict_new.json') as fp:
    hub_dict = json.load(fp)
with open('al_dict_new.json') as fp:
    al_dict = json.load(fp)
# for h in hub_dict:
#     if hub_dict[h]['type'] == 'unknown' and 'Forms and Transliterations' in get_hub_text(h):
#         with open(f'bh_divided/{h}.html') as fp:
#             file = fp.read()
#         file = file.split('Forms and Transliterations')[0]
#         with open(f'bh_divided/{h}.html', 'w') as fp:
#             fp.write(file)

al_mis = {x: len(get_al_text(x)) for x in al_dict if not al_dict[x]['hub']}
hub_mis = {x: len(get_hub_text(x)) for x in hub_dict if 'al' not in hub_dict[x]}
x=0
for al in al_mis:
    num = al.split('_')[0]
    hub_options = [x for x in hub_mis if num in x and al_mis[al]*0.5 < hub_mis[x] < al_mis[al]*2.5]
    for option in hub_options:
        if similar(al, option):
            al_dict[al] = {'hub': option}
            hub_dict[option] = {'al': al, 'type': 'regular'}
            hub_mis.pop(option)
            x += 1
            break
print(x)
with open('hub_dict_new.json', 'w') as fp:
    json.dump(hub_dict, fp)
with open('al_dict_new.json', 'w') as fp:
    json.dump(al_dict, fp)
