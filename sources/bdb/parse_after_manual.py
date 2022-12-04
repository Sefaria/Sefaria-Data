import re
import json
import csv
import django
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import InputError
from itertools import chain
from bs4 import BeautifulSoup

def remove_non_hebrew(string):
    return re.sub(r'[^\u0590-\u05f5 ]', '', string)

def split_sub(hw):
    hw, occur = hw.split('<sub>')
    occur = occur.split('</sub>')[0].strip()
    return hw.strip(), occur

def find_hw(text):
    text = text.replace('', '‡').strip()
    text = re.sub('^I+\d+', '', text).strip().replace(']]', ']').replace('', '').replace('#xa7;', '§').replace('', '')
    hebrew_sequnce = '\\u0590-\\u05f5'
    hebrew = '[\\u0590-\\u05f5]'
    dagger = '(?:† ?)'
    double = '(?:‡ ?)'
    num = '(?:I*[Vv]?I*\.*)'
    nums = f'(?:{num},? ?)*'
    reg = f'^{double}?{dagger}?{nums}?{dagger}?\[?{dagger}?(?:<strong>)?[א-ת\(]'
    hw = re.findall(reg, text)
    if not hw:
        print('problem with headword', text[:150])
        return
    hw = hw[0]
    ret_dict = {}
    if '‡' in hw:
        ret_dict['peculiar'] = True
        text = text.replace('‡', '', 1).strip()
    if '†' in hw:
        ret_dict['all_cited'] = True
        text = text.replace('†', '', 1).strip()
    nums = [n.strip() for n in re.findall(nums, hw) if n.strip()]
    if nums:
        text = text.replace(nums[0], '')
        ret_dict['ordinal'] = nums[0].replace('v', 'V').strip()
    if 'strong' in hw:
        text = text.replace('<strong>', '', 1).replace('</strong>', '', 1)
    text = ' '.join(text.split())
    if len(text.split()) < 2:
        print('entry is too short', text)
        return
    if '[' in hw:
        in_bra = text.split('[')[1].split(']')[0]
        if len(in_bra.split()) > 10 or len(in_bra.split()) == 1 or ']' in text.split()[0] or ']' not in text:
            ret_dict['brackets'] = 'first_word'
        else:
            ret_dict['brackets'] = 'all'
            text = text.split(']')[1]
            if re.search('[a-z\?]', in_bra):
                ret_dict['headword'], appendix = re.split(f'({hebrew}+)', in_bra, 1)[1:]
                ret_dict['headword_appendix'] = re.sub(f'({hebrew}+)', r'<span dir="rtl">\1</span>', appendix) #dont strip
            else:
                in_bra = remove_non_hebrew(in_bra)
                ret_dict['headword'], alt_headwords = in_bra.split(None, 1)
                ret_dict['alt_headwords'] = [{'word': w} for w in alt_headwords.split()]
            if '<sub>' in ret_dict['headword']:
                ret_dict['headword'], ret_dict['occurrences'] = split_sub(ret_dict['headword'])
            if 'alt_headwords' in ret_dict:
                for alt in ret_dict['alt_headwords']:
                    if 'sub' in alt['word']:
                        alt['word'], alt['occurrences'] = split_sub(alt['word'])
            return ret_dict, text
    ret_dict['headword'], text = text.split(None, 1)
    ret_dict['headword'] = re.sub('[\[\],]', '', ret_dict['headword'])
    if '<sub>' in ret_dict['headword']:
        ret_dict['headword'], ret_dict['occurrences'] = split_sub(ret_dict['headword'])
    if re.search(f'^ *{hebrew}', text):
        alt_headwords, text = re.split(f'((?:[{hebrew_sequnce}, ](?: *<sub>[^<]*?</sub>)?)+)', text, 1)[1:]
        print(alt_headwords, 11111, text[:50])
        alt_headwords = remove_non_hebrew(alt_headwords)
        ret_dict['alt_headwords'] = [{'word': w.replace(',', '')} for w in alt_headwords.split()]
        for alt in ret_dict['alt_headwords']:
            if 'sub' in alt['word']:
                alt['word'], alt['occurences'] = split_sub(alt['word'])
    text = text.strip()
    return ret_dict, text

