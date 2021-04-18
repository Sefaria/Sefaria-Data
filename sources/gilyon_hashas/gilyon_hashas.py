import django
django.setup()
from sefaria.model import *
import re
from sources.functions import getGematria
from sefaria.utils.talmud import section_to_daf

with open('gilyon_hashas.txt', encoding='utf-8') as fp:
    data = fp.readlines()

N,Y=0,0
mases = {}
for line in data:
    line = line.strip()
    if not line:
        continue

    loc = re.findall('גליון הש"ס מסכת (.*?) דף (.*?) עמוד ([אב])', line)
    if loc:
        mas, daf, amud = loc[0]
        mas = f'{Ref(mas)}'
        i = getGematria(daf) * 2 - 3 + getGematria(amud)
        try:
            mases[mas][i]
        except (IndexError, KeyError) as e:
            if isinstance(e, KeyError):
                mases[mas] = []
            mases[mas] += [[] for _ in range(i+1-len(mases[mas]))]
        continue

    if '.' in line:
        l1, l2 = line.split('.', 1)
    mases[mas][i].append(f'<b>{l1}.</b>{l2}')

    if any(line.startswith(g) for g in ["גמ'", "גמרא", "מתני", 'במשנה', "במתני'", "בגמ'"]):
        base = mas
    elif any(line.startswith(r) for r in ['רש"י', 'ברש"י']):
        base = f'Rashi on {mas}'
    elif any(line.startswith(r) for r in ['רשב"ם', 'ברשב"ם']):
        base = f'Rashbam on {mas}'
    elif any(line.startswith(t) for t in ["תוס", 'תוד"ה', "בתוס'", 'תוספות', 'תד"ה']):
        base = f'Tosafot on {mas}'
    elif any(line.startswith(s) for s in ['בהר"ן', 'בר"ן', 'ר"נ', 'בהר"נ']):
        base = f'Ran on {mas}'
    elif line.startswith("שם"):
        pass
    elif any(line.startswith(s) for s in ['בא"ד', 'בסה"ד']):
        base = 'same'
    elif any(line.startswith(s) for s in ['ד"ה', 'בד"ה']):
        pass
    else:
        #print(mas, line)
        base = ''
        continue

    dh = line.split('.')[0]
    page = section_to_daf(i+1)
    if base == mas:
        pass
    elif base != 'same':
        if 'ד"ה' in dh:
            dh = dh.split('ד"ה')[1]
        else:
            dh = ' '.join(dh.split()[1:])
        dh = re.split("וכו'|כו'", dh)[0].strip()
        options = []
        for n, g_line in enumerate(Ref(f'{base} {page}').text('he').text):
            for m, com in enumerate(g_line):
                com = ' '.join(com.split()[:len(dh.split())+1])
                if dh in com:
                    options.append(n)
        if len(options) != 1:
