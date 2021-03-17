import re
import json
from rif_utils import path, maor_tags

def mark_pars(string, masechet, milchemet=False):
    if masechet == 'intro':
        string = re.sub(' \n |\n | \n', '\n', string)
        return re.sub('\n+', '\nA', string)
    string = re.sub(':([^<])', r':A\1', string)
    while re.search(r'([\(\[][^\)\]]*)A([^\)\]]*[\)\]])', string):
        string = re.sub(r'([\(\[][^\)\]]*)A([^\)\]]*[\)\]])', r'\1\2', string)
    if masechet != 'intro' and not milchemet:
        endtag = maor_tags[masechet]['ch end']
        if endtag:
            string = re.sub(f'({endtag}[^@\n]*)([@\n])', r'\1A\2', string)
    elif milchemet:
        for br in re.findall('A[^A]{1,28}', string):
            if 'אמר' in br and 'הכותב' in br:
                new = br[1:].lstrip()
                string = re.sub(br, f'<br>{new}', string)
        if masechet in ['Sukkah', 'Sanhedrin', 'Avodah Zarah']:
            endtag = '@99'
            string = re.sub(f'({endtag}[^@\n]*)([@\n])', r'\1A\2', string)
    return string

def split_pages(string):
    page_nums = re.findall(r'##(\d{1,2})([ab])', string)
    page_nums = [int(daf) * 2 - 1 if amud == 'b' else int(daf) * 2 - 2 for daf, amud in page_nums]
    string = string.replace('##', 'B##')
    string = re.sub(r'A\sB', 'AB', string)
    string = re.sub('A([^AB]{1,17})(B##\d{1,2}[ab])', r'A\2\1', string) #less than 17 characters probably means
    middles = re.findall(r'[^A]B(##\d{1,2}[ab])', string) #page in middle of paragraph
    for middle in middles:
        string = re.sub(f'B({middle}[^A]*A)', r'\1B', string)
    pages = [page.strip() for page in string.split('B')][1:]
    new = [[] for _ in range(page_nums[-1]+1)]
    if len(pages) != len(page_nums):
        print(f'error {len(pages)} pages and {len(page_nums)} page numbers')
        return []
    for num in page_nums:
        new[num] = pages.pop(0)
    return new

def split_pars(page):
    return [sec.strip() for sec in page.split('A') if sec.strip() != '']

def parse_text(string, masechet):
    string = string.replace('@@', '##')
    string = re.sub('\ufeff', '', string)
    string = re.sub(' +', ' ', string)
    note_reg = r'(?:\*\)?\[|\[\*\)?) *([^\]]*?) *\]'
    new = r'<sup>*</sup><i class="footnote">\1</i>'
    string = re.sub(note_reg, new, string)
    string = string.replace('> ', '>')
    if masechet in ['Ketubot', 'Chullin']:
        string = re.sub('@66([^@:\n]*)@77', r'<small>\1</small>', string)
        if '@66' in string or '@77' in string:
            print('small tags in text', re.findall('@[67]{1,2}.{1,20}', string))
    return string

def parse(data, masechet, d2=True, milchemet=False):
    data = parse_text(data, masechet)
    data = mark_pars(data, masechet, milchemet=milchemet)
    if not d2:
        data = split_pars(data)
    else:
        data = split_pages(data)
        data = [split_pars(page) if page else [] for page in data]
    return data

def execute():
    for masechet in list(maor_tags) + ['intro']:
        if masechet == 'Rosh Hshanah': continue
        print(masechet)
        for mefaresh in ['maor', 'milchemet']:
            print(mefaresh)
            try:
                with open(f'{path}/commentaries/splitted/{mefaresh}_{masechet}.txt', encoding='utf-8') as fp:
                    data = fp.read()
            except FileNotFoundError:
                continue
            if masechet in ['intro', 'Chagigah', 'Sotah']:
                data = parse(data, masechet, d2=False)
            elif mefaresh == 'milchemet':
                data = parse(data, masechet, milchemet=True)
            else:
                data = parse(data, masechet)
            with open(f'{path}/commentaries/json/{mefaresh}_{masechet}.json', 'w') as fp:
                json.dump(data, fp)

if __name__ == '__main__':
    execute()
