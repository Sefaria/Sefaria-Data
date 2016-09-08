# -*- coding: utf-8 -*-
import math
import re
#import numpy as np
import json
import codecs
import csv

calDBRoot = "cal DB"
calDBFile = calDBRoot + "/bavliwords.txt"
sefariaRoot = "sefaria talmud"

def calClean(calIn):
    if type(calIn) == list:
        return [calClean(tempCalIn) for tempCalIn in calIn]
    else:
        return re.sub(r'[!?<>{}\+=/\[\]\^\*\-\|#0-9\"]',"",calIn)

def cal2heb(calIn,withshinsin=True):
    hebStr = ""
    cal2hebDic = {
        ")" : "א",
        "b" : "ב",
        "g" : "ג",
        "d" : "ד",
        "h" : "ה",
        "w" : "ו",
        "z" : "ז",
        "x" : "ח",
        "T" : "ט",
        "y" : "י",
        "k" : "כ",
        "K" : "ך",
        "l" : "ל",
        "m" : "מ",
        "M" : "ם",
        "n" : "נ",
        "N" : "ן",
        "s" : "ס",
        "(" : "ע",
        "p" : "פ",
        "P" : "ף",
        "c" : "צ",
        "C" : "ץ",
        "q" : "ק",
        "r" : "ר",
        "$" : "שׁ",
        "&" : "שׂ",
        "t" : "ת",
        "@" : " "  #TODO think about what @ means syntactically
    }

    no_shinsin_dic = {"$":"ש","&":"ש"}
    if type(calIn) == list:
       return [cal2heb(tempCalIn,withshinsin) for tempCalIn in calIn]
    else:
        for char in calIn:
            if char in cal2hebDic.keys():
                if char in no_shinsin_dic and not withshinsin:
                    hebStr += no_shinsin_dic[char]
                else:
                    hebStr += cal2hebDic[char]
            else:
                hebStr += char

    return unicode(hebStr,'utf-8')

def daf2num(daf,side):
    return daf*2 + side - 2

def num2daf(num):
    daf = math.ceil(num/2.0)
    side = (num % 2)
    sideLetter = "a" if side == 1 else "b"
    return str(int(daf)) + sideLetter

def parseJBALine(line,shouldConvert,withshinsin=True):
    line = line.rstrip()
    lineArray = re.split(r'\t+', line)
    if len(lineArray) < 2: #this line doesn't have enough info
        return {}
    word = lineArray[0]
    synInfo = lineArray[1]
    prefixList = []
    prefix_POSList = []
    hasPrefix = False

    prefixRegStr = r'[a-zA-Z]+(#[0-9])?_? [a-zA-Z][0-9]{0,2}\+'
    prefixMultiPattern = re.compile(r'((' + prefixRegStr + ')+)')
    prefixSinglePattern = re.compile(prefixRegStr)
    prefixMultiMatch = prefixMultiPattern.match(synInfo)
    if prefixMultiMatch:
        hasPrefix = True
        prefixIter = prefixSinglePattern.finditer(prefixMultiMatch.group(1))
        for prefixInfo in prefixIter:
            prefixInfoArray = prefixInfo.group(0).split(" ")
            prefixList.append(prefixInfoArray[0])
            prefix_POSList.append(prefixInfoArray[1][:-1]) #skip +
        synInfo = synInfo[prefixMultiMatch.span()[1]:]
    synArray = synInfo.split(" ")
    head_word = synArray[0]
    POS = synArray[1]

    lineObj = {}
    if shouldConvert:
        lineObj["head_word"] = cal2heb(calClean(head_word),withshinsin=withshinsin)
        lineObj["POS"] = POS
        lineObj["word"] = cal2heb(calClean(word),withshinsin=withshinsin)
        if hasPrefix:
            lineObj["prefix"] = cal2heb(calClean(prefixList),withshinsin=withshinsin)
            lineObj["prefix_POS"] = prefix_POSList
    else:
        lineObj["head_word"] = calClean(head_word)
        lineObj["POS"] = POS
        lineObj["word"] = calClean(word)
        if hasPrefix:
            lineObj["prefix"] = calClean(prefixList)
            lineObj["prefix_POS"] = prefix_POSList

    return lineObj

def parseCalLine(line,shouldConvert,withshinsin=True):
    line = line.rstrip()
    lineArray = re.split(r'\t+', line)

    pos = lineArray[0]
    lineObj = {
        "book_num" : int(pos[0:5]),
        "ms" : pos[5:7],
        "pg_num" : int(pos[7:10]),
        "side" : int(pos[10:11]),
        "line_num" : int(pos[11:13])
    }

    word_num = lineArray[1]
    lineObj["word_num"] = int(word_num)

    synInfo = lineArray[2]
    prefixList = []
    prefix_POSList = []
    hasPrefix = False

    prefixRegStr = r'[a-zA-Z]+(#[0-9])?_? [a-zA-Z][0-9]{0,2}\+'
    prefixMultiPattern = re.compile(r'((' + prefixRegStr + ')+)')
    prefixSinglePattern = re.compile(prefixRegStr)
    prefixMultiMatch = prefixMultiPattern.match(synInfo)
    if prefixMultiMatch:
        hasPrefix = True
        prefixIter = prefixSinglePattern.finditer(prefixMultiMatch.group(1))
        for prefixInfo in prefixIter:
            prefixInfoArray = prefixInfo.group(0).split(" ")
            prefixList.append(prefixInfoArray[0])
            prefix_POSList.append(prefixInfoArray[1][:-1]) #skip +
        synInfo = synInfo[prefixMultiMatch.span()[1]:]
    synArray = synInfo.split(" ")
    head_word = synArray[0]
    if (len(synArray) == 1):
        yo = 3
    POS = synArray[1]

    word = synArray[2]

    if shouldConvert:
        lineObj["head_word"] = cal2heb(calClean(head_word),withshinsin=withshinsin)
        lineObj["POS"] = POS
        lineObj["word"] = cal2heb(calClean(word),withshinsin=withshinsin)
        if hasPrefix:
            lineObj["prefix"] = cal2heb(calClean(prefixList),withshinsin=withshinsin)
            lineObj["prefix_POS"] = prefix_POSList
    else:
        lineObj["head_word"] = calClean(head_word)
        lineObj["POS"] = POS
        lineObj["word"] = calClean(word)
        if hasPrefix:
            lineObj["prefix"] = calClean(prefixList)
            lineObj["prefix_POS"] = prefix_POSList

    return lineObj

