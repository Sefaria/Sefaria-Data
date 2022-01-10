import django
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import BookNameError
import re
from sources.functions import getGematria

with open('chidushei_agadot.txt', encoding='utf-8') as fp:
    data = fp.read()

missings = []
for book, daf, amud in re.findall('(חידושי אגדות מסכת .{,15}) דף (.{,3}) עמוד ([אב])', data):
    try:
        i = library.get_index(f"{book.replace('מסכת', 'על')}")
    except BookNameError:
        try:
            i = library.get_index(f"{book.replace('מסכת', 'על מסכת')}")
        except BookNameError:
            try:
                i = library.get_index(f" {book.replace('מסכת', 'על מסכת')}")
            except BookNameError:
                missings.append(f'{book} {daf} {amud}')
                continue
        if Ref(f'{i.title} {getGematria(daf)}{"a" if amud ==  "א" else "b"}') not in i.all_section_refs():
            missings.append(f'{i.title} {getGematria(daf)}{"a" if amud ==  "א" else "b"}')

masechtot = [' '.join(m.split()[:4]) for m in missings]
missings_more = [m for m in missings if masechtot.count(' '.join(m.split()[:4])) > 5]
missings_less = [m for m in missings if m not in missings_more]

with open('chidushei_agadot_missings_more.txt', 'w', encoding='utf-8') as fp:
    fp.write('\n'.join(missings_more))
with open('chidushei_agadot_missings_less.txt', 'w', encoding='utf-8') as fp:
    fp.write('\n'.join(missings_less))

with open('chidushei_halachot.txt', encoding='utf-8') as fp:
    data = fp.read()

missings = []
for book, daf, amud in re.findall('(חידושי הלכות מסכת .{,15}) דף (.{,3}) עמוד ([אב])', data):
    try:
        i = library.get_index(f"{book.replace('מסכת', 'על')}")
    except BookNameError:
        try:
            i = library.get_index(f"{book.replace('מסכת', 'על מסכת')}")
        except BookNameError:
            try:
                i = library.get_index(f" {book.replace('מסכת', 'על מסכת')}")
            except BookNameError:
                book = book.replace('חידושי', 'חדושי')
                try:
                    i = library.get_index(f"{book.replace('מסכת', 'על')}")
                except BookNameError:
                    try:
                        i = library.get_index(f"{book.replace('מסכת', 'על מסכת')}")
                    except BookNameError:
                        try:
                            i = library.get_index(f" {book.replace('מסכת', 'על מסכת')}")
                        except BookNameError:
                            print(f'{book} {daf} {amud}')
                            missings.append(f'{book} {daf} {amud}')
                            continue
        if Ref(f'{i.title} {getGematria(daf)}{"a" if amud ==  "א" else "b"}') not in i.all_section_refs():
            missings.append(f'{i.title} {getGematria(daf)}{"a" if amud ==  "א" else "b"}')

masechtot = [' '.join(m.split()[:4]) for m in missings]
missings_more = [m for m in missings if masechtot.count(' '.join(m.split()[:4])) > 5]
missings_less = [m for m in missings if m not in missings_more]

with open('chidushei_halacho_missings_more.txt', 'w', encoding='utf-8') as fp:
    fp.write('\n'.join(missings_more))
with open('chidushei_halacho_missings_less.txt', 'w', encoding='utf-8') as fp:
    fp.write('\n'.join(missings_less))
