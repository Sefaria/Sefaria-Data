# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-

import re
import os
if __name__ == "__main__":
    files = [file.replace(".txt", "") for file in os.listdir(".") if not file.endswith("2.txt") and file.endswith(".txt") and not file.startswith("comm_wout")]
    files = ["yevamot", "kiddushin"]
    for file in files:
        print file
        f = open(file+".txt", 'r')
        arr_text = []
        for count, line in enumerate(f):
            line = line.replace("\n", "").replace("\r", "")
            if len(line) == 0:
                continue
            no_match = True
            line = line.replace("@33", "").replace("\n", "").replace("\r", "")
            lines = line.split('@44ע"ב')
            for count, line in enumerate(lines):
                if lines[count].startswith("@99") or lines[count].startswith("@22"):
                    lines[count] = ""
                    continue
                while lines[count][0] != '@':
                    lines[count] = lines[count][1:]
                if line.find("@11") != 0 and line.find("@00") == -1:
                    lines[count] = "@11"+line
            arr_text += lines
        f.close()
        f = open(file+"2.txt", 'w')
        for line in arr_text:
            if len(line) == 0:
                continue
            while line.rfind("@11") > 2:
                pos = line.rfind("@11")
                assert line[0:pos].rfind("@11") == 0 or line.find("@00") == 0 or line.find("@99") is 0, line[0:pos]
                f.write(line[0:pos]+"\n")
                line = line[pos:]
            print line
            print line.find("@00")
            assert line.rfind("@11") is 0 or line.find("@00") is 0, line.rfind("@11")
            f.write(line+"\n")
        f.close()
'''
import re
import os
import pdb
files = os.curdir
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
pass
p = re.compile('@\d\dע"\ב')
for file in files:
    new_file = open(file+"22.txt", 'w')
    f = open(file, 'r')
    for line in f:
        no_match = True
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

                if len(paras)==1:
                    new_file.write(para_0)
                elif len(paras)==2:
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
                            para_1 += word.replace("@55","").replace("@44","").replace("@77","") + " "
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
'''