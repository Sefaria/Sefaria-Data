from sources.functions import *
info = []
for p in PlaceSet():
    en = [x['text'] for x in p.names if x['lang'] == 'en']
    he = [x['text'] for x in p.names if x['lang'] == 'he']
    loc = p.point['coordinates']
    info.append([en, he, loc])

with open("Places Info.csv", 'w') as f:
    writer = csv.writer(f)
    writer.writerow(["English", "Hebrew", "Location"])
    writer.writerows(info)