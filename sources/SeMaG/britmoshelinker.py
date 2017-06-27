# -*- coding: utf-8 -*-

__author__ = 'stevenkaplan'
import json
import re
from sources.functions import *

def in_order(arr):
    curr = 0
    new_arr = []
    for each in arr:
        poss = getGematria(each)
        poss = fixChetHay(poss, curr)
        if 1 <= poss - curr < 10:
            new_arr.append(poss)
            curr = poss
        elif poss == curr:
            new_arr.append(poss+1)
            curr += 1
        else:
            if poss == 110 and curr == 105:
                curr = 106
                new_arr.append(106)


    assert new_arr == sorted(new_arr)

    return new_arr


def get_semag_link_data(semag_ja):
    link_dict = {}
    total = 0
    poss = 0
    mitzvot = 0
    for mitzvah_num, mitzvah in enumerate(semag_ja):
        link_dict[mitzvah_num] = []
        finds = []
        if re.findall(u"\d+", mitzvah[0]) != []:
            print mitzvah_num+1
        for siman_num, siman in enumerate(mitzvah):
            finds += re.findall(u"""\([\u0590-\u05FF|\"]+\)""", siman)
        poss += len(finds)
        finds = in_order(finds)
        link_dict[mitzvah_num] += finds
        total += len(finds)
        pass

    #print total
    #print poss
    return link_dict

def get_brit_moshe_link_data(brit_ja):
    link_dict = {}
    total = 0
    poss = 0
    for mitzvah_num, mitzvah in enumerate(brit_ja):
        #if mitzvah == []:
        #    print mitzvah_num+1
        #if mitzvah != [] and re.findall(u"\d+", mitzvah[0][0]) != []:
        #    print mitzvah_num
        link_dict[mitzvah_num] = []
        finds = []
        for siman_num, siman in enumerate(mitzvah):
            for comment_num, comment in enumerate(siman):
                finds += re.findall(u"""\([\u0590-\u05FF|\"]+\)""", comment)
        poss += len(finds)
        finds = in_order(finds)
        link_dict[mitzvah_num] += finds
        total += len(finds)
        pass

    #print total
    #print poss
    return link_dict


if __name__ == "__main__":
    pattern = re.compile(u"""\([\u0590-\u05FF|\"]+\)""")
    json_semag = json.load(open("semag.json"))
    json_brit = json.load(open("britmoshe.json"))
    semag_content = {"Volume One": get_semag_link_data(json_semag["text"]["Volume One"][""]),
                     "Volume Two": get_semag_link_data(json_semag["text"]["Volume Two"][""])}
    #brit_moshe_content = {"Volume One": get_brit_moshe_link_data(json_brit["text"]["Volume One"]),
    #                 "Volume Two": get_brit_moshe_link_data(json_brit["text"]["Volume Two"])}

    #checkLengthsDicts(semag_content["Volume One"], brit_moshe_content["Volume One"])
    #checkLengthsDicts(semag_content["Volume Two"], brit_moshe_content["Volume Two"])

    '''
    Iterate through each volume and mitzvah of semag and create as many links as there are values in list
    Walk through Brit Moshe's segments where you set a variable to the current one and when you get to a new linked one that
    has a parenthesis with a letter in it, create a ranged link and reset that variable.
    Need to check that the same number per mitzvah is in Brit Moshe as in SeMaG


    1. Get content for Brit Moshe and make sure the numbers for each mitzvah are same as in SMaG.
    2.
    json_brit = json.load(open("britmoshe.json"))
    volumes = {}
    volumes["Volume One"] = json_brit["text"]["Volume One"]
    volumes["Volume Two"] = json_brit["text"]["Volume Two"]
    for volume_name, volume_content in volumes.items():
        for mitzvah_num, mitzvah in enumerate(volume_content):
            for siman_num, siman in enumerate(mitzvah):
                for segment_num, segment in enumerate(siman):
                    pass

    '''