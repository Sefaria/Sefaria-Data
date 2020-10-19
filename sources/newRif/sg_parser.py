import re
import json
from rif_utils import path, tags_map
from data_utilities.util import getGematria
from tags_fix_and_check import tags_by_criteria, save_tags, next_gem
from tags_compare import compare_tags_nums, compare_tags, OrderedCounter

def letters_sequence(letters: list):
    #letters is list of tuples. first element is the letter and the second gives the page
    for p, page in enumerate(letters):
        prev = 0
        for n, letter in enumerate(page):
            if getGematria(letter[0]) != next_gem(prev):
                print(f'sequence problem in {p} page. {letter} comes after {0 if n==0 else page[n-1]}')
            prev = getGematria(letter[0])

def check_sequence(ja, letter_regex):
    letters = []
    for p, page in enumerate(ja):
        letters_page = []
        for par in page:
            if re.findall(letter_regex+'.', par):
                letters_page.append((re.findall(letter_regex+'.', par)[0], p+1))
            else:
                print(f'no tag letter {par}')
        if letters_page:
            letters.append(letters_page)
    letters_sequence(letters)


def parse_sg_pars(data, masechet):
    data = re.sub('\ufeff|\u200f', '', data)
    data = re.sub(r'[\[\{]\*\)([^\]\}]*)[\]\}]', r' <sup>*</sup><i class="footnote">\1</i>', data)
    data = re.sub('(">|i>) ', r'\1', data)
    data = re.sub(' (</)', r'\1', data)
    letter_tag = tags_map[masechet]['sg letter']
    title_tag = tags_map[masechet]['sg_title']
    data = [letter_tag + par for par in data.split(letter_tag)]

    if not tags_map[masechet]['sg_page']: #on masechtot with data tag, the first piece can be part of the next page
        if len(data) == 1:
            print('no letter tag', data)
        else:
            if data[0] != '@11':
                data[1] = data[0][3:] + ' ' + data[1]
            data.pop(0)
    else:
        if len(data) != 1 and len(data[0]) < 12: #12 for @22@88כד:
            data[1] = data[0][3:] + ' ' + data[1]
            data.pop(0)
        else:
            data[0] = data[0][3:]
    prev = 0

    for n, par in enumerate(data):
        par = re.sub(tags_map[masechet]['sg_del'], '', par)
        par = re.sub(' +', ' ', par.strip())
        par = re.sub('(?:' + title_tag + r')((?:לשון ריא"ז|[^@\n]*)(?:@\d\d)?)', r'<br><b>\1</b><br>', par)
        par = par.replace('\n', '')
        par = re.sub('^<br>', '', par)
        par = re.sub('<br>[.:]', '<br>', par)
        if par.endswith('<br>'):
            title = par.split('<br>')[-2]
            try:
                data[n+1] = f'{title}<br>{data[n+1]}'
                par = '<br>'.join(par.split('<br>')[:-2])
            except IndexError:
                par = par[:-4]
        par = re.sub('(: |:)(?!<| <|$| $)', ':<br>', par)

        letter = re.findall(letter_tag + '.[ @]', par)
        if letter == []:
            if not tags_map[masechet]['sg_page'] and n != 0:
                data[n-1] += f'<br>{par.replace(letter_tag, "")}'
                par = ''
            else:
                par = re.sub(letter_tag, '', par)
        else:
            gim = getGematria(letter[0])
            if gim != 1 and gim != next_gem(prev):
                print(f'{gim} after {prev}, {par}')
            prev = gim

        data[n] = par

    if tags_map[masechet]['sg_page'] and len(data) != 1 and len(data[0]) < 9: #9 for @88כד:
        data[1] = data[0][3:] + ' ' + data[1]
        data.pop(0)

    data = [par for par in data if par != '']
    return data

def execute():
    for masechet in tags_map:
        if masechet == 'Nedarim': continue
        print(masechet)
        with open(path+'/commentaries/SG_{}.txt'.format(masechet), encoding='utf-8') as fp:
            data = fp.read()

        page_tag = tags_map[masechet]['sg_page']
        letter_tag = tags_map[masechet]['sg letter']
        tags = tags_by_criteria(masechet, value=lambda x: x['referred text']==1)
        unknowns = tags_by_criteria(masechet, value=lambda x: x['referred text']==0 and x['style']==3)
        lengths = []

        if page_tag:
            data = data.split('@88')[1:]
            newdata = []
            for page in data:
                try:
                    daf, amud = re.search('^דף ([א-ס][א-ט]?) ע"([אב])', page).groups()
                    daf_num = getGematria(daf)
                    if amud == 'א': amud = 1
                    elif amud == 'ב': amud = 2
                    else: print('amud isnt valid', page[:30])
                    section = daf_num * 2 - 3 + amud
                    while len(newdata) < section: newdata.append([])
                    page = re.sub('דף [א-ס][א-ט]? ע"[אב]', '', page).strip()
                    #previously i've replace it with f'@88{daf}{"." if amud==1 else ":"}' for having the originl paging.
                except (ValueError, AttributeError):
                    print('daf and amud arent valid', page[:30])
                page = parse_sg_pars(page, masechet)
                newdata.append(page)

            #daf tags in data are according to print. this unites parts that in seperate pages
            for n, page in enumerate(newdata):
                if page != [] and letter_tag not in page[0]:
                    last_real_page = n - 1 #maybe there is one comment over more than 2 pages
                    while newdata[last_real_page] == []: last_real_page -= 1
                    newdata[last_real_page][-1] += ' ' + page[0]
                    page.pop(0)

            lengths = [len(page) for page in newdata if page != []]

        else:
            data = parse_sg_pars(data, masechet)
            splitted = []
            cou = 0
            for par in data:
                if letter_tag + 'א' in par:
                    if cou:
                        lengths.append(cou)
                        splitted.append(page_text)
                        letters_page = []
                    cou = 1
                    page_text = []
                else:
                    cou += 1
                page_text.append(par)
            lengths.append(cou)
            splitted.append(page_text)
            newtags, counter = compare_tags_nums(tags, lengths, unknowns, 1)
            tags.update(newtags)
            save_tags(tags, masechet)
            if len(counter) > 0:
                newdata = [[] for n in range(max([int(page) for page in counter]) + 1)]
                for page in counter:
                    newdata[int(page)] = splitted.pop(0)

        tags.update(compare_tags(tags, lengths, unknowns, 1))
        check_sequence(newdata, letter_tag)
        save_tags(tags, masechet)

        newdata = [[re.sub(' +', ' ', re.sub(letter_tag+'.|@', '', par)).strip() for par in page] for page in newdata]
        with open(path+'/commentaries/json/SG_{}.json'.format(masechet), 'w') as fp:
            json.dump(newdata, fp)

if __name__ == '__main__':
    execute()
