import re
import csv
import django
django.setup()
from sefaria.model import *

CSV = []

def strip_cantilation(string):co
    return re.sub('[\u0591-\u05af\u05bd\u05c0]', '', string)

def replace_yidish(string):
    return string.replace('ײ', 'יי').replace('װ', 'וו')

def handle_double_vowel(string):
    global CSV
    double_reg = '(יי|וו)'
    nikkud_reg = '([\u05b0-\u05c7]*)'
    result = ''
    last_index = 0
    iter = re.finditer(f'{double_reg}{nikkud_reg}', string)
    changed = False
    for match in iter:
        letter = match.group(1)[0]
        nikkud = match.group(2)
        start, end = match.span()
        result += string[last_index:start]
        if nikkud and nikkud not in '\u05bc\u05ba\u05b9':
            result += f'{letter}{nikkud}{letter}'
            changed = True
        else:
            result += match.group()
        last_index = end
    if changed:
        CSV[-1]['after nikkud'] = result + string[last_index:]

def remove_maqaf(string):
    return string.replace('־', ' ')

def remove_colons(string, segment_number):
    string = string.replace('׃', ':')
    string = string.replace(':\.', '.')
    if segment_number != 1:
        string = re.sub('(?<!הלכה):', '.', string)
    return string

def remove_whitespaces(string):
    return ' '.join(string.split())

def handle_dot_above(string):
    global CSV
    if '\u0307' in string:
        CSV[-1]['has dots above'] = 'TRUE'

def do_all(string, tref, *args):
    global CSV
    CSV.append({'ref': tref, 'old': string})
    string = strip_cantilation(string)
    string = replace_yidish(string)
    string = remove_maqaf(string)
    string = remove_colons(string, Ref(tref).sections[-1])
    string = remove_whitespaces(string)
    CSV[-1]['new'] = string
    handle_double_vowel(string)
    handle_dot_above(string)

def change_text_recursive(text_obj, action):
    if isinstance(text_obj, dict):
        for key in text_obj:
            change_text_recursive(text_obj[key], action)
    else:  # list
        for e, element in enumerate(text_obj):
            if isinstance(element, list):
                change_text_recursive(element, action)
            else:
                text_obj[e] = action(element, e+1)

def change_version_text(version, action):
    change_text_recursive(version.chapter, action)
    ver.save()

if __name__ == '__main__':
    for index in library.get_indexes_in_corpus('Yerushalmi'):
        ver = Version().load({'title': index, 'versionTitle': 'The Jerusalem Talmud, edition by Heinrich W. Guggenheimer. Berlin, De Gruyter, 1999-2015'})
        if not ver:
            print('no version:', index)
        # change_version_text(ver, do_all)
        ver.walk_thru_contents(do_all)
    with open('yerushalmi.csv', 'w') as fp:
        w = csv.DictWriter(fp, fieldnames=['ref', 'old', 'new', 'after nikkud', 'has dots above'])
        w.writeheader()
        for row in CSV:
            w.writerow(row)
