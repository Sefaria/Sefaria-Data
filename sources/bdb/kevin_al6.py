import json
import csv

if __name__ == '__main__':
    with open('hub_dict_new.json') as fp:
        hub_dict = json.load(fp)
    with open('kev_dict.json') as fp:
        kev_dict = json.load(fp)
    with open('manu.csv', newline='') as fp:
        data = list(csv.DictReader(fp))
    for row in data:
        kev = row['kevin'].strip()
        hub = row['hub'].strip()
        if kev == '.':
            continue
        kev_dict[kev]['hub'] = hub
        try:
            hub_dict[hub]['kevin'] = kev
        except KeyError:
            hub_dict[hub] = {'kevin': kev, 'type': 'vide entry'}
        if row['add'].strip():
            hub_dict[hub]['add'] = True
    with open('hub_dict_new.json', 'w') as fp:
        json.dump(hub_dict, fp)
    with open('kev_dict.json', 'w') as fp:
        json.dump(kev_dict, fp)

