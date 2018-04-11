# -*- coding: utf-8 -*-

import re
import codecs
import math
import json

# TODO think about what @ means syntactically
# TODO i believe + => tet from examples but there's no explicit mention of that on cal
cal2hebDic = {u")": u"א", u"b": u"ב", u"g": u"ג", u"d": u"ד", u"h": u"ה",
              u"w": u"ו", u"z": u"ז", u"x": u"ח", u"T": u"ט", u"y": u"י",
              u"k": u"כ", u"K": u"ך", u"l": u"ל", u"m": u"מ", u"M": u"ם",
              u"n": u"נ", u"N": u"ן", u"s": u"ס", u"(": u"ע", u"p": u"פ",
              u"P": u"ף", u"c": u"צ", u"C": u"ץ", u"q": u"ק", u"r": u"ר",
              u"$": u"שׁ", u"&": u"שׂ", u"t": u"ת", u"@": u" ", u"+": u"ט"}
heb2calDic = {v: k for k, v in cal2hebDic.iteritems()
              if not k == u'$' and not k == u'&'}

letter2sofit = {u'צ': u'ץ', u'פ': u'ף', u'נ': u'ן', u'מ': u'ם', u'כ': u'ך'}
sofit2letter = {v: k for k, v in letter2sofit.iteritems()}
with open("../data/Cal-Data-Files/dialects.json", "rb") as fp:
    dialect_schema = json.load(fp)

class CalParsingException(Exception):
    pass


def calClean(calIn):
    if type(calIn) == list:
        return [calClean(tempCalIn) for tempCalIn in calIn]
    else:
        return re.sub(r'[!?<>{}\+/\[\]\^\*\|#0-9\"\.]', "", calIn)


def cal2heb(calIn, withshinsin=True):
    hebStr = u""

    no_shinsin_dic = {u"$": u"ש", u"&": u"ש"}
    if type(calIn) == list:
        return [cal2heb(tempCalIn, withshinsin) for tempCalIn in calIn]
    else:
        for ichar, char in enumerate(calIn):
            if char in cal2hebDic:
                if char in no_shinsin_dic and not withshinsin:
                    hebStr += no_shinsin_dic[char]
                else:
                    hebStr += cal2hebDic[char]
            else:
                hebStr += char

    return hebStr


def heb2cal(hebIn):
    calStr = ""

    heb2calDic[u'ש'] = '$'
    if type(hebIn) == list:
        return [heb2cal(tempHebIn) for tempHebIn in hebIn]
    else:
        for char in hebIn:
            if char in heb2calDic:
                calStr += heb2calDic[char]
            else:
                calStr += char

    return calStr


def daf2num(daf, side):
    return daf*2 + side - 2


def num2daf(num):
    daf = math.ceil(num/2.0)
    side = (num % 2)
    sideLetter = "a" if side == 1 else "b"
    return str(int(daf)) + sideLetter


def parseJBALine(line, shouldConvert, withshinsin=True):
    line = line.rstrip()
    lineArray = re.split(ur'\t+', line)
    if len(lineArray) < 2:  # this line doesn't have enough info
        return {}
    word = lineArray[0]
    synInfo = lineArray[1]
    prefixList = []
    prefix_POSList = []
    hasPrefix = False

    prefixRegStr = ur'[a-zA-Z]+(#[0-9])?_? [a-zA-Z][0-9]{0,2}\+'
    prefixMultiPattern = re.compile(ur'((' + prefixRegStr + ur')+)')
    prefixSinglePattern = re.compile(prefixRegStr)
    prefixMultiMatch = prefixMultiPattern.match(synInfo)
    if prefixMultiMatch:
        hasPrefix = True
        prefixIter = prefixSinglePattern.finditer(prefixMultiMatch.group(1))
        for prefixInfo in prefixIter:
            prefixInfoArray = prefixInfo.group(0).split(u" ")
            prefixList.append(prefixInfoArray[0])
            prefix_POSList.append(prefixInfoArray[1][:-1])  # skip +
        synInfo = synInfo[prefixMultiMatch.span()[1]:]
    synArray = synInfo.split(u" ")
    head_word = synArray[0]
    POS = synArray[1]

    lineObj = {}
    if shouldConvert:
        lineObj["head_word"] = cal2heb(calClean(head_word), withshinsin)
        lineObj["POS"] = POS
        lineObj["word"] = cal2heb(calClean(word), withshinsin)
        if hasPrefix:
            lineObj["prefix"] = cal2heb(calClean(prefixList), withshinsin)
            lineObj["prefix_POS"] = prefix_POSList
    else:
        lineObj["head_word"] = calClean(head_word)
        lineObj["POS"] = POS
        lineObj["word"] = calClean(word)
        if hasPrefix:
            lineObj["prefix"] = calClean(prefixList)
            lineObj["prefix_POS"] = prefix_POSList


    return lineObj