def calLine2hebLine(calLine):
    lineObj = parseCalLine(calLine,True)
    return str(lineObj["book_num"]) + \
        str(lineObj["ms"]) + str(lineObj["pg_num"]) + str(lineObj["side"]) + \
        str(lineObj["line_num"]) + "\t" + str(lineObj["word_num"]) + "\t" + \
        lineObj["head_word"] + " " + lineObj["POS"] + " " + lineObj["word"]

def caldb2hebdb(calFilename,hebFilename):
    with open(calFilename,'r') as cal:
        with open(hebFilename,'w') as heb:
            for calLine in cal:
                hebLine = calLine2hebLine(calLine)
                heb.write(hebLine + "\n")

def saveUTFStr(obj,outFilename):
    objStr = json.dumps(obj, indent=4, ensure_ascii=False)
    with open(outFilename, "w") as f:
        f.write(objStr.encode('utf-8'))

def saveHeadwordHashtable(calFilename,outFilename):
    hash = {}
    with open(calFilename,"r") as cal:
        for calLine in cal:
            lineObj = parseCalLine(calLine,True)
            try:
                tempSet = hash[lineObj["head_word"]]
                tempSet.add(lineObj["word"])
            except KeyError:
                tempSet = set()
                tempSet.add(lineObj["word"])
                hash[lineObj["head_word"]] = tempSet
    with open(outFilename,"w") as out:
        keys = hash.keys()
        keys.sort()
        for key in keys:
            listStr = ""
            isFirst = True
            for el in hash[key]:
                listStr = listStr + el if isFirst else listStr + ", " + el
                isFirst = False
            out.write("%s - %s\n" % (key,listStr))

def savePOSHashtable(calFilename,outFilename):
    obj = {}
    with open(calFilename,"r") as cal:
        for calLine in cal:
            lineObj = parseCalLine(calLine,True)
            try:
                tempSet = set(obj[lineObj["word"]])
                tempSet.add(lineObj["POS"])
                obj[lineObj["word"]] = list(tempSet)
            except KeyError:
                obj[lineObj["word"]] = [lineObj["POS"]]

    posCountList = np.empty(shape=[len(obj.keys())])
    with codecs.open(outFilename + ".txt","w",encoding="utf-8") as out:
        keys = obj.keys()
        keys.sort()
        for i,key in enumerate(keys):
            listStr = ""
            isFirst = True
            posCountList[i] = (len(obj[key]))
            for el in obj[key]:
                listStr = listStr + el if isFirst else listStr + ", " + el
                isFirst = False
            out.write("%s - %s\n" % (key,listStr))

    saveUTFStr(obj,outFilename + ".json")
    print "AVG POS: %s" % np.mean(posCountList)
    print "VAR POS: %s" % np.var(posCountList)

def saveJBAForms(outFilename):
    obj = {}
    with open("jbaforms.txt", 'rb') as jba:
        for line in jba:
            lineObj = parseJBALine(line,True,False)
            if lineObj == {}:
                continue
            try:
                obj[lineObj["word"]].append(lineObj)
            except KeyError:
                obj[lineObj["word"]] = [lineObj]

    for word in obj:
        pos_dic = {}
        head_dic = {}
        for lineObj in reversed(obj[word]):
            if lineObj["POS"] in pos_dic and lineObj["head_word"] in head_dic:
                obj[word].remove(lineObj)
            else:
                pos_dic[lineObj["POS"]] = True
                head_dic[lineObj["head_word"]] = True


    saveUTFStr(obj, outFilename + ".json")



def stupidTagger(outFilename):
    jba = json.load(open(calDBRoot + "/POSHashtable.json","r"),encoding="utf8")
    sef = json.load(open(sefariaRoot + "/Berakhot.json","r"),encoding="utf8")
    daf = sef["text"][3]
    with codecs.open(outFilename,"w","utf-8") as out:
        for line in daf:
            posLine = ""
            lineArray = line.rstrip().split(" ")
            for word in lineArray:
                try:
                    posList = list(jba[word])
                    if len(posList) >= 1:
                        posLine += "%s(%s) " % (word,posList)
                except KeyError:
                    posLine += "%s(UKN) " % word
            out.write(posLine+"\n")



#print cal2heb("(ny")
#print daf2num(21,1)
#print num2daf(3)

#caldb2hebdb("cal DB/bavliwords.txt","cal DB/bavliwordsHE.txt")
#saveHeadwordHashtable("cal DB/bavliwords.txt","cal DB/headwordHashtable.txt")
#savePOSHashtable("cal DB/bavliwords.txt","cal DB/POSHashtable")
#saveJBAForms("JBAHashtable")
#stupidTagger("output/stupidBerakhot.txt")
