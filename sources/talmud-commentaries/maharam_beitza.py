__author__ = 'eliav'
import re


def open_file():
    with open("source/maharam_beitza.txt", 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8').strip()
        return ucd_text

def parse_dapim(text):
    shas = 0
    tosafos = 0
    rashi = 0
    amud_num = 'b'
    daf = re.split(ur'@11([^@]*)', text)
    maharam = [[],[]]
    parshan =[]
    for daf_num, content in zip(daf[1::2], daf[2::2]):
        dibuhamatchil = re.split(ur'@44', content)
        for dh in dibuhamatchil[1:]:
            mefaresh = re.split(ur'@55', dh)
            if mefaresh[0]=ur 'ד"ה':
                print mefaresh[0] + mefaresh[1]
