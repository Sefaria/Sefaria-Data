import sys
import os
# for a script located two directories below this file
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
from sources.local_settings import *
sys.path.insert(0, SEFARIA_PROJECT_PATH)
os.environ['DJANGO_SETTINGS_MODULE'] = "local_settings"
from sources.functions import *
import re

def not_blank(s):
    while " " in s:
        s = s.replace(" ","")
    return (len(s.replace("\n","").replace("\r","").replace("\t",""))!=0);

with open("Akeidat Yitzchak English.txt") as myFile:
    lines = myFile.readlines()
akeida_box = []
gate_box = []
for line in lines:
    if "@" in line:
        if len(gate_box)>0:
            akeida_box.append([gate_box])
            gate_box = []
    elif not_blank(line):
        gate_box.append(line)
akeida_box.append([gate_box])

version = {
    'versionTitle': 'Akeydat Yitzchak by Eliyahu Munk',
    'versionSource': 'www.urimpublications.com',
    'language': 'en',
    'text': akeida_box
}

post_text('Akeidat Yitzchak', version,weak_network=True)