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

with open("Akeidat Yitzchak - en - Akeydat Yitzchak by Eliyahu Munk.txt") as myFile:
    lines = myFile.readlines()
akeida_box = []
gate_box = []
for line in lines:
    if re.search(r"^Gate \d+$",line):
        if len(gate_box)>0:
            akeida_box.append([gate_box])
            gate_box = []
        if len(akeida_box)==105:
            break
    elif not_blank(line):
        gate_box.append(line)
    
for gindex, gate in enumerate(akeida_box):
    for pindex, paragraph in enumerate(gate):
        print gindex, pindex, paragraph
        
version = {
    'versionTitle': 'Akeydat Yitzchak by Eliyahu Munk',
    'versionSource': 'www.urimpublications.com',
    'language': 'en',
    'text': akeida_box
}

post_text('Akeidat Yitzchak', version,weak_network=True)