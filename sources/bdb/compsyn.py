import json
import os
import re
from hub_al import is_hebrew
import django
django.setup()
from sefaria.model import *
import csv
from synopsys import get_kev_text, get_al_text, get_hub_text

def split_by_block(string, block, neutral=[]):
    in_block = ord(string[0]) in block
    subs = [['', in_block]]
    for letter in string:
        if ord(letter) in block:
            in_block = True
        elif letter not in neutral:
            in_block = False
        if in_block == subs[-1][1]:
            subs[-1][0] += letter
        else:
            subs.append([letter, ord(letter) in block])
    return subs

def has_char_from_block(string, block):
    return any(ord(l) in block for l in string)

if __name__ == '__main__':
    B,S,M,SA,MA=0,0,0,0,0
    BP,BN = 0,0
    pa,amp=set(),set()
    output = []
    with open('hub_dict_new.json') as fp:
        hub_dict = json.load(fp)
    heb_block = range(1424, 1525)
    folder = 'new_synopsys'
    for file in os.listdir(folder):
        print(file)
        with open(f'{folder}/{file}') as fp:
            data = json.load(fp)
        better_balance = 0
        newdata = []
        better_heb_subs = []
        kev_heb_subs = []
        if len(data['witnesses']) == 3:
            better = 2
        else:
            better = 0

        # hebrew
        for word in data['table']:
            for x in word:
                for y in x:
                    y['t'] = re.sub(r'\\[xu]\d*', '', y['t']).replace('\\', '').replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<')
            word = [' '.join([y['t'] for y in x]) for x in word]
            all_words = ''.join(word)
            if re.search(r'[^A-Za-z …\.,\<\>\(\)\[\]\+\d\?\!&:;\-\'’׳"\|\*‖–§—‡†√=\\ḤÈîöüäâé]', all_words):
                if better == 2:
                    word[2] = re.sub('(י)-(הוה)', r'\1\2', word[2])
                subs = [split_by_block(x, heb_block, '()[]$') if x else [] for x in word]
                lens = [len([y for y in x if y[1]]) for x in subs]
                if lens[1] != lens[better]:
                    better_balance += lens[1] - lens[better]
                better_heb_subs += [x[0] for x in subs[better] if x[1]]
                kev_heb_subs += [x[0] for x in subs[1] if x[1]]
                for sub in kev_heb_subs:
                    if not better_heb_subs:
                        continue
                    if 'פ' in sub and better == 0: #no al hatorah
                        for pe in [m.start() for m in re.finditer('פ', sub)]:
                            stripped_index = len(re.sub('[^א-ת]', '', sub[:pe]))
                            better_stripped = re.sub('[^א-ת]', '', better_heb_subs[0])
                            print(subs, sub, better_heb_subs, pe, better_stripped, stripped_index)
                            try:
                                if better_stripped[stripped_index] in ['מ', 'פ']:
                                    if better_stripped[stripped_index] == 'מ':
                                        mem_index = better_stripped[:stripped_index + 1].count('מ') - 1
                                        index = [m.start() for m in re.finditer('מ', better_heb_subs[0])][mem_index]
                                        better_heb_subs[0] = better_heb_subs[0][:index] + 'פ' + better_heb_subs[0][index+1:]
                                else:
                                    print('peh in kevin has no mem in hub', subs, sub, better_heb_subs, pe, better_stripped, index)
                                print(222,sub, better_heb_subs[0])
                            except IndexError:
                                print('index error', subs, sub, better_heb_subs)
                    word[1] = word[1].replace(sub, better_heb_subs.pop(0))
                    kev_heb_subs.pop(0)
                newdata.append(word)

            else:
                newdata.append(word)
        print(' '.join([x[1] for x in newdata]))
        if better_balance != 0:
            hub_dict[file.split('.')[0]]['no_heb_balance'] = True
            print('no hebrew balance')

        # sup
        kev_sup, hub_sup = [], []
        all_sups = []
        sup = False
        kev_words = []
        # for word in data['table']:
        #    newdata.append([' '.join([y['t'] for y in x]) for x in word])
        for w, word in enumerate(newdata):
            if '<sup>' in word[0]:
                hub_start = None
                sup = True
                sup_start = None
                if ':' not in word[1] and '<sup>' not in word[1]:
                    for i in range(w-1, -1, -1):
                        if newdata[i][0]:
                            sup_start = i
                            break
                if sup_start == None:
                    sup_start = w
                hub_sup = []
            if sup:
                hub_sup.append(word[0])
                if hub_start == None and word[0] != '<sup>':
                    hub_start = w

            if '</sup>' in word[0]:
                sup = False
                replace = True
                change = False
                sup_end = w
                hub = re.sub('</?sup>', '', ' '.join([h for h in hub_sup if h])).strip().replace('on the passage', 'ad loc.').replace('critical note', 'crit. n.')
                if hub == 'L' or not hub:
                    continue
                kev_sup = [x[1] for x in newdata[sup_start:w+1]]

                beginning = kev_sup[:hub_start - sup_start + 1]
                for b, begin in enumerate(beginning):
                    if ':' in begin:
                        pre_sup, kev_sup[b] = beginning[b].split(':', 1)
                        kev_sup = kev_sup[b:]
                        sup_start += b
                        break
                    else:
                        pre_sup = None

                for x in kev_sup[:]:
                    if x:
                        break
                    else:
                        sup_start += 1
                        kev_sup.pop(0)
                for x in kev_sup[::-1]:
                    if x:
                        break
                    else:
                        sup_end -= 1
                        kev_sup.pop(-1)


                kev_sup = [k.replace('\)', ')') for k in kev_sup]
                kev = ' '.join([k for k in kev_sup if k])
                if kev_sup:
                    while kev_sup and re.search('^<[^a>][^>]*?>', kev_sup[0]):
                        kev_sup[0] = re.sub('^<[^>]*?>', '', kev_sup[0]).strip()
                        if not kev_sup[0]:
                            kev_sup.pop(0)
                            sup_start += 1
                    while kev_sup and re.search('<[^>]*?[^a]>$', kev_sup[-1]):
                        kev_sup[-1] = re.sub('<[^>]*?[^a]>$', '', kev_sup[-1]).strip()
                        if not kev_sup[-1]:
                            kev_sup.pop(-1)
                            sup_end -= 1
                    if kev_sup:
                        if ':' in kev_sup[0]:
                            kev_sup[0] = kev_sup[0].split(':', 1)[1]
                            if not kev_sup[0]:
                                kev_sup.pop(0)
                                sup_start += 1
                        if kev_sup and '—' in kev_sup[-1]:
                            kev_sup[-1] = kev_sup[-1].split('—')[0]
                            if not kev_sup[-1]:
                                kev_sup.pop(-1)
                                sup_end -= 1
                        elif kev_sup and kev_sup[-1] and kev_sup[-1] != '</sup>' and kev_sup[-1][-1] != hub[-1]:
                            for k, keword in enumerate(newdata[sup_end + 1:]):
                                if keword[1]:
                                    if '—' in keword[1].split()[0]:
                                        to_add = keword[1].split('—')[0]
                                        if to_add and hub.split()[-1] in to_add:
                                            kev_sup += ['' for _ in range(k)]
                                            kev_sup.append(to_add)
                                            sup_end += k + 1
                                    break
                            kev = ' '.join(kev_sup).strip()
                        if kev_sup:
                            if ')' in kev_sup[-1] and kev.count(')') > kev.count('('):
                                kev_sup[-1] = kev_sup[-1].split(')')[0]
                            if ']' in kev_sup[-1] and kev.count(']') > kev.count('[(]'):
                                kev_sup[-1] = kev_sup[-1].split(']')[0]
                            if '<a' in kev_sup[-1]:
                                kev_sup[-1] = kev_sup[-1].split('<a')[0]
                            if not kev_sup[-1]:
                                kev_sup.pop(-1)
                                sup_end -= 1
                    kev = ' '.join(kev_sup).strip()
                    while kev_sup and re.search('[,;—]$', kev_sup[-1]):
                        kev_sup[-1] = re.sub('[,;—]$', '', kev_sup[-1])
                        if not kev_sup[-1]:
                            kev_sup.pop(-1)
                            sup_end -= 1
                if kev.startswith('<a ') and '</a>' not in kev:
                    for k, keword in enumerate(newdata[sup_end + 1:]):
                        sup_end += 1
                        if '</a>' in keword[1]:
                            kev_sup.append(keword[1].split('</a>')[0] + '</a>')
                            break
                        else:
                            kev_sup.append(keword[1])
                        if len([k for k in kev_sup[-k-1:] if k]) > 3:
                            print(11111, 'no ending tag a', kev_sup)

                kev = ' '.join(kev_sup).strip()
                if not kev or (not re.search('<a.*?</a>', kev) and (kev[0] != hub[0] or kev[-1] != hub[-1])):
                    if ';' in kev:
                        for k, ks in enumerate(kev_sup):
                            if ';' in ks:
                                sup_start += k
                                kev_sup[k] = kev_sup[k].split(';')[0].strip()
                                kev_sup = kev_sup[k:]
                                if not kev_sup[0]:
                                    kev_sup.pop(0)
                                    sup_start += 1
                                break
                    if kev.startswith('href='):
                        for i in range(sup_start - 1, -1, -1):
                            if newdata[i][1]:
                                if '<a' in newdata[i][1]:
                                    kev_sup = ['<a'] + ['' for _ in range(sup_start-i-1)] + kev_sup
                                    sup_start = i
                                else:
                                    print('no starting a tag', kev)
                                break
                    kev = ' '.join(kev_sup)
                    if kev.startswith('<a ') and '</a>' not in kev:
                        for k, keword in enumerate(newdata[sup_end + 1:]):
                            sup_end += 1
                            if '</a>' in keword[1]:
                                kev_sup.append(keword[1].split('</a>')[0] + '</a>')
                                break
                            else:
                                kev_sup.append(keword[1])
                            if len([k for k in kev_sup[-k - 1:] if k]) > 3:
                                print(11111, 'no ending tag a', kev_sup)

                    if 'Ar. ' in kev:
                        for k, ks in enumerate(kev_sup):
                            if 'Ar.' in ks:
                                kev_sup[k] = kev_sup[k].split('Ar.')[0].strip()
                                kev_sup = kev_sup[:k+1]
                                if not kev_sup[-1]:
                                    kev_sup.pop(-1)
                                sup_end = sup_start + len(kev_sup) - 1
                                break
                    kev = ' '.join(kev_sup).strip()
                    for x in kev_sup[::-1]:
                        if x:
                            break
                        else:
                            sup_end -= 1
                            kev_sup.pop(-1)
                    if kev.endswith('.') and kev[-2] == hub[-1]:
                        if not kev_sup[-1].endswith('.'):
                            print('. in the end but not in the last word', kev, kev_sup)
                        kev_sup[-1] = kev_sup[-1][:-1]
                    if kev and hub.count(' ') > 1 and kev.split()[-1] == hub.split()[-2]:
                        for k, keword in enumerate(newdata[sup_end + 1:]):
                            if keword[1]:
                                if hub.split()[-1] in keword[1]:
                                    kev_sup += ['' for _ in range(k)] + [hub.split()[-1]]
                                    sup_end += k + 1
                                break
                    if not re.search('<a.*?</a>', ' '.join(kev_sup)):
                        kev_sup = [k.strip() for k in kev_sup]
                        kev_to_search = ' 话 '.join(kev_sup).strip()
                        hub_to_serach = '[话 ]+'.join([re.escape(h) for h in hub.split()])
                        if re.search(f'(?:^|\\b){hub_to_serach}(?:$|\\b|\))', kev) and '</a>' not in kev:
                            temp, temp2 = re.findall(f'^(.*?)(?:^|\\b){hub_to_serach}(?:$|\\b|\))(.*?)$', kev_to_search)[0]
                            cut_start, cut_end = temp.count('话'), temp2.count('话')
                            sup_start += cut_start
                            sup_end -= cut_end
                            kev_sup = kev_sup[cut_start:-cut_end if cut_end!=0 else None]
                            kev_sup[-1] = hub.split()[-1]
                            kev = ' '.join(kev_sup).strip()
                        else:
                            if kev.count(' ') > 1 and kev.split()[1] == hub.split()[0]:
                                kev_sup = kev_sup[1:]
                                sup_start += 1
                            if kev.count(' ') > 1 and kev.split()[-2] == hub.split()[-1]:
                                kev_sup = kev_sup[:-1]
                                sup_end -= 1
                kev = ' '.join([k.strip() for k in kev_sup if k])
                if '<sup>' in kev and '</sup>' in kev:
                    kev = re.sub('<sup> *:?(.*?)</sup>', r'\1', kev)
                    replace = False
                if re.search('<a.*?</a>', kev) and len(hub) < 5 and any(b in kev for b in ['Isaiah', 'Zechariah']) and hub!='Hpt':
                    change = True
                all_sups.append({'start': sup_start, 'end': sup_end, 'replace': replace, 'change': change, 'kev': kev, 'hub': hub})
                if not kev or (not re.search('<a.*?</a>', kev) and (kev[0] != hub[0] or kev[-1] != hub[-1])):
                    all_sups[-1]['match'] = False
                else:
                    all_sups[-1]['match'] = True

        nex = None
        for s, sup in enumerate(all_sups[::-1]):
            if not sup['replace']:
                continue
            if sup['match']:
                first, last = sup['kev'].split()[0], sup['kev'].split()[-1]
                for word in newdata[sup['start']:sup['end']+1]:
                    if word[1]:
                        if first in word[1]:
                            if ':' not in word[1]:
                                for w in newdata[sup['start']-1: -1: -1]:
                                    if w[1]:
                                        w[1] = re.sub(':$', '', w[1])
                                        break
                            s_word = word
                        else:
                            sup['match'] = False
                        break
                if sup['match']:
                    for word in reversed(newdata[sup['start']:sup['end'] + 1]):
                        if word[1]:
                            if last in word[1]:
                                e_word = word
                                nex = sup['start']
                                sup['match'] = True
                            else:
                                sup['match'] = 'just first'
                            break

            indexes = []
            for su in all_sups:
                if su['match'] != False:
                    indexes.append(su['start'])
                if su['match'] == True:
                    indexes.append(su['end'])
            if sup['match'] != True:
                first, last = sup['hub'].split()[0], sup['hub'].split()[-1]
                if nex:
                    prevs = [ind for ind in indexes if prev < ind]
                    prev = prevs[-1] + 1 if prevs else 0
                else:
                    prev = max(indexes) if indexes else 0
                options = [x[1] for x in newdata[prev:nex]]
                if sup['match'] == False:
                    starts = [w for w, word in enumerate(options) if f':{first}' in word]
                    if file in ['5934_1.json', '8530_0.json']:
                        print(prev,nex, options)
                        print(first,starts)
                    if len(starts) == 1:
                        prev = prev + starts[0] + 1
                        s_word = newdata[prev-1]
                        sup['match'] = 'just first'
                    elif len(starts) == 0:
                        starts = [w for w, word in enumerate(options) if f'{first}' in word]
                        if len(starts) == 1:
                            prev = prev + starts[0] + 1
                            s_word = newdata[prev-1]
                            sup['match'] = 'just first'
                if sup['match'] == 'just first':
                    if len(sup['hub'].split()) == 1:
                        e_word = s_word
                        sup['match'] = True
                        nex = prev
                    else:
                        options = [x[1] for x in newdata[prev:nex]]
                        ends = [w for w, word in enumerate(options) if f'{last}' in word]
                        if file in ['5934_1.json', '8530_0.json']:
                            print(prev,nex, options)
                            print(last,ends)
                        if len(ends) == 1:
                            e_word = newdata[prev + ends[0]]
                            sup['match'] = True
                            nex = prev
            if sup['match'] != True:
                if 'sups' in hub_dict:
                    hub_dict[file.split('.')[0]]['sups'].append(sup['hub'])
                else:
                    hub_dict[file.split('.')[0]]['sups'] = [sup['hub']]
            else:
                e_word[1] = re.sub(f' *{re.escape(last)}', f'{last}</sup>', e_word[1])
                s_word[1] = re.sub(f':? *{re.escape(first)}', f'<sup>{first}', s_word[1])
                if sup['change']:
                    dele = False
                    for word in newdata:
                        if word is s_word:
                            word[1] = re.sub(f'<sup>{re.escape(first)}', f'<sup>{sup["hub"]}', word[1])
                            dele = True
                        elif word is e_word:
                            word[1] = re.sub(f'{re.escape(last)}</sup>', f'</sup>', word[1])
                            break
                        elif dele:
                            word[1] = ''

        sources = [[''] for _ in range(3)]
        for i, source in zip(range(len(data['witnesses'])), sources):
            source[0] = ' '.join([n[i] for n in newdata if n])
            source[0] = re.sub(' +', ' ', source[0])

        sources[1][0] = sources[1][0].replace('Is: <sup>2 </sup>, Is: <sup>3 </sup>', 'Is<sup>2,3</sup>')

        #greek
        greek_ranges = [[769, 773, 8710], range(771, 772), range(775, 805), range(806, 818), range(819, 1024), range(7936, 8205), range(8241, 8304), range(65856, 65936), range(118784, 119040)]
        greek_block = [x for y in greek_ranges for x in list(y)]
        greek_reg = f"[{''.join(chr(x) for x in greek_block)}]"
        neutral = ' ̆.̥,·ʼPs̲AĪ̂̅'
        kev_greeks = split_by_block(sources[1][0], greek_block, neutral) #space, comma, period, ·
        better_greeks = split_by_block(sources[better][0], greek_block, neutral)
        kev_greeks, better_greeks = [x[0] for x in kev_greeks if x[1]], [x[0] for x in better_greeks if x[1]]
        if len(kev_greeks) != len(better_greeks):
            hub_dict[file.split('.')[0]]['no_greek_balance'] = True
            print('no greek balance', kev_greeks, better_greeks)
        else:
            for kg, bg in zip(kev_greeks, better_greeks):
                sources[1][0] = re.sub(f'\.?[AI]?{kg}', bg, sources[1][0], 1)
        sources[1][0] = re.sub(r' ([\)\.,])', r'\1', sources[1][0])
        sources[1][0] = re.sub(r'\( ', r'(', sources[1][0])
        sources[1][0] = re.sub(r'([Α-ϡ]) (\.,)', r'\1\2', sources[1][0])
        sources[1][0] = re.sub(r'([Α-ϡ]) ([\(\[][Α-ϡ])', r'\1\2', sources[1][0])
        sources[1][0] = re.sub(r'([Α-ϡ][\)\]]) ([Α-ϡ])', r'\1\2', sources[1][0])

        #arabic/persian ethipoian syriac
        arabic_block = range(1536, 1792)
        ethipian_block = range(4608, 4989)
        syr_block = range(1792, 1872)
        semirics_blocs = [x for b in [arabic_block, syr_block, ethipian_block] for x in b]
        better_sem = split_by_block(sources[better][0], semirics_blocs, ' ')
        better_sem = [x[0] for x in better_sem if x[1]]
        kev_sem = re.findall('ግዕዝ|اَلْعَرَبِيَّةُ|ܠܫܢܐ|فارسی', sources[1][0])
        if kev_sem and better == 0:
            hub_dict[file.split('.')[0]]['insert arabic / syriac/ ethiopian'] = True
            sources[1][0] = re.sub('ግዕዝ|اَلْعَرَبِيَّةُ|ܠܫܢܐ|فارسی', 'SEMITIC', sources[1][0])
        elif better == 2:
            if len(better_sem) != len(kev_sem):
                print('no semitic balance')
                hub_dict[file.split('.')[0]]['no balance of arabic / syriac/ ethiopian'] = True
                sources[1][0] = re.sub('ግዕዝ|اَلْعَرَبِيَّةُ|ܠܫܢܐ|فارسی', 'SEMITIC', sources[1][0])
            else:
                for b in better_sem:
                    sources[1][0] = re.sub('ግዕዝ|اَلْعَرَبِيَّةُ|ܠܫܢܐ|فارسی', b, sources[1][0], 1)
        if 'INSERT-SAMARITAN' in sources[1][0]:
            hub_dict[file.split('.')[0]]['samaritan'] = True

        #gothic
        for pair in [('LXX', '𝔊'), ('SYRVER', '𝔖'), ('VUL', '𝔙'), ('TARGUM', '𝔗'), ('HCT', 'ℌ')]:
            sources[1][0] = sources[1][0].replace(*pair)

        sources[1][0] = re.sub('(?<!href="/)Psalm', 'ψ', sources[1][0])
        sources[1][0] = re.sub(':? <su', '<su', sources[1][0])
        sources[1][0] = re.sub(' ([\.,;\)\]]|</)', r'\1', sources[1][0])
        sources[1][0] = re.sub('([\[\(]|<[^/]*?>) ', r'\1', sources[1][0])
        sources[1][0] = re.sub(r'(</?sup>)\1', r'\1', sources[1][0])

        hub_dict[file.split('.')[0]]['text'] = sources[1][0]

    with open('hub_dict_final.json', 'w') as fp:
        json.dump(hub_dict, fp)

    problems = {}
    for hub in hub_dict:
        v = hub_dict[hub]
        problems[hub] = {'problems': []}
        problem = problems[hub]
        if not hub_dict[hub]['kevin']:
            problem['problems'] = 'we missing, addenda?'
            continue
        if f'{hub}.json' not in os.listdir(folder):
            problem['problems'].append('no synopsis')
            continue
        if v['type'] == 'new from add' or 'add' in v:
            problem['problems'].append('addenda')
        if 'no_heb_balance' in v:
            problem['problems'].append('no hebrew balance')
        if 'samaritan' in v:
            problem['problems'].append('samaritan')
        if 'no balance of arabic / syriac/ ethiopian' in v:
            problem['problems'].append('no balance of arabic / syriac/ ethiopian')
        if 'insert arabic / syriac/ ethiopian' in v:
            problem['problems'].append('insert arabic / syriac/ ethiopian')
        if 'no_greek_balance' in hub_dict[hub]:
            problem['problems'].append('no greek balance')
        if 'sups' in v:
            problem['problems'].append(f'superscriptss to add: {hub_dict[hub]["sups"]}')
        problem['problems'] = '\n'.join(problem['problems'])
    for problem in problems:
        if not problems[problem]['problems']:
            print(hub_dict[problem]['text'])
            continue
        else:
            problems[problem].update({'id': hub_dict[problem]['kevin'] if hub_dict[problem]['kevin'] else problem,
                                      'text': hub_dict[problem]['text'] if 'text' in hub_dict[problem] else get_kev_text(hub_dict[problem]['kevin']) if hub_dict[problem]['kevin'] else '',
                                     'al hatorah text': get_al_text(hub_dict[problem]['al']) if 'al' in hub_dict[problem] and hub_dict[problem]['al'] else '',
                                      'al hatorah link': f'https://mg.alhatorah.org/Dictionary/{hub_dict[problem]["al"].split("_")[0]}' if 'al' in hub_dict[problem] and hub_dict[problem]['al'] else '',
                                      'biblehub text': ' '.join(get_hub_text(problem).split()),
                                      'biblehub link': f'https://biblehub.com/bdb/{problem.split("_")[0]}.htm'
                                      })
            if not hub_dict[problem]['kevin']:
                problems[problem]['text'] = problems[problem]['text'].replace('Psalm Psalm', 'Psalms')
                problems[problem]['text'] = re.sub(':? <sup', '<sup', problems[problem]['text'])
                problems[problem]['text'] = re.sub(' ([^\.,;\)\]]|</)', r'\1', problems[problem]['text'])
                problems[problem]['text'] = re.sub('([\[\(]|<[^/]) ', r'\1', problems[problem]['text'])
                problems[problem]['text'] = problems[problem]['text'].replace('ₑ', 'ᵉ')

    with open('kev_dict_new.json') as fp:
        kevd = json.load(fp)
    for k in kevd:
        if not kevd[k]['hub']:
            problems[k] = {'id': k, 'text': get_kev_text(k), 'problems': 'no other sources'}

    with open('problems.csv', 'w', newline='', encoding='utf-8') as fp:
        w = csv.DictWriter(fp, fieldnames=['id', 'text', 'al hatorah text', 'al hatorah link', 'biblehub text', 'biblehub link', 'problems'])
        w.writeheader()
        for p in problems:
            if not problems[p]['problems']:
                continue
            w.writerow(problems[p])

        #sup
    #     hub_sups = re.findall('<sup>(.*?)</sup>', sources[0][0])
    #     kev_sups = re.findall(r'[^\d]:[^ <——]|: <a|<sup>.*?</sup>', sources[1][0])
    #     if len(hub_sups) == len(kev_sups):
    #         B+=1
    #         for h, k in zip(hub_sups, kev_sups):
    #             h = h.strip()
    #             if 'sup' in k:
    #                 if h and k and h[0] == k[5]:
    #                     BP+=1
    #                 else:
    #                     BN+1
    #             elif h and h[0] == k[-1]:
    #                 BP += 1
    #             elif k == ': <a':
    #                 try:
    #                     Ref(h)
    #                     BP+=1
    #                 except:
    #                     BN+=1
    #                     print(11111, k, h)
    #             else:
    #                 BN+=1
    #                 print(22222, k, h)
    #     elif len(hub_sups) < len(kev_sups):
    #         S+=1
    #         SA += len(kev_sups) - len(hub_sups)
    #     else:
    #         M+=1
    #         MA += len(hub_sups) - len(kev_sups)
    # print(B,BP,BN)
    # print(S,SA/S)
    # print(M,MA/M)
