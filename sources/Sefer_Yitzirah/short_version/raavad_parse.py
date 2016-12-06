# encoding=utf-8

import codecs
import re
from data_utilities.util import ja_to_xml, multiple_replace
from sources.functions import post_text, post_index
from sefaria.model import *
from sefaria.datatype.jagged_array import JaggedArray

def raavad_parse():
    with codecs.open('yitzira_raavad.txt', 'r', 'utf-8') as fp:
        lines = fp.readlines()
    # init JA and there depths
    ja_sp = [] # JA starting points in the txt

    # dictionary for line ocr tag fixing
    replace_dict = {u'@(44|13|31)': u'<b>', u'@(45|14|32)': u'</b>',# bold in text
                    u'@(03|04|10|11|98|99)' : u'' # TODO: what to do with 55, (picture) 56, don't forget to pop the slik what is 41,42
                    # ur'(@(11|12|66|67)|\[\*.*?\])': u''  # ocr tags that are not relevant (including erasing footnotes)
                    }
    # check if we got to the end of the legend and change to started
    startJA = None
    for line_num, line in enumerate(lines):
        if line == u'\n':
            startJA = line_num + 1  # ignoring the book name from text
            ja_sp.append(startJA)

    ja_fifty = fifty_parse(lines[ja_sp[0]+1:ja_sp[1]],replace_dict)
    ja_32_hakdama_n = threty_two_parse(lines[ja_sp[1]:ja_sp[2]], replace_dict, 'hakdama_n')
    ja_32_netivot = threty_two_parse(lines[ja_sp[2]:ja_sp[3]], replace_dict, 'netivot')
    ja_32_hakdama_p = threty_two_parse(lines[ja_sp[3]:ja_sp[4]], replace_dict, 'hakdama_p')
    ja_32_perush = threty_two_parse(lines[ja_sp[4]:ja_sp[5]], replace_dict, 'perush')
    ja_raavad_perush = raavad_perush_parse(lines[ja_sp[5]:], replace_dict)

    ja_32_perush[0] = ja_32_hakdama_p[0] + '<br>' + ja_32_hakdama_p[1] + '<br>' + ja_32_perush[0]
    ja_to_xml(ja_32_perush, ['netiv'], 'test.xml')
    return ja_fifty, ja_32_netivot, ja_raavad_perush, ja_32_perush,ja_32_hakdama_n


def fifty_parse(lines, replace_dict):
    # start the parsing of part fifty
    arr = []
    perek = []
    peska = []
    for line in lines:
        if line.find(ur'@05') is not -1:
            if perek:
                peska = ' '.join(peska)
                perek.append(peska)
                peska = []
                arr.append(perek)
                perek = []
        else:
            if (line.find(u'@13') is not -1) and (peska):
                peska = ' '.join(peska)
                perek.append(peska)
                peska = []
            line = multiple_replace(line, replace_dict, using_regex=True)
            peska.append(line.strip())
    peska = ' '.join(peska)
    perek.append(peska)
    arr.append(perek)
    ja_to_xml(arr,['perek', 'piska'], 'raavad_50.xml')

    return arr


def threty_two_parse(lines, replace_dict, str):
    # start the parsing of 32 netivot
    arr = []
    netiv = []
    first = True
    for line in lines:
        if re.search(u'@(13|03)', line):# and (netiv):
            if first:
                first = False
            else:
                netiv = ' '.join(netiv)
                arr.append(netiv)
                netiv = []
        line = multiple_replace(line, replace_dict, using_regex=True)
        netiv.append(line.strip())
    netiv = ' '.join(netiv)
    arr.append(netiv)
    ja_to_xml(arr, ['netiv'], '{}{}'.format(str,'_32.xml'))

    return arr


def raavad_perush_parse(lines, replace_dict):
    # start the parsing of part raavad text itself
    arr = []
    first_p = True
    first_m = True
    first_d = True
    perek = []
    mishna = []
    dibur = []
    for line in lines:
        if line.find(u'@00') is not -1:
            # perek
            if first_p:
                first_p = False
            else:
                dibur = ' '.join(dibur)
                mishna.append(dibur)
                dibur = []
                perek.append(mishna)
                mishna = []
                arr.append(perek)
                perek = []
                first_m = True  # since this is opening a new perek

        elif line.find(u'@22') is not -1:  # notice that this parsing is given that there is no text on same line with @22 and @00
            # mishna
            if first_m:
                first_m = False
            else:
                dibur = ' '.join(dibur)
                mishna.append(dibur)
                dibur = []
                perek.append(mishna)
                mishna = []
                first_d = True  # since this is opening a new mishna
        else:
            # this line is going to be part of the dibur
            # Dibur Hamatchil
            if re.search(u'@(31|98)', line) and (not first_d):# and not first_d:  # probably start a new dibur
                    dibur = ' '.join(dibur)
                    mishna.append(dibur)
                    dibur = []
            else:
                if first_d:
                    first_d = False
            # segment ocr tag fixing
            line = multiple_replace(line, replace_dict, using_regex=True)
            dibur.append(line)
    dibur = ' '.join(dibur)
    mishna.append(dibur)
    perek.append(mishna)
    arr.append(perek)
    ja_to_xml(arr,['perek', 'mishna', 'dibur'], 'raavad_text.xml')

    return arr

for x in raavad_parse():
    print x