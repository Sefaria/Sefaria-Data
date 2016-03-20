# -*- coding: utf-8 -*-
import json
import re
import sys
from sefaria.model import *
sys.path.insert(1, '../sources/genuzot')
import helperFunctions as Helper
import hebrew

mas = str(sys.argv[1])
shas = TextChunk(Ref("Tosafot on %s" %mas), "he").text
print len(shas)
newShas =[]
#try:
for daf in shas:
    newDaf=[]
    for line in daf:
        newLine=[]
        for DH in line:
            if "-" not in DH:
                new_dh = re.sub(ur"\.", " -", DH, count = 1)
            else:
                new_dh =DH
            newLine.append(new_dh)
        newDaf.append(newLine)
    newShas.append(newDaf)
#except Exception as e:
 #   print "%s did not work" %mas

#print newShas[3][0][0]

text_whole = {
        "title": 'Tosafot'  ,
        "versionTitle": "Wikisource Tosafot",
        "versionSource":  "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
        "language": "he",
        "text": newShas,
    }
    #save
Helper.mkdir_p("preprocess_json/")
with open("preprocess_json/Tosafot_on_{}.json".format(mas), 'w') as out:
    json.dump(text_whole, out)



#Helper.createBookRecord(book_record())
with open("preprocess_json/Tosafot_on_%s.json" %mas, 'r') as filep:
    file_text = filep.read()
mas = re.sub("_"," ", mas.strip())
Helper.postText("Tosafot on {}".format(mas) , file_text, False)