def parseDictLine(line, shouldConvert):
    line = line.rstrip()
    lineArray = re.split(ur'\t+', line)

    head_word, POS = lineArray[0].split(u' ')
    if POS == u"V":
        if len(lineArray) == 5:
            POS += lineArray[1]
            offset = 1
        else:
            offset = 0
    else:
        offset = 0

    dialectStr = lineArray[2+offset]
    if u"-" in dialectStr:
        removed_dialects = dialectStr.split(u"-")[1:]  # purposefully also remove 0 dialect which has special meaning
        removed_dialects += [u"0"]
        included_dialects = filter(lambda x: x not in removed_dialects, dialect_schema.keys())
        dialects = reduce(
                          lambda a, b: a + b, [[u"{}{}".format(dCat, dSub) for
                          dSub in dialect_schema[dCat].keys()] for dCat in
                          included_dialects], [])
    else:
        dialects = [d for d in re.findall(ur"\d{2}", dialectStr)]

    definition = re.sub(ur"<aram>(.+?)</aram>", lambda m: cal2heb(m.group(1), True), lineArray[3+offset])

    lineObj = {
        u"head_word": re.sub(ur"([כמנפצ])$", lambda m: letter2sofit[m.group(1)],
                             cal2heb(head_word, True) if shouldConvert else
                             head_word, 1),
        u"POS": POS,
        u"def_num": lineArray[1 + offset].strip(),
        u"dialects": dialects,
        u"definition": definition
    }

    if lineObj[u"head_word"] == u"שרי" and lineObj[u"POS"] == u"N":
        print line
    try:
        possible_chars = u"".join(list(set(cal2hebDic.values())))
        assert re.search(ur"^[" + re.escape(possible_chars) + ur"]+(?:#\d)?_?$", lineObj["head_word"]) is not None
    except AssertionError:
        raise CalParsingException(u"Error in head_word. line:\n\t{}\n".format(line))
    try:
        assert re.search(ur"^[a-zA-Z]{,2}(?:\d{1,2})?$", lineObj["POS"]) is not None
    except AssertionError:
        raise CalParsingException(u"Error in POS. line:\n\t{}\n".format(line))
    try:
        assert re.search(ur"^\d(?:\.\d){0,3}$", lineObj["def_num"]) is not None
    except AssertionError:
        raise CalParsingException(u"Error in def_num. line:\n\t{}\n".format(line))
    try:
        assert all([dialect_schema[di[0]][di[1]] for di in lineObj["dialects"]])
    except (AssertionError, KeyError):
        raise CalParsingException(u"Error in dialects. line:\n\t{}\n".format(line))
    try:
        assert len(lineObj["definition"]) > 0
    except AssertionError:
        raise CalParsingException(u"Error in definition. line:\n\t{}\n".format(line))

    return lineObj


def parseBCalLine(line, shouldConvert):
    #TODO what are brackets? optional letters?
    #TODO what are >? it seems it usually has the same word on both sides and that the word doesn't appear in the dict
    line = line.rstrip()
    cal_part, dict_part = line.split(u"\t")
    cal_word, cal_pos = cal_part.split(u" ")
    dict_word, dict_pos = dict_part.split(u" ")
    return {
        "cal_word": re.sub(ur"([כמנפצ])$", lambda m: letter2sofit[m.group(1)],
                             cal2heb(cal_word, True) if shouldConvert else
                             cal_word, 1),
        "cal_pos": cal_pos,
        "dict_word": re.sub(ur"([כמנפצ])$", lambda m: letter2sofit[m.group(1)],
                             cal2heb(dict_word, True) if shouldConvert else
                             dict_word, 1),
        "dict_pos": dict_pos
    }


