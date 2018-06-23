# -*- coding: utf-8 -*-

from sefaria.model import *
from sefaria.model.schema import *
import collections
import urllib
import urllib2
import csv
import sys
import re
import json
import divrey_chamudot_menachot
import maadaney_yom_tov_menachot
sys.path.insert(1, '../../genuzot')
import helperFunctions as Helper
import hebrew
sys.path.insert(0, '../../Match/')
from match import Match
masechet = str(sys.argv[1])
if "_" in masechet:
    mas = re.sub("_", " ", masechet)
else:
    mas = masechet
masechet_he = Index().load({"title":mas}).get_title("he")
links =[]
shas = TextChunk(Ref("%s" % masechet), "he").text


def makeLink(talmud, roash):
    return {
            "refs": [
               talmud,
                roash ],
            "type": "commentary",
            "auto": True,
            "generated_by": "Rosh_%s" % masechet,
            }


def postText(ref1, ref2, text, serializeText = True):
    if serializeText:
        textJSON = json.dumps(text)
    else:
        textJSON = text
    ref1 = ref1.replace(" ", "_")
    ref2 = ref2.replace(" ", "_")
    url = 'http://' + Helper.server + '/api/texts/{}_{}?index_after=0'.format(ref1,ref2)
    print url
    values = {
        'json': textJSON,
        'apikey': Helper.apikey
    }
    print values
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        print response.read()
    except urllib2.HTTPError, e:
        print 'Error code: ', e.code
        print e.read()


def link_yomtov(parsed_text,):
    Helper.createBookRecord(maadaney_yom_tov_menachot.book_record())
    file = maadaney_yom_tov_menachot.open_file(record = "yomtov")
    names_list, cut = maadaney_yom_tov_menachot.cut_to_parts(file)
    print depth(cut), "cut"
    parsed = maadaney_yom_tov_menachot.parse(cut)
    print len(maadaney_yom_tov_menachot.partslist)
    for i, (name, tx) in enumerate(zip(maadaney_yom_tov_menachot.partslist,parsed)):
        clean_text = maadaney_yom_tov_menachot.clean(tx)
        #print (clean_text[0])
        maadaney_yom_tov_menachot.save_parsed_text(clean_text,record = "yomtov", part=name)
        maadaney_yom_tov_menachot.run_post_to_api(record = "yomtov", part=name)
        count = 0
        print len(parsed_text[i])
        for k, siman in enumerate(parsed_text[i]):
            print name, k
            #if re.match('\(.\)', siman):
            if isinstance(siman, unicode):
                if len(re.findall(ur'\(\*\)',siman))>0:
                    a = re.findall('\(\*\)', siman)
                    part = re.sub("_"," ",name.strip())
                    for j, b in enumerate(a):
                         count +=1
                         roash = "Rosh on %s, " % masechet + part + "." + str(k+1) + "." + str(1)
                         shmuel = "Maadaney Yom Tov on " + masechet + "," + " " + part + "." + str(count)
                         links.append(makeLink(roash, shmuel))
            for l ,text in enumerate(siman):
                if len(re.findall(ur'\(\*\)',text))>0:
                    a = re.findall('\(\*\)', text)
                    part = re.sub("_"," ",name.strip())
                    for j, b in enumerate(a):
                         count +=1
                         roash = "Rosh on %s, " % masechet + part + "." + str(k+1) + "." + str(1)
                         shmuel = "Maadaney Yom Tov on " + masechet + "," + " " + part + "." + str(count)
                         links.append(makeLink(roash, shmuel))

    #Helper.postLink(shmuellinks)


