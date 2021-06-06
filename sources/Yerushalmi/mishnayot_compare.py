# encoding=utf-8

from fuzzywuzzy import fuzz
import django
django.setup()
from sefaria.model import *
from sefaria.utils.hebrew import strip_nikkud

errors = []
tractates = library.get_indexes_in_category("Yerushalmi")
tractates = [l for l in tractates if "JTmock" in l]
for tractate in tractates:
    halakhot = [h for c in Ref(tractate).all_subrefs() for h in c.all_subrefs()]
    for halakha in halakhot:
        try:
            tg, tm = halakha.text('he', 'Guggenheimer').text[0], halakha.text('he', 'Mehon-Mamre').text[0]
        except IndexError:
            errors.append(f'{halakha.normal()}: missing segment')
            continue
        ratio = fuzz.ratio(strip_nikkud(tg), tm)
        if ratio < 70:
            errors.append(f'{halakha.normal()}: {ratio}')

print('total errors:', len(errors))
print(*errors[:20], sep='\n')
with open('mishnayot_errors.txt', 'w') as fp:
    fp.write('\n'.join(errors))



r = Ref("JTmock Avodah Zarah 3:6:1")
tg = r.text('he', 'Guggenheimer').text
tm = r.text('he', 'Mehon-Mamre').text

print(tg, tm, fuzz.ratio(strip_nikkud(tg), tm), sep='\n\n')

