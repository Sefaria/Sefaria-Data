# -*- coding: utf-8 -*-
__author__ = 'stevenkaplan'
from sources.Maharsha.parse import *
import os
from sources.functions import post_text, post_link, post_index, convertDictToArray, post_term
from sefaria.model import *


if __name__ == "__main__":

    post_term({
        "name": "Maharam",
        "scheme": "commentary_works",
        "titles": [
            {
                "lang": "en",
                "text": "Maharam",
                "primary": True
            },
            {
                "lang": "he",
                "text": u'מהר"ם',
                "primary": True
            }
        ]

    }, server="http://ste.sefaria.org")

    files = [file for file in os.listdir(".") if file.endswith("2.txt")]
    bad_linking_files = ["chullin2.txt", "eruvin2.txt", "makkot2.txt"]
    bad_section_files = ['bava batra2.txt', 'ketubot2.txt', 'kiddushin2.txt', 'sanhedrin2.txt']
    other_files = [file for file in files if file not in bad_linking_files and file not in bad_section_files]
    title = "Maharam"
    heTitle = u"""מהר"ם"""
    start = False


    #files = bad_section_files + bad_linking_files
    #files = ["makkot2.txt"]
    for file in ["avodah zarah2.txt"]:
        print file
        masechet = file.replace("2.txt", "").title()
        obj = Maharsha(masechet, title, heTitle, "http://proto.sefaria.org")
        len_masechet = len(Ref(masechet).text('he').text)
        obj.parseText(open(file), len_masechet)
        if len(obj.comm_dict) > 0:
            obj.create_index(masechet)
            text_to_post = convertDictToArray(obj.comm_dict)
            send_text = {
                                "versionTitle": "Vilna Edition",
                                "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
                                "language": "he",
                                "text": text_to_post,
                        }
            post_text("{} on {}".format(title, masechet), send_text, "on", server=obj.server)
            obj.postLinks(masechet)