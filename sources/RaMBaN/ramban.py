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

'''
perek = 5@.*?2@
daf = 2@.*?\d@
dh = 4@.*?1@
before_dh = 7@.*?4@ or 1@.*?4@

'''
prev_daf = 1
tractates = ["beitzah", "chagigah", "moed_katan", "eruvin", "pesachim", "rosh_hashanah", "sukkah", "taanit", "yoma"]

problems = open('problems.txt','w')
for tractate in tractates:
  for line in open(tractate+"_complete.txt"):
    line = line.replace("\n", "")
    if len(line.replace(' ',''))==0:
        continue
    try:
        if line.find('5')>=0:
            perek_info = re.findall('5@.*?\d@', line)[0]
        else:
            perek_info = ""
        print perek_info
        if line.find('2')>=0:
            daf_info = re.findall('2@.*?\d@', line)[0]
        else:
            daf_info = ""
        print daf_info
        dh_info = re.findall('4@.*?1@', line)[0]
        print dh_info
        if line.find('7@')>0:
          before_dh_info = re.findall('7@.*?4@', line)[0]

        else:
          poss = re.findall('1@.*?4@', line)
          if len(poss)>0:
            before_dh_info = poss[0]
          else:
            before_dh_info = ""
        print before_dh_info
    except:
        problems.write(tractate+"\n"+line+"\n\n")
        continue
    if len(daf_info)>0:
        daf = daf_info.replace("2@", "").replace("1@","").replace("7@","")
        if daf.find('דף')==-1 and daf.find('ע"')==-1:
            print 'no daf'
            #pdb.set_trace()
        if daf.find('ע"ב')>0:
            amud = 1
        else:
            amud = 0
        daf = amud+getGematria(daf.replace('ע"ב', '').replace('ע"א','').replace('דף',''))
    else:
        daf = ""
    dh = dh_info.replace("4@","").replace("1@","")
    before_dh = before_dh_info.replace("7@","").replace("1@","").replace("4@","")
problems.close()