def main_root(hw):
    # if re.search('^[א-ת]$', hw):
    # in all cases this is already a root entry. the only cases are the only letter where it's really not a root entry
    letter = '(?:[א-רת]|שׁ|שׂ)'
    em_kria = '[אה]'
    kamatz = 'ָ'
    patah = 'ַ'
    hirik = 'ִ'
    dagesh = 'ּ'
    yud = 'י'
    vav = 'ו'
    qal = f'^{letter}{dagesh}?{kamatz}{dagesh}?{letter}{patah}{letter}$'
    qal_alul = f'^{letter}{dagesh}?{kamatz}{dagesh}?{letter}{kamatz}{em_kria}$'
    ain_yud = f'^{letter}{dagesh}?{hirik}{dagesh}?{yud}{letter}$'
    ain_vav = f'^{letter}{dagesh}?{vav}{dagesh}{letter}$'
    if re.search(f'{qal}|{qal_alul}|{ain_yud}|{ain_vav}', hw):
        return True

def link_v(text, dict_url, lexicon):
    #dict_url can be different for the Aramaic
    #returns the updated text
    order = '(?:[IV]*\.? )'
    hebrew = '[\\u0590-\\u05f5]+'
    v = r'\bv\. '
    sub = '(?:sub\.? )'
    sup = '(?:supr\. )'
    nikud = 'ֱֲֳִֵֶַָֹּ'
    vs = re.findall(f'{v}{sup}?{sub}?({order})?\[?({hebrew})[\.,]?(?: {sub}({order})?({hebrew}))?', text)
    for order, headword, sup_order, sup_headword in vs:
        query = {'headword': {'$regex': f'^{headword}[⁰¹²³⁴⁵⁶⁷⁸⁹]*$'}, 'parent_lexicon': lexicon}
        if order:
            order = order.replace('.', '').strip()
            query['ordinal'] = {'$regex': f'^{order}\.?$'}
        les = LexiconEntrySet(query)
        if len(les) > 1:
            #ARAMAIC
            print('more than one entry matches')
            print(query)
            print(text[:40])
            pass
            #finding the one
        if len(les) == 0:
            query['headword']['$regex'] = f"^{nikud.join([x for x in headword])}{'[⁰¹²³⁴⁵⁶⁷⁸⁹]*'}$"
            les = LexiconEntrySet(query)
            if len(les) != 0:
                print('no entry found')
            # print(headword)
            # print(text)
            continue
        le = les[0]
        text = re.sub(f'({v}{sub}?{order}?)({re.escape(headword)})', r'\1' + f'<a dir="rtl" class="refLink" href="/{dict_url},_{le.headword}.1" data-ref="{dict_url}, {le.headword} 1">{headword.strip()}</a>', text)
        #NOTICE - we have here an rtl tag
    return text

def rtl(text):
    arabic_block = range(1536, 1792)
    ethipian_block = range(4608, 4989)
    syr_block = range(1792, 1872)
    heb_block = range(1424, 1525)
    samaritan_block = range(2048, 2111)
    semitic_letter = ''.join([chr(x) for x in chain(arabic_block, ethipian_block, syr_block, heb_block, samaritan_block)])
    semitic_space = semitic_letter + ' '
    text = re.split('(<a .*?</a>)', text)
    for ind in range(0, len(text), 2):
        text[ind] = re.sub(f'([{semitic_letter}][{semitic_space}]*[{semitic_letter}])', r'<span dir="rtl">\1</span>', text[ind])
    return ''.join(text)

def double_links(text):
    for a, b, c in re.findall(r'(<a href=".*?")(.*?</a>)((?:,? *\1.*?</a>)+)', text):
        text = text.replace(f'{a}{b}{c}', f'{a}{b}(×{c.count("href")+1})', 1)
    return text

def make_links(le):
    try:
        return list({Ref(ref.replace(r'/', '')).normal() for ref in re.findall(r'<a href="(.*?)"', le.content['senses'][0]['definition'])})
    except InputError:
        print('problem with refs:', re.findall(r'<a href="(.*?)"', le.content['senses'][0]['definition']))
        return []

def make_data_ref(text):
    soup = BeautifulSoup(text, 'html.parser')
    for a in soup.find_all('a'):
        try:
            a['data-ref'] = Ref(a['href'].replace('/', '')).normal()
        except InputError:
            print('problem with ref', a['href'])
    return str(soup).replace('&amp;', '$').replace('&lt;', '<').replace('&gt;', '>')

