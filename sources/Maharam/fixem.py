# -*- coding: utf-8 -*-
import re
import os
import pdb
'''
files = ["kiddushin"]

for file in files:
    input = open(file+".txt",'r')
    output = open(file+"2.txt",'w')
    storage = ""
    for line in input:
        line = line.replace("@22", "@11")
        line = line.replace('@11ע"ב', "@11 ")
        if line.find("@11")>=0:
            if len(storage)>0:
                storage = storage.replace("\n","")
                storage += '\n'
                output.write(storage)
                storage = ""
        storage += line
    if len(storage)>=0:
        storage = storage.replace("\n","")
        storage += '\n'
        output.write(storage)

output.close()
input.close()
pdb.set_trace()
'''
#avodah zarah not working
files = ["avodah zarah"]
p = re.compile('@\d\dע"\ב')
for file in files:
    new_file = open(file+"2.txt", 'w')
    f = open(file+".txt", 'r')
    for line in f:
        no_match = True
        line = line.replace("@66", "@11").replace("@33", "")
        words = line.split(" ")
        for word in words:
            if p.match(word):
                no_match = False
                match = p.match(word).group(0)
                paras = line.split(match)
                if len(paras) == 3 and len(paras[0])==0:
                    para_0 = paras[1]
                    para_1 = paras[2]
                elif len(paras) == 2:
                    para_1 = paras[1]
                    para_0 = paras[0]

                if len(paras) == 1:
                    new_file.write(para_0)
                elif len(paras) == 2:
                    new_file.write(para_0)
                    new_file.write("\n")
                    if para_1.find("@55")==0:
                        print "yes"
                        para_1 = para_1[3:]
                    para_1 = "@11"+para_1
                    #second and third word may have tags
                    words_para = para_1.split(" ")
                    para_1 = ""
                    count = 0
                    for count, word in enumerate(words_para):
                        if count == 1 or count == 2:
                            para_1 += word.replace("@55","").replace("@44","") + " "
                        else:
                            para_1 += word + " "
                    new_file.write(para_1)
                elif len(paras)>2 and len(paras[0])>0:
                    pdb.set_trace()
                break
        if no_match:
            print file
            new_file.write(line)
    new_file.close()



