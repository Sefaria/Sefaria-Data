# -*- coding: utf-8 -*-

import re
import os
from sefaria.model import *

if __name__ == "__main__":
    files = [file.replace(".txt", "").decode('utf-8') for file in os.listdir("./hebrew") if not file.endswith("2.txt") and file.endswith(".txt")]
    for file in files:
        print file
        f = open("./hebrew/"+file+".txt", 'r')
        try:
            he_title = file.split(" ")[-1]
            title = library.get_index(he_title).title
        except:
            he_title = " ".join(file.split(" ")[-2:])
            title = library.get_index(he_title).title

        arr_text = []
        for count, line in enumerate(f):
            line = line.replace("\n", "").replace("\r", "")
            if len(line.replace(" ", "")) == 0:
                continue
            no_match = True
            line = line.replace("@66", "@11", 1).replace("@33", "").replace("\n", "").replace("\r", "")
            chid_agadot = 'ח"א' in " ".join(line.split(" ")[0:2])
            re.split('@\d+ע"ב', line)
            lines = line.split('@44ע"ב')
            if len(lines[0]) == 0:
                continue
            for count, line in enumerate(lines):
                if lines[count].startswith("@99") or lines[count].startswith("@22"):
                    lines[count] = ""
                    continue
                while lines[count][0] == ' ':
                    lines[count] = lines[count][1:]

                if line.find("@11") != 0 and line.find("@00") == -1:
                    if chid_agadot:
                        lines[count] = "@11" + 'ח"א ' + line
                    else:
                        lines[count] = "@11"+line
            arr_text += lines
        f.close()
        f = open("./"+title+".txt", 'w')
        for line in arr_text:
            if len(line) == 0:
                continue
            while line.rfind("@11") > 2:
                pos = line.rfind("@11")
                assert line[0:pos].rfind("@11") == 0 or line.find("@00") == 0 or line.find("@99") is 0, line[0:pos]
                f.write(line[0:pos]+"\n")
                line = line[pos:]
            assert line.rfind("@11") is 0 or line.find("@00") is 0 or line.find("0") is 0, line.rfind("@11")
            f.write(line+"\n")
        f.close()