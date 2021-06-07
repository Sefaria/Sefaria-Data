# encoding=utf-8

import sys
import json


def get_segment_pieces(mapping, segment_number, one_indexed=True):
    if one_indexed:
        segment_number -= 1
    start, end = mapping['realignment'][segment_number]
    text = mapping['match_text'] [start:end]
    indices = mapping['matches'][start:end]

    return indices, text


def load_mapping(tractate, chapter):
    tractate = tractate.title().replace(' ', '_')
    with open(f'code_output/mapping_files/Jerusalem_Talmud_{tractate}/raw_chapter_{chapter}_mapping.json') as fp:
        mapping = json.load(fp)
    return mapping


def get_piece(tractate, chapter, segment):
    mapping = load_mapping(tractate, chapter)
    return get_segment_pieces(mapping, segment)


for i in range(52, 57):
    print(i)
    things, stuff = get_piece('berakhot', 4, i)
    for t, s in zip(things, stuff):
        print(t, s, sep='\n')
    print('\n\n')
    # print(*things, sep='\n')
    # print(*stuff, sep='\n\n')
