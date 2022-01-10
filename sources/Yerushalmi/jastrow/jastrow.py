import json
import django
django.setup()
import re
from sefaria.model import *
from sefaria.model.schema import *
from sefaria.system.exceptions import DuplicateRecordError
from data_utilities.dibur_hamatchil_matcher import match_ref
from sources.functions import post_link

def get_defs(entry_content):
    for sense in entry_content['senses']:
        try:
            sense['definition']
            yield sense
        except KeyError:
            get_defs(sense)

def roman_to_int(roman):
    num = 0
    if 'IV' in roman:
        num = 4
    elif 'IX' in roman:
        num = 9
    roman = re.sub('IV|IX', '', roman)
    num += roman.count('I')
    num += 5 * roman.count('V')
    num += 10 * roman.count('X')
    return num

def columns_diff(page, first):
    return 4 * (int(page[:-1]) - int(first[:-1])) + ord(page[-1]) - ord(first[-1])

mases = json.load(open('masechtot.json'))
x=0
entries = LexiconEntrySet({'parent_lexicon': 'Jastrow Dictionary'})
links = []
yer = 'Jerusalem Talmud'
for entry in entries:
    for sense in get_defs(entry.content):
        defin = sense['definition']
        ibid = ''
        found = re.findall(r'Y\. .*?[ᵃᵇᶜᵈ]', defin)
        for occur in found:
            if len(occur) > 23:
                continue

            mas = [mases[m] for m in mases if m in occur]
            if len(mas) != 1:
                continue
            mas = mas[0]
            if mas == 'ibid':
                continue

            pereks = re.findall('[IVX]+', occur)
            if len(pereks) != 1:
                continue
            perek = roman_to_int(pereks[0])
            try:
                alt = library.get_index(f'{yer} {mas}').alt_structs['Venice']['nodes'][perek-1]
            except IndexError:
                continue

            pages = re.findall('\d+[ᵃᵇᶜᵈ]', occur)
            if len(pages) != 1:
                continue
            page = pages[0]
            for l, b in [('ᵃ', 'a'), ('ᵇ', 'b'), ('ᶜ', 'c'), ('ᵈ', 'd')]:
                page = page.replace(l, b)
            column_in_perek = columns_diff(page, alt['startingAddress'])
            try:
                ref = alt['refs'][column_in_perek]
            except IndexError:
                mapping = json.load(open('mappings.json'))[mas]
                try:
                    ref = mapping[f'{page}, JTmock {mas}']
                    ref = ref.replace('JTmock', yer)
                except KeyError:
                    continue

            quote = re.findall(occur+'.{1,6}?<span dir="rtl">(.*?)</span>', defin)
            headword = re.sub('[^ א-ת]', '', entry.headword).strip()
            if len(quote) != 1:
                quote = headword
            else:
                quote = quote[0]
            quote = re.sub('[^ א-ת\'׳]', '', quote).strip()
            quote = re.sub(f"{headword[0]}(?:'|׳)", headword, quote)
            quote = re.sub('\'|׳', '', quote).strip()

            match = match_ref(Ref(ref).text('he', 'Mechon-Mamre'), [quote], lambda x: re.sub('[^ א-ת]', '', x).split(), char_threshold=0.8)['matches'][0]
            if not match:
                continue
            x += 1
            sense['definition'] = sense['definition'].replace(occur, f'<a class="refLink" href="{match.url()}" data-ref="{match.normal()}">{occur}</a>')
            entry.refs.append(match.normal())
            entry.save()
            try:
                Ref(f'Jastrow {entry.headword}')
            except DictionaryEntryNotFoundError:
                print('not found ref', entry.headword)
            links.append({'type': 'reference',
                          'refs': [Ref(f'Jastrow {entry.headword} 1').normal(), match.normal()],
                          'auto': True,
                          'generated_by': 'jastrow_yerushalmi_parser'})

post_link(links, server='http://localhost:9000', VERBOSE=False, skip_lang_check=False)
print(x)