def link_tiferet_shmuel(parsed_text,):
    Helper.createBookRecord(divrey_chamudot_menachot.book_record())
    file = divrey_chamudot_menachot.open_file(record = "chamudot")
    names_list, cut = divrey_chamudot_menachot.cut_to_parts(file)
    print depth(cut), "cut"
    parsed = divrey_chamudot_menachot.parse(cut)
    print len(divrey_chamudot_menachot.partslist)
    for i, (name, tx) in enumerate(zip(divrey_chamudot_menachot.partslist,parsed)):
        clean_text = divrey_chamudot_menachot.clean(tx)
        #print (clean_text[0])
        divrey_chamudot_menachot.save_parsed_text(clean_text,record = "chamudot", part=name)
        divrey_chamudot_menachot.run_post_to_api(record = "chamudot", part=name)
        count = 0
        for k, siman in enumerate(parsed_text[i]):
            #if re.match('\(.\)', siman):
            if isinstance(siman, unicode):
                if len(re.findall(ur'\(\*\)',siman))>0:
                    a = re.findall('\(\*\)', siman)
                    part = re.sub("_"," ",name.strip())
                    for j, b in enumerate(a):
                         count +=1
                         roash = "Rosh on %s, " % masechet + part + "." + str(k+1) + "." + str(1)
                         shmuel = "Divrey Chamudot on " + masechet + "," + " " + part + "." + str(count)
                         links.append(makeLink(roash, shmuel))
            else:
                for l ,text in enumerate(siman):
                    if len(re.findall(ur'\(\*\)',text))>0:
                        a = re.findall('\(\*\)', text)
                        part = re.sub("_"," ",name.strip())
                        for j, b in enumerate(a):
                             count +=1
                             roash = "Rosh on %s, " % masechet + part + "." + str(k+1) + "." + str(1)
                             shmuel = "Divrey Chamudot on " + masechet + "," + " " + part + "." + str(count)
                             links.append(makeLink(roash, shmuel))

    #Helper.postLink(shmuellinks)


def save_text(text,perek):
    perek = re.sub(" ", "_",perek.strip())
    text_whole = {
    "title": 'Rosh on %s' % masechet,
    "versionTitle": "Vilna Edition",
    "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
    "language": "he",
    "text": text,
    "digitizedBySefaria": True,
    "license": "Public Domain",
    "licenseVetted": True,
    "status": "locked",
    }
    Helper.mkdir_p("../preprocess_json/")
    with open("../preprocess_json/Rosh_on_{}_{}.json".format(masechet,perek), 'w') as out:
        json.dump(text_whole, out)


def run_post_to_api(perek):
    perek1 = re.sub(" ", "_",perek.strip())
    with open("../preprocess_json/Rosh_on_{}_{}.json".format(masechet,perek1), 'r') as filep:
        file_text = filep.read()
    postText("Rosh on %s," % masechet , perek , file_text, False)


def clean2(parsed):
     rosh=[]
     for i in parsed:
         seif= []
         for j in i:
            j =  re.sub(ur"\(\S?דף.*?\)","", j)
            clean_text = re.sub("(?:@|[0-9]|<|>|b|\[|\*|\]|\/|\(\*\)|[!#])","", j)
            clean_text = re.sub(ur"\(\)","",clean_text)
            seif.append(clean_text)
            #print clean_text
         if len(seif[0])>1:
            rosh.append(seif)
     return rosh


def clean1(parsed):
    rosh=[]
    for i in parsed:
        j =  re.sub(ur"\(\S?דף.*?\)","", i)
        clean_text = re.sub("(?:@|[0-9]|<|>|b|\[|\*|\]|\/|\(\*\)|[!#])","", j)
        rosh.append(clean_text)
    return rosh


def matchobj(daf_num, amud, text):
    new_shas =[]
    index = (daf_num-2)*2
    if amud=="b":
        index= index + 1
    list =text.split(" ")
    string= " ".join(list[0:7])
    string = re.sub(ur'(?:@|[0-9]|<|>|b|\[|\*|\])',"",string)
    match_obj = Match(min_ratio=50, guess =True)
    for line in shas[index]:
        new_line = re.sub(ur'<[^<]+?>',"",line)
        new_shas.append(new_line)
    #print string, daf_num, amud
    results = match_obj.match_list([string], new_shas)
    return(results)


def open_file():
    with open("../source/Rosh_on_%s.txt" % masechet, 'r') as filep:
        file_text = filep.read()
        ucd_text = unicode(file_text, 'utf-8', errors='ignore').strip()
        #print masechet_he
        return ucd_text


