import csv
import re
import django
django.setup()
from linking_utilities.parallel_matcher import ParallelMatcher
from linking_utilities.dibur_hamatchil_matcher import match_ref
from sefaria.model import *

def get_segments_for_range(ref):
    first, last = ref.split('-')
    if first.split()[:-1] == last.split()[:-1]:
        return f"{first}-{last.split()[-1]}"
    # else: #doesnt occur
    #     return [
    #         f"{first}-{Ref(first.split()[:-1]).all_segment_refs()[-1].normal().split()[-1]}",
    #         f'{last.split()[:-1]} 1:1-{last.split()[-1]}'
    #     ]

def strip(string):
    string = re.sub('\([^\)\(]*\)', '', string)
    string = re.sub('\[[^\]\[]*\]', '', string)
    string = re.sub('[^א-ת ]','',string)
    return string

def find_with_dh(text, ref):
    matches = match_ref(Ref(ref).text('he'), [strip(text)], lambda x: strip(x).split())
    return matches['matches'][0]

def find_match(text, ref):
    ref = get_segments_for_range(ref)
    min_words = int(len(text.split()) * 0.8)
    matcher = ParallelMatcher(lambda x: strip(x).split(), all_to_all=False, verbose=False, min_words_in_match=min_words,
                              both_sides_have_min_words=True)
    matches = matcher.match([ref, (row['text'], 'a')], return_obj=True)
    if not matches:
        min_words = int(len(row['text'].split()) * 0.7)
        max_between = int(len(row['text'].split()) * 0.6)
        matcher = ParallelMatcher(lambda x: strip(x).split(), all_to_all=False, verbose=False,
                                  min_words_in_match=min_words, max_words_between=max_between,
                                  both_sides_have_min_words=True)
        matches = matcher.match([ref, (row['text'], 'a')], return_obj=True)
    if not matches:
        min_words = int(len(text.split()) * 0.8)
        max_between = int(len(row['text'].split()) * 1)
        matcher = ParallelMatcher(lambda x: strip(x).split(), all_to_all=False, verbose=False,
                                  min_words_in_match=min_words, max_words_between=max_between,
                                  both_sides_have_min_words=True)
        matches = matcher.match([ref, (row['text'], 'a')], return_obj=True)
    matcher.reset()
    if matches:
        match = max(matches, key=lambda x: x.score)
        mekh, quot = (match.a, match.b) if 'Berakhot' in match.b.ref.normal() else (match.b, match.a)
        return mekh.ref
    words = strip(text).split()
    if len(words) > 14:
        first = ' '.join(words[:7])
        last = ' '.join(words[-7:])
        first = find_with_dh(first, ref)
        last = find_with_dh(last, ref)
        if first and last:
            print(111, text)
            print(strip(first.to(last).text('he').as_string()))
            print(222)
            return first.to(last)
    else:
        return find_with_dh(text, ref)
    # print(ref, text)
    # print(strip(Ref(ref).text('he').as_string()))
    # print(len(strip(text).split()))

y,n,z=0,0,0
with open('/Users/yishaiglasner/Downloads/topic_links_with_text.csv') as fp:
    data = list(csv.DictReader(fp))
    for row in data:
        ref = row['new ref']
        ref = ref.replace('Mekhilta DeRabbi Yishmael', 'Mekhilta DeRabbi Yishmael Beeri')
        row['segment ref'] = ''
        if '-' not in ref:
            row['segment ref'] = ref
        else:
            if row['text']:
                exact = None
                if '...' in row['text']:
                    first, last = row['text'].split('...')
                    first = find_match(first, ref)
                    last = find_match(last, ref)
                    if first and last:
                        try:
                            exact = first.to(last)
                        except:
                            if first.normal() == 'Mekhilta DeRabbi Yishmael Beeri, Tractate Shirah 6:19':
                                exact = last.to(first)
                else:
                    exact = find_match(row['text'], ref)
                if exact:
                    row['segment ref'] = exact.normal()
                    y+=1
                else:
                    n+=1

with open('/Users/yishaiglasner/Downloads/topic_links_segment.csv', 'w') as fp:
    w = csv.DictWriter(fp, fieldnames=list(row))
    w.writeheader()
    for row in data:
        w.writerow(row)
print(y,n,z)
