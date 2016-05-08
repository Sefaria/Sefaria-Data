# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan and yonimosenkis'
import os
import sys
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, p)
sys.path.insert(0, '../Match/')
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from sources.local_settings import *
from sources.functions import *


sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model.schema import AddressTalmud


def find_misshing_DH(max_length):

    """
    Run through Ritva Makkot, and search for lines with an unreasonable amount of words until the first period.
    :param max_length:
    :return:
    """
    text={}
    count, lines = 0, 0
    curr_daf=0
    probs = codecs.open('probs_ritva.txt', 'w', 'utf-8')
    files = ["chiddushei one.txt","chiddushei two.txt", "chiddushei three.txt", "chiddushei four.txt", "chiddushei five.txt"]
    for file in files:
        open_file = codecs.open(file, 'r', 'utf-8')
        for line in open_file:
            line = line.replace('\n','')
            if len(line)==0:
                continue
            if line.find(u"#")>=0:
                start=line.find(u"#1")
                end=line.find(u"#2")
                if start>end or start==-1 or end==-1:
                    print '# error'
                daf = line[start:end]
                if daf.find(u'ע"ב')>=0:
                    curr_daf += 1
                elif daf.find(u'דף')>=0:
                    daf = daf.split(u" ")[1]
                    poss_daf = 2*getGematria(daf)-1
                    if poss_daf < curr_daf:
                        print 'daf error'
                    curr_daf = poss_daf
                else:
                    print 'no daf'
            line = line.replace('@1','').replace('@2','')
            words = line.split()

            for index, word in enumerate(words):

                lines += 1

                if word.find(u'.') >= 0:
                    break

                elif index > max_length:
                    probs.write('file: ' + str(file) + "\n")
                    probs.write('current daf:' + AddressTalmud.toStr('en', curr_daf) + "\n")
                    probs.write('line without DH:\t' + ' '.join(words[:max_length]) + "\n\n\n")
                    count += 1
                    break

            else:
                probs.write(u'file: ' + str(file) + u"\n")
                probs.write(u'current daf:' + AddressTalmud.toStr('en', curr_daf) + u"\n")
                probs.write(u'line without DH:\t' + u' '.join(words) + u"\n\n\n")
                count += 1
    print count, lines

find_misshing_DH(15)