def book_record():
    b = u"Rosh on %s" % masechet
    a = u"פסקי הראש על" + u" " + masechet_he
    root = SchemaNode()
    root.add_title(b, "en", primary=True)
    root.add_title(a, "he", primary=True)
    root.add_title("Halachot Ketanot laRosh","en", primary= False)
    root.add_title(u'הלכות קטנות לרא"ש',"he", primary= False)
    root.key = b

    #sefer torah
    sefer_tora = SchemaNode()
    sefer_tora.add_title("Hilchot Sefer Torah", "en", primary=True)
    sefer_tora.add_title("הלכות ספר תורה", "he", primary=True)
    sefer_tora.key = sefer_tora.primary_title()

    #parts of sefer tora
    Hilchot =JaggedArrayNode()
    Hilchot.default = True
    Hilchot.depth = 2
    Hilchot.sectionNames = ["Halacha", "siman"]
    Hilchot.addressTypes = ["Integer", "Integer"]
    Hilchot.key = "default"
    Hilchot.append_to(sefer_tora)

    HaItim = JaggedArrayNode()
    HaItim.add_title("Sefer HaItim", "en", primary=True)
    HaItim.add_title("ספר העתים", "he", primary=True)
    HaItim.depth = 1
    HaItim.sectionNames = ["Siman"]
    HaItim.addressTypes = ["Integer"]
    HaItim.key = HaItim.primary_title()
    HaItim.append_to(sefer_tora)

    #mezuza
    mezuza = JaggedArrayNode()
    mezuza.add_title(u"הלכות מזוזה", "he", primary=True)
    mezuza.add_title("Hilchot Mezuza", "en", primary=True)
    mezuza.key = mezuza.primary_title()
    mezuza.depth = 2
    mezuza.sectionNames = ["Seif", "Siman"]
    mezuza.addressTypes = ["Integer","Integer"]
    #tefilin
    tefilin = SchemaNode()
    tefilin.add_title("Hilchot Tefilin", "en", primary=True)
    tefilin.add_title("הלכות תפילין", "he", primary=True)
    tefilin.key = tefilin.primary_title()
    Hilchottefilin =JaggedArrayNode()
    Hilchottefilin.default = True
    Hilchottefilin.depth = 2
    Hilchottefilin.sectionNames = ["Halacha", "Siman"]
    Hilchottefilin.addressTypes = ["Integer", "Integer"]
    Hilchottefilin.key = "default"
    Hilchottefilin.append_to(tefilin)
    shimoosha = JaggedArrayNode()
    shimoosha.depth = 1
    shimoosha.sectionNames = ["Siman"]
    shimoosha.addressTypes = ["Integer"]
    shimoosha.add_title("Shimoosha Raba", "en", primary = True)
    shimoosha.add_title("שימושא רבא", "he", primary = True)
    shimoosha.key = shimoosha.primary_title()
    shimoosha.append_to(tefilin)
    kitzur = JaggedArrayNode()
    kitzur.add_title("Kitzur Tefilin", "en", primary=True)
    kitzur.add_title("קיצור תיקון תפילין ", "he", primary=True)
    kitzur.depth = 1
    kitzur.sectionNames = ["Siman"]
    kitzur.addressTypes = ["Integer"]
    kitzur.key = kitzur.primary_title()
    kitzur.append_to(tefilin)

    #tzizit
    hilchottzitzit = SchemaNode()
    hilchottzitzit.add_title("Hilchot Tzitzit", "en", primary=True)
    hilchottzitzit.add_title("הלכות ציצית", "he", primary=True)
    hilchottzitzit.key = hilchottzitzit.primary_title()
    maintzitzit =JaggedArrayNode()
    maintzitzit.default = True
    maintzitzit.depth = 2
    maintzitzit.sectionNames = ["Halacha", "Siman"]
    maintzitzit.addressTypes = ["Integer", "Integer"]
    maintzitzit.key = "default"
    maintzitzit.append_to(hilchottzitzit)
    tzitzit = JaggedArrayNode()
    tzitzit.add_title("Making Tzitzit", "en", primary=True)
    tzitzit.add_title(ur'עשיית ציצית', "he", primary = True)
    tzitzit.key = tzitzit.primary_title()
    tzitzit.depth = 1
    tzitzit.sectionNames = ["Siman"]
    tzitzit.addressTypes = ["Integer"]
    tzitzit.append_to(hilchottzitzit)

    #tomaa
    tomaa = JaggedArrayNode()
    tomaa.add_title("Hilchot Tuma'a", "en", primary=True)
    tomaa.add_title(ur'הלכות טומאה', "he", primary = True)
    tomaa.key = tomaa.primary_title()
    tomaa.depth = 2
    tomaa.sectionNames = ["Seif","Siman"]
    tomaa.addressTypes = ["Integer", "Integer"]

    chala = JaggedArrayNode()
    chala.add_title("Hilchot Chala", "en", primary=True)
    chala.add_title(ur'הלכות חלה', "he", primary = True)
    chala.key = chala.primary_title()
    chala.depth = 2
    chala.sectionNames = ["Seif","Siman"]
    chala.addressTypes = ["Integer", "Integer"]

    chala = JaggedArrayNode()
    chala.add_title("Hilchot Chala", "en", primary=True)
    chala.add_title(ur'הלכות חלה', "he", primary = True)
    chala.key = chala.primary_title()
    chala.depth = 2
    chala.sectionNames = ["Seif","Siman"]
    chala.addressTypes = ["Integer", "Integer"]

    kilayim = JaggedArrayNode()
    kilayim.add_title("Hilchot Kilayim", "en", primary=True)
    kilayim.add_title(ur'הלכות כלאים', "he", primary = True)
    kilayim.key = kilayim.primary_title()
    kilayim.depth = 2
    kilayim.sectionNames = ["Seif","Siman"]
    kilayim.addressTypes = ["Integer", "Integer"]

    orlah = JaggedArrayNode()
    orlah.add_title("Hilchot Orlah", "en", primary=True)
    orlah.add_title(ur'הלכות ערלה', "he", primary = True)
    orlah.key = orlah.primary_title()
    orlah.depth = 2
    orlah.sectionNames = ["Seif","Siman"]
    orlah.addressTypes = ["Integer", "Integer"]

    root.append(sefer_tora)
    root.append(mezuza)
    root.append(tefilin)
    root.append(hilchottzitzit)
    root.append(tomaa)
    root.append(chala)
    root.append(kilayim)
    root.append(orlah)
    root.validate()
    indx = {
    "title": b,
    "categories": [ "Commentary2",
        "Talmud","Rosh"
    ],
    "schema": root.serialize()
    }
    return indx


