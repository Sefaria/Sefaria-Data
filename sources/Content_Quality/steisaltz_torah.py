import csv
import re
from itertools import combinations

import django
django.setup()
from sefaria.model import *

def get_parashot_refs():
    for chumash in library.get_indexes_in_category('Torah'):
        chumash = library.get_index(chumash)
        for node in chumash.alt_structs['Parasha']['nodes']:
            yield node['wholeRef'], node['sharedTitle']

def remove_nums():
    global text
    ranges_to_remove = []
    for occur in re.finditer(r' \d+ ', f' {text} '):
        num = int(occur.group())
        if parasha_name == 'Bereshit':
            to_remove = False
        elif parasha_name == 'Tazria':
            to_remove = num != 8
        elif parasha_name == 'Noach':
            to_remove = num != 205
        else:
            to_remove = nums_to_remove and num == nums_to_remove[0]
            if to_remove:
                nums_to_remove.pop(0)
            elif parasha_name == 'Emor':
                to_remove = num > 99
        if to_remove:
            ranges_to_remove.append(range(occur.start(), occur.end()-1))
    text = ''.join([char for c, char in enumerate(text) if all([c not in r for r in ranges_to_remove])])

def strip_spaces():
    global text
    text = re.sub(' +', ' ', text)
    text = re.sub(' ([\.,?!;:\]\)])', r'\1', text)
    text = re.sub('([\(\[]) ', r'\1', text)

def get_longest_ordered_sublist(num_list):
    for length in range(len(num_list), 5, -1):
        for comb in combinations(num_list, length):
            if all(comb[i] < comb[i+1] for i in range(length-1)):
                return list(comb)


changed = []
for parasha_ref, parasha_name in get_parashot_refs():
    print(parasha_name)

    nums = []
    for segment in Ref(f'Steinsaltz on {parasha_ref}').all_segment_refs():
        nums += [int(n) for n in re.findall(r' \d+ ', f' {segment.text("en").text} ')]

    nums_to_remove = get_longest_ordered_sublist(nums)
    for segment in Ref(f'Steinsaltz on {parasha_ref}').all_segment_refs():
        tc = segment.text('en', 'The Steinsaltz Tanakh - English')
        text = tc.text
        remove_nums()
        strip_spaces()
        text = re.sub(r'b>\d+', 'b>', text)
        changed.append({'ref': segment.normal(), 'old': tc.text, 'new': text})
        if text != tc.text:
            tc.text = text
            tc.save()

with open('/Users/yishaiglasner/Downloads/steinsaltz.csv', 'w') as fp:
    w = csv.DictWriter(fp, fieldnames=['ref','old','new'])
    w.writeheader()
    for row in changed:
        w.writerow(row)
