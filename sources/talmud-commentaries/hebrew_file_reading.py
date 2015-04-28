# -*- coding: utf-8 -*-
__author__ = 'eliav'
import urllib2
import json
import os
import docx
import re
from sefaria.model import *
mesechtot = [u'Mishnah Berakhot',u'Mishnah Peah',u'Mishnah Demai',u'Mishnah Kilayim',u'Mishnah Sheviit',u'Mishnah Terumot',u'Mishnah Maasrot',u'Mishnah Maaser Sheni',u'Mishnah Challah',u'Mishnah Orlah',u'Mishnah Bikkurim',u'Mishnah Shabbat',u'Mishnah Eruvin',u'Mishnah Pesachim',u'Mishnah Shekalim',u'Mishnah Yoma',u'Mishnah Sukkah',u'Mishnah Beitzah',u'Mishnah Rosh Hashanah',u'Mishnah Taanit',u'Mishnah Megillah',u'Mishnah Moed Katan',u'Mishnah Chagigah',u'Mishnah Yevamot',u'Mishnah Ketubot',u'Mishnah Nedarim',u'Mishnah Nazir',u'Mishnah Sotah',u'Mishnah Gittin',u'Mishnah Kiddushin',u'Mishnah Bava Kamma',u'Mishnah Bava Metzia',u'Mishnah Bava Batra',u'Mishnah Sanhedrin',u'Mishnah Makkot',u'Mishnah Shevuot',u'Mishnah Eduyot',u'Mishnah Avodah Zarah',u'Pirkei Avot',u'Mishnah Horayot',u'Mishnah Zevachim',u'Mishnah Menachot',u'Mishnah Chullin',u'Mishnah Bekhorot',u'Mishnah Arakhin',u'Mishnah Temurah',u'Mishnah Keritot',u'Mishnah Meilah',u'Mishnah Tamid',u'Mishnah Middot',u'Mishnah Kinnim',u'Mishnah Kelim',u'Mishnah Oholot',u'Mishnah Negaim',u'Mishnah Parah',u'Mishnah Tahorot',u'Mishnah Mikvaot',u'Mishnah Niddah',u'Mishnah Makhshirin',u'Mishnah Zavim',u'Mishnah Tevul Yom',u'Mishnah Yadayim',u'Mishnah Oktzin']

def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def babylon():
    bavli={}
    for mesechet in mesechtot:
        try:
            mas = re.sub(" ", "_", mesechet[8:])
            url = 'http://localhost:8000/api/index/' + mas
            response = urllib2.urlopen(url)
            resp = response.read()
            he_title =  json.loads(resp)["heTitleVariants"][0]
            eng_title = json.loads(resp)["title"]
            bavli[he_title] = eng_title
           # print bavli[he_title]
        except:
            continue
    return bavli


def file_list():
    vr = {}
    for f in os.listdir(u'C:/Users/eliav/Downloads/Rosh_on_Talmud-2015-03-31/Rosh on Talmud'):
        b=""
        print f
        pf = os.path.join(u'C:/Users/eliav/Downloads/Rosh_on_Talmud-2015-03-31/Rosh on Talmud', f)
        if len(f.split("."))>1 and f.split(".")[1] == "docx":
            document  = docx.opendocx(pf)
            for a in docx.getdocumenttext(document):
              b = b + a
            vr[f.split(".")[0]] = b
    files_list = vr.keys()
    return files_list, vr


def do_job(bavl, files_list,vr):
    for name in files_list:
        for bavel in bavl.keys():
            if bavel in name:

                vr[bavl[bavel]] = vr.pop(name)
    for parameter in vr.keys():
        if len(parameter.split())==2:
            if is_ascii(parameter):
               # file = open("source/Rosh_on_{}.txt".format(parameter.split()[0] + "_" + parameter.split()[1]), 'w')
               #print vr[parameter]
               # file.write(vr[parameter].encode('utf8'))
               # os.system("C:/Users/eliav/Documents/GitHub/Sefaria-Data/sources/talmud-commentaries/rosh_taanit.py {}".format(parameter.split()[0] + "_" + parameter.split()[1]))
                print parameter.strip()
                os.system("C:/Users/eliav/Documents/GitHub/Sefaria-Data/sources/talmud-commentaries/rosh_taanit.py {}".format(parameter.split()[0] + "_" + parameter.split()[1]))
        elif len(parameter.split())==1:
            if is_ascii(parameter):
                #file = open("source/Rosh_on_{}.txt".format(parameter.strip()), 'w')
                #file.write(vr[parameter].encode('utf8'))
                #os.system("C:/Users/eliav/Documents/GitHub/Sefaria-Data/sources/talmud-commentaries/rosh_taanit.py {}".format(parameter.strip()))
                print parameter.strip()
                os.system("C:/Users/eliav/Documents/GitHub/Sefaria-Data/sources/talmud-commentaries/rosh_taanit.py {}".format(parameter.strip()))
    return vr
if __name__ == '__main__':			
    bavl = babylon()
    #print bavl
    files_list, vr = file_list()
    print "sending do job"
    new_vr = do_job(bavl, files_list, vr)
   # print vr