def parseCalLine(line, shouldConvert, withshinsin=True):
    line = line.rstrip()
    lineArray = re.split(ur'\t+', line)

    pos = lineArray[0]
    lineObj = {
        "book_num": int(pos[0:5]),
        "ms": pos[5:7],
        "pg_num": int(pos[7:10]),
        "side": int(pos[10:11]),
        "line_num": int(pos[11:13])
    }

    word_num = lineArray[1]
    lineObj["word_num"] = int(word_num)

    synInfo = lineArray[2]
    prefixList = []
    prefix_POSList = []
    prefix_homograph_num_list = []
    hasPrefix = False

    calChars = ur'a-zA-Z\)\(@\&\$'
    prefixRegStr = ur'[' + calChars + ur']+(#[0-9])?_? [' + calChars+ ur'][0-9]{0,2}\+'
    prefixMultiPattern = re.compile(ur'((' + prefixRegStr + ur')+)')
    prefixSinglePattern = re.compile(prefixRegStr)
    prefixMultiMatch = prefixMultiPattern.match(synInfo)
    if prefixMultiMatch:
        hasPrefix = True
        prefixIter = prefixSinglePattern.finditer(prefixMultiMatch.group(1))
        for prefixInfo in prefixIter:
            prefixInfoArray = prefixInfo.group(0).split(" ")
            prefixList.append(prefixInfoArray[0].split("#")[0])
            prefix_POSList.append(prefixInfoArray[1][:-1])  # skip +
            prefix_homograph_num_list.append(prefixInfo.group(1) if prefixInfo.group(1) else u'')
        synInfo = synInfo[prefixMultiMatch.span()[1]:]

    synArray = synInfo.split(u" ")

    head_word_split = synArray[0].split(u'#')
    head_word = cal2heb(calClean(head_word_split[0]),withshinsin=withshinsin) if shouldConvert else calClean(head_word_split[0])
    head_word_homograph = u'#' + head_word_split[1] if len(head_word_split) > 1 else ''

    POS = synArray[1]
    word = cal2heb(calClean(synArray[2]), withshinsin) if shouldConvert else \
        calClean(synArray[2])

    prefix = cal2heb(calClean(prefixList), withshinsin) if shouldConvert else \
        calClean(prefixList)

    lineObj["head_word"] = head_word
    lineObj["homograph"] = head_word_homograph
    lineObj["POS"] = POS
    lineObj["word"] = word
    if hasPrefix:
        lineObj["prefix"] = prefix
        lineObj["prefix_POS"] = prefix_POSList
        lineObj["prefix_homograph"] = prefix_homograph_num_list

    return lineObj


def writeCalLine(lo):
    """
    I could probably write this in one line...but that's probably a bad idea
    :param lo: line_object coming from parseCalLine()
    :return:
    """
    if "prefix" in lo:
        prefix = u"+".join([u"{}{} {}".format(prefix, prefixHomo, prefixPOS) for
                            prefix, prefixPOS, prefixHomo in zip(lo["prefix"],
                            lo["prefix_POS"], lo["prefix_homograph"])])
        full_pos = u"{}+{}{} {} {}".format(prefix, lo["head_word"], lo["homograph"], lo["POS"], lo["word"])
    else:
        full_pos = u"{}{} {} {}".format(lo["head_word"], lo["homograph"], lo["POS"], lo["word"])

    return u"{book_num:05d}{ms}{pg_num:03d}{side}{line_num:02d}\t{word_num}\t{full_pos}".format(book_num=lo["book_num"],ms=lo["ms"],pg_num=lo["pg_num"],side=lo["side"],line_num=lo["line_num"],word_num=lo["word_num"],full_pos=full_pos)


def calLine2hebLine(calLine):
    lineObj = parseCalLine(calLine,True)
    return str(lineObj["book_num"]) + \
        str(lineObj["ms"]) + str(lineObj["pg_num"]) + str(lineObj["side"]) + \
        str(lineObj["line_num"]) + "\t" + str(lineObj["word_num"]) + "\t" + \
        lineObj["head_word"] + " " + lineObj["POS"] + " " + lineObj["word"]


def caldb2hebdb(calFilename, hebFilename):
    with open(calFilename, 'rb') as cal:
        with open(hebFilename, 'wb') as heb:
            for calLine in cal:
                hebLine = calLine2hebLine(calLine)
                heb.write(hebLine + "\n")
