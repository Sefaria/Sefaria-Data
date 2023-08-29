import django
django.setup()
from sefaria.model import *
import csv
from sefaria.utils.hebrew import gematria
import re

TE = [Ref(f"Zohar, Addenda, For Volume {'I'*(i)}").text('he', 'Torat Emet').text for i in range(1, 4)]
TEH = [Ref(f"Zohar, Addenda, For Volume {'I'*(i)}").text('he', 'Hebrew Torat Emet [he]').text for i in range(1, 4)]
def get_first_segment():
    global TE, TEH
    if not TE[0][0]:
        TE[0].pop(0)
        TEH[0].pop(0)
    if not TE[0]:
        TE.pop(0)
        TEH.pop(0)
    try:
        teh = TEH[0][0].pop(0)
    except IndexError:
        teh = ''
    return TE[0][0].pop(0), teh

with open('addenda_pages.csv') as fp:
    data = list(csv.DictReader(fp))
text = [[] for _ in range(3)]
te = [[] for _ in range(3)]
teh = [[] for _ in range(3)]
for row in data:
    if row['siman']:
        siman = gematria(row['siman']) - 160
    vol = row['ref'].count('I')
    text[vol - 1] += [[] for _ in range(siman-len(text[vol-1]))]
    te[vol - 1] += [[] for _ in range(siman-len(te[vol-1]))]
    teh[vol - 1] += [[] for _ in range(siman-len(teh[vol-1]))]
    rtext = ' '.join(row['text'].split())
    rtext = re.sub('{\d:(\d+[ab])} ?', r'<i data-overlay="Vilna Pages" data-value="\1"></i>', rtext)
    text[vol - 1][-1].append(rtext)
    teseg, tehseg = get_first_segment()
    te[vol - 1][-1].append(teseg)
    teh[vol - 1][-1].append(tehseg)

ver = Version().load({'title': 'Zohar TNNNG', 'versionTitle': 'Sulam'})
verte = Version().load({'title': 'Zohar TNNNG', 'versionTitle': 'Torat Emet'})
verteh = Version().load({'title': 'Zohar TNNNG', 'versionTitle': 'Hebrew Torat Emet [he]'})
for i, vol in enumerate(text):
    ver.chapter['Addenda'][f'Volume {"I"*(i+1)}'] = vol
    verte.chapter['Addenda'][f'Volume {"I" * (i + 1)}'] = te[i]
    verteh.chapter['Addenda'][f'Volume {"I" * (i + 1)}'] = teh[i]
ver.save()
verte.save()
verteh.save()