def parse(text):
    rosh = []
    parts = re.split(ur"@00(.*?)(?=@)", text)
    for name, part in zip(parts[1::2], parts[2::2]):
        print name
        if '@22' in part:
            seifim = re.split(ur'@22([^@]*)', part)
            si = []
            for index, (seif, cont) in enumerate(zip(seifim[1::2], seifim[2::2])):
                if '*' in seif:
                 #   print index + 1, re.findall('.\*.', seif)
                    pass
                #print seif , index + 1
                content = re.split('@66', cont)
                for num, co in enumerate(content):
                    si.append([co])
            rosh.append(si)
        else:
            cut = re.finditer(ur"@[16][16](.*?)@[37][37](.*)", part)
            subchap =[]
            for cuts in cut:
                subchap.append("<b>" + cuts.group(1) + "</b>" + cuts.group(2))
            rosh.append(subchap)
    return rosh


def names():
     namelist = []
     with open('../source/names of chapters Menachot Niddah.csv', 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t' )
        reader.next()
        for row in reader:
           namelist.append(row[1])
        return namelist


def search2(parsed, part):
    for k, seif in enumerate(parsed):
        for i,pasuk in enumerate(seif):
            found =  re.finditer(ur'@44[\[\(](.*?)[\]\)]@55(.*?)\.', pasuk)
            for find in found:
                daf = find.group(1)
                if daf.strip().split(' ')[0] == u"מנחות"and len(daf.strip().split(' '))<6:
                    if len(daf.strip().split(' ')) ==3:
                        daf = daf.strip().split(' ')[2]
                    elif len(daf.strip().split(' ')) ==2:
                        daf = daf.strip().split(' ')[1]
                    if daf[-1] ==".":
                        amud ="a"
                    elif daf[-1] == ":":
                        amud = "b"
                    daf_num = hebrew.heb_string_to_int(daf[0:-1])
                    #print daf_num, amud
                elif daf.strip().split(' ')[0] == u"דף":
                    daf = daf.strip().split(' ')[1]
                    if daf[-1] ==".":
                        amud ="a"
                    elif daf[-1] == ":":
                        amud = "b"
                    daf_num = hebrew.heb_string_to_int(daf[0:-1])
                    #print daf_num, amud
                elif ur"שם" not in daf and ur"דף" in daf:
                    #print daf
                    pass
                else:
                    pass
                    #print daf
                text =  find.group(2)

                try:
                    print str(k+1), str(i+1),daf_num, amud
                    found = matchobj(daf_num, amud, text)
                    line = found[1][0]
                    if line >0:
                        #print "Rosh on {}".format(masechet), daf_num, amud, found[1][0], str(i+1), ",", str(j+1) + ",", str(k+1)
                        talmud = "{}".format(masechet) +  "." + str(daf_num) + amud + "." + str(line)
                        roash = "Rosh on {}".format(masechet) + ", " + part + "." + str(k+1) + "." + str(1)
                        links.append(makeLink(talmud,roash))
                except Exception as e:
                    print e


def search1(parsed, part):
    for k, seif in enumerate(parsed):
            found =  re.finditer(ur'@44[\[\(](.*?)[\]\)]@55(.*?)\.', seif)
            for find in found:
                daf = find.group(1)
                if daf.strip().split(' ')[0] == u"מנחות"and len(daf.strip().split(' '))<6:
                    if len(daf.strip().split(' ')) ==3:
                        daf = daf.strip().split(' ')[2]
                    elif len(daf.strip().split(' ')) ==2:
                        daf = daf.strip().split(' ')[1]
                    if daf[-1] ==".":
                        amud ="a"
                    elif daf[-1] == ":":
                        amud = "b"
                    daf_num = hebrew.heb_string_to_int(daf[0:-1])
                    #print daf_num, amud
                elif daf.strip().split(' ')[0] == u"דף":
                    daf = daf.strip().split(' ')[1]
                    if daf[-1] ==".":
                        amud ="a"
                    elif daf[-1] == ":":
                        amud = "b"
                    daf_num = hebrew.heb_string_to_int(daf[0:-1])
                    #print daf_num, amud
                elif ur"שם" not in daf and ur"דף" in daf:
                    #print daf
                    pass
                else:
                    pass
                    #print daf
                text =  find.group(2)
                try:
                    found = matchobj(daf_num, amud, text)
                    line = found[1][0]
                    if line >0:
                        #print "Rosh on {}".format(masechet), daf_num, amud, found[1][0], str(i+1), ",", str(j+1) + ",", str(k+1)
                        talmud = "{}".format(masechet) +  "." + str(daf_num) + amud + "." + str(line)
                        roash = "Rosh on {}".format(masechet) + ", " + part +  "." + str(k+1)
                        links.append(makeLink(talmud,roash))
                except Exception as e:
                    print e



if __name__ == '__main__':
    depth = lambda L: isinstance(L, list) and max(map(depth, L))+1
    Helper.createBookRecord(book_record())
    text = open_file()
    parsed = parse(text)
    link_parsed = list( parsed[i] for i in [0,2,3,4,6,7,8,9,10,11]) ## need to fix the numbering
    link_tiferet_shmuel(link_parsed)
    link_yomtov(parsed)
    names =names()
    print depth(parsed[6])
    for parse, name in zip(parsed,names):
        if depth(parse) == 2:
            print name
            search2(parse, name)
            cleantext = clean2(parse)
        elif depth(parse) ==1:
            print name
            search1(parse, name)
            cleantext = clean1(parse)
        save_text(cleantext, name)
        run_post_to_api(name)
    for link in links:
       Helper.postLink(link)