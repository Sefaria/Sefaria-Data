#encoding=utf-8
import django
django.setup()
import codecs
from sefaria.model import *
from sources.functions import *
import json
from sources.Kereti.kereti import *
for comm in ["Tiferet Yisrael", "Chiddushei Hilkhot Niddah"]:
    text = get_comm_text_in_files(["Tiferet Yisrael/{}.txt".format(comm)])
    for siman in text.keys():
        text[siman] = convertDictToArray(text[siman], empty="")
    text = convertDictToArray(text)
    version = {
        "text": text,
        "language": "he",
        "versionTitle": "Ashlei Ravrevei: Shulchan Aruch Yoreh Deah, Lemberg, 1888",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002097765"
    }
    post_text("{} on Shulchan Arukh, Yoreh De'ah".format(comm), version, index_count="on")
    links, other = create_dict(title=comm, files=["Tiferet Yisrael/Base Text.txt"], siman=111)
    post_link(links)