def parse(hubd, lexicon_name):
    headwords = []
    maybe_roots = []
    keys = sorted(list(hubd), key=lambda x: int(hubd[x]['kevin'].split('_')[1]) if hubd[x]['kevin'] else 99999)
    entries = []
    n = 4 if 'Aramaic' in lexicon_name else 5
    for rid, h in enumerate(keys, 1):
        hubd[h]['rid'] = f'A{str(rid).zfill(n)}'
        if 'text' in hubd[h]:
            temp = find_hw(hubd[h]['text'])
            if not temp:
                continue
            ret_dict, hubd[h]['text'] = temp
            hubd[h].update(ret_dict)
            headwords.append(hubd[h]['headword'])
            chw = headwords.count(hubd[h]['headword'])
            if chw > 1:
                hubd[h]['headword'] += ''.join(dict(zip("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")).get(c) for c in str(chw))
            if hubd[h]['type'] == 'root entry':
                hubd[h]['root'] = True
            elif hubd[h]['type'] != 'vide entry':
                if main_root(hubd[h]['headword']):
                    maybe_roots.append({'rid': rid, 'headword': hubd[h]['headword'], 'start': hubd[h]['text'][:50]})
            if entries: #ARAMAIC
                hubd[h]['prev_hw'] = entries[-1]['headword']
                entries[-1]['next_hw'] = hubd[h]['headword']
            entries.append(hubd[h])
        else:
            print('no text')

    with open(f'roots report {lexicon_name}.csv', 'w', newline='', encoding='utf-8') as fp:
        w = csv.DictWriter(fp, fieldnames=['rid', 'headword', 'start'])
        w.writeheader()
        for x in maybe_roots:
            w.writerow(x)

    bad_refs = []
    for e in entries:
        bads = []
        for ref in re.findall('href="/(?:<sup>)?([^<]*?)["<]', e['text']):
            try:
                if not Ref(ref.replace('_', ' ')).text('he').text:
                    bads.append(ref)
            except InputError:
                bads.append(ref)
        if bads:
            bad_refs.append({'rid': e['rid'], 'headword': e['headword'], 'text': e['text'], 'bad refs': bads})
    with open(f'bad refs {lexicon_name}.csv', 'w', newline='', encoding='utf-8') as fp:
        w = csv.DictWriter(fp, fieldnames=['rid' ,'headword','text', 'bad refs'])
        w.writeheader()
        for x in bad_refs:
            w.writerow(x)

    for e in entries:
        for key in ['sups', 'insert arabic / syriac/ ethiopian', 'no balance of arabic / syriac/ ethiopian', 'samaritan', 'al', 'add', 'no_greek_balance', 'no_heb_balance', 'type', 'kevin']:
            if key in e:
                e.pop(key)
        e['parent_lexicon'] = lexicon_name
        e['quotes'] = []
        e['content'] = {'senses': [{'definition': e.pop('text')}]}
        try:
            LexiconEntry(e).save()
        except InputError: #TEMP
            print('PROBLEM')

    les = LexiconEntrySet({'parent_lexicon': lexicon_name})
    for le in les:
        # le.quotes = make_links(le) #we don't need the quotes field
        le.content['senses'][0]['definition'] = link_v(le.content['senses'][0]['definition'], 'BDB' if lexicon_name=='BDB Dictionary' else 'BDB Aramaic', le.parent_lexicon)
        le.content['senses'][0]['definition'] = rtl(le.content['senses'][0]['definition'])
        le.content['senses'][0]['definition'] = double_links(le.content['senses'][0]['definition'])
        le.content['senses'][0]['definition'] = make_data_ref(le.content['senses'][0]['definition'])
        try:
            delattr(le, 'pre_headword')
        except AttributeError:
            pass
        le.save()

if __name__ == '__main__':
    with open('hub_dict_final.json') as fp:
        hubd = json.load(fp)
    hebrew = {k: v for k, v in hubd.items() if v['kevin'] and 'Aramaic' not in v['kevin']}
    aramaic = {k: v for k, v in hubd.items() if k not in hebrew}
    print('parsing hebrew')
    parse(hebrew, 'BDB Dictionary')
    print('parsing aramaic')
    parse(aramaic, 'BDB Aramaic Dictionary')
