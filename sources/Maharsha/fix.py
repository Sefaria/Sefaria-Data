# -*- coding: utf-8 -*-

import re
import os
if __name__ == "__main__":
    files = [file.replace(".txt", "") for file in os.listdir(".") if not file.endswith("2.txt") and file.endswith(".txt")]
    for file in files:
        print file
        f = open(file+".txt", 'r')
        arr_text = []
        for count, line in enumerate(f):
            no_match = True
            line = line.replace("@66", "@11").replace("@33", "").replace("\n", "").replace("\r", "")
            lines = line.split('@44ע"ב')
            for count, line in enumerate(lines):
                if line.find("@11") != 0 and line.find("@00") != 0:
                    lines[count] = "@11"+line
            arr_text += lines
        f.close()
        f = open(file+"2.txt", 'w')
        for line in arr_text:
            while line.rfind("@11") > 2:
                pos = line.rfind("@11")
                assert line[0:pos].rfind("@11") == 0 or line.find("@00") == 0, line[0:pos]
                f.write(line[0:pos]+"\n")
                line = line[pos:]
            assert line.rfind("@11") == 0 or line.find("@00") == 0
            f.write(line+"\n")
        f.close()