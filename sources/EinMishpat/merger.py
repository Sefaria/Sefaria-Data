# -*- coding: utf-8 -*-
from __builtin__ import enumerate

from sefaria.model import *
import codecs
import regex as re
from ein_parser import fromCSV, toCSV, parse_em
import unicodecsv as csv
from collections import OrderedDict

matching_file = codecs.open(u'match_file', 'w', encoding='utf-8')
match_list = []
# a function that gives us a rough cut down of the rows on the page
def duplicate_rows_in_file(file2open, newfile):
    allrows = []
    with open(u'{}.csv'.format(newfile), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, [u'txt file line', u'Perek running counter',u'page running counter',
                                u'Perek aprx', u'Page aprx', u'Rambam', u'Semag', u'Tur Shulchan Arukh', u'original', u'problem']) #fieldnames = obj_list[0].keys())
        writer.writeheader()
        with open(file2open, 'r') as csvfile:
            file_reader = csv.DictReader(csvfile)
            for i, row in enumerate(file_reader):
                rambam_len = times(u'Mishneh', u'Rambam', row)
                semag_len = times(u'Sefer Mitzvot Gadol', u'Semag', row)
                tur_len = times(u'Tur,',u'Tur Shulchan Arukh', row)
                sa_len = times(u'Shulchan Arukh,', u'Tur Shulchan Arukh', row)
                largest = max(rambam_len, semag_len, tur_len, sa_len)
                l = 1
                for x in range(largest):
                    writer.writerows([row])
                    l += 1
                    allrows.append(row)
    return allrows
# helper function for the obove

def times(pattern, key, row):
    found = re.findall(pattern, row[key])
    if found:
        times_apper = len(found)
    else:
        times_apper = 0  # len(row[u'Rambam'])
    return times_apper

def old2koren(filename):
    mapping_dict = {}
    with open(filename, 'r') as csvfile:
        file_reader = csv.DictReader(csvfile)
        for line in file_reader:
            # line['old'] = re.sub(':', '.', line['old'])
            line['old'] = re.sub(u'(.+?)(\d{1,2}[a|b]):(\d\d?)', ur'\2.\3', line['old'])
            mapping_dict[line['old']] = line['new']
    return mapping_dict


# given this we should create sets of the Refs given and check for equality
def equal_sets(all_rows = False, oldworkfilename = False):
    #[u'daf',u'Ramabam	Semag',u'Shulchan Arukh', u'Tur'])
    with open(oldworkfilename, 'rb') as tsvin:
        tsvin = csv.DictReader(tsvin, delimiter='\t')
        # file_reader = csv.DictReader(csvfile)
        # get the set from the row of tsv
        for i, row in enumerate(tsvin):
            # row is a dictonary
            row.update((k, re.sub(u'_', u' ', row[k])) for k in row.keys())
            ram_them = row[u'Rambam_f'] # re.sub(u'_', u' ', row[u'Rambam_f'])
            ram_us = re.sub(u' (\d{1,3}):(\d{1,3})', ur'.\1.\2', all_rows[i-1][u'Rambam'])
            sa_them = row[u'Shulchan_Arukh_f']
            sa_us = all_rows[i-1][u'Tur Shulchan Arukh']
            print i, all_rows[i-1][u'original']
            print i, ram_them , ram_us
            # print i, sa_them , sa_us
            if ram_them not in ram_us:
                print ram_them not in ram_us
                # print i, all_rows[i - 1][u'original']
                print i, sa_them, sa_us
# print i, set(row[u'Rambam_f']) == all_rows[i][u'Rambam']


def collapse(comantator, column, datafile, mappingfile):
    mapp = old2koren(mappingfile)
    """
    collapse the refs to a dictonary, key: the collapsed column (segments in this case)
    value: list of refs (containing all the comantary Refs)
    each
    returns a list, bit can use dict.update(list of pairs) to geta dictonary
    """
    with open(datafile, 'rb') as tsvin:
        tsvin = csv.DictReader(tsvin, delimiter='\t')
        segments_dict = OrderedDict()
        prev = None
        for i, row in enumerate(tsvin):
            try:
                if not row[column]:
                    continue
                elif mapp[row[column]] == prev:
                    if [row[com] for com in comantator]:# and [row[com] not in segment for com in comantator]:
                        segment.extend([ls for ls in [convert_display(row[com]) for com in comantator]])
                else:
                    segment = []
                    segment.extend([ls for ls in [convert_display(row[com]) for com in comantator]])
                segments_dict[mapp[row[column]]] = segment
                prev = mapp[row[column]]
            except KeyError:
                print 'on key ' + row[com] + 'there was a problem'
        print segments_dict
        return segments_dict

def get_letters(file2open, comantator):
    """
    letter_dict = a dictionary
    key: file row number
    value: tuple (little letter, [commentator list])
    """
    if isinstance(file2open, unicode):
        # letter_dict = OrderedDict()
        with open(file2open, 'r') as csvfile:
            file_reader = csv.DictReader(csvfile)
            letter_dict = make_dict(file_reader, comantator)
    elif isinstance(file2open, list):
        file_reader = file2open
        letter_dict = make_dict(file_reader, comantator)
        # if row[u'Page aprx'] == current_page:
        #     letter_dict[row[u'page running counter']] = row[comantator]
        # else:
        #     letter_page_list.append(letter_dict)
        #     letter_dict = OrderedDict()
        # current_page = row[u'Page aprx']
    return letter_dict

def make_dict(row_lst, comantators):
    """
    row_lst is a list of rows
    comantators is a list of comantators
    """
    letter_dict = OrderedDict()
    for i, row in enumerate(row_lst):
        letter_dict[i] = (row[u'page running counter'], [row[com] for com in comantators])
    return letter_dict


