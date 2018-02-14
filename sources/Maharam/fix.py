# -*- coding: utf-8 -*-

import re
import os
if __name__ == "__main__":
    files = [file.replace(".txt", "") for file in os.listdir(".") if not file.endswith("2.txt") and file.endswith(".txt")]
    files = ["pesachim"]
    running_line = ""
    lines = []
    for file in files:
        for line in open("{}.txt".format(file)):
            line = line.replace("\n", "")
            if line.replace(" ", "").startswith("@22"):
                if len(running_line) > 0:
                    lines.append(running_line)
                running_line = line
            else:
                running_line += line
        if len(running_line) > 0:
            lines.append(line)


        lines.append(running_line)
        print file
        print len(lines)
        new_f = open("{}2.txt".format(file), 'w')
        for line in lines:
            temp_result = line.split('@22ע"ב')
            if len(temp_result) == 1:
                temp_result = line.split('@44ע"ב')
            line = line.replace("@11", "").replace("@22", "@11")
            if len(temp_result) == 1:
                new_f.write(line+"\n")
            else:
                new_f.write(temp_result[0]+"\n")
                new_f.write(temp_result[1]+"\n")