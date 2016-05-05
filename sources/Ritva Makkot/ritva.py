# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
import pdb
import os
import sys
import re
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
sys.path.insert(0, '../Match/')
from match import Match
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from local_settings import *
from functions import *


sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.model.schema import AddressTalmud
text={}
curr_daf=0
probs = open('probs_ritva.txt','w')
files = ["chiddushei one.txt","chiddushei two.txt", "chiddushei three.txt", "chiddushei four.txt", "chiddushei five.txt"]
for file in files:
    open_file = open(file)
    for line in open_file:
        line = line.replace('\n','')
        if len(line)==0:
            continue
        if line.find("#")>=0:
            start=line.find("#1")
            end=line.find("#2")
            if start>end or start==-1 or end==-1:
                print '# error'
                pdb.set_trace()
            daf = line[start:end]
            if daf.find('ע"ב')>=0:
                curr_daf += 1
            elif daf.find('דף')>=0:
                daf = daf.split(" ")[1]
                poss_daf = 2*getGematria(daf)-1
                if poss_daf < curr_daf:
                    print 'daf error'
                    pdb.set_trace()
                curr_daf = poss_daf
            else:
                print 'no daf'
                pdb.set_trace()
        if curr_daf == 155:
            pdb.set_trace()
        if line.find("@")>=0 and line.find('.')>=0:
            line = line.replace('@1','').replace('@2','')
            try:
              dh, comment = line.split(".",1)
            except:
              pdb.set_trace()

        else:
            probs.write('file: '+str(file)+"\n")
            probs.write('current daf:'+AddressTalmud.toStr('en', curr_daf)+"\n")
            probs.write('line without DH:\t'+line+"\n\n\n")
        prev_daf = curr_daf