def convert_display(link_str):
    link_str = re.sub(u'sefaria.org/', '', link_str)
    link_str = re.sub(u'_', ' ', link_str)
    link_str = re.sub(u'\.(\d{1,3})\.?(\d{0,3})', ur' \1:\2', link_str)
    if not re.search(u":\d",link_str):
        link_str = re.sub(u":", '', link_str)
    # if re.search(u":\D",link_str):
    #     link_str = re.sub(u":\D", '', link_str)
    return link_str


def placing(collapsed_segments, letter_dict):
    """find the colesest values and match the key accordingly
    note that the placingi needs to be done per page (so the little letters won't overlap in the dictionary
    need to devide the keys to pages"""

    done = object()
    seg_it = iter(collapsed_segments)
    letter_it = iter(letter_dict)
    segment = next(seg_it, done)
    letter = next(letter_it, done)
    while segment is not done:
        while letter is not done and segment is not done:
            w = weight(collapsed_segments[segment], letter_dict[letter][1])
            print w
            if w > 0:
            # if set(letter_dict[letter][1]).issubset(set(collapsed_segments[segment])):# or set(letter_dict[letter][1]).issuperset(set(collapsed_segments[segment])):
                write_match(segment, letter_dict[letter][0])
                letter = next(letter_it, done)
                break
            # print False, segment,collapsed_segments[segment], letter_dict[letter][0], letter_dict[letter][1]
            segment = next(seg_it, done)

def weight(segment, letter):
    # if not segment or not letter:
    #     return 0
    # str_seg = set(''.join(segment))
    # str_lett = set(''.join(letter))
    letter = [lt for subls in letter if subls for lt in subls]
    if segment and letter:
        return 1.0*len(set(letter).intersection(set(segment)))/(min(len(segment), len(letter)))
    # if str_lett and str_seg:
    #     return 1.0*len(set(''.join(letter)).intersection(set(''.join(segment)))) / (min(len(''.join(segment)), len(''.join(letter))))
    return 0


def write_match(segment, letter):
    matching_file.write(segment +letter)
    match_list.append((segment, letter))
    print segment, letter

def exctractRefs(datafile, col,filetype):
    refs = set()
    if filetype == u'tsv':
        with open(datafile, 'rb') as tsvin:
            tsvin = csv.DictReader(tsvin, delimiter='\t')
            for i, row in enumerate(tsvin):
                try:
                    ref = convert_display(row[col])
                    refs.add(ref)
                except:
                    continue
    if filetype == u'csv':
        with open(datafile, 'r') as csvfile:
            file_reader = csv.DictReader(csvfile)
            for i, row in enumerate(file_reader):
                try:
                    for ref in eval(row[col]):
                        refs.add(ref)
                except:
                    continue
    return refs.remove('')

if __name__ =='__main__':
    # compare all thier refs to all our refs in a whole massekhet, just to see :)
    thierRambam = exctractRefs(u'Ein Mishpat - Chagigah - Links.tsv', 'Rambam', 'tsv')
    ourRambam = exctractRefs(u'hagiga_done.csv', 'Rambam','csv')


    # # all_rows = duplicate_rows_in_file(u'beitza_done.csv', u'test_merge_egg')
    # # equal_sets(all_rows, u'Ein Mishpat - Beitzah - Links.tsv')
    # # collapsed_segments_r = collapse(u'Rambam_f', u'Daf_f', u'Ein Mishpat - Beitzah - Links.tsv')
    # # collapsed_segments_s = collapse(u'Semag_f', u'Daf_f', u'Ein Mishpat - Beitzah - Links.tsv')
    # # collapsed_segments_sa = collapse(u'Shulchan_Arukh_f', u'Daf_f', u'Ein Mishpat - Beitzah - Links.tsv')
    # collapsed_segments = collapse([u'Rambam_f',u'Semag_f',u'Shulchan_Arukh_f'], u'Daf_f', u'Ein Mishpat - Beitzah - Links.tsv', u'Beitzah_mapping.csv')
    # # letter_dict = get_letters(u'beitza_done.csv', u'Rambam')
    # massechet_he = u'ביצה'
    # massechet_en = u'beitza'
    # fromCSV(u'{}1.csv'.format(massechet_he), u'{}1.txt'.format(massechet_en))  # reads from fixed ביצה.csv to egg.txt
    # parse2 = parse_em(u'{}1.txt'.format(massechet_en), 2, u'{}1_error'.format(massechet_en))
    # # letter_dict_r = get_letters(parse2, u'Rambam')
    # # letter_dict_s = get_letters(parse2, u'Semag')
    # # letter_dict_sa = get_letters(parse2, u'Tur Shulchan Arukh')
    # letter_dict = get_letters(parse2, [u'Rambam',u'Semag',u'Tur Shulchan Arukh'])
    # fit = placing(collapsed_segments, letter_dict)
    # # print 'rambam'
    # # r = placing(collapsed_segments_r,letter_dict_r)
    # # print r
    # # print 'semag'
    # # s = placing(collapsed_segments_s, letter_dict_s)
    # # print s
    # # print 'sa'
    # # sa = placing(collapsed_segments_sa, letter_dict_sa)
    # # print sa

"""
base = them on commentary (e.g. rambam) for daf x
comments = us on rambam for daf x
input(list of refs in base, list of refs in comments)
    output boolean array len of comments. 0 if not found in base
    also list of segment connected to base
    [([1,0,0], segment A), ([1,1,1], segment B)...]


segment A - Rambam: [0,1,0], Shulchan Aruch: [1,1,1,1]
"""