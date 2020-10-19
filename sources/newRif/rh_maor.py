from rif_utils import path
from sources.functions import getGematria
import re
import json

with open(f'{path}/commentaries/shut/maor_Rosh Hashanah.txt', encoding='utf-8') as fp:
    shut = fp.read()
shut = shut.replace('\xa0', ' ')
shut = re.sub(r'(המאור ה(?:קטן|גדול) מסכת .*? דף [א-צ]{1,2} עמוד [אב])\n\n\1', r'\1', shut)
pages = re.findall(r'המאור ה(?:קטן|גדול) מסכת .*? דף ([א-צ]{1,2}) עמוד ([אב])', shut)
sections = []
num_pages = int(getGematria(pages[-1][0])) * 2
data = re.split(r'המאור ה(?:קטן|גדול) מסכת .*? דף [א-צ]{1,2} עמוד [אב] *\n', shut)[1:]
data = [page.strip() for page in data if page.strip()!='']
newdata = []
for page in data:
    page = [par.strip() for par in page.split('\n') if par.strip()!='']
    newpage = []
    for par in page:
        if par[0] == '[': par = '@22' + par
        newpage.append(par)
    daf, amud = pages.pop(0)
    daf = getGematria(daf)
    amud = 'a' if amud == 'א' else 'b'
    sec = daf * 2 -1 if amud == 'b' else daf * 2 - 2
    sections.append(sec)
    newpage[0] = f'##{daf}{amud} ' + newpage[0]
    newdata.append(newpage)

for n, page in enumerate(newdata):
    if page == []: continue
    if page[-1][-1] != '.': #means page ends in middle of paragraph
        newdata[n][-1] = newdata[n][-1] + ' ' + newdata[n+1].pop(0)

finaldata = [[] for _ in range(num_pages)]
for page in newdata:
    finaldata[sections.pop(0)] = page

with open(f'{path}/commentaries/json/maor_Rosh Hashanah.json', 'w') as fp:
    json.dump(finaldata, fp)
